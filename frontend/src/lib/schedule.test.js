import { describe, expect, it } from 'vitest'
import { buildDayLessons, dayProgress, lessonStatus, periodLabel, subjectMatches } from './schedule.js'

const lesson = (ora, inizio, fine, materia, aula = 'AULA B1', docenti = ['ROSSI Mario']) => ({ ora, inizio, fine, materia, aula, docenti })

// martedì 17 novembre 2026
const TUESDAY = new Date(2026, 10, 17, 12)
const SCHEDULE = {
	giorni: [{
		giorno: 'martedi',
		lezioni: [
			lesson(1, '08:10', '09:00', 'Tedesco'),
			lesson(2, '09:00', '09:50', 'Italiano', 'AULA B111'),
			lesson(3, '09:50', '10:40', 'Italiano', 'AULA B111'),
			lesson(4, '10:40', '11:30', 'Matematica', 'AULA D009', ['SARRI Wanda', 'PNRR AMB. (301)']),
			lesson(8, '14:30', '15:20', 'Sistemi'),
		],
	}],
}

describe('buildDayLessons', () => {
	it('unisce le ore consecutive della stessa materia e filtra i docenti finti', () => {
		const lessons = buildDayLessons(SCHEDULE, TUESDAY)
		expect(lessons.map((item) => item.materia)).toEqual(['Tedesco', 'Italiano', 'Matematica', 'Sistemi'])
		expect(lessons[1]).toMatchObject({ inizio: '09:00', fine: '10:40', ore: [2, 3] })
		expect(periodLabel(lessons[1])).toBe('2ª–3ª Ora')
		expect(lessons[2].teachers).toEqual(['SARRI Wanda'])
	})

	it('applica cambi aula su più ore, uscite e niente pomeriggio', () => {
		const changes = [
			{ data: '2026-11-17', tipo: 'cambio_aula', ora: 3, ore: [3, 4], nuova_aula: 'LAB. B201' },
			{ data: '2026-11-17', tipo: 'senza_lezioni_pomeridiane', ora: 8, ore: [8, 9, 10, 11] },
			{ data: '2026-11-18', tipo: 'uscita_anticipata', ora: 1, ore: [1] }, // altro giorno: ignorata
		]
		const lessons = buildDayLessons(SCHEDULE, TUESDAY, changes)
		const byStart = Object.fromEntries(lessons.map((item) => [item.inizio, item]))
		expect(byStart['09:00'].ore).toEqual([2]) // l'ora 3 cambia aula: il blocco di Italiano si divide
		expect(byStart['09:50']).toMatchObject({ roomChange: 'LAB. B201', room: 'LAB. B201' })
		expect(byStart['10:40'].roomChange).toBe('LAB. B201')
		expect(byStart['14:30'].cancelled).toBe('Niente lezioni pomeridiane')
		expect(byStart['08:10'].cancelled).toBeNull()
	})

	const cancelledWith = (change) => buildDayLessons(SCHEDULE, TUESDAY, [{ data: '2026-11-17', ...change }])
		.filter((item) => item.cancelled).map((item) => item.materia)

	it('entrata posticipata annulla solo le ore indicate', () => {
		expect(cancelledWith({ tipo: 'entrata_posticipata', ora: 2, ore: [1] })).toEqual(['Tedesco'])
		// entrata alle 15:20: la mattina si fa tutta, salta solo la 8ª
		expect(cancelledWith({ tipo: 'entrata_posticipata', ora: 9, ore: [8] })).toEqual(['Sistemi'])
	})

	it('uscita anticipata al mattino non toglie il pomeriggio', () => {
		// uscita alle 10:40: saltano 4ª–7ª, il pomeriggio resta
		expect(cancelledWith({ tipo: 'uscita_anticipata', ora: 4, ore: [4, 5, 6, 7] })).toEqual(['Matematica'])
		expect(cancelledWith({ tipo: 'uscita_anticipata', ora: 8, ore: [8, 9, 10, 11] })).toEqual(['Sistemi'])
	})

	it('giorno senza lezioni', () => {
		expect(buildDayLessons(SCHEDULE, new Date(2026, 10, 15, 12))).toEqual([])
		expect(buildDayLessons(undefined, TUESDAY)).toEqual([])
	})
})

describe('dayProgress', () => {
	const lessons = buildDayLessons(SCHEDULE, TUESDAY)
	const at = (time) => {
		const [hours, minutes] = time.split(':').map(Number)
		return hours * 60 + minutes
	}

	it('lezione in corso, intervallo, prima delle lezioni e fine giornata', () => {
		expect(dayProgress(lessons, at('10:50'))).toMatchObject({ mode: 'current', remaining: 40 })
		expect(dayProgress(lessons, at('12:00'))).toMatchObject({ mode: 'break', remaining: 150 })
		expect(dayProgress(lessons, at('07:30'))).toMatchObject({ mode: 'before', remaining: 40 })
		expect(dayProgress(lessons, at('16:00')).mode).toBe('finished')
		expect(dayProgress([], at('10:00')).mode).toBe('empty')
	})

	it('stato della singola lezione', () => {
		expect(lessonStatus(lessons[0], at('10:50'), true)).toBe('done')
		expect(lessonStatus(lessons[2], at('10:50'), true)).toBe('current')
		expect(lessonStatus(lessons[3], at('10:50'), true)).toBe('upcoming')
		expect(lessonStatus(lessons[0], at('10:50'), false)).toBe('upcoming')
	})
})

describe('subjectMatches', () => {
	it.each([
		['Scienze sperimentali (FISICA)', 'FISICA', true],
		['Italiano', 'LINGUA E LETTERATURA ITALIANA', true],
		['Matematica', 'MATEMATICA', true],
		['Lingua inglese', 'LINGUA E LETTERATURA ITALIANA', false],
		['Tedesco', 'MATEMATICA', false],
		['Tedesco', null, false],
	])('%s / %s -> %s', (lessonSubject, eventSubject, expected) => {
		expect(subjectMatches(lessonSubject, eventSubject)).toBe(expected)
	})
})
