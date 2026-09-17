from __future__ import annotations

import pytest

from app.services.enrichment.normalize import (
    extract_postal_code,
    normalize_address,
    normalize_domain,
    normalize_name,
    normalize_phone,
    normalize_website,
)


def test_normalize_phone_italian():
    assert normalize_phone("0831 111001") == "+390831111001"
    assert normalize_phone("+39 0831 111002") == "+390831111002"
    assert normalize_phone("0039 0831111003") == "+390831111003"
    assert normalize_phone("123") is None


def test_normalize_name_and_address():
    assert normalize_name("Pizzeria  Marechiaro!") == "pizzeria marechiaro"
    assert "roma" in normalize_address("Corso Roma 12, 72100 Brindisi")
    assert "corso" not in normalize_address("Corso Roma 12")


def test_normalize_website_and_domain():
    assert normalize_website("example.com") == "https://example.com"
    assert normalize_domain("https://www.Example.com/path") == "example.com"
    assert extract_postal_code("Via Verdi 21, 72100 Brindisi") == "72100"
