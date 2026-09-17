from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.entities import VerificationRun


def create_run(db: Session, **kwargs) -> VerificationRun:
    kwargs.setdefault("status", "queued")
    run = VerificationRun(**kwargs)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> VerificationRun | None:
    return db.get(VerificationRun, run_id)


def mark_running(db: Session, run: VerificationRun) -> None:
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    db.commit()


def update_progress(db: Session, run: VerificationRun, processed: int, results: int, message: str | None = None) -> None:
    run.processed_count = processed
    run.results_count = results
    if message:
        run.message = message
    db.commit()


def finish_run(
    db: Session,
    run: VerificationRun,
    *,
    status: str,
    results: int,
    errors: list[str],
    api_usage: dict,
    message: str | None = None,
) -> None:
    run.status = status
    run.results_count = results
    run.errors_json = json.dumps(errors, ensure_ascii=False)
    run.api_usage_json = json.dumps(api_usage, ensure_ascii=False)
    run.message = message
    run.finished_at = datetime.now(timezone.utc)
    db.commit()


def categories_of(run: VerificationRun) -> list[str]:
    if not run.categories_json:
        return []
    try:
        data = json.loads(run.categories_json)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def errors_of(run: VerificationRun) -> list[str]:
    if not run.errors_json:
        return []
    try:
        data = json.loads(run.errors_json)
        return data if isinstance(data, list) else [run.errors_json]
    except json.JSONDecodeError:
        return [run.errors_json]


def usage_of(run: VerificationRun) -> dict:
    if not run.api_usage_json:
        return {}
    try:
        data = json.loads(run.api_usage_json)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
