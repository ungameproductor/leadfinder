from __future__ import annotations

from app.models.entities import Lead
from app.services.export.csv_export import CSV_FIELDS, leads_to_csv
from app.utils.redact import redact_mapping, redact_text


def test_csv_columns_and_excludes_dnc():
    keep = Lead(
        id="11111111-1111-1111-1111-111111111111",
        name="Panificio",
        category="negozio",
        source_provider="mock",
        lead_score=80,
        priority="A",
        website_status="no_website",
        contact_status="unknown",
    )
    skip = Lead(
        id="22222222-2222-2222-2222-222222222222",
        name="Opt-out",
        source_provider="mock",
        contact_status="do_not_contact",
    )
    csv_text = leads_to_csv([keep, skip])
    header = csv_text.splitlines()[0].split(",")
    assert header == CSV_FIELDS
    assert "Panificio" in csv_text
    assert "Opt-out" not in csv_text
    assert "api_key" not in csv_text.lower()
    assert "GOOGLE" not in csv_text


def test_secrets_not_in_redacted_logs():
    text = redact_text("Using GOOGLE_MAPS_API_KEY=AIzaSecretToken123 Bearer abc.def")
    assert "AIzaSecretToken123" not in text
    assert "***" in text
    mapping = redact_mapping({"google_maps_api_key": "AIzaXXX", "query": "ristorante"})
    assert mapping["google_maps_api_key"] == "***"
    assert mapping["query"] == "ristorante"
