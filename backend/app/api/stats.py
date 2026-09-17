from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.entities import get_db
from app.repositories import lead_repo
from app.schemas import StatsOut

router = APIRouter()


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> StatsOut:
    return StatsOut(**lead_repo.stats(db))
