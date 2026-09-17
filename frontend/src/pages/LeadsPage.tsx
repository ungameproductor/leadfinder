import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Lead } from "../api";

export default function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [priority, setPriority] = useState("");
  const [category, setCategory] = useState("");
  const [website, setWebsite] = useState("");
  const [sort, setSort] = useState("lead_score");

  const params = useMemo(
    () => ({
      q: q || undefined,
      priority: priority || undefined,
      category: category || undefined,
      website_status: website || undefined,
      sort,
      order: "desc",
    }),
    [q, priority, category, website, sort],
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      api.leads(params).then((data) => {
        setItems(data.items);
        setTotal(data.total);
      });
    }, 200);
    return () => clearTimeout(timer);
  }, [params]);

  async function download() {
    const response = await fetch(api.exportCsvUrl(params), { method: "POST" });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lead-finder-brindisi.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="stack">
      <div className="intro">
        <div>
          <h2>Lead</h2>
          <p className="muted">{total} risultati. Filtra, ordina, esporta. I do-not-contact restano esclusi dal CSV.</p>
        </div>
        <button className="button" onClick={download}>
          Export CSV
        </button>
      </div>
      <div className="filters">
        <input placeholder="Cerca nome, indirizzo, telefono, email…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="">Priorità</option>
          <option value="A">A</option>
          <option value="B">B</option>
          <option value="C">C</option>
        </select>
        <input placeholder="Categoria" value={category} onChange={(e) => setCategory(e.target.value)} />
        <select value={website} onChange={(e) => setWebsite(e.target.value)}>
          <option value="">Stato sito</option>
          <option value="no_website">Senza sito</option>
          <option value="reachable">Raggiungibile</option>
          <option value="unreachable">Non raggiungibile</option>
          <option value="blocked">Bloccato</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="lead_score">Score</option>
          <option value="name">Nome</option>
          <option value="last_checked_at">Ultimo controllo</option>
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
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
                  <Link to={`/lead/${lead.id}`}>{lead.name}</Link>
                  <div className="muted small">{lead.address}</div>
                </td>
                <td>{lead.category}</td>
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
