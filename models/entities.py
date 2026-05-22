from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.constants import DEFAULT_WORK_TYPE


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class UserPreference(Base):
    """Stores user job-search preferences."""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(120), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    work_type: Mapped[str] = mapped_column(String(50), default=DEFAULT_WORK_TYPE)
    alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )


class SavedJob(Base):
    """Vacancies bookmarked by a user (unique per user_id + link)."""

    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("user_id", "link", name="uq_saved_jobs_user_link"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    salary: Mapped[str | None] = mapped_column(String(120), nullable=True)
    link: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class SentJob(Base):
    """Tracks vacancy links already sent to a user via automatic alerts."""

    __tablename__ = "sent_jobs"
    __table_args__ = (UniqueConstraint("user_id", "vacancy_link", name="uq_sent_jobs_user_link"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    vacancy_link: Mapped[str] = mapped_column(String(500), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Resume(Base):
    """Uploaded resume metadata and parsed skill profile per user."""

    __tablename__ = "resumes"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_skills: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
