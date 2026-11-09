"""One-shot backfill for web.event_images.attribution_{name,url,source_url}.

Populates the three attribution columns from the two manifests:

- Rows whose event_slug is in app/imaging/dedicated_manifest.json get the
  dedicated photographer name and the two Unsplash URLs.
- Every other row is treated as stock: its stock_filename is looked up in
  app/imaging/stock_manifest.json and the matching photographer name +
  URLs are written.

Idempotent — reruns overwrite with the same values, so it's safe to run
after `python -m app.imaging` publishes a new stock slot or after a new
dedicated photo is added to the manifest.

Prints per-source counts and lists any rows that could not be matched.
Exits non-zero if any row was un-matched, so the caller can spot a
mismatch between the DB and the manifests.

Runs against whatever DATABASE_URL is in the environment / .env — the
same connection the app uses.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `app` importable when run as `python scripts/backfill_...`
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select

from app.db import SessionLocal
from app.imaging.dedicated_manifest import load_manifest as load_dedicated
from app.imaging.stock_manifest import load_manifest as load_stock
from app.models.web import EventImage


def _index_by(entries: list[dict], key: str) -> dict[str, dict]:
    return {e[key]: e for e in entries}


def main() -> int:
    stock_by_filename = _index_by(load_stock(), "filename")
    dedicated_by_slug = _index_by(load_dedicated(), "event_slug")

    print(
        f"loaded stock manifest ({len(stock_by_filename)} entries), "
        f"dedicated manifest ({len(dedicated_by_slug)} entries)"
    )

    updated_stock = 0
    updated_dedicated = 0
    unmatched: list[tuple[int, str, str | None]] = []

    db = SessionLocal()
    try:
        rows = db.execute(select(EventImage)).scalars().all()
        print(f"scanning {len(rows)} event_images rows")

        for row in rows:
            dedicated_entry = dedicated_by_slug.get(row.event_slug or "")
            if dedicated_entry is not None:
                row.attribution_name = dedicated_entry["photographer_name"]
                row.attribution_url = dedicated_entry["photographer_url"]
                row.attribution_source_url = dedicated_entry["photo_url"]
                updated_dedicated += 1
                continue

            stock_entry = stock_by_filename.get(row.stock_filename or "")
            if stock_entry is not None:
                row.attribution_name = stock_entry["photographer_name"]
                row.attribution_url = stock_entry["photographer_url"]
                row.attribution_source_url = stock_entry["photo_url"]
                updated_stock += 1
                continue

            unmatched.append((row.id, row.event_slug, row.stock_filename))

        db.commit()
    finally:
        db.close()

    print(f"updated {updated_stock} stock rows, {updated_dedicated} dedicated rows")
    if unmatched:
        print(f"warning, {len(unmatched)} rows had no manifest match:")
        for row_id, slug, filename in unmatched:
            print(f"  id={row_id} event_slug={slug} stock_filename={filename}")
        return 1
    print("all rows matched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
