import logging
import random
from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.imaging.dedicated_manifest import load_manifest as load_dedicated_manifest
from app.imaging.stock_manifest import load_manifest
from app.models.web import EventImage

logger = logging.getLogger(__name__)

_MANIFEST = load_manifest()
_DEDICATED_MANIFEST = load_dedicated_manifest()
_DEDICATED_BY_SLUG = {e["event_slug"]: e for e in _DEDICATED_MANIFEST}
_TERRAIN_BUCKETS = ("trail", "road", "mixed")
_DEFAULT_TERRAIN = "mixed"


def _normalize_terrain(terrain) -> str:
    if terrain is None:
        return _DEFAULT_TERRAIN
    t = str(terrain).strip().lower()
    return t if t in _TERRAIN_BUCKETS else _DEFAULT_TERRAIN


def _pick_stock(terrain: str) -> dict:
    bucket = [e for e in _MANIFEST if e["terrain"] == terrain]
    if not bucket:
        bucket = [e for e in _MANIFEST if e["terrain"] == _DEFAULT_TERRAIN]
    if not bucket:
        raise RuntimeError("stock manifest has no entries")
    return random.choice(bucket)


class EventImageService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_for_events(
        self,
        events: Iterable,
        dedicated_slugs: set[str] | None = None,
    ) -> dict[int, EventImage]:
        """Resolve one EventImage per event, inserting stock rows as needed.

        Pass `dedicated_slugs` to enable the one-shot terrain self-heal on
        already-stored rows (see `_heal_defaulted_terrain`). Omitting it
        disables healing, so callers that lack the slug cache stay safe.
        """
        events = list(events)
        event_ids = [int(e["event_id"]) for e in events if e.get("event_id") is not None]
        if not event_ids:
            return {}

        existing = {
            row.event_id: row
            for row in self.db.execute(
                select(EventImage).where(EventImage.event_id.in_(event_ids))
            ).scalars()
        }

        if dedicated_slugs is not None and existing:
            self._heal_defaulted_terrain(events, existing, dedicated_slugs)

        missing = [e for e in events if int(e["event_id"]) not in existing]
        if not missing:
            return existing

        rows_to_insert = []
        for e in missing:
            terrain = _normalize_terrain(e.get("terrain_type"))
            slot = _pick_stock(terrain)
            rows_to_insert.append({
                "event_id": int(e["event_id"]),
                "event_slug": e.get("event_slug") or "",
                "kind": "stock",
                "stock_filename": slot["filename"],
                "terrain": terrain,
                "attribution_name": slot["photographer_name"],
                "attribution_url": slot["photographer_url"],
                "attribution_source_url": slot["photo_url"],
            })

        stmt = pg_insert(EventImage).values(rows_to_insert).on_conflict_do_nothing(
            index_elements=["event_id"]
        )
        self.db.execute(stmt)
        self.db.commit()

        missing_ids = [r["event_id"] for r in rows_to_insert]
        for row in self.db.execute(
            select(EventImage).where(EventImage.event_id.in_(missing_ids))
        ).scalars():
            existing[row.event_id] = row

        logger.info(f"Assigned stock tiles for {len(missing_ids)} new events")
        return existing

    def _heal_defaulted_terrain(
        self,
        events: list,
        existing: dict[int, EventImage],
        dedicated_slugs: set[str],
    ) -> int:
        """Repair stock rows that locked in `mixed` from a NULL source terrain.

        `_normalize_terrain(None)` returns `mixed`, and rows are inserted once
        on first render and never revisited, so any event first seen before the
        scraper published its terrain kept a `mixed_*` photo permanently. This
        heals such a row the next time the event renders with a real terrain.

        Deliberately **one-shot in one direction**: only rows currently stored
        as `mixed` are candidates, and only a source terrain of `road`/`trail`
        triggers a rewrite. Two consequences, both intended:

        - `terrain='mixed'` is the observable signature of the NULL default. A
          legitimately-mixed event has a source terrain that normalizes to
          `mixed` too, so it never triggers — no `terrain_source` column and
          therefore no migration is needed to tell the two apart.
        - Once repaired to `road`/`trail` a row can never be re-touched, so
          events whose races carry conflicting terrain values cannot flap on
          every page view depending on which race row is read first.

        A stored `road`/`trail` whose source now reads `mixed` is left alone —
        that direction was judged a scraper regression when
        `scripts/backfill_event_image_terrain.py` shipped, and this keeps the
        same policy.
        """
        source_terrain = {
            int(e["event_id"]): e.get("terrain_type")
            for e in events
            if e.get("event_id") is not None
        }

        updates: list[dict] = []
        for event_id, row in existing.items():
            if row.kind != "stock" or row.terrain != _DEFAULT_TERRAIN:
                continue
            # The resolver serves dedicated events from their own photo and
            # ignores stock_filename, so repairing one would swap in a stock
            # photographer's credit under a dedicated image — wrong attribution
            # on a live hero until the next startup refresh.
            if row.event_slug in dedicated_slugs:
                continue
            raw = source_terrain.get(event_id)
            if raw is None:
                continue
            new_terrain = _normalize_terrain(raw)
            if new_terrain == _DEFAULT_TERRAIN:
                continue

            slot = _pick_stock(new_terrain)
            updates.append({
                "event_id": event_id,
                "terrain": new_terrain,
                "stock_filename": slot["filename"],
                # Credits must move with the file or the page shows the wrong
                # photographer — a licensing problem, not a cosmetic one.
                "attribution_name": slot["photographer_name"],
                "attribution_url": slot["photographer_url"],
                "attribution_source_url": slot["photo_url"],
            })

        if not updates:
            return 0

        # Committed on a short-lived Session of its own, NOT self.db. Healing is
        # opportunistic maintenance, so it is correct for it to be
        # transactionally independent of the render — that argument stands on
        # its own and is why this stays.
        #
        # It is no longer load-bearing for a second reason. Committing the
        # request's session expires every object it has loaded, including the
        # core.Race rows the caller is still iterating, and re-reading an
        # expired Race used to fail outright: the view's mv_id is `uuid` and
        # the model mapped it as Text, so the load-by-PK 500'd the page.
        # Fixed at the cause in W-007 (app/models/core.py) — a commit here
        # would no longer take the page down.
        with SessionLocal() as heal_db:
            for u in updates:
                heal_db.execute(
                    update(EventImage)
                    .where(EventImage.event_id == u["event_id"])
                    .values(**{k: v for k, v in u.items() if k != "event_id"})
                )
            heal_db.commit()

        # Mirror the writes onto the rows the caller already holds so this
        # request renders the healed image rather than the stale one.
        for u in updates:
            row = existing[u["event_id"]]
            for k, v in u.items():
                if k != "event_id":
                    setattr(row, k, v)
            logger.info(
                "Healed defaulted terrain for %s: mixed -> %s",
                row.event_slug, u["terrain"],
            )

        return len(updates)

    def refresh_dedicated_attributions(self, dedicated_slugs: set[str]) -> int:
        """Update attribution columns for every event marked dedicated.

        Called once at startup, right after the dedicated slug cache is
        loaded from GCS. A row is only written when at least one of the
        three attribution fields would change, so idempotent restarts
        are a no-op after the first run.
        """
        if not dedicated_slugs or not _DEDICATED_BY_SLUG:
            return 0

        rows = self.db.execute(
            select(EventImage).where(EventImage.event_slug.in_(dedicated_slugs))
        ).scalars().all()

        updated = 0
        for row in rows:
            entry = _DEDICATED_BY_SLUG.get(row.event_slug)
            if entry is None:
                continue
            name = entry["photographer_name"]
            url = entry["photographer_url"]
            source_url = entry["photo_url"]
            if (
                row.attribution_name == name
                and row.attribution_url == url
                and row.attribution_source_url == source_url
            ):
                continue
            row.attribution_name = name
            row.attribution_url = url
            row.attribution_source_url = source_url
            updated += 1

        if updated:
            self.db.commit()
        return updated
