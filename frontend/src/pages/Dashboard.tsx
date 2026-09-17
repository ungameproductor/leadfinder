import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Stats } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <p className="banner error">{error}</p>;
  if (!stats) return <p>Caricamento…</p>;

  const cards = [
    { label: "Attività", value: stats.total, hint: "Nel database locale" },
    { label: "Priorità A", value: stats.priority_a, hint: "Opportunità più calde" },
    { label: "Priorità B", value: stats.priority_b, hint: "Da approfondire" },
    { label: "Priorità C", value: stats.priority_c, hint: "Basso segnale" },
    { label: "Senza sito", value: stats.no_website, hint: "Segnale per sviluppo web" },
    { label: "Siti problematici", value: stats.problematic_sites, hint: "Irraggiungibili o bloccati" },
    { label: "Email pubbliche", value: stats.emails_found, hint: "Trovate sul sito" },
    { label: "Confermati", value: stats.confirmed, hint: "Revisionati a mano" },
  ];

  return (
    <section>
      <div className="intro">
        <div>
          <h2>Panoramica</h2>
          <p>
            Cerca in qualsiasi città d&apos;Italia: imposta l&apos;epicentro e il raggio. I punteggi sono
            segnali interni, non preventivi.
          </p>
        </div>
        <Link className="button" to="/ricerca">
          Nuova ricerca
        </Link>
      </div>
      <div className="grid">
        {cards.map((card) => (
          <article key={card.label} className="card">
            <p className="muted">{card.label}</p>
            <strong>{card.value}</strong>
            <span>{card.hint}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
