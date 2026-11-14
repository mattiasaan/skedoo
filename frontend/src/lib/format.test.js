import { describe, expect, it } from 'vitest'
import {
	classLabel,
	formatDuration,
	parseDateKey,
	relativeDay,
	schoolDisplayName,
	schoolYear,
	teacherName,
	teacherShort,
	titleCase,
} from './format.js'

describe('nomi', () => {
	it('titleCase mantiene i numeri romani e le preposizioni', () => {
		expect(titleCase('TEDESCO II LINGUA')).toBe('Tedesco II Lingua')
		expect(titleCase('LINGUA E LETTERATURA ITALIANA')).toBe('Lingua e Letteratura Italiana')
	})

	it('teacherShort tiene solo il cognome', () => {
		expect(teacherShort('ROSSI Mario')).toBe('Prof. De Santis')
		expect(teacherShort('ROSSI MARIO')).toBe('Prof. Moretti') // tutto maiuscolo: la prima parola è il cognome
		expect(teacherShort('')).toBe('')
		expect(teacherName('ROSSI Mario')).toBe('Prof. Neri Giulia')
	})

	it('classLabel aggiunge l\'ordinale', () => {
		expect(classLabel('4A')).toBe('4ª A')
		expect(classLabel('2MAQ1')).toBe('2ª MAQ1')
		expect(classLabel(null)).toBe('')
	})

	it('schoolDisplayName unisce nome e dedica', () => {
		expect(schoolDisplayName({ nome: 'LICEO SCIENTIFICO', dedica: '"G. GALILEI"' })).toBe('Liceo Scientifico G. Galilei')
	})
})

describe('date', () => {
	const today = new Date(2026, 10, 17, 10) // martedì 17 novembre 2026

	it('relativeDay', () => {
		expect(relativeDay('2026-11-17', today)).toBe('Oggi')
		expect(relativeDay('2026-11-18', today)).toBe('Domani')
		expect(relativeDay('2026-11-16', today)).toBe('Ieri')
		expect(relativeDay('2026-11-20', today)).toBe('Venerdì')
		expect(relativeDay('2026-12-01', today)).toBe('1 dic')
	})

	it('anno scolastico da settembre', () => {
		expect(schoolYear(new Date(2026, 8, 1))).toBe('2026/2027')
		expect(schoolYear(new Date(2027, 5, 1))).toBe('2026/2027')
	})

	it('parseDateKey e durate', () => {
		expect(parseDateKey('2026-11-17').getDate()).toBe(17)
		expect(parseDateKey('non-una-data')).toBeNull()
		expect(formatDuration(15)).toBe('15 min')
		expect(formatDuration(80)).toBe('1 h 20 min')
	})
})
