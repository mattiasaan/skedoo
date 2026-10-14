// Stato di sessione dell'app: chi è l'utente, quale classe ha scelto, login e logout.
// Qualsiasi componente può leggerlo con `const { utente, classe, logout } = useAuth();`
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, logout as apiLogout } from "../api";
import { setSessionLostHandler } from "../api/client";
import { KEYS, storage } from "../lib/storage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => storage.get(KEYS.token));
  const [utente, setUtente] = useState(() => storage.get(KEYS.utente));
  const [classe, setClasseState] = useState(() => storage.get(KEYS.classe));

  const clearSession = useCallback(() => {
    [KEYS.token, KEYS.credenziali, KEYS.utente].forEach(storage.remove);
    setToken(null);
    setUtente(null);
  }, []);

  // Se il client API non riesce più a rifare il login, si torna alla schermata di accesso
  useEffect(() => setSessionLostHandler(clearSession), [clearSession]);

  const login = useCallback(async (username, password) => {
    const result = await apiLogin(username.trim(), password);
    storage.set(KEYS.token, result.access_token);
    storage.set(KEYS.credenziali, { username: username.trim(), password }); // per il ri-login automatico
    storage.set(KEYS.utente, result.utente);
    setToken(result.access_token);
    setUtente(result.utente);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      /* se il server non risponde si esce lo stesso */
    }
    clearSession();
  }, [clearSession]);

  const setClasse = useCallback((id) => {
    storage.set(KEYS.classe, id);
    setClasseState(id);
  }, []);

  const value = useMemo(
    () => ({ isLoggedIn: Boolean(token), utente, classe, login, logout, setClasse }),
    [token, utente, classe, login, logout, setClasse],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
