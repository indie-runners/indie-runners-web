import logging
import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import delete, select, update, exists, and_, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.web import Crew, CrewInvite, CrewMembership, User
from app.services.attendance_service import _is_identity_visible, is_locked
from app.services.race_service import event_location

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MIN_NAME_LEN = 2
_TOKEN_BYTES = 32
# Fixed /crews/<word> routes registered before /crews/{slug}; a crew with one of these slugs has no page.
_RESERVED_SLUGS = frozenset({"new"})
_MAX_SLUG_LEN = Crew.__table__.c.slug.type.length


def _slugify(name: str) -> str:
    lowered = name.strip().lower()
    slug = _SLUG_RE.sub("-", lowered).strip("-")
    return slug


@dataclass
class AgendaRow:
    """One occurrence at least one crew member has marked (W-077)."""
    occurrence_id: int
    display_name: str | None
    event_slug: str | None
    occurrence_year: int | None
    start_date: date | None
    is_tbc: bool
    location: str | None
    distances: list[float]
    has_page: bool
    going: list[str]  # display names of members the viewer may see
    interested: list[str]


class CrewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_crew(self, user_id: int, display_name: str) -> Crew:
        name = (display_name or "").strip()
        if len(name) < _MIN_NAME_LEN:
            raise ValueError("Crew name is too short")
        base_slug = _slugify(name)
        if not base_slug:
            raise ValueError("Crew name must include letters or numbers")
        if base_slug in _RESERVED_SLUGS:
            raise ValueError("That name is taken")
        # Refuse rather than truncate: two long names sharing a prefix would collide.
        if len(base_slug) > _MAX_SLUG_LEN:
            raise ValueError("Crew name is too long")

        now = datetime.now(timezone.utc)
        crew = Crew(
            slug=base_slug,
            display_name=name,
            created_at=now,
            created_by=user_id,
        )
        self.db.add(crew)
        try:
            self.db.flush()
        except IntegrityError:
            # The UNIQUE slug decides, so two concurrent creates cannot both win.
            self.db.rollback()
            raise ValueError("That name is taken")
        self.db.add(CrewMembership(
            crew_id=crew.id,
            user_id=user_id,
            role="admin",
            joined_at=now,
        ))
        self.db.add(CrewInvite(
            crew_id=crew.id,
            token=secrets.token_urlsafe(_TOKEN_BYTES),
            created_by=user_id,
            created_at=now,
        ))
        self.db.commit()
        logger.info("Created crew %s (id=%s) for user %s", base_slug, crew.id, user_id)
        return crew

    def get_crew_by_slug(self, slug: str) -> Crew | None:
        return self.db.execute(
            select(Crew).where(Crew.slug == slug)
        ).scalar_one_or_none()

    def list_crews_for_user(self, user_id: int) -> list[tuple[Crew, int]]:
        """(crew, member_count) for every crew the user is in, newest membership first."""
        member_count = (
            select(func.count())
            .where(CrewMembership.crew_id == Crew.id)
            .correlate(Crew)  # outer query also selects CrewMembership; keep it in this FROM
            .scalar_subquery()
        )
        rows = self.db.execute(
            select(Crew, member_count)
            .join(CrewMembership, CrewMembership.crew_id == Crew.id)
            .where(CrewMembership.user_id == user_id)
            .order_by(CrewMembership.joined_at.desc())
        ).all()
        return [(row[0], row[1]) for row in rows]

    def is_member(self, user_id: int, crew_id: int) -> bool:
        return self.db.execute(
            select(exists().where(
                and_(
                    CrewMembership.crew_id == crew_id,
                    CrewMembership.user_id == user_id,
                )
            ))
        ).scalar_one()

    def is_admin(self, user_id: int, crew_id: int) -> bool:
        return self.db.execute(
            select(exists().where(
                and_(
                    CrewMembership.crew_id == crew_id,
                    CrewMembership.user_id == user_id,
                    CrewMembership.role == "admin",
                )
            ))
        ).scalar_one()

    def list_members(self, crew_id: int) -> list[tuple[User, str]]:
        rows = self.db.execute(
            select(User, CrewMembership.role, CrewMembership.joined_at)
            .join(CrewMembership, CrewMembership.user_id == User.id)
            .where(CrewMembership.crew_id == crew_id)
            .order_by(
                (CrewMembership.role == "admin").desc(),
                CrewMembership.joined_at.asc(),
            )
        ).all()
        return [(row[0], row[1]) for row in rows]

    def list_agenda(
        self, crew_id: int, viewer_user_id: int,
    ) -> list[tuple[date, list[AgendaRow]]]:
        """Non-past occurrences members have marked, grouped by month ascending.

        A dated edition is past once attendance on it is locked (W-072, the
        day after its last day); a TBC edition sits under its expected month
        (December if unknown) and is past once that month is, the index's rule.
        """
        rows = self.db.execute(
            text("""
                SELECT a.occurrence_id, a.status, a.event_id,
                       COALESCE(e.event_display_name, a.event_display_name) AS display_name,
                       e.event_slug, o.year, o.start_date, o.end_date, o.expected_month,
                       -- a dated status with no date would otherwise crash month_of
                       (o.status = 'tbc' OR o.start_date IS NULL) AS is_tbc,
                       u.id AS user_id, u.display_name AS user_name, u.visibility,
                       EXISTS (
                           SELECT 1 FROM core.v_denormalized_event_data_upcoming v
                           WHERE v.event_slug = e.event_slug
                             AND v.occurrence_year = o.year::text
                       ) AS has_page
                FROM web.crew_memberships m
                JOIN web.users u ON u.id = m.user_id
                JOIN web.attendance a ON a.user_id = m.user_id
                JOIN core.event_occurrences o ON o.id = a.occurrence_id
                LEFT JOIN core.events e ON e.id = a.event_id
                WHERE m.crew_id = :crew_id
                ORDER BY a.created_at
            """),
            {"crew_id": crew_id},
        ).all()

        this_month = date.today().replace(day=1)

        def month_of(r) -> date | None:
            if r.is_tbc:
                return date(r.year, r.expected_month or 12, 1) if r.year else None
            return r.start_date.replace(day=1)

        def is_past(r) -> bool:
            if r.is_tbc:
                return month_of(r) is None or month_of(r) < this_month
            return is_locked(r.start_date, r.end_date)

        rows = [r for r in rows if not is_past(r)]

        mv_rows: dict[str, list] = {}
        for v in self.db.execute(
            text("""
                SELECT event_id, occurrence_id, event_location, race_location, race_date,
                       race_distance, mv_id::text AS mv_id
                FROM core.mv_denormalized_event_data WHERE event_id = ANY(CAST(:ids AS text[]))
            """),
            {"ids": sorted({str(r.event_id) for r in rows})},
        ):
            mv_rows.setdefault(v.event_id, []).append(v)

        # Every attendee here is a member of this crew, which is all the
        # predicate needs to know about their crews.
        agenda: dict[int, AgendaRow] = {}
        for r in rows:
            row = agenda.get(r.occurrence_id)
            if row is None:
                ev = mv_rows.get(str(r.event_id), [])
                edition = [v for v in ev if v.occurrence_id == str(r.occurrence_id)] or ev
                row = agenda[r.occurrence_id] = AgendaRow(
                    occurrence_id=r.occurrence_id,
                    display_name=r.display_name,
                    event_slug=r.event_slug,
                    occurrence_year=r.year,
                    start_date=None if r.is_tbc else r.start_date,
                    is_tbc=r.is_tbc,
                    location=event_location(edition),
                    distances=sorted({v.race_distance for v in edition if v.race_distance is not None}),
                    has_page=r.has_page,
                    going=[],
                    interested=[],
                )
            if _is_identity_visible(r.user_id, r.visibility, viewer_user_id, {crew_id}, {crew_id}):
                getattr(row, r.status).append(r.user_name or "?")

        months: dict[date, list[AgendaRow]] = {}
        for r in rows:
            row = agenda[r.occurrence_id]
            bucket = months.setdefault(month_of(r), [])
            if row not in bucket:
                bucket.append(row)
        for bucket in months.values():
            bucket.sort(key=lambda a: (a.is_tbc, a.start_date or date.max, a.display_name or ""))
        return sorted(months.items())

    def shares_crew_with(self, a_user_id: int, b_user_id: int) -> bool:
        a = CrewMembership.__table__.alias("a")
        b = CrewMembership.__table__.alias("b")
        return self.db.execute(
            select(exists().where(
                and_(
                    a.c.user_id == a_user_id,
                    b.c.user_id == b_user_id,
                    a.c.crew_id == b.c.crew_id,
                )
            ))
        ).scalar_one()

    def get_viewer_crew_ids(self, user_id: int | None) -> set[int]:
        if user_id is None:
            return set()
        rows = self.db.execute(
            select(CrewMembership.crew_id).where(CrewMembership.user_id == user_id)
        ).scalars().all()
        return set(rows)

    def get_attendee_crew_ids(self, user_ids: list[int]) -> dict[int, set[int]]:
        if not user_ids:
            return {}
        rows = self.db.execute(
            select(CrewMembership.user_id, CrewMembership.crew_id)
            .where(CrewMembership.user_id.in_(user_ids))
        ).all()
        result: dict[int, set[int]] = {}
        for user_id, crew_id in rows:
            result.setdefault(user_id, set()).add(crew_id)
        return result

    def active_invite_for_crew(self, crew_id: int) -> CrewInvite | None:
        return self.db.execute(
            select(CrewInvite)
            .where(CrewInvite.crew_id == crew_id)
            .where(CrewInvite.revoked_at.is_(None))
            .order_by(CrewInvite.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    def rotate_invite(self, crew_id: int, actor_user_id: int) -> CrewInvite:
        if not self.is_admin(actor_user_id, crew_id):
            raise PermissionError("Only crew admins can rotate the invite link")
        now = datetime.now(timezone.utc)
        self.db.execute(
            update(CrewInvite)
            .where(CrewInvite.crew_id == crew_id)
            .where(CrewInvite.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        fresh = CrewInvite(
            crew_id=crew_id,
            token=secrets.token_urlsafe(_TOKEN_BYTES),
            created_by=actor_user_id,
            created_at=now,
        )
        self.db.add(fresh)
        self.db.commit()
        logger.info("Rotated invite for crew %s by user %s", crew_id, actor_user_id)
        return fresh

    def find_crew_by_invite_token(self, token: str) -> Crew | None:
        return self.db.execute(
            select(Crew)
            .join(CrewInvite, CrewInvite.crew_id == Crew.id)
            .where(CrewInvite.token == token)
            .where(CrewInvite.revoked_at.is_(None))
        ).scalar_one_or_none()

    def add_member(self, crew_id: int, user_id: int) -> None:
        existing = self.db.execute(
            select(CrewMembership).where(
                CrewMembership.crew_id == crew_id,
                CrewMembership.user_id == user_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return
        self.db.add(CrewMembership(
            crew_id=crew_id,
            user_id=user_id,
            role="member",
            joined_at=datetime.now(timezone.utc),
        ))
        self.db.commit()
        logger.info("Added user %s to crew %s", user_id, crew_id)

    def remove_member(self, crew_id: int, user_id: int) -> None:
        """Take the user out of the crew and keep its soft refs valid; the caller commits.

        crews.created_by and crew_invites.created_by have no FK (W-022), so a
        crew the user leaves either goes (no one else in it) or passes to the
        longest-standing remaining member, admins first, who becomes admin.
        Shared by leave and delete_account so the two ways out agree (W-081).
        """
        self.db.execute(delete(CrewMembership).where(
            CrewMembership.crew_id == crew_id, CrewMembership.user_id == user_id,
        ))
        heir = self.db.execute(
            select(CrewMembership)
            .where(CrewMembership.crew_id == crew_id)
            .order_by((CrewMembership.role == "admin").desc(), CrewMembership.joined_at.asc())
            .limit(1)
        ).scalar_one_or_none()
        if heir is None:
            self.db.execute(delete(Crew).where(Crew.id == crew_id))
            return
        heir.role = "admin"
        self.db.execute(
            update(Crew).where(Crew.id == crew_id, Crew.created_by == user_id)
            .values(created_by=heir.user_id)
        )
        self.db.execute(
            update(CrewInvite).where(CrewInvite.crew_id == crew_id, CrewInvite.created_by == user_id)
            .values(created_by=heir.user_id)
        )
