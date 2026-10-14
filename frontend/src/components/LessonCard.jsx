import { AlertTriangle, DoorOpen, Repeat, User } from "lucide-react";
import { sentenceCase } from "../lib/dates";
import { TIPI_MODIFICA } from "../lib/changes";
import "./LessonCard.css";

/**
 * Una lezione dell'orario.
 *  lesson: lezione dall'API (con `modifica` se c'è una modifica, vedi lib/changes.js)
 *  status: "finita" | "in_corso" | "prossima" | undefined (undefined = giorno non di oggi)
 */
export default function LessonCard({ lesson, status }) {
  const { modifica } = lesson;
  const aula = modifica?.nuova_aula || lesson.aula;
  const classes = ["lesson", status && `lesson--${status}`, modifica && "lesson--changed"].filter(Boolean).join(" ");

  return (
    <article className={classes}>
      <div className="lesson__time">{lesson.inizio}</div>
      <div className="lesson__card">
        <div className="lesson__top">
          <h3>
            {sentenceCase(lesson.materia)}
            {modifica && <AlertTriangle size={16} className="lesson__warn" />}
          </h3>
          {status === "in_corso" && <span className="badge">In corso</span>}
          {status === "finita" && <span className="lesson__done">Finita</span>}
        </div>
        <p className="lesson__hours muted">
          {lesson.inizio} – {lesson.fine}
        </p>
        <div className="lesson__meta">
          {aula && (
            <span className={modifica?.nuova_aula ? "lesson__changed-text" : ""}>
              {modifica?.nuova_aula ? <Repeat size={15} /> : <DoorOpen size={15} />} {aula}
            </span>
          )}
          {lesson.docenti.length > 0 && (
            <span>
              <User size={15} /> {lesson.docenti.join(", ")}
            </span>
          )}
        </div>
        {modifica && (
          <p className="lesson__note">
            {TIPI_MODIFICA[modifica.tipo]}
            {modifica.testo ? `: ${modifica.testo}` : ""}
          </p>
        )}
      </div>
    </article>
  );
}
