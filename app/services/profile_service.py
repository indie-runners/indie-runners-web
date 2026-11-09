import logging
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.services.race_service import event_location

from app.models.web import User

logger = logging.getLogger(__name__)


@dataclass
class ProfileRow:
    event_id: int
    occurrence_id: int | None
    status: str
    race_date: date | None
    display_name: str | None
    location: str | None
    event_type: str | None
    event_slug: str | None
    occurrence_year: int | None
    expected_month: int | None  # a TBC edition's month, as the hub reads it (W-098)
    distances: list[float]
    # The event page reads the serving view and 404s off it; the view drops a
    # non-TBC race the day after it runs, so link only what it still serves.
    has_page: bool


@dataclass
class TimelineRow:
    """One entry in a profile timeline list.

    `flag` is the display status ("been_there" | "going" | "interested"),
    derived from the attendance status plus whether the date has passed —
    the shelves keep those two facts in separate lists, the timeline
    carries them on the row instead.
    """
    row: ProfileRow
    flag: str
    # The month heading the row sits under: its date's month, else a TBC
    # edition's expected month (December if unknown), the hub's rule (W-098).
    month: date | None


@dataclass
class ProfileView:
    is_visible: bool = True
    target_user: User | None = None
    going_upcoming: list[ProfileRow] = field(default_factory=list)
    going_past: list[ProfileRow] = field(default_factory=list)
    interested: list[ProfileRow] = field(default_factory=list)
    # Going and interested interleaved by date — the forward-looking view,
    # where the gap between a commitment and a maybe is the point.
    upcoming_timeline: list[TimelineRow] = field(default_factory=list)
    # Past races, most recent first. Its own section below the upcoming one
    # so a long history never pushes the calendar down.
    past_timeline: list[TimelineRow] = field(default_factory=list)


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_profile(
        self,
        target_user_id: int,
        viewer_user_id: int | None,
        viewer_crews: set[int] | None = None,
    ) -> ProfileView:
        target = self.db.execute(
            select(User).where(User.id == target_user_id)
        ).scalar_one_or_none()

        # Collapse "no such user" into "hidden" so the placeholder is the
        # only signal — no enumeration channel. See BRIEF Decision 6.
        if target is None:
            logger.info("Profile lookup for missing user %s returning hidden", target_user_id)
            return ProfileView(is_visible=False)

        viewer_crews = viewer_crews or set()
        is_self = viewer_user_id is not None and viewer_user_id == target.id
        if not self._can_view(
            target.visibility, is_self, viewer_user_id is not None,
            viewer_crews, target.id,
        ):
            logger.info(
                "Profile for user %s hidden from viewer %s (visibility=%s)",
                target.id, viewer_user_id, target.visibility,
            )
            return ProfileView(is_visible=False)

        rows = self._load_rows(target.id)
        today = date.today()

        def is_upcoming(row: ProfileRow) -> bool:
            # NULL race_date = TBC RSVP; treat as upcoming (forward-looking
            # by definition — the event has no confirmed date yet).
            return row.race_date is None or row.race_date >= today

        going_upcoming = [r for r in rows if r.status == "going" and is_upcoming(r)]
        going_past = [r for r in rows if r.status == "going" and not is_upcoming(r)]
        interested = [r for r in rows if r.status == "interested" and is_upcoming(r)]

        going_upcoming.sort(key=lambda r: r.race_date or date.max)
        going_past.sort(key=lambda r: r.race_date or date.min, reverse=True)
        interested.sort(key=lambda r: r.race_date or date.max)

        def month_of(r: ProfileRow) -> date | None:
            if r.race_date:
                return r.race_date.replace(day=1)
            if r.occurrence_year:
                return date(r.occurrence_year, r.expected_month or 12, 1)
            return None

        # Going and interested interleaved into one forward-looking list, so
        # the time between a commitment and a maybe is legible. The flag
        # travels on the row rather than being implied by which list it is in.
        upcoming_timeline = (
            [TimelineRow(r, "going", month_of(r)) for r in going_upcoming]
            + [TimelineRow(r, "interested", month_of(r)) for r in interested]
        )
        # Month ascending, then the hub's order inside a month: dated rows by
        # date, a TBC edition last under its expected month (W-098).
        upcoming_timeline.sort(key=lambda t: (
            t.month or date.max, t.row.race_date is None, t.row.race_date or date.max, t.row.display_name or "",
        ))

        # Past races are their own section. Most recent first, matching the
        # going_past shelf, so the newest result is what a reader lands on;
        # that order already puts months newest-first with rows newest-first inside.
        past_timeline = [TimelineRow(r, "been_there", month_of(r)) for r in going_past]

        logger.info(
            "Loaded profile for user %s: %s going upcoming, %s past, %s interested",
            target.id, len(going_upcoming), len(going_past), len(interested),
        )

        return ProfileView(
            is_visible=True,
            target_user=target,
            going_upcoming=going_upcoming,
            going_past=going_past,
            interested=interested,
            upcoming_timeline=upcoming_timeline,
            past_timeline=past_timeline,
        )

    def _can_view(
        self,
        visibility: str | None,
        is_self: bool,
        viewer_signed_in: bool,
        viewer_crews: set[int],
        target_user_id: int,
    ) -> bool:
        # Anon sees the placeholder even for public targets — no
        # enumeration signal, and no scraper-visible identity (BRIEF PR1
        # baseline + PLAN Decision 5).
        if is_self:
            return True
        if not viewer_signed_in:
            return False
        if visibility == "public":
            return True
        if visibility == "crews_only":
            if not viewer_crews:
                return False
            from app.services.crew_service import CrewService
            target_crews = CrewService(self.db).get_viewer_crew_ids(target_user_id)
            return bool(viewer_crews & target_crews)
        return False

    def _load_rows(self, user_id: int) -> list[ProfileRow]:
        result = self.db.execute(
            text("""
                SELECT
                    a.event_id,
                    a.occurrence_id,
                    a.status,
                    -- The snapshot is NULL when the date was unknown at mark time;
                    -- a date the edition has since gained is what the hub shows (W-098).
                    COALESCE(a.race_date, o.start_date) AS race_date,
                    COALESCE(e.event_display_name, a.event_display_name) AS display_name,
                    -- core.events.location / event_type are NULL on every row;
                    -- the scraper fills these per race on the MV. Event-level:
                    -- the attended edition first, else the edition the MV holds.
                    -- Location: event_location() over the MV rows, below.
                    -- Terrain: longest race first, as the event page's hero reads it.
                    (SELECT v.terrain_type FROM core.mv_denormalized_event_data v
                      WHERE v.event_id = a.event_id::text AND v.terrain_type IS NOT NULL
                      ORDER BY v.occurrence_id IS NOT DISTINCT FROM a.occurrence_id::text DESC,
                               v.race_distance DESC NULLS LAST, v.mv_id
                      LIMIT 1) AS event_type,
                    e.event_slug,
                    o.year AS occurrence_year,
                    o.expected_month,
                    EXISTS (
                        SELECT 1 FROM core.v_denormalized_event_data_upcoming v
                        WHERE v.event_slug = e.event_slug
                          AND v.occurrence_year = o.year::text
                    ) AS has_page
                FROM web.attendance a
                LEFT JOIN core.events e ON e.id = a.event_id
                LEFT JOIN core.event_occurrences o ON o.id = a.occurrence_id
                WHERE a.user_id = :user_id
            """),
            {"user_id": user_id},
        ).all()

        mv_rows: dict[str, list] = {}
        for v in self.db.execute(
            text("""
                SELECT event_id, occurrence_id, event_location, race_location, race_date,
                       race_distance, mv_id::text AS mv_id
                FROM core.mv_denormalized_event_data WHERE event_id = ANY(CAST(:ids AS text[]))
            """),
            {"ids": [str(row.event_id) for row in result]},
        ):
            mv_rows.setdefault(v.event_id, []).append(v)

        def _edition(row) -> list:
            ev = mv_rows.get(str(row.event_id), [])
            return [v for v in ev if v.occurrence_id == str(row.occurrence_id)] or ev

        rows: list[ProfileRow] = []
        for row in result:
            edition = _edition(row)
            rows.append(ProfileRow(
                event_id=row.event_id,
                occurrence_id=row.occurrence_id,
                status=row.status,
                race_date=row.race_date,
                display_name=row.display_name,
                location=event_location(edition),
                event_type=row.event_type,
                event_slug=row.event_slug,
                occurrence_year=row.occurrence_year,
                expected_month=row.expected_month,
                distances=sorted({v.race_distance for v in edition if v.race_distance is not None}),
                has_page=row.has_page,
            ))
        return rows
