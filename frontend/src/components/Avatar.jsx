import "./Avatar.css";

// Cerchio con le iniziali dell'utente
export default function Avatar({ nome = "", cognome = "", size = 48 }) {
  const initials = ((nome[0] || "") + (cognome[0] || "")).toUpperCase() || "?";
  return (
    <div className="avatar" style={{ width: size, height: size, fontSize: size * 0.38 }}>
      {initials}
    </div>
  );
}
