import { AlertCircle, Loader2 } from "lucide-react";
import "./Status.css";

// Tre piccoli componenti per i tre stati di ogni pagina che carica dati: caricamento, errore, vuoto.

export function Loading({ text = "Caricamento…" }) {
  return (
    <div className="status">
      <Loader2 className="status__spinner" size={26} />
      <p className="muted">{text}</p>
    </div>
  );
}

export function ErrorBox({ error, onRetry }) {
  return (
    <div className="status status--error" role="alert">
      <AlertCircle size={26} />
      <p>{error?.message || "Qualcosa è andato storto."}</p>
      {onRetry && (
        <button className="btn btn--ghost btn--small" onClick={onRetry}>
          Riprova
        </button>
      )}
    </div>
  );
}

export function Empty({ text }) {
  return (
    <div className="status">
      <p className="muted">{text}</p>
    </div>
  );
}
