// Funzioni sulle date. Tutte lavorano sull'ora locale del dispositivo e su stringhe "YYYY-MM-DD",
// che sono lo stesso formato usato dall'API.

export const GIORNI = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato"]; // chiavi dell'API
export const GIORNI_BREVI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab"];
const NOMI_GIORNO = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
const NOMI_MESE = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];

const pad = (n) => String(n).padStart(2, "0");

export function toISO(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function fromISO(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

// "lunedì 12 ottobre"
export function formatLong(date) {
  return `${NOMI_GIORNO[date.getDay()]} ${date.getDate()} ${NOMI_MESE[date.getMonth()]}`;
}

// "Oggi", "Domani" oppure "Mercoledì 14 ottobre"
export function formatRelative(iso, now = new Date()) {
  if (iso === toISO(now)) return "Oggi";
  if (iso === toISO(addDays(now, 1))) return "Domani";
  const text = formatLong(fromISO(iso));
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Il lunedì della settimana che contiene `date`. La domenica si considera già la settimana dopo.
export function startOfWeek(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const day = d.getDay(); // 0 = domenica
  return addDays(d, day === 0 ? 1 : 1 - day);
}

// I 6 giorni da lunedì a sabato della settimana `offset` (0 = questa, 1 = prossima, -1 = scorsa)
export function weekDays(offset = 0, now = new Date()) {
  const monday = addDays(startOfWeek(now), offset * 7);
  return GIORNI.map((key, i) => ({ key, label: GIORNI_BREVI[i], date: addDays(monday, i) }));
}

// "08:10" -> 490 (minuti dalla mezzanotte)
export function toMinutes(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

export function nowMinutes(now = new Date()) {
  return now.getHours() * 60 + now.getMinutes();
}

// "Mario" -> "Mario"; "ROSSI MARIO" -> "Rossi mario". Serve perché ClasseViva scrive molte cose in MAIUSCOLO.
export function sentenceCase(text) {
  if (!text) return "";
  if (text !== text.toUpperCase()) return text;
  const lower = text.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

// Chiave del giorno usata dall'API ("lunedi"...) per una data. La domenica non c'è: ritorna null.
export function dayKey(date) {
  return GIORNI[(date.getDay() + 6) % 7] || null;
}

export function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
