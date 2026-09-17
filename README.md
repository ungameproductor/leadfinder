# Lead Finder

Applicazione locale per individuare e qualificare potenziali clienti (sviluppo web, restyling, web app, software) in **qualsiasi città d'Italia**: inserisci il comune come epicentro e il raggio in km.

Non è uno scraper di Google Maps. La discovery usa un provider astratto: **mock** (demo/test) o **Google Places API ufficiale**. La verifica di sito ed email avviene solo su pagine pubbliche, con rispetto di `robots.txt`, timeout e limiti di crawl.

## Avvio rapido

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Backend + UI (dopo build del frontend, oppure UI API-only)
cd frontend && npm install && npm run build && cd ..
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). Senza `GOOGLE_MAPS_API_KEY` il provider è `mock` (dati di esempio intorno all'epicentro scelto). L'epicentro è geocodificato (Nominatim o Google).

### Sviluppo frontend

Terminale 1: `uvicorn app.main:app --app-dir backend --reload`  
Terminale 2: `cd frontend && npm install && npm run dev` → [http://127.0.0.1:5173](http://127.0.0.1:5173)

### Docker

```bash
cp .env.example .env
docker compose up --build
```

## Variabili ambiente

| Variabile | Descrizione |
| --- | --- |
| `APP_ENV` | `development` o `production` |
| `DATABASE_URL` | Default `sqlite:///./data/leads.db` |
| `DISCOVERY_PROVIDER` | `mock` o `google` |
| `GOOGLE_MAPS_API_KEY` | Chiave Maps Platform (Places + Geocoding) |
| `SEARCH_CITY` / `SEARCH_RADIUS_KM` | Suggerimento UI (l'epicentro si sceglie a ogni ricerca) |
| `MAX_RESULTS_PER_QUERY` | Limite risultati per categoria |
| `REQUEST_TIMEOUT_SECONDS` | Timeout HTTP |
| `CRAWL_MAX_PAGES_PER_DOMAIN` | Pagine max per sito |
| `CRAWL_DELAY_SECONDS` | Pausa tra richieste allo stesso dominio |
| `HTTP_USER_AGENT` | User-Agent identificabile |

I pesi di scoring sono in `config/scoring.yaml` (modificabili senza toccare il codice).

## Uso

1. **Ricerca**: città epicentro, raggio, categorie, avvia il job.
2. **Dashboard**: volumi A/B/C, senza sito, siti problematici, email trovate.
3. **Lead**: filtra, apri il dettaglio, conferma/scarta, note, priorità.
4. **Export CSV** dalla lista filtrata (esclude `do_not_contact`).

Il tool **non invia email** e non fissa prezzi. Lo score è un segnale interno per la qualificazione umana.

## Test

```bash
pytest
```

## Documentazione

- [Architettura](docs/architecture.md)
- [Data policy](docs/data-policy.md)
- [Provider](docs/providers.md)
- [Scoring](docs/scoring.md)
- [Sviluppo](docs/development.md)
