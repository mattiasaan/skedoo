// Service worker di Skedoo: SOLO notifiche push. Nessuna cache e nessun gestore `fetch`:
// l'app si carica sempre dalla rete e non può restare bloccata su una versione vecchia.
// Il contenuto delle notifiche lo prepara il backend (backend/app/push_sender.py):
//   { "title": "...", "body": "...", "tag": "variazioni-4A-2026-11-26", "url": "./#home" }

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

function readMessage(data) {
	if (!data) return {}
	try {
		return data.json() ?? {}
	} catch {
		return { body: data.text() }
	}
}

self.addEventListener('push', (event) => {
	const message = readMessage(event.data)
	event.waitUntil(self.registration.showNotification(message.title || 'Skedoo', {
		body: message.body || '',
		// stesso tag = stessa giornata: la notifica nuova sostituisce la vecchia ma suona di nuovo
		tag: message.tag || undefined,
		renotify: Boolean(message.tag),
		icon: 'icons/icon-192.png',
		// Android: iconcina nella barra di stato e nel cerchio della notifica. Conta solo la trasparenza
		// (sagoma bianca su fondo trasparente): con un'immagine piena il sistema mostra un'icona di ripiego
		badge: 'icons/badge-96.png',
		lang: 'it',
		data: { url: message.url || './#home' },
	}))
})

self.addEventListener('notificationclick', (event) => {
	event.notification.close()
	const target = new URL(event.notification.data?.url || './#home', self.registration.scope).href
	event.waitUntil((async () => {
		const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
		const open = windows.find((client) => client.url.startsWith(self.registration.scope))
		if (!open) return self.clients.openWindow(target)
		await open.focus()
		try {
			await open.navigate(target)
		} catch {
			// finestra non controllata da questo service worker: basta portarla in primo piano
		}
	})())
})
