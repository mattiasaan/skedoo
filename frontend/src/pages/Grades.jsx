import { useState } from "react";
import { fetchGrades } from "../api";
import { useApi } from "../api/useApi";
import PageHeader from "../components/PageHeader";
import { Empty, ErrorBox, Loading } from "../components/Status";
import SubjectCard from "../components/SubjectCard";
import { formatAverage, gradeTone } from "../lib/gradeMath";
import "./Grades.css";

const PERIODI = [
  { value: undefined, label: "Tutto l'anno" },
  { value: 1, label: "1° periodo" },
  { value: 2, label: "2° periodo" },
];

export default function Grades() {
  const [periodo, setPeriodo] = useState(undefined);
  const { data, loading, error, reload } = useApi(() => fetchGrades(periodo), [periodo]);

  return (
    <>
      <PageHeader title="Voti" subtitle={data ? `Anno scolastico 20${data.anno}/${Number(data.anno) + 1}` : undefined} />

      <div className="chips" style={{ marginBottom: 16 }}>
        {PERIODI.map((p) => (
          <button key={p.label} className={"chip" + (p.value === periodo ? " chip--active" : "")} onClick={() => setPeriodo(p.value)}>
            {p.label}
          </button>
        ))}
      </div>

      {loading && <Loading />}
      {error && <ErrorBox error={error} onRetry={reload} />}

      {data && (
        <div className="stack">
          <div className="card average">
            <span className="muted">Media generale</span>
            <strong className={`tone-${gradeTone(data.media_generale)}`}>{formatAverage(data.media_generale)}</strong>
          </div>

          {data.materie.length === 0 && <Empty text="Nessun voto in questo periodo." />}
          {data.materie.map((m) => (
            <SubjectCard key={m.materia_id ?? m.materia} materia={m} />
          ))}
        </div>
      )}
    </>
  );
}
