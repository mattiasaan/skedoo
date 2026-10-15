import { ChevronRight, LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import PageHeader from "../components/PageHeader";
import { sentenceCase } from "../lib/dates";

export default function Profile() {
  const { utente, classe, logout } = useAuth();

  return (
    <>
      <PageHeader title="Profilo" />
      <div className="stack">
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Avatar nome={utente?.nome} cognome={utente?.cognome} size={56} />
          <div>
            <h2 style={{ fontSize: 18 }}>
              {sentenceCase(utente?.nome)} {sentenceCase(utente?.cognome)}
            </h2>
            <p className="muted" style={{ fontSize: 13 }}>
              {utente?.id}
            </p>
          </div>
        </div>

        <Link to="/classe" className="card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span>
            <span className="muted" style={{ display: "block", fontSize: 12 }}>
              Classe
            </span>
            {classe || "Non scelta"}
          </span>
          <ChevronRight size={20} className="muted" />
        </Link>

        <button className="btn btn--danger" onClick={logout}>
          <LogOut size={20} /> Esci
        </button>
        <p className="muted" style={{ fontSize: 12, textAlign: "center" }}>
          Uscendo, i dati di sessione salvati su questo dispositivo vengono cancellati.
        </p>
      </div>
    </>
  );
}
