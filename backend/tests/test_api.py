from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

from app.models.entities import Lead
from app.schemas import Coordinates, PlaceCandidate, SearchRequest
from app.services.jobs.pipeline import run_search_job
from app.repositories import lead_repo, run_repo


def test_health_and_categories(client: TestClient):
    assert client.get("/api/health").json()["status"] == "ok"
    data = client.get("/api/config/categories").json()
    assert data["location"]["country"] == "Italy"
    assert any(item["id"] == "ristorante" for item in data["categories"])


def test_leads_crud_and_stats(client: TestClient, db):
    lead = Lead(name="Test Lead", category="bar", source_provider="mock", lead_score=42, priority="B")
    db.add(lead)
    db.commit()
    lead_id = lead.id

    listed = client.get("/api/leads").json()
    assert listed["total"] >= 1
    detail = client.get(f"/api/leads/{lead_id}").json()
    assert detail["name"] == "Test Lead"
    patched = client.patch(f"/api/leads/{lead_id}", json={"manual_status": "confirmed", "notes": "ok"}).json()
    assert patched["manual_status"] == "confirmed"
    stats = client.get("/api/stats").json()
    assert stats["total"] >= 1
    csv_text = client.post("/api/export/csv").text
    assert "company_name" in csv_text


@respx.mock
def test_search_job_idempotent_with_mock(client: TestClient, db, monkeypatch):
    respx.route().mock(return_value=httpx.Response(200, text="<html></html>"))

    def fake_search(self, query, center, radius_m, max_results=20):
        return [
            PlaceCandidate(
                external_id="idem-1",
                name="Idem Bar",
                category="bar",
                address="Via Test 1, 72100 Brindisi",
                city="Brindisi",
                postal_code="72100",
                phone="+39 0831 999001",
                website=None,
                provider="mock",
            )
        ]

    monkeypatch.setattr("app.services.discovery.mock.MockDiscoveryProvider.search_places", fake_search)
    monkeypatch.setattr(
        "app.services.jobs.pipeline.geocode_city",
        lambda city, country="Italy", postal_code=None: Coordinates(latitude=45.46, longitude=9.19),
    )

    payload = SearchRequest(
        city="Milano",
        radius_km=10,
        categories=["bar"],
        max_results=5,
        provider="mock",
        verify_websites=False,
    )
    import json as jsonlib

    run = run_repo.create_run(
        db,
        kind="search",
        provider="mock",
        query="bar",
        city="Milano",
        radius_km=10,
        categories_json=jsonlib.dumps(["bar"]),
    )
    run_search_job(db, run.id, payload)
    run_search_job(db, run.id, payload)
    rows, total = lead_repo.list_leads(db, q="Idem Bar")
    assert total == 1
    assert rows[0].priority == "A"
    scoped, scoped_total = lead_repo.list_leads(db, run_id=run.id, only_new=True)
    assert scoped_total == 1
    assert scoped[0].name == "Idem Bar"
    facets = client.get("/api/leads/facets").json()
    assert "Milano" in facets["cities"]
    assert any(item["id"] == run.id for item in facets["runs"])


def test_search_endpoint_does_not_block(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.search.job_runner.submit", lambda *args, **kwargs: None)
    response = client.post(
        "/api/search",
        json={"city": "Milano", "radius_km": 5, "categories": ["bar"], "verify_websites": False},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] in {"queued", "running"}
    poll = client.get(f"/api/search/{body['id']}")
    assert poll.status_code == 200
