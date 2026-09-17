# Architettura — Lead Finder

## Scopo

Applicazione locale per discovery e qualificazione di attività economiche in Italia. L'utente imposta un comune come epicentro e un raggio in km. L'output è un elenco di lead con score commerciale, priorità A/B/C e suggerimento di servizio. Non è uno scraper di Google Maps.

## Componenti

```
UI (React)  →  API FastAPI  →  Job runner (thread)
                                  ├── DiscoveryProvider (mock | google)
                                  ├── Normalizzazione + deduplica
                                  ├── Website checker (HTTP + robots.txt)
                                  ├── Estrazione email pubbliche
                                  ├── Quality score + lead scoring
                                  └── SQLite via repository layer
```

| Layer | Responsabilità |
| --- | --- |
| UI | Dashboard, ricerca, lista/dettaglio lead, azioni manuali, export |
| API | Contratto HTTP interno, avvio job, query, patch, CSV |
| Jobs | Pipeline asincrona sostituibile in futuro con coda (Celery/RQ) |
| Discovery | Interfaccia astratta; adapter Google Places e mock |
| Website / enrichment | Verifica HTTP prudente, email pubbliche, evidenze |
| Scoring | Pesi in `config/scoring.yaml`, evidenze testuali |
| Persistence | Repository su SQLAlchemy; SQLite oggi, PostgreSQL dopo |

## Flusso

1. Configurazione (centro, raggio, categorie, limite).
2. Discovery attività via provider ufficiale o mock.
3. Normalizzazione e deduplicazione (place ID, nome+indirizzo, telefono, dominio).
4. Enrichment contatti già presenti nel provider.
5. Verifica sito, estrazione email, quality check.
6. Lead scoring e classificazione A/B/C.
7. Review manuale.
8. Export CSV.

Un errore su una singola attività non interrompe il job. I job sono idempotenti: i lead già noti vengono aggiornati, non duplicati.

## Job in background

`POST /api/search` e `POST /api/leads/{id}/verify` non bloccano la request. Lo stato vive in `verification_runs`. L'interfaccia `JobRunner` è sostituibile.

## Estensioni previste

PostgreSQL, worker separato, più provider, metriche PageSpeed, CRM, mappa. Playwright non è usato nell'MVP e non va introdotto per aggirare limiti o sistemi anti-bot.
