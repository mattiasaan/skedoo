import { filenameFromDisposition } from './download.js'
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

async function send(path, { method = 'GET', body, auth = true, params, accept = 'application/json' } = {}) {
	const query = params
		? '?' + new URLSearchParams(Object.entries(params).filter(([, value]) => value != null && value !== '')).toString()
		: ''
	const headers = { Accept: accept }
	if (body !== undefined) headers['Content-Type'] = 'application/json'
	const token = auth ? getToken() : null
	if (token) headers.Authorization = `Bearer ${token}`

	try {
		return await fetch(`${API_BASE}${path}${query === '?' ? '' : query}`, {
			method,
			headers,
			body: body === undefined ? undefined : JSON.stringify(body),
		})
	} catch {
		throw new ApiError(0, 'network_error', 'Impossibile raggiungere il server. Controlla la connessione.')
	}
}

async function readJson(response) {
	const text = response.status === 204 ? '' : await response.text()
	if (!text) return null
	try {
		return JSON.parse(text)
	} catch {
		return null
	}
}

/** Errore per una risposta non ok; con 401 di sessione avvisa l'app, che riporta al login. */
async function failure(response, auth) {
	const payload = await readJson(response)
	const code = payload?.code ?? (response.status === 422 ? 'validation_error' : 'http_error')
	const error = new ApiError(response.status, code, errorMessage(response.status, payload))
	if (auth && response.status === 401 && AUTH_ERRORS.has(code)) {
		window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT, { detail: error }))
	}
	return error
}

async function request(path, options = {}) {
	const response = await send(path, options)
	if (!response.ok) throw await failure(response, options.auth ?? true)
	return readJson(response)
}

/**
 * Scarica un file dal backend (allegati, materiali). `onProgress(frazione | null)`: null se la dimensione non è nota.
 * Restituisce { kind: 'file', blob, filename } oppure { kind: 'json', data } (es. il link di un materiale).
 */
async function download(path, { onProgress } = {}) {
	const response = await send(path, { accept: '*/*' })
	if (!response.ok) throw await failure(response, true)
	const type = (response.headers.get('Content-Type') ?? '').split(';')[0].trim().toLowerCase()
	if (type === 'application/json') return { kind: 'json', data: await readJson(response) }

	const total = Number(response.headers.get('Content-Length')) || 0
	const filename = filenameFromDisposition(response.headers.get('Content-Disposition'))
	const chunks = []
	let received = 0
	try {
		const reader = response.body.getReader()
		for (;;) {
			const { done, value } = await reader.read()
			if (done) break
			chunks.push(value)
			received += value.length
			onProgress?.(total ? Math.min(1, received / total) : null)
		}
	} catch {
		// il server chiude la connessione se il file supera il limite durante il trasferimento
		throw new ApiError(0, 'download_failed', 'Download interrotto: controlla la connessione e riprova.')
	}
	if (total && received < total) throw new ApiError(0, 'download_failed', 'Download incompleto: riprova.')
	return { kind: 'file', blob: new Blob(chunks, { type: type || 'application/octet-stream' }), filename }
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
	boardAttachment: (codice, id, numero, options) =>
		download(`/bacheca/${encodeURIComponent(codice)}/${encodeURIComponent(id)}/allegati/${encodeURIComponent(numero)}`, options),
	material: (id, options) => download(`/didattica/${encodeURIComponent(id)}`, options),
	changes: (classe) => request('/changes', { params: { classe } }),
}
