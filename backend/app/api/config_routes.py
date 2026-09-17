from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.services.discovery.categories import load_categories

router = APIRouter()


@router.get("/config/categories")
def categories() -> dict:
    settings = get_settings()
    return {
        "location": {
            "city": settings.search_city,
            "country": settings.search_country,
            "postal_code": settings.search_postal_code or None,
            "latitude": settings.search_latitude,
            "longitude": settings.search_longitude,
            "radius_km": settings.search_radius_km,
        },
        "provider": settings.discovery_provider,
        "has_google_key": bool(settings.google_maps_api_key),
        "categories": load_categories(),
        "max_results_per_query": settings.max_results_per_query,
    }
