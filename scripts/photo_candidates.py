"""Ranked shortlist of events worth a dedicated photo.

Read-only. Answers "what should I shoot for next" before any Unsplash
work starts, so the expensive step (searching and picking a photo by eye)
is only spent on events where it changes what visitors see.

Three signals, all already in the database:

- engagement (going_count, interested_count) — the index route sorts tiles
  by exactly this, so high-engagement events are the most-seen tiles on the
  site and the ones whose generic stock photo is most visible.
- stock collision count — how many other events share this event's
  stock_filename. resolver.py hashes events into a terrain bucket by md5,
  so with 53 stock files across ~233 events every file is shared. Two
  high-engagement events colliding on the same photo is the most visible
  duplication the site can produce.
- terrain bucket pressure — mixed holds 11 files against trail's 22 and
  road's 20, so mixed events collide roughly twice as hard. Reported as
  context, not as a case for growing the buckets: stock is the fallback
  for events with no location and events where no suitable photo exists,
  so a successful conversion run shrinks what stock has to cover.

Events that already have a dedicated photo are excluded: they are the
finished work, not the backlog.

Ranking is engagement first, collisions second — a tile nobody looks at
does not get better by being unique. Pass --by-collision to invert that
when the goal is deduplicating the grid rather than dressing the top of it.

Dedicated photos only pay off where the location is recognisable (the
existing 13 are all landmarks: Brandenburg Gate, Parthenon, Big Ben...).
This script cannot judge that, so it ranks by impact and leaves the
recognisability call to the human reading the list.

The location shown is read from RaceService itself, so it is exactly the
string the home page tile renders (race_location off the earliest-dated
race, not an aggregate). A photo is picked for the event as the site
presents it, so the search query should start from the rendered value.
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
from app.imaging.stock_manifest import load_manifest as load_stock_manifest
from app.services.race_service import RaceFilters, RaceService

# Below this many files, a terrain bucket's events collide hard enough to be
# worth noting when choosing what to convert next.
THIN_BUCKET = 15


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="how many candidates to print. Default 20.",
    )
    parser.add_argument(
        "--by-collision",
        action="store_true",
        help="rank by stock collision count instead of engagement.",
    )
    parser.add_argument(
        "--country",
        help="restrict to one country. Despite the name, event_country_code "
             "holds lowercase full names ('germany'), not ISO codes.",
    )
    args = parser.parse_args()

    dedicated_slugs = load_dedicated_slugs()
    print(f"loaded {len(dedicated_slugs)} dedicated slugs (excluded from the list)")

    db = SessionLocal()
    try:
        # Locations come from RaceService, not from a reimplementation of its
        # grouping. An earlier version rebuilt the "earliest-dated race" logic
        # in SQL and disagreed with the tile on 11 events — ties on the sort
        # key resolve differently in Postgres than in the Python first-see
        # loop. Calling the same code the index route calls makes the value
        # the rendered one by construction.
        tile_locations = {
            item.event_slug: item.location
            for item in RaceService(db).list_races(RaceFilters())
        }

        # One row per event. The MV is race-grained, so engagement is joined
        # per occurrence and the event fields are read via MIN/MAX over rows
        # that carry identical values at event grain (see ARCHITECTURE.md,
        # "The core read model") rather than off an arbitrary first row.
        #
        # event_id and occurrence_id are both text in the MV (it projects
        # everything as text) but integer in web.event_images and
        # web.attendance, so both need an explicit ::int before they join.
        rows = db.execute(text("""
            WITH events AS (
                SELECT r.event_id::int              AS event_id,
                       MIN(r.event_slug)            AS event_slug,
                       MIN(r.event_display_name)    AS name,
                       MIN(r.event_country_code)    AS country,
                       MIN(r.occurrence_id::int)    AS occurrence_id,
                       MIN(r.occurrence_status)     AS occurrence_status
                FROM core.v_denormalized_event_data_upcoming r
                GROUP BY r.event_id::int
            ),
            engagement AS (
                SELECT a.occurrence_id,
                       COUNT(*) FILTER (WHERE a.status = 'going')      AS going_count,
                       COUNT(*) FILTER (WHERE a.status = 'interested') AS interested_count
                FROM web.attendance a
                GROUP BY a.occurrence_id
            ),
            collisions AS (
                -- Dedicated events keep a stale stock_filename (resolver.py
                -- serves them by slug and never reads the column), so their
                -- rows are excluded or they inflate every count they touch.
                SELECT ei.stock_filename,
                       COUNT(*) AS shared_by
                FROM web.event_images ei
                WHERE ei.kind = 'stock'
                  AND ei.stock_filename IS NOT NULL
                  AND NOT (ei.event_slug = ANY(:dedicated))
                GROUP BY ei.stock_filename
            )
            SELECT e.event_slug,
                   e.name,
                   e.country,
                   e.occurrence_status,
                   COALESCE(g.going_count, 0)       AS going_count,
                   COALESCE(g.interested_count, 0)  AS interested_count,
                   ei.terrain                       AS terrain,
                   ei.stock_filename                AS stock_filename,
                   COALESCE(c.shared_by, 0)         AS shared_by
            FROM events e
            LEFT JOIN engagement g ON g.occurrence_id = e.occurrence_id
            LEFT JOIN web.event_images ei ON ei.event_id = e.event_id
            LEFT JOIN collisions c ON c.stock_filename = ei.stock_filename
            -- ::text because a bare NULL parameter has no inferrable type.
            -- lower() so --country Germany matches the stored 'germany'.
            WHERE (CAST(:country AS text) IS NULL OR e.country = lower(:country))
        """), {
            "country": args.country,
            "dedicated": sorted(dedicated_slugs),
        }).all()

        candidates = [r for r in rows if r.event_slug not in dedicated_slugs]
        skipped = len(rows) - len(candidates)

        print(
            f"{len(rows)} events, {skipped} already dedicated, "
            f"{len(candidates)} candidates"
        )

        if args.by_collision:
            candidates.sort(
                key=lambda r: (-r.shared_by, -r.going_count, -r.interested_count)
            )
            print("ranked by stock collision count")
        else:
            candidates.sort(
                key=lambda r: (-r.going_count, -r.interested_count, -r.shared_by)
            )
            print("ranked by engagement")

        # Bucket pressure: how thin is each terrain's stock library. Read from
        # the manifest, not from the candidate rows — under --country the
        # filtered set only sees the files its own events happen to hash to,
        # which would report a full bucket as thin.
        bucket_files: dict[str, set[str]] = {}
        for entry in load_stock_manifest():
            terrain = entry.get("terrain")
            if terrain:
                bucket_files.setdefault(terrain, set()).add(entry["filename"])

        print()
        for r in candidates[: args.limit]:
            engagement = f"{r.going_count}g/{r.interested_count}i"
            tbc = " [TBC]" if r.occurrence_status == "tbc" else ""
            # No location means the search step has no query to build, so
            # flag it rather than letting it read as an ordinary candidate.
            location = (
                tile_locations.get(r.event_slug) or "NO LOCATION — cannot search"
            )
            # events_on_file, not shared_with: the count includes this event,
            # so 1 means the file is unique to it.
            print(
                f"{engagement:>10}  events_on_file={r.shared_by:<3} "
                f"{r.terrain or '?':<6} {r.event_slug}{tbc}"
            )
            print(f"{'':>10}  {r.name} — {location}, {r.country or '??'}")

        print()
        print("terrain buckets (stock files in the manifest):")
        for terrain, files in sorted(bucket_files.items()):
            # Reported as context for how hard the remaining stock events
            # collide, not as a recommendation to grow the bucket: stock is
            # the fallback now, so a successful conversion run means these
            # files serve fewer events over time, not more.
            note = "  <- thin, collisions hit harder here" if len(files) < THIN_BUCKET else ""
            print(f"  {terrain:<6} {len(files)} files{note}")

        no_engagement = sum(
            1 for r in candidates if r.going_count == 0 and r.interested_count == 0
        )
        no_location = sum(
            1 for r in candidates if not tile_locations.get(r.event_slug)
        )
        print()
        print(
            f"{no_engagement} of {len(candidates)} candidates have zero engagement. "
            "Ranking below that line is effectively arbitrary."
        )
        print(
            f"{no_location} have no race_location at all and cannot be searched "
            "without picking a query by hand."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
