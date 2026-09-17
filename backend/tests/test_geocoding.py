from __future__ import annotations

import httpx
import respx

from app.services.discovery.geocoding import _nominatim_geocode_cached, geocode_city


@respx.mock
def test_nominatim_geocodes_italian_city(monkeypatch):
    monkeypatch.setattr("app.services.discovery.geocoding.get_settings", lambda: type("S", (), {
        "google_maps_api_key": "",
        "http_user_agent": "LeadFinder/1.0 test",
        "request_timeout_seconds": 5.0,
    })())
    _nominatim_geocode_cached.cache_clear()
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(
            200,
            json=[{"lat": "45.4642", "lon": "9.1900", "display_name": "Milano, Lombardia, Italia"}],
        )
    )
    coords = geocode_city("Milano")
    assert round(coords.latitude, 2) == 45.46
    assert round(coords.longitude, 2) == 9.19
    request = respx.calls.last.request
    assert b"countrycodes=it" in request.url.query or "countrycodes=it" in str(request.url)


@respx.mock
def test_unknown_city_raises(monkeypatch):
    monkeypatch.setattr("app.services.discovery.geocoding.get_settings", lambda: type("S", (), {
        "google_maps_api_key": "",
        "http_user_agent": "LeadFinder/1.0 test",
        "request_timeout_seconds": 5.0,
    })())
    _nominatim_geocode_cached.cache_clear()
    respx.get("https://nominatim.openstreetmap.org/search").mock(return_value=httpx.Response(200, json=[]))
    try:
        geocode_city("Cittàinesistentexyz")
        assert False, "expected error"
    except Exception as exc:
        assert "non trovata" in str(exc).lower() or "inesistente" in str(exc).lower() or "Città" in str(exc)
