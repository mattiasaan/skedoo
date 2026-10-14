// Modifiche all'orario (cambi aula, assenze, entrate/uscite).
//
// ⚠️ NON È ANCORA COLLEGATO AL BACKEND.
// Quando esisterà l'endpoint, sostituisci il corpo di `fetchChanges` con una chiamata a `request()`,
// per esempio:  return request(`/changes?classe=${classId}`);
// Il formato di ogni modifica è descritto in lib/changes.js.
import { addDays, toISO } from "../lib/dates";

// I dati di esempio si vedono solo in sviluppo (npm run dev), oppure se imposti VITE_MOCK_CHANGES=true.
// In produzione, senza endpoint, l'app non mostra modifiche inventate agli studenti.
const USE_MOCK = import.meta.env.DEV || import.meta.env.VITE_MOCK_CHANGES === "true";

function mockChanges() {
  const today = toISO(new Date());
  const tomorrow = toISO(addDays(new Date(), 1));
  return [
    { id: 1, data: today, ora: 2, tipo: "cambio_aula", testo: "Aula cambiata per manutenzione attrezzature", nuova_aula: "Lab B" },
    { id: 2, data: today, ora: 4, tipo: "assente", testo: "La classe resta in aula con un supplente" },
    { id: 3, data: tomorrow, ora: null, tipo: "entrata_posticipata", testo: "Entrata alla seconda ora (09:00)" },
  ];
}

export async function fetchChanges(classId) { // eslint-disable-line no-unused-vars
  return USE_MOCK ? mockChanges() : [];
}
