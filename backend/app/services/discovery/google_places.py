from __future__ import annotations

import logging

import httpx

from app.config import Settings, get_settings
from app.schemas import Coordinates, PlaceCandidate, PlaceDetails
from app.services.discovery.base import DiscoveryError
from app.utils.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.utils.http import retry_call

logger = logging.getLogger(__name__)

PLACES_SEARCH = "https://places.googleapis.com/v1/places:searchText"
PLACE_DETAILS = "https://places.googleapis.com/v1/places/{place_id}"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

FIELD_MASK_SEARCH = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.businessStatus",
    ]
)
FIELD_MASK_DETAILS = ",".join(
    [
        "id",
        "displayName",
        "formattedAddress",
        "location",
        "types",
        "nationalPhoneNumber",
        "internationalPhoneNumber",
        "websiteUri",
        "businessStatus",
    ]
)


class GooglePlacesProvider:
    name = "google"

    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self.breaker = CircuitBreaker()
        self.usage = {"search_calls": 0, "details_calls": 0, "geocode_calls": 0, "errors": 0}

    def _headers(self, field_mask: str) -> dict[str, str]:
        key = self.settings.google_maps_api_key
        if not key:
            raise DiscoveryError("GOOGLE_MAPS_API_KEY non configurata")
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": field_mask,
            "User-Agent": self.settings.http_user_agent,
        }

    def _client_or(self) -> httpx.Client:
        if self._client:
            return self._client
        return httpx.Client(timeout=self.settings.request_timeout_seconds)

    def geocode(self, city: str, postal_code: str, country: str) -> Coordinates:
        params = {
            "address": f"{postal_code} {city} {country}",
            "key": self.settings.google_maps_api_key,
        }
        client = self._client_or()
        owns = self._client is None
        try:

            def _call() -> httpx.Response:
                self.usage["geocode_calls"] += 1
                response = client.get(GEOCODE_URL, params=params)
                response.raise_for_status()
                return response

            try:
                response = self.breaker.call(lambda: retry_call(_call))
            except CircuitOpenError as exc:
                raise DiscoveryError(str(exc)) from exc
            payload = response.json()
            results = payload.get("results") or []
            if not results:
                raise DiscoveryError(f"Geocoding senza risultati per {city} {postal_code}")
            loc = results[0]["geometry"]["location"]
            return Coordinates(latitude=float(loc["lat"]), longitude=float(loc["lng"]))
        except DiscoveryError:
            raise
        except Exception as exc:
            self.usage["errors"] += 1
            logger.warning("geocode_failed", extra={"error": str(exc)})
            raise DiscoveryError(f"Geocoding non riuscito: {exc}") from exc
        finally:
            if owns:
                client.close()

    def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_m: int,
        max_results: int = 20,
    ) -> list[PlaceCandidate]:
        body = {
            "textQuery": query,
            "maxResultCount": min(max(max_results, 1), 20),
            "languageCode": "it",
            "regionCode": "IT",
            "locationBias": {
                "circle": {
                    "center": {"latitude": center.latitude, "longitude": center.longitude},
                    "radius": float(radius_m),
                }
            },
        }
        client = self._client_or()
        owns = self._client is None
        try:

            def _call() -> httpx.Response:
                self.usage["search_calls"] += 1
                response = client.post(PLACES_SEARCH, headers=self._headers(FIELD_MASK_SEARCH), json=body)
                response.raise_for_status()
                return response

            try:
                response = self.breaker.call(lambda: retry_call(_call))
            except CircuitOpenError as exc:
                raise DiscoveryError(str(exc)) from exc
            places = response.json().get("places") or []
            return [self._to_candidate(item, query) for item in places]
        except DiscoveryError:
            raise
        except Exception as exc:
            self.usage["errors"] += 1
            logger.warning("places_search_failed", extra={"error": str(exc), "query": query})
            raise DiscoveryError(f"Places search non riuscita: {exc}") from exc
        finally:
            if owns:
                client.close()

    def get_place_details(self, external_id: str) -> PlaceDetails | None:
        place_id = external_id.removeprefix("places/")
        url = PLACE_DETAILS.format(place_id=place_id)
        client = self._client_or()
        owns = self._client is None
        try:

            def _call() -> httpx.Response:
                self.usage["details_calls"] += 1
                response = client.get(url, headers=self._headers(FIELD_MASK_DETAILS))
                response.raise_for_status()
                return response

            response = self.breaker.call(lambda: retry_call(_call))
            return self._to_details(response.json())
        except Exception as exc:
            self.usage["errors"] += 1
            logger.warning("place_details_failed", extra={"error": str(exc), "id": external_id})
            return None
        finally:
            if owns:
                client.close()

    def _to_candidate(self, item: dict, query: str) -> PlaceCandidate:
        loc = item.get("location") or {}
        display = item.get("displayName") or {}
        address = item.get("formattedAddress")
        types = item.get("types") or []
        return PlaceCandidate(
            external_id=item.get("id") or "",
            name=display.get("text") or query,
            category=_category_from_types(types, query),
            address=address,
            city=_city_from_address(address),
            postal_code=_postal_from_address(address),
            latitude=loc.get("latitude"),
            longitude=loc.get("longitude"),
            phone=item.get("nationalPhoneNumber") or item.get("internationalPhoneNumber"),
            website=item.get("websiteUri"),
            provider="google",
        )

    def _to_details(self, item: dict) -> PlaceDetails:
        base = self._to_candidate(item, item.get("displayName", {}).get("text", ""))
        return PlaceDetails(
            **base.model_dump(),
            types=item.get("types") or [],
            raw_status=item.get("businessStatus"),
        )


def _postal_from_address(address: str | None) -> str | None:
    if not address:
        return None
    import re

    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None


def _city_from_address(address: str | None) -> str | None:
    if not address:
        return None
    import re

    match = re.search(r"\b\d{5}\s+([^,]+)", address)
    if match:
        return match.group(1).strip()
    return None


def _category_from_types(types: list[str], fallback: str) -> str:
    mapping = {
        "restaurant": "ristorante",
        "pizza_restaurant": "pizzeria",
        "bar": "bar",
        "hair_salon": "parrucchiere",
        "beauty_salon": "centro_estetico",
        "gym": "palestra",
        "dentist": "dentista",
        "physiotherapist": "fisioterapista",
        "real_estate_agency": "agenzia_immobiliare",
        "car_repair": "officina",
        "photographer": "fotografo",
        "lodging": "hotel",
        "bed_and_breakfast": "bb",
        "store": "negozio",
    }
    for t in types:
        if t in mapping:
            return mapping[t]
    return fallback.split(" ")[0]
