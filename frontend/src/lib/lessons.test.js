import { describe, expect, it } from 'vitest'
import { hoursOf, isLongTopic, registerBlocks, topicPreview, topicsForBlock, uniqueTopics } from './lessons.js'

const lesson = (ora, materia, argomento, extra = {}) => ({
	id: `${ora}-${materia}`, ora, durata: 1, materia, docente: 'ROSSI Mario', tipo: 'Lezione', compresenza: false, argomento, ...extra,
})

describe('registro di classe', () => {
	it('calcola le ore coperte da una firma', () => {
		expect(hoursOf({ ora: 2, durata: 2 })).toEqual([2, 3])
		expect(hoursOf({ ora: 4 })).toEqual([4])
		expect(hoursOf({ ora: null })).toEqual([])
	})

	it('toglie gli argomenti vuoti e ripetuti', () => {
		const topics = uniqueTopics([
			lesson(3, 'FISICA', 'Introduzione al corso'),
			lesson(4, 'FISICA', 'introduzione  al corso'),
			lesson(5, 'FISICA', null),
		])
		expect(topics).toEqual([{ text: 'Introduzione al corso', teacher: 'ROSSI Mario', type: 'Lezione' }])
	})

	it("abbina l'argomento al blocco dell'orario per ora e materia", () => {
		const register = {
			data: '2026-10-06',
			lezioni: [
				lesson(1, 'MATEMATICA', 'Equazioni'),
				lesson(2, 'LINGUA E CULTURA STRANIERA INGLESE', 'Present perfect'),
				lesson(2, 'SOSTEGNO', 'Supporto', { compresenza: true }),
			],
		}
		expect(topicsForBlock(register, { materia: 'Inglese', ore: [2] }).map((topic) => topic.text)).toEqual(['Present perfect'])
		expect(topicsForBlock(register, { materia: 'Matematica', ore: [1] })[0].text).toBe('Equazioni')
		expect(topicsForBlock(register, { materia: 'Storia', ore: [5] })).toEqual([])
	})

	it('con nomi diversi usa la sola lezione firmata in quelle ore', () => {
		const register = { data: '2026-10-06', lezioni: [lesson(3, 'TECNOLOGIE E PROGETTAZIONE', 'Socket TCP')] }
		expect(topicsForBlock(register, { materia: 'TPSIT', ore: [3, 4] })[0].text).toBe('Socket TCP')
		const two = { data: '2026-10-06', lezioni: [lesson(3, 'A', 'uno'), lesson(4, 'B', 'due')] }
		expect(topicsForBlock(two, { materia: 'TPSIT', ore: [3, 4] })).toEqual([])
	})

	it('unisce le ore consecutive per le scuole senza orario', () => {
		const blocks = registerBlocks({
			data: '2026-10-06',
			lezioni: [
				lesson(1, 'FISICA', 'Moto'),
				lesson(2, 'FISICA', 'Moto'),
				lesson(2, 'FISICA', 'Laboratorio: misure', { compresenza: true, docente: 'VERDI Luca' }),
				lesson(3, 'STORIA', null),
			],
		})
		expect(blocks).toHaveLength(2)
		expect(blocks[0]).toMatchObject({ materia: 'FISICA', ore: [1, 2], teachers: ['ROSSI Mario'], inizio: null })
		expect(blocks[0].topics.map((topic) => topic.text)).toEqual(['Moto', 'Laboratorio: misure'])
		expect(blocks[1].topics).toEqual([])
		expect(registerBlocks(undefined)).toEqual([])
	})

	it("prepara l'anteprima e riconosce i testi lunghi", () => {
		expect(topicPreview([{ text: 'Uno\ndue' }, { text: 'tre' }])).toBe('Uno due • tre')
		expect(topicPreview([])).toBeNull()
		expect(isLongTopic('breve')).toBe(false)
		expect(isLongTopic('a'.repeat(400))).toBe(true)
		expect(isLongTopic('1\n2\n3\n4\n5\n6\n7')).toBe(true)
	})
})
