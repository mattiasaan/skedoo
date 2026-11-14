// Tutto ciò che resta sul dispositivo: token, profilo, classe scelta e piccole preferenze.
// localStorage può non essere disponibile (navigazione privata, permessi): ogni accesso è protetto.

const KEYS = {
	token: 'token',
	user: 'utente',
}

function read(key) {
	try {
		return localStorage.getItem(key)
	} catch {
		return null
	}
}

function write(key, value) {
	try {
		if (value == null) localStorage.removeItem(key)
		else localStorage.setItem(key, value)
	} catch {
		// storage non disponibile: la sessione vale solo finché la pagina resta aperta
	}
}

export function getToken() {
	return read(KEYS.token)
}

export function getStoredUser() {
	try {
		return JSON.parse(read(KEYS.user) ?? 'null')
	} catch {
		return null
	}
}

// La classe è salvata per utente: su un dispositivo condiviso ognuno ritrova la propria.
function classKey(userId) {
	return `skedoo:class:${String(userId ?? '').toLowerCase()}`
}

export function getClassId(userId) {
	return read(classKey(userId))
}

export function setClassId(userId, classId) {
	write(classKey(userId), classId)
}

export function saveSession(token, user) {
	write(KEYS.token, token)
	write(KEYS.user, user ? JSON.stringify(user) : null)
}

export function saveUser(user) {
	write(KEYS.user, user ? JSON.stringify(user) : null)
}

export function clearSession() {
	write(KEYS.token, null)
	write(KEYS.user, null)
}

// ---------- preferenze e stati locali (compiti completati, avvisi chiusi...) ----------
export function readJson(key, fallback) {
	try {
		const value = JSON.parse(read(`skedoo:${key}`) ?? 'null')
		return value ?? fallback
	} catch {
		return fallback
	}
}

export function writeJson(key, value) {
	write(`skedoo:${key}`, JSON.stringify(value))
}

// ---------- scuola ----------
function normalize(value) {
	return String(value ?? '')
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.replace(/[^a-z0-9 ]/gi, ' ')
		.replace(/\s+/g, ' ')
		.trim()
		.toUpperCase()
}

/** Gli orari (e quindi selezione classe, orario di oggi e variazioni) esistono solo per il Galilei di Bolzano. */
export function isGalileiSchool(school) {
	if (!school) return false
	const name = normalize(`${school.dedica ?? ''} ${school.nome ?? ''}`)
	return name.includes('GALILEI') && normalize(school.citta) === 'BOLZANO'
}
