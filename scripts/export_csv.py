#!/usr/bin/env python3
"""Esporta i lead in CSV."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.entities import SessionLocal, init_db  # noqa: E402
from app.repositories import lead_repo  # noqa: E402
from app.services.export.csv_export import leads_to_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CSV lead")
    parser.add_argument("--out", default="data/leads.csv")
    parser.add_argument("--priority", default=None)
    args = parser.parse_args()
    init_db()
    db = SessionLocal()
    rows, _ = lead_repo.list_leads(db, priority=args.priority, exclude_dnc=True, limit=5000)
    csv_text = leads_to_csv(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(csv_text, encoding="utf-8")
    print(f"scritto {out} ({len(rows)} righe, DNC esclusi)")
    db.close()


if __name__ == "__main__":
    main()
