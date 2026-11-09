import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.web import User, AuthIdentity, Crew, CrewInvite, CrewMembership
from app.services.crew_service import CrewService

logger = logging.getLogger(__name__)


def short_display_name(userinfo: dict) -> str | None:
    """'Paulo M.' from Google's given_name + family_name initial; else first and last tokens of given_name or name (W-090, W-091)."""
    given = (userinfo.get("given_name") or "").strip()
    family = (userinfo.get("family_name") or "").strip()
    if given and family:
        return f"{given} {family[0]}."
    tokens = (given or userinfo.get("name") or "").split()
    if not tokens:
        return None
    return tokens[0] if len(tokens) == 1 else f"{tokens[0]} {tokens[-1][0]}."


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user_from_google(self, userinfo: dict) -> User:
        if not userinfo.get("email_verified"):
            raise ValueError("Google account email is not verified")

        email = userinfo["email"]
        now = datetime.now(timezone.utc)

        user = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                display_name=short_display_name(userinfo),
                avatar_url=userinfo.get("picture"),
                created_at=now,
                updated_at=now,
            )
            self.db.add(user)
            self.db.flush()

            identity = AuthIdentity(
                user_id=user.id,
                provider="google",
                provider_user_id=userinfo.get("sub"),
                provider_email=email,
                created_at=now,
                last_used_at=now,
            )
            self.db.add(identity)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user id={user.id}")
        else:
            user.display_name = short_display_name(userinfo)
            user.avatar_url = userinfo.get("picture")
            user.updated_at = now

            identity = self.db.execute(
                select(AuthIdentity).where(
                    AuthIdentity.user_id == user.id,
                    AuthIdentity.provider == "google",
                )
            ).scalar_one_or_none()

            if identity is None:
                identity = AuthIdentity(
                    user_id=user.id,
                    provider="google",
                    provider_user_id=userinfo.get("sub"),
                    provider_email=email,
                    created_at=now,
                    last_used_at=now,
                )
                self.db.add(identity)
            else:
                identity.last_used_at = now

            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Updated existing user id={user.id}")

        return user

    def delete_account(self, user_id: int) -> None:
        """Remove the user and everything that references them, in one transaction.

        attendance and auth_identities go by ON DELETE CASCADE (verified in
        the DB, not just the model). Crews go through CrewService.remove_member,
        the same hand-over as leaving (W-081): each crew the user is in either
        goes (no one else in it) or passes to the longest-standing remaining
        member, admins first.
        """
        crew_ids = self.db.execute(
            select(CrewMembership.crew_id).where(CrewMembership.user_id == user_id)
        ).scalars().all()
        crews = CrewService(self.db)
        for crew_id in crew_ids:
            crews.remove_member(crew_id, user_id)

        # A soft ref outside the user's own crews would survive the loop; refuse rather than leave it dangling.
        leftover = self.db.execute(
            select(func.count()).select_from(Crew).where(Crew.created_by == user_id)
        ).scalar_one() + self.db.execute(
            select(func.count()).select_from(CrewInvite).where(CrewInvite.created_by == user_id)
        ).scalar_one()
        if leftover:
            self.db.rollback()
            raise RuntimeError(f"user {user_id} still referenced by {leftover} crew/invite rows")

        self.db.execute(delete(User).where(User.id == user_id))
        self.db.commit()
        logger.info("Deleted account user id=%s (%d crews touched)", user_id, len(crew_ids))


if __name__ == "__main__":
    assert short_display_name({"given_name": "Paulo", "family_name": "Morales"}) == "Paulo M."
    assert short_display_name({"given_name": "Paulo"}) == "Paulo"
    assert short_display_name({"given_name": "Paulo Morales"}) == "Paulo M."
    assert short_display_name({"given_name": "Ana María", "family_name": "García López"}) == "Ana María G."
    assert short_display_name({"name": "Paulo Morales Castillo"}) == "Paulo C."
    assert short_display_name({"name": "Paulo"}) == "Paulo"
    assert short_display_name({"name": "  ", "given_name": ""}) is None
    print("ok")
