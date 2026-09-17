from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Lead
from app.services.enrichment.dedupe import find_existing_lead
from app.services.enrichment.normalize import normalize_place
from app.schemas import PlaceCandidate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_lead(db: Session, lead_id: str) -> Lead | None:
    return db.get(Lead, lead_id)


def upsert_candidate(db: Session, candidate: PlaceCandidate) -> tuple[Lead, bool, float]:
    existing, confidence = find_existing_lead(db, candidate)
    data = normalize_place(candidate)
    if existing:
        for key, value in data.items():
            if value in (None, "") and key not in {"website_status"}:
                continue
            if key == "website" and existing.website and value != existing.website:
                existing.website = value
            elif getattr(existing, key, None) in (None, "", "unknown") or key in {
                "name",
                "category",
                "address",
                "city",
                "postal_code",
                "latitude",
                "longitude",
                "phone",
                "source_provider",
                "source_external_id",
            }:
                setattr(existing, key, value)
        existing.match_confidence = max(existing.match_confidence or 0, confidence)
        existing.last_checked_at = _now()
        return existing, False, confidence

    lead = Lead(
        **data,
        first_seen_at=_now(),
        last_checked_at=_now(),
        match_confidence=confidence,
        phase_status="discovered",
        website_status="no_website" if not data.get("website") else "unknown",
    )
    db.add(lead)
    db.flush()
    return lead, True, confidence


def list_leads(
    db: Session,
    *,
    q: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    website_status: str | None = None,
    manual_status: str | None = None,
    has_email: bool | None = None,
    exclude_dnc: bool = False,
    sort: str = "lead_score",
    order: str = "desc",
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[Lead], int]:
    stmt: Select[tuple[Lead]] = select(Lead)
    count_stmt = select(func.count(Lead.id))
    filters = []
    if q:
        like = f"%{q.strip()}%"
        filters.append(
            or_(
                Lead.name.ilike(like),
                Lead.address.ilike(like),
                Lead.public_email.ilike(like),
                Lead.phone.ilike(like),
                Lead.category.ilike(like),
            )
        )
    if priority:
        filters.append(Lead.priority == priority.upper())
    if category:
        filters.append(Lead.category == category)
    if website_status:
        filters.append(Lead.website_status == website_status)
    if manual_status:
        filters.append(Lead.manual_status == manual_status)
    if has_email is True:
        filters.append(Lead.public_email.is_not(None))
    if has_email is False:
        filters.append(Lead.public_email.is_(None))
    if exclude_dnc:
        filters.append(Lead.contact_status != "do_not_contact")
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    sort_map = {
        "lead_score": Lead.lead_score,
        "name": Lead.name,
        "priority": Lead.priority,
        "last_checked_at": Lead.last_checked_at,
        "first_seen_at": Lead.first_seen_at,
        "category": Lead.category,
    }
    col = sort_map.get(sort, Lead.lead_score)
    stmt = stmt.order_by(col.asc() if order == "asc" else col.desc())
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.offset(offset).limit(limit)).all()
    return list(rows), int(total)


def stats(db: Session) -> dict[str, int]:
    def count(*where) -> int:
        stmt = select(func.count(Lead.id))
        if where:
            stmt = stmt.where(*where)
        return int(db.scalar(stmt) or 0)

    return {
        "total": count(),
        "priority_a": count(Lead.priority == "A"),
        "priority_b": count(Lead.priority == "B"),
        "priority_c": count(Lead.priority == "C"),
        "no_website": count(Lead.website_status == "no_website"),
        "problematic_sites": count(
            Lead.website_status.in_(["unreachable", "blocked", "error", "redirect_only"])
        ),
        "emails_found": count(Lead.public_email.is_not(None)),
        "confirmed": count(Lead.manual_status == "confirmed"),
        "discarded": count(Lead.manual_status == "discarded"),
        "do_not_contact": count(Lead.contact_status == "do_not_contact"),
    }


def apply_patch(lead: Lead, data: dict) -> Lead:
    for key, value in data.items():
        if value is not None:
            setattr(lead, key, value)
    return lead


def decode_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else [str(value)]
    except json.JSONDecodeError:
        return [raw]
