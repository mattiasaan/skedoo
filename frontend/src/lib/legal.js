// Documenti legali pubblici: raggiungibili da #privacy, #cookie e #termini, con o senza login.
// I testi stanno in src/legal/*.md e vengono caricati solo quando servono.

export const LEGAL_DOCS = {
	privacy: { title: 'Informativa privacy', load: () => import('../legal/privacy.md?raw') },
	cookie: { title: 'Cookie policy', load: () => import('../legal/cookie.md?raw') },
	termini: { title: 'Termini di servizio', load: () => import('../legal/termini.md?raw') },
}

/** "#privacy" -> "privacy"; qualsiasi altro hash -> null. */
export function legalDocFromHash(hash = window.location.hash) {
	const id = hash.replace(/^#\/?/, '').toLowerCase()
	return Object.hasOwn(LEGAL_DOCS, id) ? id : null
}
