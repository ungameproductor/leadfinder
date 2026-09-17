from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import Lead
from app.repositories import lead_repo, run_repo
from app.schemas import Coordinates, PlaceCandidate, SearchRequest
from app.services.discovery.base import DiscoveryError
from app.services.discovery.categories import load_categories, search_query_for
from app.services.discovery.factory import get_provider
from app.services.discovery.geocoding import geocode_city
from app.services.scoring.engine import score_lead
from app.services.website.checker import WebsiteChecker, WebsiteCheck

logger = logging.getLogger(__name__)


def apply_check_to_lead(lead: Lead, check: WebsiteCheck) -> None:
    lead.website_status = check.status
    lead.website_quality_score = check.quality_score
    lead.website_quality_evidence = json.dumps(check.quality_evidence, ensure_ascii=False)
    lead.quality_data_insufficient = check.insufficient
    lead.email_status = check.email_status
    if check.emails:
        lead.public_email, lead.email_source_url = check.emails[0]
    if check.final_url and check.status == "reachable":
        lead.website = check.final_url
    result = score_lead(
        website_status=lead.website_status,
        quality_score=lead.website_quality_score,
        responsive=check.responsive,
        has_email=bool(lead.public_email),
        has_phone=bool(lead.phone),
        has_address=bool(lead.address),
        quality_insufficient=lead.quality_data_insufficient,
        notes=lead.notes,
    )
    lead.lead_score = result.score
    lead.priority = result.priority
    lead.suggested_service = result.suggested_service
    lead.scoring_evidence = json.dumps(result.evidence, ensure_ascii=False)
    lead.last_checked_at = datetime.now(timezone.utc)
    lead.phase_status = "scored"


def resolve_center(request: SearchRequest, provider) -> Coordinates:
    if request.latitude is not None and request.longitude is not None:
        return Coordinates(latitude=request.latitude, longitude=request.longitude)
    return geocode_city(request.city, request.country, request.postal_code or None)


def run_search_job(db: Session, run_id: str, request: SearchRequest) -> None:
    run = run_repo.get_run(db, run_id)
    if not run:
        return
    run_repo.mark_running(db, run)
    settings = get_settings()
    provider_name = request.provider or settings.discovery_provider
    provider = get_provider(provider_name)
    errors: list[str] = []
    usage = {"provider": getattr(provider, "name", provider_name)}
    created = 0
    processed = 0

    try:
        center = resolve_center(request, provider)
        run.latitude = center.latitude
        run.longitude = center.longitude
        db.commit()
    except DiscoveryError as exc:
        run_repo.finish_run(db, run, status="failed", results=0, errors=[str(exc)], api_usage=usage, message=str(exc))
        return

    categories = request.categories or [item["id"] for item in load_categories()]
    radius_m = int(request.radius_km * 1000)
    all_candidates: list[PlaceCandidate] = []

    for category in categories:
        query = f"{search_query_for(category)} {request.city}"
        try:
            found = provider.search_places(query, center, radius_m, max_results=min(request.max_results, settings.max_results_per_query))
            for item in found:
                if not item.category:
                    item.category = category
                item.city = request.city
                if item.provider == "mock" and item.address:
                    item.address = item.address.replace("Brindisi", request.city).replace("72100 ", "")
                all_candidates.append(item)
        except Exception as exc:
            logger.warning("category_search_failed", extra={"category": category, "error": str(exc)})
            errors.append(f"{category}: {exc}")

    if hasattr(provider, "usage"):
        usage.update(getattr(provider, "usage"))

    checker = WebsiteChecker(settings) if request.verify_websites else None
    seen_ids: set[str] = set()

    for candidate in all_candidates:
        processed += 1
        try:
            lead, is_new, _confidence = lead_repo.upsert_candidate(db, candidate)
            if lead.contact_status == "do_not_contact":
                continue
            if is_new:
                created += 1
            if lead.id not in seen_ids:
                seen_ids.add(lead.id)
                if checker:
                    check = checker.check(lead.website)
                    apply_check_to_lead(lead, check)
                else:
                    result = score_lead(
                        website_status=lead.website_status or ("no_website" if not lead.website else "unknown"),
                        quality_score=lead.website_quality_score,
                        has_email=bool(lead.public_email),
                        has_phone=bool(lead.phone),
                        has_address=bool(lead.address),
                        quality_insufficient=bool(lead.website) and lead.website_status in {"unknown", "redirect_only"},
                        notes=lead.notes,
                    )
                    lead.lead_score = result.score
                    lead.priority = result.priority
                    lead.suggested_service = result.suggested_service
                    lead.scoring_evidence = json.dumps(result.evidence, ensure_ascii=False)
            db.commit()
        except Exception as exc:
            db.rollback()
            errors.append(f"{candidate.name}: {exc}")
            logger.warning("lead_pipeline_failed", extra={"name": candidate.name, "error": str(exc)})
        run_repo.update_progress(db, run, processed, len(seen_ids), message=f"Elaborati {processed} candidati")

    status = "completed" if not errors or seen_ids else "completed_with_errors"
    run_repo.finish_run(
        db,
        run,
        status=status,
        results=len(seen_ids),
        errors=errors,
        api_usage=usage,
        message=f"{len(seen_ids)} lead unici, {created} nuovi",
    )


def verify_lead(db: Session, lead: Lead) -> Lead:
    if lead.contact_status == "do_not_contact":
        return lead
    check = WebsiteChecker().check(lead.website)
    apply_check_to_lead(lead, check)
    db.commit()
    db.refresh(lead)
    return lead
