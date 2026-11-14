import { describe, expect, it } from 'vitest'
import { flattenAgenda, monthRange, toAgendaItem, upcomingRange } from './agenda.js'
import { parseRoute } from './routes.js'

describe('agenda', () => {
	it('riconosce verifiche, compiti ed eventi', () => {
		expect(toAgendaItem({ id: 1, tipo: 'annotazione', materia: 'MATEMATICA', testo: 'Verifica scritta sui limiti' }, '2026-11-19'))
			.toMatchObject({ kind: 'verifica', label: 'VERIFICA', tone: 'danger', title: 'Verifica di Matematica' })
		expect(toAgendaItem({ id: 2, tipo: 'compito', materia: 'ITALIANO', testo: 'Leggere il canto V' }, '2026-11-18'))
			.toMatchObject({ kind: 'compito', title: 'Compiti di Italiano', key: 'agenda-2-2026-11-18' })
		expect(toAgendaItem({ id: 3, tipo: 'evento', materia: null, testo: 'Assemblea di istituto. In aula magna' }, '2026-11-20'))
			.toMatchObject({ kind: 'evento', title: 'Assemblea di istituto' })
	})

	it('appiattisce i giorni', () => {
		const items = flattenAgenda({ giorni: [{ data: '2026-11-18', eventi: [{ id: 1, tipo: 'compito', testo: 'x' }] }] })
		expect(items).toHaveLength(1)
		expect(items[0].date).toBe('2026-11-18')
		expect(flattenAgenda(undefined)).toEqual([])
	})

	it('intervalli: mese da lunedì a domenica, prossimi giorni', () => {
		const range = monthRange(new Date(2026, 10, 17))
		expect(range.da).toBe('2026-10-26') // lunedì della settimana del 1° novembre
		expect(range.a).toBe('2026-12-06') // domenica della settimana del 30 novembre
		expect(upcomingRange(new Date(2026, 10, 17), 14)).toEqual({ da: '2026-11-17', a: '2026-11-30' })
	})
})

describe('route', () => {
	it.each([
		['#voti', { path: 'voti', tab: 'voti' }],
		['#profilo/assenze', { path: 'profilo/assenze', tab: 'profilo' }],
		['#HOME/BACHECA', { path: 'home/bacheca', tab: 'home' }],
		['#qualcosa', { path: 'home', tab: 'home' }],
		['', { path: 'home', tab: 'home' }],
	])('%s', (hash, expected) => {
		expect(parseRoute(hash)).toEqual(expected)
	})
})
