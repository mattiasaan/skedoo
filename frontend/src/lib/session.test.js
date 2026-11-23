import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
	accountTypeLabel, getOtherAccount, getStoredUser, getToken, sameAccount, saveOtherAccount, saveOtherToken, saveSession, shouldRefreshToken,
	swapAccounts, tokenIssuedAt,
} from './session.js'

function jwt(payload) {
	const b64 = (value) => btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
	return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64(payload)}.firma`
}

describe('token', () => {
	const now = Date.UTC(2026, 10, 22, 12)

	it("legge l'istante di emissione", () => {
		expect(tokenIssuedAt(jwt({ iat: now / 1000, sub: 'S1X' }))).toBe(now)
		expect(tokenIssuedAt('non-un-jwt')).toBeNull()
		expect(tokenIssuedAt(jwt({ sub: 'S1X' }))).toBeNull()
	})

	it('si rinnova dopo 12 ore', () => {
		const hour = 60 * 60 * 1000
		expect(shouldRefreshToken(jwt({ iat: (now - hour) / 1000 }), now)).toBe(false)
		expect(shouldRefreshToken(jwt({ iat: (now - 13 * hour) / 1000 }), now)).toBe(true)
		expect(shouldRefreshToken('illeggibile', now)).toBe(true) // il server dirà se è ancora valido
		expect(shouldRefreshToken(null, now)).toBe(false)
	})
})

describe('secondo account', () => {
	const student = { id: 'S1234567X', nome: 'MARIO', tipo: 'studente' }
	const parent = { id: 'G1234567X', nome: 'MARIO', tipo: 'genitore' }

	beforeEach(() => {
		const data = new Map()
		vi.stubGlobal('localStorage', {
			getItem: (key) => (data.has(key) ? data.get(key) : null),
			setItem: (key, value) => data.set(key, String(value)),
			removeItem: (key) => data.delete(key),
		})
	})

	it("scambia l'account attivo con quello in attesa, token compresi", () => {
		saveSession('token-studente', student)
		saveOtherAccount({ token: 'token-genitore', user: parent })

		expect(swapAccounts()?.user.id).toBe(parent.id)
		expect(getToken()).toBe('token-genitore')
		expect(getStoredUser().tipo).toBe('genitore')
		expect(getOtherAccount()).toEqual({ token: 'token-studente', user: student })

		swapAccounts()
		expect(getToken()).toBe('token-studente')
	})

	it('senza secondo account non cambia nulla', () => {
		saveSession('token-studente', student)
		expect(swapAccounts()).toBeNull()
		expect(getToken()).toBe('token-studente')
	})

	it('il rinnovo aggiorna solo il token in attesa', () => {
		saveOtherAccount({ token: 'vecchio', user: parent })
		saveOtherToken('nuovo')
		expect(getOtherAccount()).toEqual({ token: 'nuovo', user: parent })
		saveOtherAccount(null)
		saveOtherToken('ignorato')
		expect(getOtherAccount()).toBeNull()
	})

	it('riconosce lo stesso account e il tipo', () => {
		expect(sameAccount(student, { id: 's1234567x' })).toBe(true)
		expect(sameAccount(student, parent)).toBe(false)
		expect(sameAccount(null, parent)).toBe(false)
		expect(accountTypeLabel(parent)).toBe('Account genitore')
		expect(accountTypeLabel({ id: 'mario@example.com' })).toBeNull()
	})
})
