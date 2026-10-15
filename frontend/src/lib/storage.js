// Piccolo wrapper di localStorage. Se il browser lo blocca (navigazione privata...) l'app funziona lo stesso,
// ma al riavvio bisogna rifare il login.
const PREFIX = "skedoo.";

export const storage = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(PREFIX + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(value));
    } catch {
      /* ignora */
    }
  },
  remove(key) {
    try {
      localStorage.removeItem(PREFIX + key);
    } catch {
      /* ignora */
    }
  },
};

// Chiavi usate nell'app (così sono tutte in un posto solo)
export const KEYS = {
  token: "token", // JWT della sessione
  utente: "utente", // { id, nome, cognome }
  classe: "classe", // id della classe scelta, es. "1A"
};
