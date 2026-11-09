import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urlencode

from sqlalchemy import Integer, and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.core import Race
from app.schemas.race import EventListItem
from app.services.attendance_service import is_locked

logger = logging.getLogger(__name__)

_NORDIC = {"finland", "sweden", "norway", "iceland", "denmark"}
_COASTAL = {"portugal", "ireland", "croatia"}

# Display labels for the race_format slugs the MV emits. Slugs not listed
# here are title-cased by format_label rather than dropped, so a new
# scraper value surfaces as readable text instead of vanishing.
_FORMAT_LABELS = {
    "backyard_ultra": "Backyard Ultra",
    "relay": "Relay",
    "timed": "Timed",
    "virtual": "Virtual",
    "stage_race": "Stage Race",
    "multi_day": "Multi-Day",
    "self_supported": "Self-Supported",
}

# Formats offered in the advanced filter panel, and the whitelist incoming
# ?format= values are checked against. Deliberately a static list rather than
# a DISTINCT query over the MV: the column is a JSON array string, so a
# DISTINCT would return array literals ('["relay", "timed"]') rather than
# slugs, and would need per-request parsing to be useful. These four are what
# the scraper currently emits — when it starts emitting a new slug, add it
# here (and to _FORMAT_LABELS if the title-cased default reads badly).
RACE_FORMAT_CHOICES: list[tuple[str, str]] = [
    ("relay", _FORMAT_LABELS["relay"]),
    ("timed", _FORMAT_LABELS["timed"]),
    ("backyard_ultra", _FORMAT_LABELS["backyard_ultra"]),
    ("virtual", _FORMAT_LABELS["virtual"]),
]

RACE_FORMAT_SLUGS = frozenset(slug for slug, _ in RACE_FORMAT_CHOICES)


@dataclass
class RaceFilters:
    distance_min: Optional[float] = None
    distance_max: Optional[float] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    country: Optional[str] = None
    search: Optional[str] = None
    # Advanced filters — surfaced behind the toggle on the index page.
    formats: list[str] = field(default_factory=list)
    cutoff_min: Optional[float] = None
    cutoff_max: Optional[float] = None


def format_date_range(start: Optional[date], end: Optional[date]) -> str:
    if start is None:
        return "—"
    if end is None or end == start:
        return start.strftime("%-d %b %Y")
    if start.year != end.year:
        return f"{start.strftime('%-d %b %Y')} – {end.strftime('%-d %b %Y')}"
    if start.month != end.month:
        return f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y')}"
    return f"{start.strftime('%-d')} – {end.strftime('%-d %b %Y')}"


def gcal_url(title: str, start: Optional[date], end: Optional[date], location: Optional[str]) -> Optional[str]:
    """Google Calendar "add event" link for an all-day event; None without a start date."""
    if start is None:
        return None
    # All-day dates take an exclusive end, so the last day + 1.
    last = end if end is not None and end > start else start
    params = {"action": "TEMPLATE", "text": title, "dates": f"{start:%Y%m%d}/{last + timedelta(days=1):%Y%m%d}"}
    if location:
        params["location"] = location
    return "https://calendar.google.com/calendar/render?" + urlencode(params, safe="/")


def event_location(rows) -> Optional[str]:
    """An event's location (W-070): `event_location` (HQ), else the first race in
    first-see order (race_date, then mv_id) with a `race_location`, else None.
    Takes any rows exposing those four attributes; sorts them itself."""
    for r in rows:
        if r.event_location:
            return r.event_location
    for r in sorted(rows, key=lambda r: (r.race_date is None, r.race_date or date.min, r.mv_id)):
        if r.race_location:
            return r.race_location
    return None


def format_tbc_expected(year: Optional[int], month: Optional[int]) -> str:
    if year is None:
        return "TBC"
    if month is None or not 1 <= month <= 12:
        return f"{year} (TBC)"
    return f"{date(year, month, 1).strftime('%B')} {year} (TBC)"


def parse_race_formats(raw: Optional[str]) -> list[str]:
    """Turn the MV's race_format text into a list of format slugs.

    The column holds a JSON array serialised as text ('["relay", "timed"]').
    Returns [] for anything unusable — NULL, blank, malformed JSON, a JSON
    scalar instead of a list — so callers never need to guard.
    """
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        logger.warning("Unparseable race_format value: %r", raw)
        return []
    if not isinstance(parsed, list):
        return []
    return [v.strip() for v in parsed if isinstance(v, str) and v.strip()]


def format_label(slug: str) -> str:
    """Display label for a race_format slug. Unknown slugs are title-cased."""
    return _FORMAT_LABELS.get(slug, slug.replace("_", " ").title())


def race_format_labels(raw: Optional[str]) -> list[str]:
    """parse_race_formats + format_label, deduped, in a stable order."""
    seen: dict[str, None] = {}
    for slug in parse_race_formats(raw):
        seen.setdefault(format_label(slug), None)
    return list(seen)


