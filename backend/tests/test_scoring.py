from __future__ import annotations

from app.services.scoring.engine import score_lead


def test_no_website_is_priority_a():
    result = score_lead(
        website_status="no_website",
        quality_score=None,
        has_email=True,
        has_phone=True,
        has_address=True,
    )
    assert result.score >= 70
    assert result.priority == "A"
    assert result.suggested_service == "Sviluppo sito web"
    assert any("Nessun sito" in item for item in result.evidence)


def test_modern_site_lowers_score():
    result = score_lead(
        website_status="reachable",
        quality_score=88,
        responsive=True,
        has_email=True,
        has_phone=True,
        has_address=True,
    )
    assert result.priority in {"B", "C"}
    assert result.suggested_service == "Analisi preliminare"


def test_weights_are_configurable():
    config = {
        "weights": {"no_website": 5, "phone": 0, "public_email": 0, "local_presence": 0},
        "thresholds": {"priority_a": 70, "priority_b": 40, "quality_very_low": 35, "quality_modern": 75},
    }
    result = score_lead(website_status="no_website", quality_score=None, config=config)
    assert result.score == 5
    assert result.priority == "C"
