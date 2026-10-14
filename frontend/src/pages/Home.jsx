import { Clock, User } from "lucide-react";
import { Link } from "react-router-dom";
import { fetchAgenda, fetchChanges, fetchSchedule } from "../api";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import Banner from "../components/Banner";
import ClassRequired from "../components/ClassRequired";
import LessonCard from "../components/LessonCard";
import PageHeader from "../components/PageHeader";
import { ErrorBox, Loading } from "../components/Status";
import { TIPI_MODIFICA, applyChanges, changesOfDay } from "../lib/changes";
import { addDays, dayKey, formatLong, formatRelative, sentenceCase, toISO } from "../lib/dates";
import { currentOrNext, lessonStatus } from "../lib/lessons";
import "./Home.css";

export default function Home() {
  const { utente, classe } = useAuth();
  const now = new Date();
  const today = toISO(now);

  // Tre caricamenti indipendenti: se l'agenda fallisce, l'orario si vede lo stesso
  const schedule = useApi(() => (classe ? fetchSchedule(classe) : Promise.resolve(null)), [classe]);
  const changes = useApi(() => (classe ? fetchChanges(classe) : Promise.resolve([])), [classe]);
  const agenda = useApi(() => fetchAgenda(today, toISO(addDays(now, 6))), []);

  const dayChanges = changesOfDay(changes.data || [], today);
  const day = schedule.data?.giorni.find((g) => g.giorno === dayKey(now));
  const lessons = day ? applyChanges(day.lezioni, dayChanges) : [];
  const focus = currentOrNext(lessons, now);

  return (
    <>
      <PageHeader
        title={`Ciao, ${sentenceCase(utente?.nome) || "studente"}!`}
        subtitle={formatLong(now)}
        right={<Avatar nome={utente?.nome} cognome={utente?.cognome} />}
      />

      {!classe ? (
        <ClassRequired />
      ) : (
        <div className="stack">
          {dayChanges.length > 0 && (
            <Banner title="Ultime modifiche">
              {dayChanges.map((c) => (
                <p key={c.id}>
                  {TIPI_MODIFICA[c.tipo]}
                  {c.ora ? ` (${c.ora}ª ora)` : ""}: {c.testo}
                </p>
              ))}
            </Banner>
          )}

          {schedule.loading && <Loading />}
          {schedule.error && <ErrorBox error={schedule.error} onRetry={schedule.reload} />}

          {schedule.data && (
            <>
              <h2 className="section-title">{focus && lessonStatus(focus, now) === "in_corso" ? "In corso" : "Prossima lezione"}</h2>
              <NextLesson lesson={focus} hasSchool={lessons.length > 0} />

              {lessons.length > 0 && (
                <>
                  <div className="section-head">
                    <h2 className="section-title">Orario di oggi</h2>
                    <Link to="/orario" className="link-small">
                      Vedi orario
                    </Link>
                  </div>
                  <div className="stack" style={{ gap: 10 }}>
                    {lessons.map((l) => (
                      <LessonCard key={l.inizio} lesson={l} status={lessonStatus(l, now)} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          <div className="section-head">
            <h2 className="section-title">In agenda</h2>
            <Link to="/agenda" className="link-small">
              Vedi tutto
            </Link>
          </div>
          {agenda.loading && <Loading />}
          {agenda.error && <ErrorBox error={agenda.error} onRetry={agenda.reload} />}
          {agenda.data && <AgendaPreview giorni={agenda.data.giorni} />}
        </div>
      )}
    </>
  );
}

// Riquadro verde grande con la lezione in corso o la prossima
function NextLesson({ lesson, hasSchool }) {
  if (!lesson) {
    return (
      <div className="card">
        <p>{hasSchool ? "Per oggi le lezioni sono finite 🎉" : "Oggi non hai lezione."}</p>
      </div>
    );
  }
  const aula = lesson.modifica?.nuova_aula || lesson.aula;
  return (
    <div className="hero">
      <div className="hero__top">
        <div>
          <p className="hero__label">{lesson.ora ? `${lesson.ora}ª ora` : "Lezione"}</p>
          <h3>{sentenceCase(lesson.materia)}</h3>
        </div>
        {aula && (
          <div className="hero__room">
            <span>Aula</span>
            <strong>{aula}</strong>
          </div>
        )}
      </div>
      <div className="hero__meta">
        <span>
          <Clock size={16} /> {lesson.inizio} – {lesson.fine}
        </span>
        {lesson.docenti.length > 0 && (
          <span>
            <User size={16} /> {lesson.docenti.join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}

// Le prime voci dell'agenda dei prossimi giorni (la pagina completa è /agenda)
function AgendaPreview({ giorni }) {
  const items = giorni.flatMap((g) => g.eventi.map((e) => ({ ...e, data: g.data }))).slice(0, 4);
  if (items.length === 0) return <div className="card muted">Niente in agenda per i prossimi giorni.</div>;
  return (
    <div className="stack" style={{ gap: 10 }}>
      {items.map((e) => (
        <div key={e.id} className="card agenda-mini">
          <span className="badge">{formatRelative(e.data)}</span>
          <p className="agenda-mini__subject">{sentenceCase(e.materia) || "Evento"}</p>
          <p className="muted agenda-mini__text">{e.testo}</p>
        </div>
      ))}
    </div>
  );
}
