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

/** "#profilo/assenze" -> { path: 'profilo/assenze', tab: 'profilo' }. Percorsi sconosciuti -> Home. */
export function parseRoute(hash = window.location.hash) {
	const path = decodeURIComponent(hash.replace(/^#\/?/, '')).toLowerCase()
	if (SUBPAGES[path]) return { path, tab: SUBPAGES[path] }
	if (TABS.some((tab) => tab.id === path)) return { path, tab: path }
	return { path: 'home', tab: 'home' }
}
