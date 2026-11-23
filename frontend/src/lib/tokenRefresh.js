import { api } from './api.js'
import { getOtherAccount, getToken, saveOtherToken, saveToken, shouldRefreshToken } from './session.js'

const pending = { active: null, other: null }

/**
 * Rinnova un token con più di 12 ore. Gli errori si ignorano (si riprova la volta dopo): per l'account attivo
 * un 401 (sessione chiusa, 90 giorni dal login) lo gestisce già api.js riportando al login; per quello in attesa
 * il 401 si scopre solo passando a quell'account, che chiede di nuovo la password.
 */
function refresh(slot, read, save, explicit) {
	const token = read()
	if (pending[slot] || !shouldRefreshToken(token)) return pending[slot] ?? Promise.resolve()
	pending[slot] = api.refresh(explicit ? token : undefined)
		.then((data) => {
			// nel frattempo l'utente può essere uscito, aver cambiato account o rifatto il login: non si sovrascrive
			if (data?.access_token && read() === token) save(data.access_token)
		})
		.catch(() => {})
		.finally(() => {
			pending[slot] = null
		})
	return pending[slot]
}

/** Rinnova il token dell'account attivo e quello dell'eventuale secondo account (studente/genitore). */
export function refreshTokenIfStale() {
	return Promise.all([
		refresh('active', getToken, saveToken, false),
		refresh('other', () => getOtherAccount()?.token ?? null, saveOtherToken, true),
	])
}
