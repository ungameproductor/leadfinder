# Data policy e compliance

Questo documento descrive dati raccolti, fonti, retention e limiti d'uso. Non sostituisce una consulenza legale. Prima di contatti commerciali vanno rispettati GDPR, normativa italiana e termini dei provider.

## Finalità

Supportare la qualificazione commerciale B2B/local business per servizi di sviluppo web e software. I dati servono a capire se un'attività ha un sito, se è raggiungibile e come contattarla tramite recapiti già pubblici.

## Dati raccolti

| Dato | Fonte tipica | Necessario? |
| --- | --- | --- |
| Nome attività, categoria, indirizzo, coordinate | Provider Places / mock | Sì |
| Telefono e sito | Provider, se esposti pubblicamente | Sì, se disponibili |
| Email pubblica | Pagine pubbliche del sito (homepage, contatti, about, privacy) | Solo se già pubblicata |
| Score, evidenze tecniche, note interne | Calcolo locale / operatore | Sì, interni |
| Stato contatto / opt-out | Operatore | Sì, per non ricontattare |

Non si raccolgono: password, credenziali, dati da aree autenticate, dati da data broker, dati personali non necessari (es. recapiti di persone fisiche non pubblicati come contatto aziendale).

## Fonti ammesse

- API ufficiali configurate (Google Places / Geocoding) nei limiti di licenza e quota.
- Pagine pubbliche del sito dell'attività, con rispetto di `robots.txt`, timeout, rate limit e tetto di pagine.
- Inserimento e correzione manuale da parte dell'operatore.

Fonti non ammesse: scraping del DOM di Google Maps, browser automation per eludere CAPTCHA/login/paywall, proxy rotation, bypass anti-bot, fonti illegali.

## Conservazione della provenienza

Ogni lead memorizza `source_provider`, `source_external_id`, URL di provenienza dell'email, timestamp di prima vista e ultimo controllo. Le evidenze di scoring sono testuali e verificabili.

## Retention e cancellazione

- Retention predefinita: 24 mesi dall'ultimo controllo, salvo obbligo diverso.
- Cancellazione: impostare lo stato manuale `do_not_contact` o eliminare il record dal database locale (`data/leads.db`).
- Export CSV non include segreti, token o chiavi API.

## Opt-out e contatto

- Stato `contact_status=do_not_contact` esclude il lead da export e da ulteriori verifiche automatiche.
- L'MVP **non invia email** e **non automatizza campagne**.
- Qualsiasi outreach resta attività umana, dopo verifica di base giuridica e registro delle opposizioni ove applicabile.

## Sicurezza

- Segreti solo in variabili d'ambiente.
- Logging con redazione di API key e token.
- Se l'app è esposta in rete, proteggere gli endpoint (reverse proxy, autenticazione). Nell'MVP locale non è prevista autenticazione.
