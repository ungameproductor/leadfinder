import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type AppConfig, type SearchRun } from "../api";

const CITY_KEY = "lead-finder-city";
const RADIUS_KEY = "lead-finder-radius";

export default function SearchPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [city, setCity] = useState("");
  const [radius, setRadius] = useState(10);
  const [maxResults, setMaxResults] = useState(20);
  const [selected, setSelected] = useState<string[]>([]);
  const [verify, setVerify] = useState(true);
  const [run, setRun] = useState<SearchRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.config().then((data) => {
      setConfig(data);
      const savedCity = localStorage.getItem(CITY_KEY);
      const savedRadius = localStorage.getItem(RADIUS_KEY);
      setCity(savedCity || data.location.city || "");
      setRadius(savedRadius ? Number(savedRadius) : data.location.radius_km);
      setSelected(data.categories.slice(0, 6).map((c) => c.id));
    });
  }, []);

  useEffect(() => {
    if (!run || ["completed", "completed_with_errors", "failed"].includes(run.status)) return;
    const timer = setInterval(async () => {
      const next = await api.getSearch(run.id);
      setRun(next);
      if (["completed", "completed_with_errors", "failed"].includes(next.status)) {
        setBusy(false);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [run]);

  async function start() {
    if (!config) return;
    const epicenter = city.trim();
    if (epicenter.length < 2) {
      setError("Inserisci una città italiana come epicentro.");
      return;
    }
    setBusy(true);
    setError(null);
    localStorage.setItem(CITY_KEY, epicenter);
    localStorage.setItem(RADIUS_KEY, String(radius));
    try {
      const created = await api.startSearch({
        city: epicenter,
        country: "Italy",
        radius_km: radius,
        categories: selected,
        max_results: maxResults,
        verify_websites: verify,
      });
      setRun(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore");
      setBusy(false);
    }
  }

  if (!config) return <p>Caricamento configurazione…</p>;

  return (
    <section className="stack">
      <div>
        <h2>Ricerca</h2>
        <p className="muted">
          Epicentro in Italia e raggio in km. Provider:{" "}
          {config.has_google_key ? "Google Places (ufficiale)" : "mock (demo, senza chiave API)"}.
        </p>
      </div>
      <div className="epicenter">
        <label>
          Città (epicentro)
          <input
            type="text"
            placeholder="Milano, Roma, Bari…"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            autoComplete="address-level2"
          />
        </label>
        <label>
          Raggio: {radius} km
          <input type="range" min={1} max={80} value={radius} onChange={(e) => setRadius(Number(e.target.value))} />
        </label>
      </div>
      <label>
        Limite risultati per categoria
        <input type="number" min={1} max={config.max_results_per_query} value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value))} />
      </label>
      <fieldset>
        <legend>Categorie</legend>
        <div className="chips">
          {config.categories.map((cat) => (
            <label key={cat.id} className="chip">
              <input
                type="checkbox"
                checked={selected.includes(cat.id)}
                onChange={() =>
                  setSelected((curr) => (curr.includes(cat.id) ? curr.filter((id) => id !== cat.id) : [...curr, cat.id]))
                }
              />
              {cat.label}
            </label>
          ))}
        </div>
      </fieldset>
      <label className="chip">
        <input type="checkbox" checked={verify} onChange={(e) => setVerify(e.target.checked)} />
        Verifica siti ed email pubbliche dopo la discovery
      </label>
      <div className="actions">
        <button className="button" disabled={busy || selected.length === 0 || city.trim().length < 2} onClick={start}>
          {busy ? "Job in corso…" : "Avvia ricerca"}
        </button>
        {run && ["completed", "completed_with_errors"].includes(run.status) && (
          <button className="button ghost" onClick={() => navigate(`/lead?run=${run.id}`)}>
            Apri lead ({run.results_count})
          </button>
        )}
      </div>
      {error && <p className="banner error">{error}</p>}
      {run && (
        <article className="card">
          <p className="muted">Job {run.id.slice(0, 8)} — {run.status}</p>
          <p>{run.message || `Processati ${run.processed_count}, unici ${run.results_count}`}</p>
          {run.errors.length > 0 && <ul>{run.errors.map((item) => <li key={item}>{item}</li>)}</ul>}
        </article>
      )}
    </section>
  );
}
