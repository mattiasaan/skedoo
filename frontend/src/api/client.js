// Client HTTP verso il backend. Tutte le chiamate dell'app passano da `request()`.
//
// Cosa fa per te:
//  - aggiunge il token (Authorization: Bearer ...)
//  - trasforma gli errori in `ApiError` con status, code e un messaggio in italiano
//  - se la sessione è scaduta (401 session_expired / invalid_token) rifà da solo il login con le
//    credenziali salvate e ripete la chiamata una volta; se non riesce, esce dall'app.
import { KEYS, storage } from "../lib/storage";

const BASE = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(status, code, message, retryAfter = null) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}

// Messaggi mostrati all'utente per ogni codice d'errore del backend (vedi README del backend)
const MESSAGES = {
  invalid_credentials: "Username o password non corretti.",
  too_many_attempts: "Troppi tentativi di accesso. Riprova tra qualche minuto.",
  rate_limited: "Troppe richieste. Aspetta qualche secondo e riprova.",
  classeviva_error: "ClasseViva non risponde in questo momento. Riprova tra poco.",
  database_unavailable: "Il servizio non è raggiungibile. Riprova tra poco.",
  class_not_found: "Classe non trovata.",
  date_out_of_range: "Data fuori dall'anno scolastico.",
  range_too_large: "Intervallo di date troppo grande.",
  invalid_range: "Intervallo di date non valido.",
  network: "Impossibile contattare il server. Controlla la connessione.",
};

// L'app registra qui cosa fare quando la sessione è persa del tutto (di solito: tornare al login)
let onSessionLost = () => {};
export function setSessionLostHandler(fn) {
  onSessionLost = fn;
}

async function send(path, { method = "GET", body, token }) {
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network", MESSAGES.network);
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    /* risposta senza JSON */
  }

  if (!response.ok) {
    const code = data?.code || "error";
    const retryAfter = Number(response.headers.get("Retry-After")) || null;
    const message = MESSAGES[code] || data?.message || "Qualcosa è andato storto. Riprova.";
    throw new ApiError(response.status, code, message, retryAfter);
  }
  return data;
}

// Se più chiamate scoprono insieme che la sessione è scaduta, il login si fa una volta sola
let refreshing = null;

async function refreshLogin() {
  if (!refreshing) {
    refreshing = (async () => {
      const credenziali = storage.get(KEYS.credenziali);
      if (!credenziali) throw new ApiError(401, "session_expired", "Sessione scaduta.");
      const result = await send("/auth/login", { method: "POST", body: credenziali });
      storage.set(KEYS.token, result.access_token);
      storage.set(KEYS.utente, result.utente);
    })().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}

export async function request(path, options = {}) {
  const { auth = true, ...rest } = options;
  if (!auth) return send(path, rest);

  try {
    return await send(path, { ...rest, token: storage.get(KEYS.token) });
  } catch (error) {
    const expired = error.status === 401 && ["session_expired", "invalid_token", "not_authenticated"].includes(error.code);
    if (!expired) throw error;

    try {
      await refreshLogin();
    } catch (loginError) {
      // password cambiata, nessuna credenziale salvata... non si può continuare
      if (loginError.status === 401) onSessionLost();
      throw loginError;
    }
    return send(path, { ...rest, token: storage.get(KEYS.token) });
  }
}
