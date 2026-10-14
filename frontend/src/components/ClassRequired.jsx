import { Link } from "react-router-dom";

// Mostrato dalle pagine che servono la classe (Home, Orario) se l'utente non l'ha ancora scelta
export default function ClassRequired() {
  return (
    <div className="card stack" style={{ alignItems: "center", textAlign: "center", marginTop: 24 }}>
      <h2 style={{ fontSize: 18 }}>Scegli la tua classe</h2>
      <p className="muted">Serve per mostrarti l'orario giusto.</p>
      <Link to="/classe" className="btn">
        Scegli classe
      </Link>
    </div>
  );
}
