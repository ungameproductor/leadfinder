# Provider di discovery

## Principio

Il dominio applicativo parla di `PlaceCandidate` / `PlaceDetails`. Non dipende da Google. Ogni fonte implementa `DiscoveryProvider`.

## Provider supportati

### `mock` (predefinito senza chiave)

Dati di esempio per sviluppo, test e demo, riposizionati intorno all'epicentro geocodificato. Non rappresenta un elenco reale di attività.

### `google` (opzionale, ufficiale)

Usa Google Maps Platform:

- Geocoding API per risolvere il comune epicentro (alternativa: Nominatim, solo Italia).
- Places API (New): `places:searchText` e Place Details.

Campi richiesti (field mask): identificativo, nome, indirizzo, coordinate, tipi, telefono nazionale, URI sito. Non si richiedono campi non necessari.

Configurazione:

```
DISCOVERY_PROVIDER=google
GOOGLE_MAPS_API_KEY=...
```

Abilitare in Google Cloud le API Places e Geocoding. I costi dipendono dal listino Google; l'applicazione registra `api_usage` (chiamate, errori) quando disponibile e **non** incorpora prezzi fissi nel codice.

Limiti: quote, ToS, attributi richiesti dal provider. Se un campo non è restituito, resta vuoto. Non si inventano dati.

## Interfaccia

```python
class DiscoveryProvider(Protocol):
    def search_places(self, query, center, radius_m, max_results) -> list[PlaceCandidate]: ...
    def get_place_details(self, external_id) -> PlaceDetails | None: ...
```

## Cosa non è un provider

Browser automation, scraping HTML di Maps, rotazione proxy, elusione di CAPTCHA o rate limit. Se una funzione non è supportata dall'API, si documenta un TODO e si lascia il campo vuoto.
