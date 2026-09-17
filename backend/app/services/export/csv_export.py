from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from app.models.entities import Lead

CSV_FIELDS = [
    "lead_id",
    "company_name",
    "category",
    "address",
    "city",
    "postal_code",
    "latitude",
    "longitude",
    "phone",
    "email",
    "email_source_url",
    "website",
    "website_status",
    "website_quality_score",
    "lead_score",
    "priority",
    "suggested_service",
    "source_provider",
    "source_external_id",
    "first_seen_at",
    "last_checked_at",
    "notes",
]


def leads_to_csv(leads: Iterable[Lead]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        if lead.contact_status == "do_not_contact":
            continue
        writer.writerow(
            {
                "lead_id": lead.id,
                "company_name": lead.name,
                "category": lead.category or "",
                "address": lead.address or "",
                "city": lead.city or "",
                "postal_code": lead.postal_code or "",
                "latitude": lead.latitude if lead.latitude is not None else "",
                "longitude": lead.longitude if lead.longitude is not None else "",
                "phone": lead.phone or "",
                "email": lead.public_email or "",
                "email_source_url": lead.email_source_url or "",
                "website": lead.website or "",
                "website_status": lead.website_status,
                "website_quality_score": lead.website_quality_score if lead.website_quality_score is not None else "",
                "lead_score": lead.lead_score,
                "priority": lead.priority,
                "suggested_service": lead.suggested_service or "",
                "source_provider": lead.source_provider,
                "source_external_id": lead.source_external_id or "",
                "first_seen_at": lead.first_seen_at.isoformat() if lead.first_seen_at else "",
                "last_checked_at": lead.last_checked_at.isoformat() if lead.last_checked_at else "",
                "notes": lead.notes or "",
            }
        )
    return buffer.getvalue()