def truncate_for_meta(text: Optional[str], limit: int = 160) -> Optional[str]:
    """Shorten prose to fit a <meta name="description"> without cutting a word.

    Search engines display roughly 155-160 characters. Source descriptions run
    271-490 chars, so nearly every one needs trimming. Cuts on the last space
    before the limit and appends an ellipsis; returns the text untouched when
    it already fits.
    """
    if not text:
        return None
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    window = collapsed[:limit]
    # No space to break on means one absurdly long token — hard-cut instead of
    # returning the whole window, so the limit always holds.
    cut = window.rsplit(" ", 1)[0] if " " in window else window[: limit - 1]
    return f"{cut.rstrip(',;:.—- ')}…"


def assign_gradient(terrain_type: Optional[str], country: Optional[str]) -> str:
    c = (country or "").lower()
    if c in _NORDIC:
        return "nordic"
    if c in _COASTAL:
        return "coastal"
    t = (terrain_type or "").lower()
    if t == "trail":
        return "trail"
    if t == "road":
        return "road"
    if t in ("mixed", "other"):
        return "mixed"
    return "road"


class RaceService:
    def __init__(self, db: Session):
        self.db = db

    def list_races(self, filters: RaceFilters) -> list[EventListItem]:
        logger.info("Listing races with filters")

        yesterday = date.today() - timedelta(days=1)
        current_month_start = date.today().replace(day=1)

        # First of the expected month (December if null), the date a TBC
        # occurrence is judged by.
        expected_date = func.make_date(
            Race.occurrence_year.cast(Integer),
            func.coalesce(Race.occurrence_expected_month.cast(Integer), 12),
            1,
        )
        # Row order before grouping: real race_date if present, else the
        # expected date. Kept on race_date for TBC rows too — their
        # inherited dates are the only thing ordering an event's races, and
        # first-see reads the first row.
        sort_key = func.coalesce(Race.race_date, expected_date)
        # Date filters judge a TBC row by its expected date even when it has
        # a race_date: that one is last edition's, inherited, not a claim
        # about this occurrence (scraper contract, 2026-09-05).
        filter_key = case(
            (Race.occurrence_status == "tbc", expected_date),
            else_=sort_key,
        )

        stmt = select(Race).where(
            or_(
                and_(
                    Race.race_date.isnot(None),
                    Race.race_date >= yesterday,
                ),
                and_(
                    Race.occurrence_status == "tbc",
                    Race.occurrence_year.isnot(None),
                    func.make_date(
                        Race.occurrence_year.cast(Integer),
                        func.coalesce(Race.occurrence_expected_month.cast(Integer), 12),
                        1,
                    ) >= current_month_start,
                ),
            )
        )

        if filters.date_from is not None:
            stmt = stmt.where(filter_key >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(filter_key <= filters.date_to)
        if filters.country:
            stmt = stmt.where(Race.event_country_code.ilike(filters.country))
        if filters.search:
            term = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(
                    Race.event_display_name.ilike(term),
                    Race.event_name.ilike(term),
                    Race.race_location.ilike(term),
                    Race.terrain_type.ilike(term),
                )
            )

        # mv_id breaks sort_key ties so first-see doesn't follow the query
        # plan. Same final key as the profile (W-027).
        stmt = stmt.order_by(sort_key.asc(), Race.mv_id)

        rows = self.db.execute(stmt).scalars().all()

        # Group rows by event_id, collecting all distances
        # Use an ordered dict to preserve date ordering (first occurrence = earliest date)
        events: dict[str, dict] = {}
        for r in rows:
            eid = r.event_id
            if eid not in events:
                is_tbc = r.occurrence_status == "tbc"
                try:
                    expected_year = int(r.occurrence_year) if r.occurrence_year else None
                except (TypeError, ValueError):
                    expected_year = None
                try:
                    expected_month = int(r.occurrence_expected_month) if r.occurrence_expected_month else None
                except (TypeError, ValueError):
                    expected_month = None
                events[eid] = {
                    "event_id": eid,
                    "event_slug": r.event_slug,
                    "occurrence_year": r.occurrence_year,
                    "occurrence_id": int(r.occurrence_id) if r.occurrence_id is not None else None,
                    "name": r.event_display_name or r.event_name or "",
                    "rows": [],
                    "country": r.event_country_code,
                    "race_date": r.race_date,
                    "race_date_end": r.race_date,
                    "distances": [],
                    "formats": set(),
                    "cutoffs": [],
                    "terrain_type": r.terrain_type,
                    "race_status": r.race_status,
                    "registration_open": set(),
                    "prices": [],
                    "is_tbc": is_tbc,
                    "attendance_locked": is_locked(r.occurrence_start_date, r.occurrence_end_date),
                    "expected_month": expected_month,
                    "expected_year": expected_year,
                }
            else:
                if r.race_date is not None:
                    cur_end = events[eid]["race_date_end"]
                    if cur_end is None or r.race_date > cur_end:
                        events[eid]["race_date_end"] = r.race_date
            events[eid]["rows"].append(r)
            if r.race_distance is not None:
                events[eid]["distances"].append(r.race_distance)
            # Collected on every row, not only first-see: format lives on the
            # individual race, and the first row seen is the earliest-dated
            # one, which frequently has no format while a later sibling does.
            events[eid]["formats"].update(parse_race_formats(r.race_format))
            events[eid]["registration_open"].add(r.registration_open)
            # Same per-row rationale as formats. Zero and negative values are
            # dropped as bad source data — a race cannot have a 0h cutoff, and
            # keeping them would let junk rows satisfy a cutoff_max query.
            if r.cutoff_time is not None and r.cutoff_time > 0:
                events[eid]["cutoffs"].append(r.cutoff_time)
            # Same per-row rationale: the tile shows the range across races.
            # NULL price is unknown, never free, so it is skipped; so is a
            # positive price with no currency, whose unit is unknown. Zero is
            # free in any currency.
            p = r.registration_price
            if p is not None and (p == 0 or r.price_currency is not None):
                events[eid]["prices"].append((p, r.price_currency))

        # Apply distance filter: keep event if any distance matches
        def _matches_distance(distances: list[float]) -> bool:
            if not distances:
                return filters.distance_min is None and filters.distance_max is None
            return any(
                (filters.distance_min is None or d >= filters.distance_min)
                and (filters.distance_max is None or d <= filters.distance_max)
                for d in distances
            )

        # Format is race-level but tiles are event-level, so an event matches
        # if ANY of its races carries one of the requested formats — the same
        # convention _matches_distance uses. Applied post-grouping because the
        # column is a JSON array string, not a queryable relation.
        wanted_formats = set(filters.formats)

        cutoff_filtered = filters.cutoff_min is not None or filters.cutoff_max is not None

        # ANY-of-races again, but with the opposite empty-set rule to distance:
        # an event with no cutoff data anywhere is excluded once a cutoff range
        # is requested. Asking for races under 12h means asking for races whose
        # cutoff is known — "unknown" is not an answer to that question.
        def _matches_cutoff(cutoffs: list[float]) -> bool:
            if not cutoff_filtered:
                return True
            return any(
                (filters.cutoff_min is None or c >= filters.cutoff_min)
                and (filters.cutoff_max is None or c <= filters.cutoff_max)
                for c in cutoffs
            )

        result = []
        for ev in events.values():
            if not _matches_distance(ev["distances"]):
                continue
            if wanted_formats and not (ev["formats"] & wanted_formats):
                continue
            if not _matches_cutoff(ev["cutoffs"]):
                continue
            distances = sorted(set(ev["distances"]))
            prices = ev["prices"]
            price = price_max = price_currency = None
            currencies = {c for v, c in prices if v > 0}
            if len(currencies) > 1:
                # Never a range across currencies: earliest-dated positive price, alone.
                price, price_currency = next((v, c) for v, c in prices if v > 0)
            elif prices:
                price = min(v for v, _ in prices)
                top = max(v for v, _ in prices)
                price_max = top if top > price else None
                price_currency = next(iter(currencies), None)
            # ANY-of-races, as formats: open if any race is; closed only if
            # some race says so and none is open; NULL stays unknown.
            reg = ev["registration_open"]
            registration_open = True if True in reg else (False if False in reg else None)
            if ev["is_tbc"]:
                display = format_tbc_expected(ev["expected_year"], ev["expected_month"])
            else:
                display = format_date_range(ev["race_date"], ev["race_date_end"])
            result.append(EventListItem(
                event_id=ev["event_id"],
                event_slug=ev["event_slug"],
                occurrence_year=ev["occurrence_year"],
                occurrence_id=ev["occurrence_id"],
                name=ev["name"],
                location=event_location(ev["rows"]),
                country=ev["country"],
                race_date=ev["race_date"],
                race_date_end=ev["race_date_end"],
                race_date_display=display,
                attendance_locked=ev["attendance_locked"],
                distances=distances,
                terrain_type=ev["terrain_type"],
                race_status=ev["race_status"],
                registration_open=registration_open,
                price=price,
                price_max=price_max,
                price_currency=price_currency,
                gradient_class=assign_gradient(ev["terrain_type"], ev["country"]),
                going_count=0,
                is_tbc=ev["is_tbc"],
                expected_month=ev["expected_month"],
                expected_year=ev["expected_year"],
            ))

        logger.info(f"Returned {len(result)} events")
        return result

    def country_list(self) -> list[str]:
        rows = self.db.execute(
            select(Race.event_country_code)
            .where(Race.event_country_code.isnot(None))
            .distinct()
            .order_by(Race.event_country_code)
        ).scalars().all()
        return [r for r in rows if r]
