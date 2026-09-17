# Sviluppo

## Convenzioni

- Python 3.12+, type hints, Pydantic v2, SQLAlchemy 2.
- Domain logic nei `services`; adapter in `discovery`; I/O HTTP/DB isolati.
- Segreti solo in environment. I log passano da `utils.redact`.
- Test accanto alle funzionalità core (`backend/tests`).

## Comandi

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
uvicorn app.main:app --reload --app-dir backend
```

Frontend (sviluppo):

```bash
cd frontend
npm install
npm run dev
```

Vite fa proxy di `/api` verso `http://127.0.0.1:8000`.

## Troubleshooting

- **Nessun risultato Google**: verificare Places API + Geocoding abilitate e fatturazione; in assenza di chiave usare `DISCOVERY_PROVIDER=mock`.
- **Coordinate mancanti**: non inserire valori inventati; lasciare vuoti `SEARCH_LATITUDE` / `SEARCH_LONGITUDE` e usare il geocoding.
- **robots.txt blocca il crawl**: comportamento atteso; `website_status=blocked`.
- **Database locked**: un solo processo Uvicorn in locale è sufficiente (`--workers 1`).
