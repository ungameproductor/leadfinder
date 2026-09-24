from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.models.entities import get_db
from app.repositories import lead_repo
from app.services.export.csv_export import leads_to_csv

router = APIRouter()


@router.post("/export/csv")
def export_csv(
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
) -> PlainTextResponse:
    rows, _total = lead_repo.list_leads(
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
        exclude_dnc=True,
        limit=5000,
    )
    csv_text = leads_to_csv(rows)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="lead-finder-brindisi.csv"'},
    )
