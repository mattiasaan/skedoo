import { nowMinutes, toMinutes } from "./dates";

// Stato di una lezione rispetto a un momento: "finita" | "in_corso" | "prossima"
export function lessonStatus(lesson, now = new Date()) {
  const minutes = nowMinutes(now);
  if (minutes >= toMinutes(lesson.fine)) return "finita";
  if (minutes >= toMinutes(lesson.inizio)) return "in_corso";
  return "prossima";
}

// La lezione in corso, oppure la prossima di oggi. null se per oggi sono finite.
export function currentOrNext(lessons, now = new Date()) {
  return (
    lessons.find((l) => lessonStatus(l, now) === "in_corso") ||
    lessons.find((l) => lessonStatus(l, now) === "prossima") ||
    null
  );
}
