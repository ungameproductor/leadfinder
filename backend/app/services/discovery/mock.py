from __future__ import annotations

from app.schemas import Coordinates, PlaceCandidate, PlaceDetails
from app.services.discovery.base import DiscoveryProvider

# Coordinate documentate solo per il dataset mock (centro Brindisi, fonte ISTAT/OSM approssimata).
MOCK_CENTER = Coordinates(latitude=40.6383, longitude=17.9458)

MOCK_PLACES: list[PlaceCandidate] = [
    PlaceCandidate(
        external_id="mock-panificio-corso",
        name="Panificio del Corso",
        category="negozio",
        address="Corso Roma 12, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6391,
        longitude=17.9452,
        phone="+39 0831 111001",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-pizzeria-mare",
        name="Pizzeria Marechiaro",
        category="pizzeria",
        address="Via del Mare 8, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6360,
        longitude=17.9489,
        phone="+39 0831 111002",
        website="https://example.com",
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-dentista-adriatico",
        name="Studio Dentistico Adriatico",
        category="dentista",
        address="Via Verdi 21, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6402,
        longitude=17.9411,
        phone="+39 0831 111003",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-bar-stazione",
        name="Bar Stazione",
        category="bar",
        address="Piazza Crispi 3, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6348,
        longitude=17.9387,
        phone="+39 0831 111004",
        website="https://this-domain-should-not-exist-xyz-brindisi.invalid",
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-palestra-ionio",
        name="Palestra Ionio",
        category="palestra",
        address="Via Appia 104, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6319,
        longitude=17.9365,
        phone="+39 0831 111005",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-estetico-perla",
        name="Centro Estetico Perla",
        category="centro_estetico",
        address="Via San Lorenzo 7, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6377,
        longitude=17.9433,
        phone=None,
        website="https://example.org",
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-agenzia-casa",
        name="Agenzia Casa Brindisi",
        category="agenzia_immobiliare",
        address="Via Santi 15, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6388,
        longitude=17.9471,
        phone="+39 0831 111007",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-officina-meccanica",
        name="Officina Meccanica Greco",
        category="officina",
        address="Via Provinciale per Mesagne 44, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6295,
        longitude=17.9302,
        phone="+39 0831 111008",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-bb-porto",
        name="B&B Porto Vecchio",
        category="bb",
        address="Via del Porto 2, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6415,
        longitude=17.9510,
        phone="+39 0831 111009",
        website="https://example.net",
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-fotografo-luce",
        name="Fotografo Luce Salentina",
        category="fotografo",
        address="Via De Leo 9, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6399,
        longitude=17.9440,
        phone="+39 0831 111010",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-ristorante-scoglio",
        name="Ristorante Lo Scoglio",
        category="ristorante",
        address="Lungomare Regina Margherita 18, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6428,
        longitude=17.9522,
        phone="+39 0831 111011",
        website=None,
        provider="mock",
    ),
    PlaceCandidate(
        external_id="mock-parrucchiere-taglio",
        name="Parrucchieri Taglio Vivo",
        category="parrucchiere",
        address="Via Osanna 5, 72100 Brindisi",
        city="Brindisi",
        postal_code="72100",
        latitude=40.6372,
        longitude=17.9420,
        phone="+39 0831 111012",
        website="https://example.com/shop",
        provider="mock",
    ),
]


def _shift_place(place: PlaceCandidate, center: Coordinates) -> PlaceCandidate:
    shifted = place.model_copy()
    if place.latitude is not None and place.longitude is not None:
        shifted.latitude = center.latitude + (place.latitude - MOCK_CENTER.latitude)
        shifted.longitude = center.longitude + (place.longitude - MOCK_CENTER.longitude)
    return shifted


class MockDiscoveryProvider:
    name = "mock"

    def search_places(
        self,
        query: str,
        center: Coordinates,
        radius_m: int,
        max_results: int = 20,
    ) -> list[PlaceCandidate]:
        needle = query.lower().strip()
        results: list[PlaceCandidate] = []
        for place in MOCK_PLACES:
            cat = (place.category or "").replace("_", " ").lower()
            hay = " ".join(filter(None, [place.name, place.category])).lower()
            if cat and cat in needle:
                results.append(_shift_place(place, center))
            elif any(token in hay for token in needle.split() if len(token) > 3):
                results.append(_shift_place(place, center))
        if not results:
            results = [_shift_place(place, center) for place in MOCK_PLACES]
        return results[:max_results]

    def get_place_details(self, external_id: str) -> PlaceDetails | None:
        for place in MOCK_PLACES:
            if place.external_id == external_id:
                return PlaceDetails(**place.model_dump())
        return None
