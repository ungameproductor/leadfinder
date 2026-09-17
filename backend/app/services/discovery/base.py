from __future__ import annotations

from typing import Protocol

from app.schemas import Coordinates, PlaceCandidate, PlaceDetails


class DiscoveryProvider(Protocol):
    name: str

    def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_m: int,
        max_results: int = 20,
    ) -> list[PlaceCandidate]: ...

    def get_place_details(self, external_id: str) -> PlaceDetails | None: ...


class DiscoveryError(RuntimeError):
    pass
