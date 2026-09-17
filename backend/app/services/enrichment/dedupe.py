from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Lead
from app.schemas import PlaceCandidate
from app.services.enrichment.normalize import normalize_address, normalize_domain, normalize_name, normalize_phone


def find_existing_lead(db: Session, candidate: PlaceCandidate) -> tuple[Lead | None, float]:
    if candidate.external_id:
        lead = db.scalar(
            select(Lead).where(
                Lead.source_provider == candidate.provider,
                Lead.source_external_id == candidate.external_id,
            )
        )
        if lead:
            return lead, 1.0

    phone = normalize_phone(candidate.phone)
    if phone:
        lead = db.scalar(select(Lead).where(Lead.phone == phone))
        if lead:
            return lead, 0.9

    domain = normalize_domain(candidate.website)
    if domain:
        leads = db.scalars(select(Lead).where(Lead.website.is_not(None))).all()
        for existing in leads:
            if normalize_domain(existing.website) == domain:
                return existing, 0.8

    name_key = normalize_name(candidate.name)
    addr_key = normalize_address(candidate.address)
    if name_key and addr_key:
        leads = db.scalars(select(Lead).where(Lead.name.is_not(None))).all()
        for existing in leads:
            if normalize_name(existing.name) == name_key and normalize_address(existing.address) == addr_key:
                return existing, 0.7

    return None, 1.0
