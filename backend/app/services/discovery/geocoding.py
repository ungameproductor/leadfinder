from __future__ import annotations

import logging
from functools import lru_cache

import httpx

from app.config import get_settings
from app.schemas import Coordinates
from app.services.discovery.base import DiscoveryError
from app.utils.http import retry_call

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_city(city: str, country: str = "Italy", postal_code: str | None = None) -> Coordinates:
    """Risolve un comune italiano in coordinate. Google se c'è la chiave, altrimenti Nominatim."""
    name = (city or "").strip()
    if not name:
        raise DiscoveryError("Indica una città italiana come epicentro")
    country = (country or "Italy").strip() or "Italy"
    cap = (postal_code or "").strip() or None
    settings = get_settings()
    if settings.google_maps_api_key:
        try:
            return _google_geocode(name, country, cap, settings.google_maps_api_key, settings)
        except DiscoveryError as exc:
            logger.warning("google_geocode_fallback_nominatim", extra={"error": str(exc)})
    return _nominatim_geocode(name, country, cap, settings)


def _query_label(city: str, postal_code: str | None, country: str) -> str:
    parts = [p for p in (postal_code, city, country) if p]
    return ", ".join(parts)


@lru_cache(maxsize=128)
def _nominatim_geocode_cached(query: str, user_agent: str, timeout: float) -> tuple[float, float]:
    with httpx.Client(timeout=timeout, headers={"User-Agent": user_agent, "Accept-Language": "it"}) as client:

        def _call() -> httpx.Response:
            response = client.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "it",
                    "addressdetails": 0,
                },
            )
            response.raise_for_status()
            return response

        response = retry_call(_call)
    results = response.json()
    if not results:
        raise DiscoveryError(f"Città non trovata in Italia: {query}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def _nominatim_geocode(city: str, country: str, postal_code: str | None, settings) -> Coordinates:
    query = _query_label(city, postal_code, country)
    try:
        lat, lon = _nominatim_geocode_cached(query, settings.http_user_agent, settings.request_timeout_seconds)
    except DiscoveryError:
        raise
    except Exception as exc:
        logger.warning("nominatim_failed", extra={"error": str(exc), "query": query})
        raise DiscoveryError(f"Geocoding non riuscito per {city}: {exc}") from exc
    return Coordinates(latitude=lat, longitude=lon)


def _google_geocode(city: str, country: str, postal_code: str | None, api_key: str, settings) -> Coordinates:
    address = _query_label(city, postal_code, country)
    with httpx.Client(timeout=settings.request_timeout_seconds) as client:

        def _call() -> httpx.Response:
            response = client.get(
                GOOGLE_GEOCODE_URL,
                params={
                    "address": address,
                    "components": "country:IT",
                    "language": "it",
                    "key": api_key,
                },
            )
            response.raise_for_status()
            return response

        response = retry_call(_call)
    payload = response.json()
    results = payload.get("results") or []
    if not results:
        raise DiscoveryError(f"Geocoding Google senza risultati per {city}")
    loc = results[0]["geometry"]["location"]
    return Coordinates(latitude=float(loc["lat"]), longitude=float(loc["lng"]))
