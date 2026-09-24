import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type AppConfig, type Lead, type LeadFacets } from "../api";

function formatRun(run: LeadFacets["runs"][number]) {
  const when = run.started_at
    ? new Date(run.started_at).toLocaleString("it-IT", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
    : "";
  const place = run.city || "Ricerca";
  return `${place} · ${when} · ${run.new_count} nuovi / ${run.results_count}`;
}

export default function LeadsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [facets, setFacets] = useState<LeadFacets | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const runParam = searchParams.get("run");
  const activeRun = runParam && runParam !== "all" ? runParam : undefined;
  const q = searchParams.get("q") || "";
  const priority = searchParams.get("priority") || "";
  const category = searchParams.get("category") || "";
  const city = searchParams.get("city") || "";
  const website = searchParams.get("website") || "";
  const sort = searchParams.get("sort") || "lead_score";
  const onlyNew = searchParams.get("only_new") === "1";

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  }

  useEffect(() => {
    api.facets().then(setFacets).catch(() => setFacets({ cities: [], categories: [], runs: [] }));
    api.config().then(setConfig).catch(() => setConfig(null));
  }, []);

  useEffect(() => {
    if (!facets || runParam !== null) return;
    const next = new URLSearchParams(searchParams);
    next.set("run", facets.runs[0]?.id || "all");
    setSearchParams(next, { replace: true });
  }, [facets, runParam, searchParams, setSearchParams]);

  const params = useMemo(
    () => ({
      q: q || undefined,
      priority: priority || undefined,
      category: category || undefined,
      city: city || undefined,
      website_status: website || undefined,
      run_id: activeRun,
      only_new: onlyNew ? "true" : undefined,
      sort,
      order: "desc",
    }),
    [q, priority, category, city, website, sort, activeRun, onlyNew],
  );

  useEffect(() => {
    if (runParam === null) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      api.leads(params).then((data) => {
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
      });
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [params, runParam]);

  const listQuery = searchParams.toString();

  function categoryLabel(value: string) {
    return config?.categories.find((item) => item.id === value)?.label || value;
  }

  async function download() {
    const response = await fetch(api.exportCsvUrl(params), { method: "POST" });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lead-finder.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const selectedRun = facets?.runs.find((run) => run.id === activeRun);
  const summary = selectedRun
    ? `${total} contatti della ricerca su ${selectedRun.city || "questa zona"}. I nuovi sono in cima ed etichettati.`
    : `${total} risultati in archivio. Filtra, ordina, esporta. I do-not-contact restano esclusi dal CSV.`;

  return (
    <section className="stack">
      <div className="intro">
        <div>
          <h2>Lead</h2>
          <p className="muted">{summary}</p>
        </div>
        <button className="button" onClick={download}>
          Export CSV
        </button>
      </div>
      <div className="filters">
        <select value={runParam || ""} onChange={(e) => setFilter("run", e.target.value)}>
          <option value="" disabled>
            Ricerca
          </option>
          <option value="all">Tutti i lead</option>
          {facets?.runs.map((run) => (
            <option key={run.id} value={run.id}>
              {formatRun(run)}
            </option>
          ))}
        </select>
        <label className="chip">
          <input type="checkbox" checked={onlyNew} onChange={(e) => setFilter("only_new", e.target.checked ? "1" : "")} />
          Solo nuovi
        </label>
        <input placeholder="Cerca nome, indirizzo, telefono, email…" value={q} onChange={(e) => setFilter("q", e.target.value)} />
        <select value={priority} onChange={(e) => setFilter("priority", e.target.value)}>
          <option value="">Priorità</option>
          <option value="A">A</option>
          <option value="B">B</option>
          <option value="C">C</option>
        </select>
        <select value={city} onChange={(e) => setFilter("city", e.target.value)}>
          <option value="">Città</option>
          {facets?.cities.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={category} onChange={(e) => setFilter("category", e.target.value)}>
          <option value="">Categoria</option>
          {facets?.categories.map((item) => (
            <option key={item} value={item}>
              {categoryLabel(item)}
            </option>
          ))}
        </select>
        <select value={website} onChange={(e) => setFilter("website", e.target.value)}>
          <option value="">Stato sito</option>
          <option value="no_website">Senza sito</option>
          <option value="reachable">Raggiungibile</option>
          <option value="unreachable">Non raggiungibile</option>
          <option value="blocked">Bloccato</option>
        </select>
        <select value={sort} onChange={(e) => setFilter("sort", e.target.value === "lead_score" ? "" : e.target.value)}>
          <option value="lead_score">Score</option>
          <option value="name">Nome</option>
          <option value="last_checked_at">Ultimo controllo</option>
          <option value="first_seen_at">Prima vista</option>
        </select>
      </div>
      <div className="table-wrap">
        <table className="leads-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Città</th>
              <th>Cat.</th>
              <th>Sito</th>
              <th>Telefono</th>
              <th>Email</th>
              <th>Score</th>
              <th>Pri.</th>
              <th>Servizio</th>
            </tr>
          </thead>
          <tbody>
            {items.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <Link to={listQuery ? `/lead/${lead.id}?${listQuery}` : `/lead/${lead.id}`}>{lead.name}</Link>
                  {lead.is_new ? <span className="tag-new">Nuovo</span> : null}
                  <div className="muted small">{lead.address}</div>
                </td>
                <td>{lead.city || "—"}</td>
                <td>{lead.category ? categoryLabel(lead.category) : "—"}</td>
                <td>{lead.website_status}</td>
                <td>
                  {lead.phone ? (
                    <a href={`tel:${lead.phone.replace(/\s+/g, "")}`}>{lead.phone}</a>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{lead.public_email || "—"}</td>
                <td>{lead.lead_score}</td>
                <td>
                  <span className={`prio prio-${lead.priority}`}>{lead.priority}</span>
                </td>
                <td>{lead.suggested_service}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
