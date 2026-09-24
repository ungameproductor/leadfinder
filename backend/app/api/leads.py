from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.entities import get_db
from app.repositories import lead_repo, run_repo
from app.schemas import LeadOut, LeadPatch, RunOut
from app.services.jobs.pipeline import verify_lead
from app.services.jobs.runner import job_runner

router = APIRouter()


def serialize_lead(lead) -> LeadOut:
    return LeadOut(
        id=lead.id,
        source_provider=lead.source_provider,
        source_external_id=lead.source_external_id,
        name=lead.name,
        category=lead.category,
        address=lead.address,
        city=lead.city,
        postal_code=lead.postal_code,
        latitude=lead.latitude,
        longitude=lead.longitude,
        phone=lead.phone,
        website=lead.website,
        public_email=lead.public_email,
        email_source_url=lead.email_source_url,
        website_status=lead.website_status,
        website_quality_score=lead.website_quality_score,
        website_quality_evidence=lead_repo.decode_json_list(lead.website_quality_evidence),
        email_status=lead.email_status,
        lead_score=lead.lead_score,
        priority=lead.priority,
        suggested_service=lead.suggested_service,
        notes=lead.notes,
        scoring_evidence=lead_repo.decode_json_list(lead.scoring_evidence),
        match_confidence=lead.match_confidence,
        phase_status=lead.phase_status,
        first_seen_at=lead.first_seen_at,
        last_checked_at=lead.last_checked_at,
        manual_status=lead.manual_status,
        contact_status=lead.contact_status,
        quality_data_insufficient=lead.quality_data_insufficient,
        is_new=getattr(lead, "is_new", None),
    )


@router.get("/leads/facets")
def lead_facets(db: Session = Depends(get_db)) -> dict:
    return lead_repo.lead_facets(db)


@router.get("/leads")
def list_leads(
    db: Session = Depends(get_db),
    q: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    city: str | None = None,
    run_id: str | None = None,
    only_new: bool = False,
    website_status: str | None = None,
    manual_status: str | None = None,
    has_email: bool | None = None,
    sort: str = "lead_score",
    order: str = "desc",
    limit: int = Query(200, le=500),
    offset: int = 0,
) -> dict:
    rows, total = lead_repo.list_leads(
        db,
        q=q,
        priority=priority,
        category=category,
        city=city,
        run_id=run_id,
        only_new=only_new,
        website_status=website_status,
        manual_status=manual_status,
        has_email=has_email,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "items": [serialize_lead(row) for row in rows]}


@router.get("/leads/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)) -> LeadOut:
    lead = lead_repo.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    return serialize_lead(lead)


@router.patch("/leads/{lead_id}")
def patch_lead(lead_id: str, payload: LeadPatch, db: Session = Depends(get_db)) -> LeadOut:
    lead = lead_repo.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")
    lead_repo.apply_patch(lead, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead)


@router.post("/leads/{lead_id}/verify", status_code=202)
def verify(lead_id: str, db: Session = Depends(get_db)) -> RunOut:
    lead = lead_repo.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(404, "Lead non trovato")

    def _job(session, lid: str) -> None:
        item = lead_repo.get_lead(session, lid)
        if item:
            verify_lead(session, item)

    run = run_repo.create_run(
        db,
        kind="verify",
        provider=lead.source_provider,
        query=lead.id,
        city=lead.city,
        status="queued",
    )
    job_runner.submit(_job, lead_id)
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
        categories=[],
        status=run.status,
        results_count=run.results_count,
        processed_count=run.processed_count,
        errors=[],
        api_usage={},
        message=run.message,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
