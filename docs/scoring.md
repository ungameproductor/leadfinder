# Scoring e priorità

I pesi vivono in `config/scoring.yaml`. Modificarli non richiede cambiamenti al codice. Ogni regola produce un'evidenza testuale.

## Website quality score (0–100)

Indicativo, separato dal lead score. Non afferma che un sito è «vecchio» senza evidenze.

Penalità: HTTPS assente/problematico, irraggiungibilità, viewport assente, tecnologia evidentemente obsoleta (es. Frameset, Flash), errori HTTP, CTA/contatti assenti, TTFB molto alto se misurabile.

Bonus: HTTPS, viewport, recapiti visibili, markup moderno (HTML5, meta description).

Se i dati non bastano, `quality_data_insufficient=true` e si applica il peso `insufficient_data` sul lead score, non una diagnosi di obsolescenza.

## Lead score commerciale

Esempio iniziale (sovrascrivibile nel YAML):

| Segnale | Peso |
| --- | --- |
| Nessun sito | +55 |
| Sito non raggiungibile | +30 |
| Quality score molto basso | +25 |
| Non responsive | +20 |
| Email pubblica | +10 |
| Telefono | +5 |
| Presenza locale/indirizzo completo | +10 |
| Sito moderno e completo | −20 |
| Dati insufficienti | −10 |

Lo score è limitato a 0–100. I valori nel YAML possono discostarsi dall'esempio della specifica: di default un'attività **senza sito**, con telefono e indirizzo, raggiunge la priorità A.

Priorità:

- **A** ≥ `priority_a` (default 70)
- **B** tra `priority_b` e `priority_a` (default 40–69)
- **C** sotto `priority_b`

Recensioni e reputazione, se un giorno disponibili, sono segnali deboli: non dimostrano il bisogno di un sito.

## Servizio suggerito

| Evidenza | Suggerimento |
| --- | --- |
| Nessun sito | Sviluppo sito web |
| Quality bassa / non raggiungibile / non responsive | Restyling / sito professionale |
| Note con catalogo/prenotazione | Web app o integrazione da valutare |
| Note con automazione | Automazione |
| Note con software esistente | Manutenzione/evolutive |
| Caso ambiguo | Analisi preliminare |

Il suggerimento non è una diagnosi certa né un preventivo. I listini interni non vengono mostrati né calcolati.
