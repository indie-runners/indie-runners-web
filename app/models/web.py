from datetime import date, datetime

from sqlalchemy import BigInteger, Date, Integer, Text, String, TIMESTAMP, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Google OAuth columns
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    # Strava columns — kept until migration 004 drops them
    strava_athlete_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    firstname: Mapped[str | None] = mapped_column(Text)
    lastname: Mapped[str | None] = mapped_column(Text)
    profile_photo_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="public")

    attendance: Mapped[list["Attendance"]] = relationship(back_populates="user")
    auth_identities: Mapped[list["AuthIdentity"]] = relationship(back_populates="user")


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_auth_identity_provider_user"),
        UniqueConstraint("user_id", "provider", name="uq_auth_identity_user_provider"),
        Index("idx_auth_identities_user_id", "user_id"),
        {"schema": "web"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("web.users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str | None] = mapped_column(String(255))
    provider_email: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    user: Mapped["User"] = relationship(back_populates="auth_identities")


class EventImage(Base):
    __tablename__ = "event_images"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_event_images_event_id"),
        Index("idx_event_images_event_slug", "event_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="stock")
    stock_filename: Mapped[str | None] = mapped_column(String(255))
    terrain: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str | None] = mapped_column(String(50))
    attribution: Mapped[str | None] = mapped_column(String(255))
    attribution_name: Mapped[str | None] = mapped_column(String(500))
    attribution_url: Mapped[str | None] = mapped_column(String(500))
    attribution_source_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


class Crew(Base):
    __tablename__ = "crews"
    __table_args__ = (
        Index("idx_crews_created_by", "created_by"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)

    memberships: Mapped[list["CrewMembership"]] = relationship(back_populates="crew", cascade="all, delete-orphan")
    invites: Mapped[list["CrewInvite"]] = relationship(back_populates="crew", cascade="all, delete-orphan")


class CrewMembership(Base):
    __tablename__ = "crew_memberships"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'member')", name="ck_crew_memberships_role"),
        Index("idx_crew_memberships_user", "user_id"),
    )

    crew_id: Mapped[int] = mapped_column(Integer, ForeignKey("web.crews.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("web.users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    crew: Mapped["Crew"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship()


class CrewInvite(Base):
    __tablename__ = "crew_invites"
    __table_args__ = (
        Index("idx_crew_invites_crew_id", "crew_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crew_id: Mapped[int] = mapped_column(Integer, ForeignKey("web.crews.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    crew: Mapped["Crew"] = relationship(back_populates="invites")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        CheckConstraint("status IN ('going', 'interested')", name="ck_attendance_status"),
        UniqueConstraint("user_id", "occurrence_id", name="uq_attendance_user_occurrence"),
        Index("idx_attendance_event_id", "event_id"),
        Index("idx_attendance_occurrence_id", "occurrence_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("web.users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurrence_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    race_date: Mapped[date | None] = mapped_column(Date)
    event_display_name: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="attendance")
