import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { ceilToQuarter, countedGrades, formatAverage, formatSchoolGrade, gradeTone, votoNecessario } from "../lib/gradeMath";
import { sentenceCase } from "../lib/dates";
import "./SubjectCard.css";

const OBIETTIVI = [6, 7, 8]; // medie che l'utente può scegliere nel calcolatore

// Una materia: media, elenco voti (aprendola) e calcolatore "che voto mi serve?"
export default function SubjectCard({ materia }) {
  const [open, setOpen] = useState(false);
  const tone = gradeTone(materia.media);

  return (
    <article className="card subject">
      <button className="subject__head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <div>
          <h3>{sentenceCase(materia.materia)}</h3>
          <p className="muted">
            {countedGrades(materia.voti).length} voti
          </p>
        </div>
        <span className={`subject__avg tone-${tone}`}>{formatAverage(materia.media)}</span>
        <ChevronDown size={18} className={"subject__chevron" + (open ? " is-open" : "")} />
      </button>

      {open && (
        <div className="subject__body">
          <ul className="grades">
            {materia.voti.map((v) => (
              <li key={v.id} className={v.annullato ? "is-cancelled" : ""}>
                <span className={`grade tone-${gradeTone(v.valore)}`}>{v.voto || "–"}</span>
                <div>
                  <p>
                    {v.tipo || "Voto"}
                    {v.peso != null && v.peso !== 1 ? ` · peso ${v.peso}` : ""}
                    {v.annullato ? " · annullato" : ""}
                  </p>
                  <p className="muted grades__sub">
                    {v.data.split("-").reverse().join("/")}
                    {v.note ? ` · ${v.note}` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
          <Calculator voti={materia.voti} />
        </div>
      )}
    </article>
  );
}

// "Per avere almeno 6 alla prossima verifica ti serve ..."
function Calculator({ voti }) {
  const [obiettivo, setObiettivo] = useState(6);
  const [peso, setPeso] = useState(1);
  const result = votoNecessario(voti, obiettivo, peso);

  return (
    <div className="calc">
      <p className="calc__title">Che voto mi serve?</p>
      <div className="calc__row">
        <span className="muted">Voglio la media di</span>
        <div className="chips">
          {OBIETTIVI.map((o) => (
            <button key={o} className={"chip" + (o === obiettivo ? " chip--active" : "")} onClick={() => setObiettivo(o)}>
              {o}
            </button>
          ))}
        </div>
      </div>
      <div className="calc__row">
        <span className="muted">La verifica vale</span>
        <div className="chips">
          {[1, 2].map((p) => (
            <button key={p} className={"chip" + (p === peso ? " chip--active" : "")} onClick={() => setPeso(p)}>
              {p === 1 ? "peso 1" : "peso 2 (doppia)"}
            </button>
          ))}
        </div>
      </div>

      <p className="calc__result">
        {result.stato === "gia_ok" && <>Sei già sopra il {obiettivo}: qualunque voto va bene per restarci.</>}
        {result.stato === "serve" && (
          <>
            Ti serve almeno <strong>{formatSchoolGrade(ceilToQuarter(result.voto))}</strong>
            {ceilToQuarter(result.voto) % 1 !== 0 && <span className="muted"> ({ceilToQuarter(result.voto).toString().replace(".", ",")})</span>}.
          </>
        )}
        {result.stato === "irraggiungibile" && (
          <>
            Con una sola verifica non arrivi al {obiettivo}: anche con 10 la media sarebbe {formatAverage(result.mediaConDieci)}.
          </>
        )}
      </p>
    </div>
  );
}
