// Notifiche push (Web Push): il service worker public/sw.js le mostra, il backend le invia quando compaiono
// variazioni nuove per la classe. L'iscrizione è del DISPOSITIVO: una sola, con la classe dell'account in uso.
import { api } from './api.js'

const SW_URL = 'sw.js' // relativo alla pagina: funziona anche sotto un percorso (GitHub Pages)

export class PushError extends Error {
	constructor(code, message) {
		super(message)
		this.name = 'PushError'
		this.code = code
	}
}

export function isIos(nav = globalThis.navigator) {
	return /iPad|iPhone|iPod/.test(nav?.userAgent ?? '') || (nav?.platform === 'MacIntel' && nav?.maxTouchPoints > 1)
}

export function isStandalone(env = globalThis) {
	return Boolean(env.matchMedia?.('(display-mode: standalone)')?.matches || env.navigator?.standalone)
}

/**
 * Cosa permette il dispositivo:
 * 'ok' | 'denied' (bloccate dall'utente) | 'needs-install' (iPhone/iPad: solo dall'app aggiunta alla Home) | 'unsupported'
 */
export function pushSupport(env = globalThis) {
	const nav = env.navigator
	if (!nav?.serviceWorker || !env.PushManager || !env.Notification) {
		return isIos(nav) && !isStandalone(env) ? 'needs-install' : 'unsupported'
	}
	return env.Notification.permission === 'denied' ? 'denied' : 'ok'
}

/** Chiave VAPID base64url -> byte (applicationServerKey). */
export function base64UrlToBytes(value) {
	const base64 = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (value.length % 4)) % 4)
	return Uint8Array.from(atob(base64), (char) => char.charCodeAt(0))
}

/** La chiave con cui è stata creata l'iscrizione è ancora quella del server? (le chiavi VAPID possono cambiare) */
export function sameKey(buffer, bytes) {
	if (!buffer) return true // il browser non la espone: si tiene l'iscrizione
	const current = new Uint8Array(buffer)
	return current.length === bytes.length && current.every((byte, index) => byte === bytes[index])
}

async function registration() {
	await navigator.serviceWorker.register(SW_URL, { scope: './' })
	return navigator.serviceWorker.ready // subscribe vuole un service worker già attivo
}

async function existingSubscription() {
	if (!navigator.serviceWorker) return null
	const reg = await navigator.serviceWorker.getRegistration() // quella che controlla questa pagina, senza crearla
	return reg ? reg.pushManager.getSubscription() : null
}

/** Crea (o riusa) l'iscrizione del browser e la registra sul server per la classe. */
async function subscribeDevice(classId) {
	const [reg, { public_key: publicKey }] = await Promise.all([registration(), api.pushPublicKey()])
	const key = base64UrlToBytes(publicKey)
	let subscription = await reg.pushManager.getSubscription()
	if (subscription && !sameKey(subscription.options?.applicationServerKey, key)) {
		await subscription.unsubscribe()
		subscription = null
	}
	subscription ??= await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key })
	await api.pushSubscribe(subscription.toJSON(), classId)
}

/** Dal pulsante "attiva": chiede il permesso (serve un clic dell'utente) e iscrive il dispositivo. */
export async function enablePush(classId) {
	const support = pushSupport()
	if (support !== 'ok') throw new PushError(support, 'Notifiche non disponibili su questo dispositivo')
	const permission = await Notification.requestPermission()
	if (permission !== 'granted') throw new PushError('denied', 'Permesso per le notifiche non concesso')
	await subscribeDevice(classId)
}

/** Cancella l'iscrizione dal server e dal browser. Nessun errore se non c'era. */
export async function disablePush() {
	const subscription = await existingSubscription()
	if (!subscription) return
	try {
		await api.pushUnsubscribe(subscription.endpoint)
	} catch {
		// server irraggiungibile: cancellata dal browser, il server la scarta al primo invio (410)
	}
	await subscription.unsubscribe()
}

/**
 * Allinea il dispositivo alla preferenza dell'account in uso (all'avvio, al cambio di classe o di account).
 * `classId` null = notifiche spente. Restituisce 'on', 'off' oppure 'denied' (permesso tolto dal browser).
 */
export async function syncPush(classId) {
	const support = pushSupport()
	if (support === 'unsupported' || support === 'needs-install') return 'off'
	if (!classId) {
		await disablePush()
		return 'off'
	}
	if (Notification.permission !== 'granted') return 'denied'
	await subscribeDevice(classId)
	return 'on'
}
