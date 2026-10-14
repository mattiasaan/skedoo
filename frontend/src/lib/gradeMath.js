// Calcoli sui voti. Stesse regole del backend: media pesata, senza i voti annullati,
// con peso 0 o non numerici (es. "Ottimo").

export function countedGrades(voti) {
  return voti.filter((v) => !v.annullato && v.valore != null && v.peso !== 0);
}

export function weightedAverage(voti) {
  const counted = countedGrades(voti);
  const totalWeight = counted.reduce((sum, v) => sum + (v.peso ?? 1), 0);
  if (!totalWeight) return null;
  return counted.reduce((sum, v) => sum + v.valore * (v.peso ?? 1), 0) / totalWeight;
}

/**
 * Che voto serve alla prossima verifica per arrivare alla media `obiettivo`?
 * Ritorna { stato, voto, mediaConDieci }
 *   stato "gia_ok"        -> ci sei già, qualunque voto va bene (anche 0)
 *   stato "serve"         -> devi prendere almeno `voto`
 *   stato "irraggiungibile" -> neanche 10 basta; `mediaConDieci` è la media che avresti con un 10
 */
export function votoNecessario(voti, obiettivo, peso = 1) {
  const counted = countedGrades(voti);
  const somma = counted.reduce((s, v) => s + v.valore * (v.peso ?? 1), 0);
  const pesoTotale = counted.reduce((s, v) => s + (v.peso ?? 1), 0);

  const necessario = (obiettivo * (pesoTotale + peso) - somma) / peso;
  if (necessario <= 0) return { stato: "gia_ok" };
  if (necessario > 10) {
    return { stato: "irraggiungibile", mediaConDieci: (somma + 10 * peso) / (pesoTotale + peso) };
  }
  return { stato: "serve", voto: necessario };
}

// 7.25 -> "7+", 7.5 -> "7½", 6.75 -> "7-", 8 -> "8": come si scrivono i voti a scuola
export function formatSchoolGrade(value) {
  const rounded = Math.round(value * 4) / 4;
  const base = Math.floor(rounded);
  const frac = rounded - base;
  if (frac === 0) return String(base);
  if (frac === 0.25) return `${base}+`;
  if (frac === 0.5) return `${base}½`;
  return `${base + 1}-`;
}

// Arrotonda per eccesso al quarto di voto: il voto minimo non può essere "6,13", è 6+
export function ceilToQuarter(value) {
  return Math.ceil(value * 4 - 1e-9) / 4;
}

export function formatAverage(value) {
  return value == null ? "–" : value.toFixed(2).replace(".", ",");
}

// Colore del voto: "ok" (>= 6), "bad" (< 6), "none" (senza valore numerico)
export function gradeTone(value) {
  if (value == null) return "none";
  return value >= 6 ? "ok" : "bad";
}
