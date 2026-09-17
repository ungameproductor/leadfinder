from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import get_db
from app.repositories import run_repo
from app.schemas import RunOut, SearchRequest
from app.services.jobs.pipeline import run_search_job
from app.services.jobs.runner import job_runner

router = APIRouter()


def serialize_run(run) -> RunOut:
    return RunOut(
        id=run.id,
        kind=run.kind,
        provider=run.provider,
        query=run.query,
        city=run.city,
        postal_code=run.postal_code,
        latitude=run.latitude,
        longitude=run.longitude,
        radius_km=run.radius_km,
        categories=run_repo.categories_of(run),
        status=run.status,
        results_count=run.results_count,
        processed_count=run.processed_count,
        errors=run_repo.errors_of(run),
        api_usage=run_repo.usage_of(run),
        message=run.message,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


@router.post("/search", status_code=202)
def start_search(payload: SearchRequest, db: Session = Depends(get_db)) -> RunOut:
    settings = get_settings()
    provider = payload.provider or settings.discovery_provider
    run = run_repo.create_run(
        db,
        kind="search",
        provider=provider,
        query=",".join(payload.categories) if payload.categories else "all",
        city=payload.city,
        postal_code=payload.postal_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_km=payload.radius_km,
        categories_json=json.dumps(payload.categories, ensure_ascii=False),
        status="queued",
    )
    job_runner.submit(run_search_job, run.id, payload)
    return serialize_run(run)


@router.get("/search/{run_id}")
def get_search(run_id: str, db: Session = Depends(get_db)) -> RunOut:
    run = run_repo.get_run(db, run_id)
    if not run:
        raise HTTPException(404, "Job non trovato")
    return serialize_run(run)
