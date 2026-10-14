import { Search } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchClasses } from "../api";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import PageHeader from "../components/PageHeader";
import { ErrorBox, Loading } from "../components/Status";
import "./ClassPicker.css";

// Scelta della classe (si apre al primo accesso e dal Profilo)
export default function ClassPicker() {
  const { classe, setClasse } = useAuth();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const { data: classes, loading, error, reload } = useApi(fetchClasses, []);

  function choose(id) {
    setClasse(id);
    navigate("/", { replace: true });
  }

  const visible = (classes || []).filter((c) => c.nome.replace(/\s/g, "").toLowerCase().includes(search.replace(/\s/g, "").toLowerCase()));

  return (
    <div className="app app--no-nav stack">
      <PageHeader title="La tua classe" subtitle="L'orario che vedrai è quello di questa classe" />
      <div className="input">
        <Search size={20} />
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Cerca, per esempio 3B" aria-label="Cerca classe" />
      </div>

      {loading && <Loading />}
      {error && <ErrorBox error={error} onRetry={reload} />}
      {classes && visible.length === 0 && <p className="muted">Nessuna classe trovata.</p>}

      <div className="class-grid">
        {visible.map((c) => (
          <button key={c.id} className={"class-grid__item" + (c.id === classe ? " is-selected" : "")} onClick={() => choose(c.id)}>
            {c.nome}
          </button>
        ))}
      </div>
    </div>
  );
}
