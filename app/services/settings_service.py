import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.web import User

logger = logging.getLogger(__name__)

_SELECTABLE_LEVELS = frozenset({"public", "crews_only"})


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_visibility(self, user_id: int, level: str) -> None:
        if level not in _SELECTABLE_LEVELS:
            raise ValueError(f"Invalid visibility level: {level!r}")

        self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(visibility=level, updated_at=datetime.now(timezone.utc))
        )
        self.db.commit()
        logger.info("Updated visibility for user %s to %s", user_id, level)
