import { useCallback, useEffect, useState } from "react";

/**
 * Carica dei dati quando la pagina si apre.
 *
 *   const { data, loading, error, reload } = useApi(() => fetchGrades(), []);
 *
 * Il secondo argomento sono le "dipendenze": quando cambiano, i dati si ricaricano
 * (es. useApi(() => fetchGrades(periodo), [periodo])).
 */
export function useApi(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    loader()
      .then((data) => !cancelled && setState({ data, loading: false, error: null }))
      .catch((error) => !cancelled && setState({ data: null, loading: false, error }));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadCount]);

  const reload = useCallback(() => setReloadCount((n) => n + 1), []);
  return { ...state, reload };
}
