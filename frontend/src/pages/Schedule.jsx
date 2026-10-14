import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { fetchChanges, fetchSchedule } from "../api";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import ClassRequired from "../components/ClassRequired";
import LessonCard from "../components/LessonCard";
import PageHeader from "../components/PageHeader";
import { Empty, ErrorBox, Loading } from "../components/Status";
import { applyChanges, changesOfDay, dayWideChanges, TIPI_MODIFICA } from "../lib/changes";
import { capitalize, dayKey, formatLong, toISO, weekDays } from "../lib/dates";
import { lessonStatus } from "../lib/lessons";
import "./Schedule.css";

export default function Schedule() {
  const { classe } = useAuth();
  const now = new Date();
  const todayISO = toISO(now);

  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedKey, setSelectedKey] = useState(dayKey(now) || "lunedi"); // la domenica parte da lunedì

  const schedule = useApi(() => (classe ? fetchSchedule(classe) : Promise.resolve(null)), [classe]);
  const changes = useApi(() => (classe ? fetchChanges(classe) : Promise.resolve([])), [classe]);

  if (!classe) {
    return (
      <>
        <PageHeader title="Orario" />
        <ClassRequired />
      </>
    );
  }

  const days = weekDays(weekOffset, now);
  const selected = days.find((d) => d.key === selectedKey) || days[0];
  const selectedISO = toISO(selected.date);

  const dayData = schedule.data?.giorni.find((g) => g.giorno === selected.key);
  const dayChanges = changesOfDay(changes.data || [], selectedISO);
  const lessons = dayData ? applyChanges(dayData.lezioni, dayChanges) : [];
  const isToday = selectedISO === todayISO;

  return (
    <>
      <PageHeader
        title="Orario"
        subtitle={schedule.data ? `Classe ${schedule.data.nome}` : undefined}
        right={
          <div className="week-nav">
            <button className="icon-btn" onClick={() => setWeekOffset(weekOffset - 1)} aria-label="Settimana precedente">
              <ChevronLeft size={20} />
            </button>
            <button className="icon-btn" onClick={() => setWeekOffset(weekOffset + 1)} aria-label="Settimana successiva">
              <ChevronRight size={20} />
            </button>
          </div>
        }
      />

      {/* righe dei giorni: Lun 12, Mar 13... */}
      <div className="days">
        {days.map((d) => {
          const hasLessons = schedule.data?.giorni.some((g) => g.giorno === d.key);
          const hasChanges = changesOfDay(changes.data || [], toISO(d.date)).length > 0;
          const cls = ["day", d.key === selected.key && "is-selected", toISO(d.date) === todayISO && "is-today", schedule.data && !hasLessons && "is-off"]
            .filter(Boolean)
            .join(" ");
          return (
            <button key={d.key} className={cls} onClick={() => setSelectedKey(d.key)}>
              <span>{d.label}</span>
              <strong>{d.date.getDate()}</strong>
              {hasChanges && <i className="day__dot" />}
            </button>
          );
        })}
      </div>

      <p className="schedule__date muted">{capitalize(formatLong(selected.date))}</p>

      {schedule.loading && <Loading />}
      {schedule.error && <ErrorBox error={schedule.error} onRetry={schedule.reload} />}

      {schedule.data && (
        <div className="stack" style={{ gap: 10 }}>
          {dayWideChanges(dayChanges).map((c) => (
            <div key={c.id} className="schedule__daywide">
              <strong>{TIPI_MODIFICA[c.tipo]}</strong> {c.testo}
            </div>
          ))}
          {lessons.length === 0 && <Empty text="Nessuna lezione in questo giorno." />}
          {lessons.map((l) => (
            <LessonCard key={l.inizio} lesson={l} status={isToday ? lessonStatus(l, now) : undefined} />
          ))}
        </div>
      )}
    </>
  );
}
