import { useCallback, useEffect, useSyncExternalStore } from 'react'

// Cache in memoria condivisa da tutte le schermate: cambiare tab non rifà le richieste
// (il backend limita le chiamate a ClasseViva a 20 al minuto per utente).
const STALE_MS = 5 * 60 * 1000
const cache = new Map() // key -> { data, error, time, promise }
const listeners = new Set()
let version = 0 // cambia a ogni modifica della cache: fa ridisegnare chi la usa
let generation = 0 // cambia solo quando la cache viene svuotata (logout, "Sincronizza")

function notify() {
	version += 1
	listeners.forEach((listener) => listener())
}

function subscribe(listener) {
	listeners.add(listener)
	return () => listeners.delete(listener)
}

function load(key, fetcher, force = false) {
	const entry = cache.get(key)
	if (entry?.promise) return entry.promise
	if (!force && entry && !entry.error && Date.now() - entry.time < STALE_MS) return Promise.resolve(entry.data)

	// una risposta arrivata dopo uno svuotamento (es. logout) non deve tornare in cache:
	// sarebbe visibile al prossimo utente dello stesso dispositivo
	const startedIn = generation
	const promise = fetcher()
		.then((data) => {
			if (startedIn !== generation) return data
			cache.set(key, { data, error: null, time: Date.now(), promise: null })
			notify()
			return data
		})
		.catch((error) => {
			if (startedIn !== generation) throw error
			cache.set(key, { data: entry?.data, error, time: Date.now(), promise: null })
			notify()
			throw error
		})
	cache.set(key, { ...(entry ?? {}), promise })
	notify()
	return promise
}

/** Svuota la cache (logout o "Sincronizza ora"). */
export function clearApiCache() {
	generation += 1
	cache.clear()
	notify()
}

/**
 * Dati da un endpoint con cache condivisa.
 * `key` null = richiesta disattivata (es. classe non ancora scelta).
 */
export function useApi(key, fetcher) {
	useSyncExternalStore(subscribe, () => version)
	const currentGeneration = generation

	// si (ri)carica quando cambia la chiave o dopo uno svuotamento della cache con la schermata aperta
	useEffect(() => {
		if (key == null) return
		load(key, fetcher).catch(() => {})
		// fetcher cambia identità a ogni render: la chiave basta a identificare la richiesta
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key, currentGeneration])

	/** Richiede di nuovo i dati: la promessa vale true se l'aggiornamento è riuscito. */
	const reload = useCallback(() => {
		if (key == null) return Promise.resolve(false)
		return load(key, fetcher, true).then(() => true, () => false)
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key])

	const entry = key == null ? null : cache.get(key)
	return {
		data: entry?.data,
		error: entry?.error ?? null,
		loading: key != null && (!entry || Boolean(entry.promise)) && entry?.data === undefined,
		refreshing: Boolean(entry?.promise),
		reload,
	}
}
