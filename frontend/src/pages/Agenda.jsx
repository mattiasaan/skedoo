import { BookOpen, Calendar, NotebookPen } from "lucide-react";
import { useState } from "react";
import { fetchAgenda } from "../api";
import { useApi } from "../api/useApi";
import PageHeader from "../components/PageHeader";
import { Empty, ErrorBox, Loading } from "../components/Status";
import { addDays, formatRelative, sentenceCase, toISO } from "../lib/dates";
import "./Agenda.css";

// Cosa mostrare per ogni tipo di evento dell'API
const TIPI = {
  compito: { label: "Compito", icon: BookOpen, className: "badge badge--warning" },
  annotazione: { label: "Annotazione", icon: NotebookPen, className: "badge" },
  evento: { label: "Evento", icon: Calendar, className: "badge" },
};

const INTERVALLI = [
  { giorni: 14, label: "Prossimi 14 giorni" },
  { giorni: 30, label: "Prossimi 30 giorni" },
];

export default function Agenda() {
  const [giorni, setGiorni] = useState(14);
  const { data, loading, error, reload } = useApi(() => {
    const oggi = new Date();
    return fetchAgenda(toISO(oggi), toISO(addDays(oggi, giorni - 1)));
  }, [giorni]);

  return (
    <>
      <PageHeader title="Agenda" subtitle="Compiti ed eventi" />

      <div className="chips" style={{ marginBottom: 16 }}>
        {INTERVALLI.map((i) => (
          <button key={i.giorni} className={"chip" + (i.giorni === giorni ? " chip--active" : "")} onClick={() => setGiorni(i.giorni)}>
            {i.label}
          </button>
        ))}
      </div>

      {loading && <Loading />}
      {error && <ErrorBox error={error} onRetry={reload} />}
      {data && data.giorni.length === 0 && <Empty text="Niente in agenda in questo periodo." />}

      <div className="stack">
        {data?.giorni.map((giorno) => (
          <section key={giorno.data} className="stack" style={{ gap: 10 }}>
            <h2 className="section-title">{formatRelative(giorno.data)}</h2>
            {giorno.eventi.map((e) => {
              const tipo = TIPI[e.tipo] || TIPI.evento;
              return (
                <article key={e.id} className="card agenda-event">
                  <div className="agenda-event__head">
                    <span className={tipo.className}>{tipo.label}</span>
                    {!e.tutto_il_giorno && e.ora_inizio && (
                      <span className="muted agenda-event__time">
                        {e.ora_inizio}
                        {e.ora_fine ? ` – ${e.ora_fine}` : ""}
                      </span>
                    )}
                  </div>
                  {e.materia && <h3>{sentenceCase(e.materia)}</h3>}
                  {e.testo && <p className="agenda-event__text">{e.testo}</p>}
                  {e.autore && <p className="muted agenda-event__author">{e.autore}</p>}
                </article>
              );
            })}
          </section>
        ))}
      </div>
    </>
  );
}
