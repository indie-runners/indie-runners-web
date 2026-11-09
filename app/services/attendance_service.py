import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select, delete, func, text
from sqlalchemy.orm import Session

from app.models.web import Attendance, User

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"going", "interested"}
_AVATAR_PALETTE = ["#4a7c59", "#2e6b9e", "#8b5e3c", "#6b4c8a"]


@dataclass
class AttendanceUserInfo:
    id: int
    display_name: str | None
    avatar_url: str | None


@dataclass
class AttendanceSummary:
    going_count: int
    interested_count: int
    going_users: list[AttendanceUserInfo]
    interested_users: list[AttendanceUserInfo]
    going_hidden_count: int = 0
    interested_hidden_count: int = 0


def _is_identity_visible(
    user_id: int,
    visibility: str | None,
    viewer_user_id: int | None,
    viewer_crews: set[int],
    attendee_crews: set[int],
) -> bool:
    if viewer_user_id is None:
        return False
    if viewer_user_id == user_id:
        return True
    if visibility == "public":
        return True
    if visibility == "crews_only":
        return bool(viewer_crews & attendee_crews)
    return False


def is_locked(start_date: date | str | None, end_date: date | str | None) -> bool:
    """Attendance on an occurrence is frozen the day after its last known day (W-072).

    TBC has no dates and never locks. end_date is the scraper's claim; a race dated
    after it (one occurrence, 2026-10-30) is their defect, not read around here.
    """
    last_day = end_date or start_date
    if isinstance(last_day, str):  # the view carries dates as text
        last_day = date.fromisoformat(last_day)
    return last_day is not None and last_day < date.today()


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db

    def _occurrence_dates(self, occurrence_id: int) -> tuple[date | None, date | None]:
        row = self.db.execute(
            text("SELECT start_date, end_date FROM core.event_occurrences WHERE id = :oid"),
            {"oid": occurrence_id},
        ).one_or_none()
        return (row.start_date, row.end_date) if row else (None, None)

    def _event_display_name(self, event_id: int) -> str | None:
        row = self.db.execute(
            text("SELECT event_display_name FROM core.events WHERE id = :eid"),
            {"eid": event_id},
        ).one_or_none()
        return row.event_display_name if row else None

    def mark_attendance(self, user_id: int, event_id: int, occurrence_id: int, status: str) -> None:
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status: {status!r}")
        start_date, end_date = self._occurrence_dates(occurrence_id)
        if is_locked(start_date, end_date):
            raise ValueError("This event has already taken place")

        existing = self.db.execute(
            select(Attendance).where(
                Attendance.user_id == user_id,
                Attendance.occurrence_id == occurrence_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.status = status
            logger.info("Marked attendance for user %s event %s occurrence %s status %s", user_id, event_id, occurrence_id, status)
        else:
            race_date = start_date
            if race_date is None:
                logger.info("No upcoming occurrence found for event %s, storing null race date", event_id)
            display_name = self._event_display_name(event_id)
            self.db.add(Attendance(
                user_id=user_id,
                event_id=event_id,
                occurrence_id=occurrence_id,
                status=status,
                created_at=datetime.now(timezone.utc),
                race_date=race_date,
                event_display_name=display_name,
            ))
            logger.info("Marked attendance for user %s event %s occurrence %s status %s", user_id, event_id, occurrence_id, status)

        self.db.commit()

    def clear_attendance(self, user_id: int, occurrence_id: int) -> None:
        if is_locked(*self._occurrence_dates(occurrence_id)):
            raise ValueError("This event has already taken place")
        existing = self.db.execute(
            select(Attendance).where(
                Attendance.user_id == user_id,
                Attendance.occurrence_id == occurrence_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            return

        self.db.execute(
            delete(Attendance).where(
                Attendance.user_id == user_id,
                Attendance.occurrence_id == occurrence_id,
            )
        )
        self.db.commit()
        logger.info("Cleared attendance for user %s occurrence %s", user_id, occurrence_id)

    def get_attendance_for_user(self, user_id: int, occurrence_ids: list[int]) -> dict[int, str]:
        if not occurrence_ids:
            return {}
        rows = self.db.execute(
            select(Attendance.occurrence_id, Attendance.status).where(
                Attendance.user_id == user_id,
                Attendance.occurrence_id.in_(occurrence_ids),
            )
        ).all()
        return {row.occurrence_id: row.status for row in rows}

    def get_attendance_summary(
        self,
        occurrence_ids: list[int],
        viewer_user_id: int | None = None,
        viewer_crews: set[int] | None = None,
    ) -> dict[int, AttendanceSummary]:
        if not occurrence_ids:
            return {}

        rows = self.db.execute(
            select(
                Attendance.occurrence_id,
                Attendance.status,
                User.id,
                User.display_name,
                User.avatar_url,
                User.visibility,
            )
            .join(User, User.id == Attendance.user_id)
            .where(Attendance.occurrence_id.in_(occurrence_ids))
            .order_by(Attendance.occurrence_id, Attendance.created_at)
        ).all()

        viewer_crews = viewer_crews or set()
        attendee_crews_map: dict[int, set[int]] = {}
        if viewer_crews:
            crews_only_ids = sorted({
                row.id for row in rows if row.visibility == "crews_only"
            })
            if crews_only_ids:
                # Lazy import to avoid a circular dep at module load.
                from app.services.crew_service import CrewService
                attendee_crews_map = CrewService(self.db).get_attendee_crew_ids(crews_only_ids)

        summaries: dict[int, dict] = {}
        for row in rows:
            oid = row.occurrence_id
            if oid not in summaries:
                summaries[oid] = {
                    "going": 0,
                    "interested": 0,
                    "going_users": [],
                    "interested_users": [],
                    "going_hidden": 0,
                    "interested_hidden": 0,
                }
            attendee_crews = attendee_crews_map.get(row.id, set())
            visible = _is_identity_visible(
                row.id, row.visibility, viewer_user_id,
                viewer_crews, attendee_crews,
            )
            if row.status == "going":
                summaries[oid]["going"] += 1
                if visible:
                    summaries[oid]["going_users"].append(
                        AttendanceUserInfo(
                            id=row.id,
                            display_name=row.display_name,
                            avatar_url=row.avatar_url,
                        )
                    )
                else:
                    summaries[oid]["going_hidden"] += 1
            elif row.status == "interested":
                summaries[oid]["interested"] += 1
                if visible:
                    summaries[oid]["interested_users"].append(
                        AttendanceUserInfo(
                            id=row.id,
                            display_name=row.display_name,
                            avatar_url=row.avatar_url,
                        )
                    )
                else:
                    summaries[oid]["interested_hidden"] += 1

        result: dict[int, AttendanceSummary] = {}
        for oid in occurrence_ids:
            if oid in summaries:
                s = summaries[oid]
                result[oid] = AttendanceSummary(
                    going_count=s["going"],
                    interested_count=s["interested"],
                    going_users=s["going_users"],
                    interested_users=s["interested_users"],
                    going_hidden_count=s["going_hidden"],
                    interested_hidden_count=s["interested_hidden"],
                )
            else:
                result[oid] = AttendanceSummary(
                    going_count=0,
                    interested_count=0,
                    going_users=[],
                    interested_users=[],
                )

        events_with_attendance = sum(1 for s in result.values() if s.going_count + s.interested_count > 0)
        logger.info("Loaded attendance summary for %s occurrences, %s with attendance", len(occurrence_ids), events_with_attendance)
        return result
