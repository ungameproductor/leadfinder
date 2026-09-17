from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DISCOVERY_PROVIDER", "mock")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "")
os.environ.setdefault("APP_ENV", "test")
os.environ["CRAWL_DELAY_SECONDS"] = "0"


@pytest.fixture
def db_engine(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from app.config import get_settings

    get_settings.cache_clear()
    from app import models as models_pkg
    from app.models import entities

    engine = entities.make_engine(get_settings())
    entities.Base.metadata.create_all(bind=engine)
    entities.engine = engine
    entities.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    models_pkg.SessionLocal = entities.SessionLocal
    models_pkg.engine = engine
    from app.services.jobs import runner as job_runner_mod
    from app.api import search as search_api
    from app.api import leads as leads_api

    job_runner_mod.SessionLocal = entities.SessionLocal
    yield engine
    get_settings.cache_clear()


@pytest.fixture
def db(db_engine) -> Generator:
    from app.models.entities import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_engine, monkeypatch) -> TestClient:
    from app.models.entities import SessionLocal, get_db
    from app.main import app

    def _override():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
