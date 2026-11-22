// Navigazione: la schermata corrente vive nell'hash dell'URL (#voti, #profilo/assenze...),
// così il tasto "indietro" del browser e il refresh funzionano senza un router esterno.

export const TABS = [
	{ id: 'home', label: 'Home', icon: 'grid' },
	{ id: 'agenda', label: 'Agenda', icon: 'calendar' },
	{ id: 'voti', label: 'Voti', icon: 'chart' },
	{ id: 'profilo', label: 'Profilo', icon: 'person' },
]

/** Sottoschermate: percorso -> tab evidenziata nella navigazione. */
export const SUBPAGES = {
	'home/compiti': 'home',
	'home/bacheca': 'home',
	'profilo/assenze': 'profilo',
	'profilo/materiali': 'profilo',
}

// Dashboard di una materia: "#agenda/materia/Fisica". La prima parte è la tab da cui la si apre:
// resta evidenziata nella navigazione ed è la schermata a cui torna "indietro".
const SUBJECT_ROUTE = /^(home|agenda|voti|profilo)\/materia\/(.+)$/i

/** Percorso della dashboard della materia `name`, aperta dalla tab `tab`. */
export function subjectPath(tab, name) {
	return `${TABS.some((item) => item.id === tab) ? tab : 'home'}/materia/${encodeURIComponent(name)}`
}

/**
 * "#profilo/assenze" -> { path: 'profilo/assenze', tab: 'profilo' }.
 * "#agenda/materia/Fisica" -> { path: 'materia', tab: 'agenda', subject: 'Fisica' }. Percorsi sconosciuti -> Home.
 */
export function parseRoute(hash = window.location.hash) {
	let raw
	try {
		raw = decodeURIComponent(hash.replace(/^#\/?/, ''))
	} catch {
		return { path: 'home', tab: 'home' } // hash scritto a mano con una codifica non valida
	}
	const subject = SUBJECT_ROUTE.exec(raw)
	if (subject && subject[2].trim()) return { path: 'materia', tab: subject[1].toLowerCase(), subject: subject[2].trim() }
	const path = raw.toLowerCase()
	if (SUBPAGES[path]) return { path, tab: SUBPAGES[path] }
	if (TABS.some((tab) => tab.id === path)) return { path, tab: path }
	return { path: 'home', tab: 'home' }
}
