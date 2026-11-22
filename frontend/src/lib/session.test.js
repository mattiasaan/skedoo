import { describe, expect, it } from 'vitest'
import { shouldRefreshToken, tokenIssuedAt } from './session.js'

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
