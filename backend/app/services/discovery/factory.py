from __future__ import annotations

from app.config import Settings, get_settings
from app.services.discovery.base import DiscoveryProvider
from app.services.discovery.google_places import GooglePlacesProvider
from app.services.discovery.mock import MockDiscoveryProvider


def get_provider(name: str | None = None, settings: Settings | None = None) -> DiscoveryProvider:
    settings = settings or get_settings()
    chosen = (name or settings.discovery_provider or "mock").lower().strip()
    if chosen == "google":
        if not settings.google_maps_api_key:
            return MockDiscoveryProvider()
        return GooglePlacesProvider(settings)
    return MockDiscoveryProvider()
