from __future__ import annotations

import json

import httpx
import respx
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.models.entities import Lead
from app.repositories import run_repo
from app.schemas import Coordinates, PlaceCandidate, SearchRequest
from app.services.jobs.pipeline import run_search_job


@respx.mock
def test_end_to_end_mock_provider(db: Session, monkeypatch):
    home = """
    <html><head><meta name="viewport" content="width=device-width"></head>
    <body><a href="mailto:info@locale-test.example">mail</a></body></html>
    """
    respx.get("https://locale-test.example/robots.txt").mock(return_value=httpx.Response(200, text="User-agent: *\nAllow: /\n"))
    respx.get("https://locale-test.example").mock(
        return_value=httpx.Response(200, text=home, headers={"content-type": "text/html"})
    )
    respx.get(url__startswith="https://locale-test.example/").mock(
        return_value=httpx.Response(200, text=home, headers={"content-type": "text/html"})
    )

    def fake_search(self, query, center, radius_m, max_results=20):
        return [
            PlaceCandidate(
                external_id="e2e-1",
                name="Ristorante Demo",
                category="ristorante",
                address="Via Demo 1, 72100 Brindisi",
                city="Brindisi",
                postal_code="72100",
                phone="0831 123456",
                website="https://locale-test.example",
                provider="mock",
            ),
            PlaceCandidate(
                external_id="e2e-2",
                name="Pizzeria Senza Sito",
                category="pizzeria",
                address="Via Demo 2, 72100 Brindisi",
                city="Brindisi",
                postal_code="72100",
                phone="0831 654321",
                website=None,
                provider="mock",
            ),
        ]

    monkeypatch.setattr("app.services.discovery.mock.MockDiscoveryProvider.search_places", fake_search)
    monkeypatch.setattr(
        "app.services.jobs.pipeline.geocode_city",
        lambda city, country="Italy", postal_code=None: Coordinates(latitude=45.4642, longitude=9.19),
    )

    payload = SearchRequest(
        city="Milano",
        radius_km=8,
        categories=["ristorante", "pizzeria"],
        provider="mock",
        verify_websites=True,
        max_results=10,
    )
    run = run_repo.create_run(
        db,
        kind="search",
        provider="mock",
        query="ristorante,pizzeria",
        city="Milano",
        radius_km=8,
        categories_json=json.dumps(["ristorante", "pizzeria"]),
    )
    run_search_job(db, run.id, payload)
    db.refresh(run)
    leads = list(db.scalars(select(Lead)))
    assert run.status in {"completed", "completed_with_errors"}
    assert len(leads) == 2
    by_name = {lead.name: lead for lead in leads}
    assert by_name["Pizzeria Senza Sito"].website_status == "no_website"
    assert by_name["Pizzeria Senza Sito"].priority == "A"
    assert by_name["Ristorante Demo"].public_email == "info@locale-test.example"
    assert by_name["Ristorante Demo"].email_source_url
    assert by_name["Ristorante Demo"].city == "Milano"
    assert by_name["Ristorante Demo"].suggested_service
