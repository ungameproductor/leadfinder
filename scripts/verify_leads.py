#!/usr/bin/env python3
"""Riesegue la verifica sito/email su lead esistenti."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.models.entities import Lead, SessionLocal, init_db  # noqa: E402
from app.services.jobs.pipeline import verify_lead  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica siti dei lead")
    parser.add_argument("--id", dest="lead_id", default=None)
    args = parser.parse_args()
    init_db()
    db = SessionLocal()
    if args.lead_id:
        leads = [db.get(Lead, args.lead_id)]
    else:
        leads = list(db.scalars(select(Lead).where(Lead.contact_status != "do_not_contact")))
    ok = 0
    for lead in leads:
        if not lead:
            continue
        verify_lead(db, lead)
        ok += 1
        print(f"{lead.name}: {lead.website_status} score={lead.lead_score} {lead.priority}")
    print(f"verificati={ok}")
    db.close()


if __name__ == "__main__":
    main()
