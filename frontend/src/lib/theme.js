// Colore d'accento dell'app (blu o verde). La scelta vale per il dispositivo,
// non per l'utente, così si applica anche alla schermata di login.
const STORAGE_KEY = 'skedoo-accent'
export const ACCENTS = ['blue', 'green']

export function readAccent() {
	try {
		const value = localStorage.getItem(STORAGE_KEY)
		return ACCENTS.includes(value) ? value : 'blue'
	} catch {
		return 'blue'
	}
}

export function applyAccent(accent) {
	if (accent === 'green') document.documentElement.dataset.accent = 'green'
	else delete document.documentElement.dataset.accent
}

export function setAccent(accent) {
	applyAccent(accent)
	try {
		localStorage.setItem(STORAGE_KEY, accent)
	} catch {
		// storage non disponibile: la scelta vale solo per questa sessione
	}
}
