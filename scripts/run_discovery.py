#!/usr/bin/env python3
"""Avvia una ricerca da CLI (stesso pipeline dell'UI)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.entities import SessionLocal, init_db  # noqa: E402
from app.repositories import run_repo  # noqa: E402
from app.schemas import SearchRequest  # noqa: E402
from app.services.jobs.pipeline import run_search_job  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Discovery lead per città italiana")
    parser.add_argument("--city", required=True, help="Comune epicentro, es. Milano")
    parser.add_argument("--radius-km", type=float, default=10)
    parser.add_argument("--categories", nargs="*", default=["ristorante", "pizzeria", "bar"])
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    payload = SearchRequest(
        city=args.city,
        radius_km=args.radius_km,
        categories=args.categories,
        max_results=args.max_results,
        provider=args.provider,
        verify_websites=not args.no_verify,
    )
    run = run_repo.create_run(
        db,
        kind="search",
        provider=payload.provider or "mock",
        query=",".join(payload.categories),
        city=payload.city,
        postal_code=payload.postal_code,
        radius_km=payload.radius_km,
        categories_json=json.dumps(payload.categories),
    )
    run_search_job(db, run.id, payload)
    db.refresh(run)
    print(f"status={run.status} results={run.results_count} message={run.message}")
    db.close()


if __name__ == "__main__":
    main()
