import { api } from './api.js'
import { getToken, saveToken, shouldRefreshToken } from './session.js'

let pending = null

/**
 * Rinnova il token se ha più di 12 ore. Gli errori di rete si ignorano (si riprova la volta dopo);
 * un 401 (sessione chiusa, 90 giorni dal login) lo gestisce già api.js riportando al login.
 */
export function refreshTokenIfStale() {
	const token = getToken()
	if (pending || !shouldRefreshToken(token)) return pending ?? Promise.resolve()
	pending = api.refresh()
		.then((data) => {
			// nel frattempo l'utente può essere uscito o aver rifatto il login: non si sovrascrive quel token
			if (data?.access_token && getToken() === token) saveToken(data.access_token)
		})
		.catch(() => {})
		.finally(() => {
			pending = null
		})
	return pending
}
