"""One-shot backfill for web.event_images.terrain (and stock_filename).

Fixes rows that silently defaulted to terrain='mixed' at insert time
because the source core.v_denormalized_event_data_upcoming row had a
NULL terrain_type (the common case for TBC occurrences). See
docs/ARCHITECTURE.md and app/services/event_image_service.py.

Targets stock rows where source terrain_type is now populated and
disagrees with the assigned terrain. Deliberate exclusions:

- source terrain_type = 'other': _normalize_terrain maps 'other' -> 'mixed'
  by design, so those are not bugs.
- rows currently assigned 'trail' whose source now says 'mixed': the only
  way a row ever got 'trail' is that the source said 'trail' at insert
  time and later flipped to 'mixed'. Manual inspection judged those to
  be scraper regressions, not fixes to preserve. Skipped.
- rows whose event_slug is a dedicated slug: resolver.py bypasses
  stock_filename for dedicated events, so terrain has no user-facing
  effect on those.

Each fixed row gets a fresh stock_filename picked at random from the
correct terrain bucket (same picker as insert time) plus the matching
attribution columns from the stock manifest, so the row stays internally
consistent.

Dry-run by default. Prints per-row before/after. Pass --apply to commit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import text

from app.db import SessionLocal
from app.imaging.dedicated_index import load_dedicated_slugs
from app.services.event_image_service import _pick_stock


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="commit the changes. Without this flag the script only prints.",
    )
    args = parser.parse_args()

    dedicated_slugs = load_dedicated_slugs()
    print(f"loaded {len(dedicated_slugs)} dedicated slugs (will be skipped)")

    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT ei.id,
                   ei.event_slug,
                   ei.terrain          AS assigned_terrain,
                   ei.stock_filename   AS assigned_filename,
                   lower(r.terrain_type) AS source_terrain,
                   r.occurrence_status
            FROM web.event_images ei
            JOIN core.v_denormalized_event_data_upcoming r
              ON r.event_id::int = ei.event_id
            WHERE ei.kind = 'stock'
              AND r.terrain_type IS NOT NULL
              AND lower(r.terrain_type) IN ('road', 'trail', 'mixed')
              AND lower(r.terrain_type) <> ei.terrain
              AND NOT (ei.terrain = 'trail' AND lower(r.terrain_type) = 'mixed')
        """)).all()

        targeted = [r for r in rows if r.event_slug not in dedicated_slugs]
        skipped_dedicated = len(rows) - len(targeted)

        print(
            f"found {len(rows)} candidate rows, "
            f"{skipped_dedicated} skipped as dedicated, "
            f"{len(targeted)} to update"
        )

        by_status: dict[str, int] = {}
        for r in targeted:
            by_status[r.occurrence_status] = by_status.get(r.occurrence_status, 0) + 1
        for status, n in sorted(by_status.items()):
            print(f"  {status}: {n}")

        # De-dupe: the join with the MV can return multiple rows per
        # event_image (one per race in the MV). We only want to touch each
        # event_images row once.
        seen: set[int] = set()
        updates: list[tuple[int, str, str, str, str, dict]] = []
        for r in targeted:
            if r.id in seen:
                continue
            seen.add(r.id)
            slot = _pick_stock(r.source_terrain)
            updates.append((
                r.id,
                r.event_slug,
                r.assigned_terrain,
                r.source_terrain,
                r.assigned_filename,
                slot,
            ))

        print(f"unique event_images rows to update: {len(updates)}")
        print()

        for row_id, slug, old_terrain, new_terrain, old_file, slot in updates:
            print(
                f"id={row_id} slug={slug} "
                f"{old_terrain} -> {new_terrain}, "
                f"file: {old_file} -> {slot['filename']}"
            )

        if not args.apply:
            print()
            print(f"DRY RUN. {len(updates)} rows would be updated. "
                  f"Re-run with --apply to commit.")
            return 0

        print()
        print(f"applying {len(updates)} updates...")
        for row_id, _slug, _old_t, new_terrain, _old_f, slot in updates:
            db.execute(text("""
                UPDATE web.event_images
                   SET terrain = :terrain,
                       stock_filename = :filename,
                       attribution_name = :name,
                       attribution_url = :url,
                       attribution_source_url = :source_url
                 WHERE id = :id
            """), {
                "terrain": new_terrain,
                "filename": slot["filename"],
                "name": slot["photographer_name"],
                "url": slot["photographer_url"],
                "source_url": slot["photo_url"],
                "id": row_id,
            })
        db.commit()
        print(f"committed {len(updates)} updates")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
