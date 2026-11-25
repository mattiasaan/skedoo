import { describe, expect, it } from 'vitest'
import { base64UrlToBytes, isIos, isStandalone, pushSupport, sameKey } from './push.js'

const IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1'
const ANDROID = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36'

function browser({ userAgent = ANDROID, push = true, permission = 'default', standalone = false, platform = 'Linux' } = {}) {
	return {
		navigator: { userAgent, platform, maxTouchPoints: 5, serviceWorker: push ? {} : undefined },
		PushManager: push ? function PushManager() {} : undefined,
		Notification: push ? { permission } : undefined,
		matchMedia: () => ({ matches: standalone }),
	}
}

describe('supporto delle notifiche push', () => {
	it('riconosce i browser che le supportano', () => {
		expect(pushSupport(browser())).toBe('ok')
		expect(pushSupport(browser({ permission: 'granted' }))).toBe('ok')
		expect(pushSupport(browser({ permission: 'denied' }))).toBe('denied')
		expect(pushSupport(browser({ push: false }))).toBe('unsupported')
	})

	it("su iPhone serve l'app aggiunta alla Home", () => {
		expect(pushSupport(browser({ userAgent: IPHONE, push: false }))).toBe('needs-install')
		// installata ma iOS troppo vecchio (prima della 16.4): non c'è niente da fare
		expect(pushSupport(browser({ userAgent: IPHONE, push: false, standalone: true }))).toBe('unsupported')
		expect(pushSupport(browser({ userAgent: IPHONE, standalone: true }))).toBe('ok')
	})

	it("riconosce l'iPad che si presenta come Mac", () => {
		expect(isIos({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel', maxTouchPoints: 5 })).toBe(true)
		expect(isIos({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel', maxTouchPoints: 0 })).toBe(false)
		expect(isStandalone({ matchMedia: () => ({ matches: false }), navigator: { standalone: true } })).toBe(true)
	})
})

describe('chiave VAPID', () => {
	it('converte da base64url', () => {
		expect([...base64UrlToBytes('AQID_-8')]).toEqual([1, 2, 3, 255, 239])
		expect(base64UrlToBytes('B' + 'A'.repeat(86))).toHaveLength(65)
	})

	it("confronta la chiave dell'iscrizione con quella del server", () => {
		const key = Uint8Array.from([4, 1, 2])
		expect(sameKey(Uint8Array.from([4, 1, 2]).buffer, key)).toBe(true)
		expect(sameKey(Uint8Array.from([4, 1, 3]).buffer, key)).toBe(false)
		expect(sameKey(null, key)).toBe(true)
	})
})
