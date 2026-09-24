from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_provider: Mapped[str] = mapped_column(String(64), default="mock")
    source_external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    public_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website_status: Mapped[str] = mapped_column(String(32), default="unknown")
    website_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    website_quality_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_status: Mapped[str] = mapped_column(String(32), default="unknown")
    lead_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    priority: Mapped[str] = mapped_column(String(8), default="C", index=True)
    suggested_service: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scoring_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    phase_status: Mapped[str] = mapped_column(String(32), default="discovered")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manual_status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    contact_status: Mapped[str] = mapped_column(String(32), default="unknown")
    quality_data_insufficient: Mapped[bool] = mapped_column(Boolean, default=False)


class RunLead(Base):
    __tablename__ = "run_leads"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lead_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    kind: Mapped[str] = mapped_column(String(32), default="search")
    provider: Mapped[str] = mapped_column(String(64), default="mock")
    query: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    categories_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    errors_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def make_engine(settings: Settings | None = None):
    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    url = settings.database_url
    if url.startswith("sqlite:///"):
        url = f"sqlite:///{settings.sqlite_path}"
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, future=True, connect_args=connect_args)
    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
