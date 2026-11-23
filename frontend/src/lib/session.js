// Tutto ciò che resta sul dispositivo: token, profilo, classe scelta e piccole preferenze.
// localStorage può non essere disponibile (navigazione privata, permessi): ogni accesso è protetto.

const KEYS = {
	token: 'token',
	user: 'utente',
	lastLogin: 'skedoo:ultimo-accesso',
	other: 'skedoo:altro-account',
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

// Il token si rinnova (POST /auth/refresh) quando ha più di 12 ore: chi usa l'app almeno una volta
// a settimana non deve mai rifare il login (il server lo chiede solo dopo 90 giorni dall'accesso).
const REFRESH_AFTER_MS = 12 * 60 * 60 * 1000

/** Istante di emissione del token (ms), letto dal payload del JWT; null se non si legge. Non verifica nulla: lo fa il server. */
export function tokenIssuedAt(token) {
	try {
		const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
		const iat = JSON.parse(atob(payload)).iat
		return Number.isFinite(iat) ? iat * 1000 : null
	} catch {
		return null
	}
}

export function shouldRefreshToken(token, now = Date.now()) {
	if (!token) return false
	const issued = tokenIssuedAt(token)
	return issued == null || now - issued > REFRESH_AFTER_MS
}

export function saveToken(token) {
	write(KEYS.token, token)
}

export function saveSession(token, user) {
	write(KEYS.token, token)
	write(KEYS.user, user ? JSON.stringify(user) : null)
}

export function saveUser(user) {
	write(KEYS.user, user ? JSON.stringify(user) : null)
}

// Chi viene buttato fuori (sessione scaduta) ritrova username e nome già pronti: basta la password,
// che il gestore di password del browser può inserire da solo. Il logout volontario li cancella.
export function rememberLastLogin(user) {
	write(KEYS.lastLogin, user?.id ? JSON.stringify({ id: user.id, nome: user.nome ?? '' }) : null)
}

export function getLastLogin() {
	try {
		const value = JSON.parse(read(KEYS.lastLogin) ?? 'null')
		return typeof value?.id === 'string' && value.id ? value : null
	} catch {
		return null
	}
}

export function clearSession() {
	write(KEYS.token, null)
	write(KEYS.user, null)
}

// ---------- secondo account (studente <-> genitore) ----------
// L'account attivo resta in `token`/`utente`; l'altro aspetta qui con il suo token, così si passa
// dall'uno all'altro senza rifare il login. Sul dispositivo non c'è mai una password, solo i due JWT.

export function getOtherAccount() {
	try {
		const value = JSON.parse(read(KEYS.other) ?? 'null')
		return typeof value?.token === 'string' && value.token && value.user?.id ? value : null
	} catch {
		return null
	}
}

export function saveOtherAccount(account) {
	write(KEYS.other, account?.token && account.user?.id ? JSON.stringify({ token: account.token, user: account.user }) : null)
}

export function saveOtherToken(token) {
	const other = getOtherAccount()
	if (other) saveOtherAccount({ ...other, token })
}

/** L'account attivo diventa quello in attesa e viceversa. Restituisce il nuovo account attivo (o null). */
export function swapAccounts() {
	const other = getOtherAccount()
	if (!other) return null
	const token = getToken()
	const user = getStoredUser()
	saveOtherAccount(token && user ? { token, user } : null)
	saveSession(other.token, other.user)
	return other
}

/** Stesso account ClasseViva? Gli username non distinguono maiuscole e minuscole. */
export function sameAccount(first, second) {
	return Boolean(first?.id && second?.id) && String(first.id).toLowerCase() === String(second.id).toLowerCase()
}

/** "Account genitore" / "Account studente" (o null se ClasseViva non lo dice). */
export function accountTypeLabel(user) {
	if (user?.tipo === 'genitore') return 'Account genitore'
	if (user?.tipo === 'studente') return 'Account studente'
	return null
}

// ---------- preferenze e stati locali (compiti completati, circolari lette...) ----------
// Salvati per utente: su un dispositivo condiviso ognuno ritrova solo i propri.
function userKey(key) {
	const userId = String(getStoredUser()?.id ?? 'anonimo').toLowerCase()
	return `skedoo:${userId}:${key}`
}

export function readJson(key, fallback) {
	try {
		const value = JSON.parse(read(userKey(key)) ?? 'null')
		return value ?? fallback
	} catch {
		return fallback
	}
}

export function writeJson(key, value) {
	write(userKey(key), JSON.stringify(value))
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
