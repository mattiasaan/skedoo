import { Eye, EyeOff, GraduationCap, LockKeyhole, LogIn, User } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import "./Login.css";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password); // se va a buon fine, App.jsx porta da solo alla Home
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  return (
    <div className="app app--no-nav login">
      <div className="login__logo">
        <GraduationCap size={44} />
      </div>
      <h1>Benvenuto su Skedoo</h1>
      <p className="muted">Accedi con le credenziali del registro elettronico</p>

      <form className="stack" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <div className="input">
            <User size={20} />
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Il tuo username ClasseViva"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              required
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <div className="input">
            <LockKeyhole size={20} />
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="La tua password"
              autoComplete="current-password"
              required
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Nascondi password" : "Mostra password"}>
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
        </div>

        {error && (
          <p className="login__error" role="alert">
            {error}
          </p>
        )}

        <button className="btn" disabled={loading || !username || !password}>
          <LogIn size={20} /> {loading ? "Accesso in corso…" : "Accedi con ClasseViva"}
        </button>
        <p className="login__privacy muted">Le credenziali non vengono salvate su questo dispositivo.</p>
      </form>
    </div>
  );
}
