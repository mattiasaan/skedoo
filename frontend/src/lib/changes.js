// Modifiche all'orario (assenze, cambi aula, entrate/uscite). Il backend non le ha ancora:
// qui c'è solo la logica per mostrarle. I dati arrivano da api/changes.js.
//
// Una modifica è fatta così:
// {
//   id: 1,
//   data: "2026-10-12",          // giorno interessato
//   ora: 2,                      // numero d'ora, oppure null se riguarda tutta la giornata
//   tipo: "cambio_aula",         // vedi TIPI_MODIFICA
//   testo: "Aula cambiata per manutenzione",
//   nuova_aula: "Lab B"          // solo per cambio_aula
// }

export const TIPI_MODIFICA = {
  cambio_aula: "Cambio aula",
  assente: "Docente assente",
  supplenza: "Supplenza",
  entrata_posticipata: "Entrata posticipata",
  uscita_anticipata: "Uscita anticipata",
};

export function changesOfDay(changes, iso) {
  return changes.filter((c) => c.data === iso);
}

// Aggiunge a ogni lezione il campo `modifica` (o null) se per quell'ora c'è una modifica.
export function applyChanges(lessons, dayChanges) {
  return lessons.map((lesson) => ({
    ...lesson,
    modifica: dayChanges.find((c) => c.ora != null && c.ora === lesson.ora) || null,
  }));
}

// Le modifiche che riguardano tutta la giornata (es. entrata posticipata)
export function dayWideChanges(dayChanges) {
  return dayChanges.filter((c) => c.ora == null);
}
