import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type Lead } from "../api";

export default function LeadDetailPage() {
  const { id } = useParams();
  const [lead, setLead] = useState<Lead | null>(null);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.lead(id).then((data) => {
      setLead(data);
      setNotes(data.notes || "");
    });
  }, [id]);

  async function patch(body: Record<string, string>) {
    if (!id) return;
    const updated = await api.patchLead(id, body);
    setLead(updated);
  }

  async function verify() {
    if (!id) return;
    setBusy(true);
    await api.verifyLead(id);
    setTimeout(async () => {
      setLead(await api.lead(id));
      setBusy(false);
    }, 1500);
  }

  if (!lead) return <p>Caricamento lead…</p>;

  return (
    <section className="stack">
      <p>
        <Link to="/lead">← Elenco</Link>
      </p>
      <div className="intro">
        <div>
          <p className="eyebrow">
            {lead.city} {lead.postal_code} · fonte {lead.source_provider}
          </p>
          <h2>{lead.name}</h2>
          <p className="muted">{lead.address}</p>
        </div>
        <span className={`prio prio-${lead.priority} large`}>{lead.priority}</span>
      </div>
      <div className="grid two">
        <article className="card">
          <h3>Contatti e sito</h3>
          <dl>
            <dt>Telefono</dt>
            <dd>{lead.phone || "—"}</dd>
            <dt>Sito</dt>
            <dd>{lead.website || "assente"}</dd>
            <dt>Stato sito</dt>
            <dd>{lead.website_status}</dd>
            <dt>Quality</dt>
            <dd>
              {lead.website_quality_score ?? "n/d"}
              {lead.quality_data_insufficient ? " · dati insufficienti" : ""}
            </dd>
            <dt>Email</dt>
            <dd>{lead.public_email || "non trovata"}</dd>
            <dt>Fonte email</dt>
            <dd>{lead.email_source_url || "—"}</dd>
          </dl>
        </article>
        <article className="card">
          <h3>Valutazione</h3>
          <p>
            Score {lead.lead_score} · {lead.suggested_service}
          </p>
          <p className="muted">Il suggerimento non è una diagnosi certa né un prezzo.</p>
          <ul>
            {lead.scoring_evidence.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <h4>Evidenze sito</h4>
          <ul>
            {lead.website_quality_evidence.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
      <article className="card stack">
        <h3>Revisione manuale</h3>
        <div className="actions wrap">
          <button onClick={() => patch({ manual_status: "confirmed" })}>Conferma</button>
          <button onClick={() => patch({ manual_status: "discarded" })}>Scarta</button>
          <button onClick={() => patch({ contact_status: "do_not_contact" })}>Do not contact</button>
          <select value={lead.priority} onChange={(e) => patch({ priority: e.target.value })}>
            <option>A</option>
            <option>B</option>
            <option>C</option>
          </select>
          <input
            value={lead.category || ""}
            onBlur={(e) => patch({ category: e.target.value })}
            onChange={(e) => setLead({ ...lead, category: e.target.value })}
            placeholder="Categoria"
          />
          <button disabled={busy} onClick={verify}>
            {busy ? "Verifica…" : "Riesegui verifica sito"}
          </button>
        </div>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} placeholder="Note interne" />
        <button className="button" onClick={() => patch({ notes })}>
          Salva note
        </button>
        <p className="muted small">
          Stato: {lead.manual_status} · contatto {lead.contact_status} · visto {lead.first_seen_at} ·
          controllo {lead.last_checked_at || "—"}
        </p>
      </article>
    </section>
  );
}
