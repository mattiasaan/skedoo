import { getToken } from './session.js'

// In sviluppo le chiamate passano dal proxy di Vite (/api -> http://localhost:8000, vedi vite.config.js):
// niente problemi di CORS e funziona anche aprendo il sito dal telefono sulla rete locale.
const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export const UNAUTHORIZED_EVENT = 'skedoo:unauthorized'
const AUTH_ERRORS = new Set(['not_authenticated', 'invalid_token', 'session_expired'])

export class ApiError extends Error {
	constructor(status, code, message) {
		super(message)
		this.name = 'ApiError'
		this.status = status
		this.code = code
	}
}

function errorMessage(status, payload) {
	if (payload?.message) return payload.message
	if (status === 422) return 'Dati non validi, controlla i campi inseriti.'
	if (status === 429) return 'Troppe richieste, riprova tra poco.'
	if (status >= 500) return 'Il server non risponde correttamente, riprova tra poco.'
	return 'Errore nella comunicazione con il server.'
}

async function request(path, { method = 'GET', body, auth = true, params } = {}) {
	const query = params
		? '?' + new URLSearchParams(Object.entries(params).filter(([, value]) => value != null && value !== '')).toString()
		: ''
	const headers = { Accept: 'application/json' }
	if (body !== undefined) headers['Content-Type'] = 'application/json'
	const token = auth ? getToken() : null
	if (token) headers.Authorization = `Bearer ${token}`

	let response
	try {
		response = await fetch(`${API_BASE}${path}${query === '?' ? '' : query}`, {
			method,
			headers,
			body: body === undefined ? undefined : JSON.stringify(body),
		})
	} catch {
		throw new ApiError(0, 'network_error', 'Impossibile raggiungere il server. Controlla la connessione.')
	}

	const text = response.status === 204 ? '' : await response.text()
	let payload = null
	if (text) {
		try {
			payload = JSON.parse(text)
		} catch {
			payload = null
		}
	}

	if (!response.ok) {
		const code = payload?.code ?? (response.status === 422 ? 'validation_error' : 'http_error')
		const error = new ApiError(response.status, code, errorMessage(response.status, payload))
		if (auth && response.status === 401 && AUTH_ERRORS.has(code)) {
			window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT, { detail: error }))
		}
		throw error
	}

	return payload
}

// ---------- endpoint ----------
export const api = {
	login: (username, password) => request('/auth/login', { method: 'POST', body: { username, password }, auth: false }),
	me: () => request('/auth/me'),
	logout: () => request('/auth/logout', { method: 'POST' }),

	classes: () => request('/schedules/classes'),
	schedule: (classId) => request(`/schedules/${encodeURIComponent(classId)}`),

	grades: () => request('/grades'),
	agenda: (da, a) => request('/agenda', { params: { da, a } }),
	absences: () => request('/assenze'),
	didactics: () => request('/didattica'),
	board: () => request('/bacheca'),
	boardItem: (codice, id) => request(`/bacheca/${encodeURIComponent(codice)}/${encodeURIComponent(id)}`),
	changes: (classe) => request('/changes', { params: { classe } }),
}
