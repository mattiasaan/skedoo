import { describe, expect, it } from 'vitest'
import {
	averageLabel,
	averageTimeline,
	currentTerm,
	generalAverage,
	gradeCounts,
	requiredGrade,
	subjectsForTerm,
	termsOf,
	weightedAverage,
} from './grades.js'

const grade = (id, data, valore, extra = {}) => ({ id, data, valore, voto: String(valore), tipo: 'Scritto', peso: 1, annullato: false, periodo_pos: 1, ...extra })

const GRADES = {
	materie: [
		{ materia: 'MATEMATICA', voti: [grade(3, '2026-11-12', 8.5), grade(2, '2026-10-08', 6, { tipo: 'Orale', peso: 2 }), grade(1, '2026-09-22', 7)] },
		{ materia: 'ITALIANO', voti: [grade(5, '2026-10-03', null, { voto: 'Ottimo' }), grade(4, '2026-10-01', 4, { annullato: true })] },
		{ materia: 'STORIA', voti: [grade(6, '2027-02-10', 9, { periodo_pos: 2 })] },
	],
}

describe('medie', () => {
	it('media pesata con le stesse regole del backend', () => {
		expect(weightedAverage(GRADES.materie[0].voti)).toBeCloseTo((8.5 + 6 * 2 + 7) / 4)
		expect(weightedAverage(GRADES.materie[1].voti)).toBeNull() // giudizio e voto annullato non contano
		expect(weightedAverage([grade(1, '2026-10-01', 3, { peso: 0 })])).toBeNull()
	})

	it('periodi e filtro per periodo', () => {
		expect(termsOf(GRADES).map((term) => term.label)).toEqual(['1° Quadrimestre', '2° Quadrimestre'])
		expect(termsOf({ materie: [GRADES.materie[0]] }).map((term) => term.pos)).toEqual([1, 2]) // il 2° si mostra anche vuoto
		expect(currentTerm(GRADES)).toBe(2)
		const first = subjectsForTerm(GRADES, 1)
		expect(first.map((subject) => subject.name)).toEqual(['Matematica', 'Italiano'])
		expect(subjectsForTerm(GRADES, null)).toHaveLength(3)
	})

	it('media generale, conteggi e andamento', () => {
		const subjects = subjectsForTerm(GRADES, 1)
		expect(generalAverage(subjects)).toBeCloseTo(weightedAverage(GRADES.materie[0].voti))
		expect(gradeCounts(subjects)).toEqual({ total: 4, written: 3, oral: 1 })
		const timeline = averageTimeline(subjects)
		expect(timeline.map((point) => point.date)).toEqual(['2026-09-22', '2026-10-08', '2026-11-12'])
		expect(timeline.at(-1).value).toBeCloseTo(generalAverage(subjects))
	})

	it('voto necessario per raggiungere un obiettivo', () => {
		const subject = { voti: [grade(1, '2026-10-01', 5.5), grade(2, '2026-10-02', 6)] }
		expect(requiredGrade(subject, 6)).toEqual({ value: 6.5, count: 2 }) // (6*3 - 11.5) = 6.5
		expect(requiredGrade(subject, 9).value).toBeGreaterThan(10)
		expect(requiredGrade({ voti: [] }, 7)).toEqual({ value: 7, count: 0 })
		// obiettivo a quarti: 6.25*3 - 11.5 = 7.25
		expect(requiredGrade(subject, 6.25).value).toBe(7.25)
		// pesi non binari (0.1, 0.2): il risultato esatto 6.75 (calcolato 6.750000000000001) non deve salire a 7 per errori di virgola mobile
		const fractional = { voti: [grade(1, '2026-10-01', 5, { peso: 0.1 }), grade(2, '2026-10-02', 6, { peso: 0.2 })] }
		expect(requiredGrade(fractional, 6.5).value).toBe(6.75)
	})

	it('etichette', () => {
		expect(averageLabel(8.2)).toBe('Ottimo')
		expect(averageLabel(5.8)).toBe('Insufficiente')
		expect(averageLabel(null)).toBe('Nessun voto')
	})
})
