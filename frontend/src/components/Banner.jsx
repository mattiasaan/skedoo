import { Info, X } from "lucide-react";
import { useState } from "react";
import "./Banner.css";

// Riquadro che si può chiudere. Usato in Home per le "ultime modifiche" all'orario.
export default function Banner({ title, children }) {
  const [open, setOpen] = useState(true);
  if (!open) return null;
  return (
    <div className="banner">
      <Info size={20} className="banner__icon" />
      <div className="banner__body">
        <strong>{title}</strong>
        {children}
      </div>
      <button className="banner__close" onClick={() => setOpen(false)} aria-label="Chiudi">
        <X size={18} />
      </button>
    </div>
  );
}
