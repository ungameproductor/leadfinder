from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Lead, RunLead, VerificationRun
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


def link_run_lead(db: Session, run_id: str, lead_id: str, *, is_new: bool) -> None:
    row = db.get(RunLead, (run_id, lead_id))
    if row:
        row.is_new = bool(row.is_new or is_new)
        return
    db.add(RunLead(run_id=run_id, lead_id=lead_id, is_new=is_new))


def _latest_search_start(db: Session):
    return db.scalar(
        select(func.max(VerificationRun.started_at)).where(
            VerificationRun.kind == "search",
            VerificationRun.status.in_(["completed", "completed_with_errors"]),
        )
    )


def _run_has_links(db: Session, run_id: str) -> bool:
    return bool(db.scalar(select(func.count(RunLead.lead_id)).where(RunLead.run_id == run_id)))


def list_leads(
    db: Session,
    *,
    q: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    city: str | None = None,
    run_id: str | None = None,
    only_new: bool = False,
    website_status: str | None = None,
    manual_status: str | None = None,
    has_email: bool | None = None,
    exclude_dnc: bool = False,
    sort: str = "lead_score",
    order: str = "desc",
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[Lead], int]:
    linked = bool(run_id and _run_has_links(db, run_id))
    run = db.get(VerificationRun, run_id) if run_id else None
    fresh_since = None
    if only_new and not linked:
        fresh_since = run.started_at if run else _latest_search_start(db)
    if linked:
        stmt: Select[tuple[Lead]] = select(Lead).join(RunLead, RunLead.lead_id == Lead.id).distinct()
        count_stmt = select(func.count(func.distinct(Lead.id))).join(RunLead, RunLead.lead_id == Lead.id)
    else:
        stmt = select(Lead)
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
    if city:
        filters.append(func.lower(Lead.city) == city.strip().lower())
    elif run and not linked and run.city:
        filters.append(func.lower(Lead.city) == run.city.strip().lower())
    if linked and run_id:
        filters.append(RunLead.run_id == run_id)
    if linked and only_new:
        filters.append(RunLead.is_new.is_(True))
    if fresh_since is not None:
        filters.append(Lead.first_seen_at >= fresh_since)
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
    direction = col.asc() if order == "asc" else col.desc()
    if linked:
        stmt = stmt.order_by(RunLead.is_new.desc(), direction)
    else:
        stmt = stmt.order_by(direction)
    total = db.scalar(count_stmt) or 0
    rows = list(db.scalars(stmt.offset(offset).limit(limit)).all())
    if fresh_since is not None:
        for row in rows:
            row.is_new = True  # type: ignore[attr-defined]
    elif rows and not linked:
        since = _latest_search_start(db)
        if since is not None:
            for row in rows:
                row.is_new = bool(row.first_seen_at and row.first_seen_at >= since)  # type: ignore[attr-defined]
    if linked and rows:
        flags = {
            link.lead_id: link.is_new
            for link in db.scalars(
                select(RunLead).where(RunLead.run_id == run_id, RunLead.lead_id.in_([row.id for row in rows]))
            ).all()
        }
        for row in rows:
            row.is_new = bool(flags.get(row.id, False))  # type: ignore[attr-defined]
    return rows, int(total)


def lead_facets(db: Session) -> dict:
    cities = [
        value
        for value in db.scalars(
            select(Lead.city).where(Lead.city.is_not(None), Lead.city != "").distinct().order_by(Lead.city)
        ).all()
        if value
    ]
    categories = [
        value
        for value in db.scalars(
            select(Lead.category)
            .where(Lead.category.is_not(None), Lead.category != "")
            .distinct()
            .order_by(Lead.category)
        ).all()
        if value
    ]
    runs = list(
        db.scalars(
            select(VerificationRun)
            .where(VerificationRun.kind == "search")
            .order_by(VerificationRun.started_at.desc())
            .limit(20)
        ).all()
    )
    run_ids = [run.id for run in runs]
    counts: dict[str, tuple[int, int]] = {}
    if run_ids:
        grouped = db.execute(
            select(RunLead.run_id, RunLead.is_new, func.count(RunLead.lead_id))
            .where(RunLead.run_id.in_(run_ids))
            .group_by(RunLead.run_id, RunLead.is_new)
        ).all()
        for run_id, is_new, count in grouped:
            total, fresh = counts.get(run_id, (0, 0))
            total += int(count)
            if is_new:
                fresh += int(count)
            counts[run_id] = (total, fresh)
    payload = []
    for run in runs:
        if run.id in counts:
            total, fresh = counts[run.id]
        else:
            total = run.results_count
            fresh = 0
            if run.started_at is not None:
                newer_starts = [
                    item.started_at
                    for item in runs
                    if item.started_at and item.started_at > run.started_at
                ]
                window = [Lead.first_seen_at >= run.started_at]
                if newer_starts:
                    window.append(Lead.first_seen_at < min(newer_starts))
                fresh = int(db.scalar(select(func.count(Lead.id)).where(*window)) or 0)
        payload.append(
            {
                "id": run.id,
                "city": run.city,
                "status": run.status,
                "started_at": run.started_at,
                "results_count": total,
                "new_count": fresh,
            }
        )
    return {
        "cities": cities,
        "categories": categories,
        "runs": payload,
    }


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
