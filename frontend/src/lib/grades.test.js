import { describe, expect, it } from 'vitest'
import {
	averageLabel,
	averageTimeline,
	currentTerm,
	generalAverage,
	gradeCounts,
	requiredGrade,
	subjectAverage,
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
		// "non fa media" (noAverage): resta in lista ma non entra nel calcolo, né nel simulatore
		expect(weightedAverage([grade(1, '2026-10-01', 8), grade(2, '2026-10-02', 2, { fa_media: false })])).toBe(8)
		expect(requiredGrade({ voti: [grade(1, '2026-10-01', 6), grade(2, '2026-10-02', 2, { fa_media: false })] }, 6)).toEqual({ value: 6, count: 1 })
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
		// pesi non binari (0.1): il risultato esatto 9 (calcolato 9.000000000000004) non deve salire a 9.25 per errori di virgola mobile
		const fractional = { voti: [1, 2, 3].map((id) => grade(id, '2026-10-01', 5, { peso: 0.1 })) }
		expect(requiredGrade(fractional, 6).value).toBe(9)
		// caso reale (tedesco: 8, 6, 5.5 con peso 100): per il 6.75 serve 7.5, non "neanche un 10"
		const percent = { voti: [grade(1, '2026-10-01', 8, { peso: 100 }), grade(2, '2026-10-02', 6, { peso: 100 }), grade(3, '2026-10-03', 5.5, { peso: 100 })] }
		expect(requiredGrade(percent, 6.75).value).toBe(7.5)
		expect(requiredGrade(percent, 7).value).toBe(8.5)
	})

	it('Galilei: pratici a 1/3, scritti e orali a 2/3', () => {
		const voti = [grade(1, '2026-10-01', 8), grade(2, '2026-10-02', 6, { tipo: 'Orale' }), grade(3, '2026-10-03', 4, { tipo: 'Pratico' })]
		expect(subjectAverage(voti, true)).toBeCloseTo(7 * (2 / 3) + 4 * (1 / 3)) // 6
		expect(subjectAverage(voti, false)).toBeCloseTo(6) // le altre scuole: media pesata normale (qui coincide per caso)
		expect(subjectAverage([grade(1, '2026-10-01', 5, { tipo: 'Pratico' })], true)).toBe(5) // un solo gruppo: la sua media
		expect(subjectAverage([grade(1, '2026-10-01', 9), grade(2, '2026-10-02', 3, { tipo: 'Pratico' })], true)).toBeCloseTo(7)
		expect(subjectAverage([grade(1, '2026-10-01', 9), grade(2, '2026-10-02', 3, { tipo: 'Pratico' })], false)).toBeCloseTo(6)

		const data = { materie: [{ materia: 'INFORMATICA', voti }] }
		const [subject] = subjectsForTerm(data, null, { practicalSplit: true })
		expect(subject.media).toBeCloseTo(6)
		expect(subjectsForTerm(data, null)[0].media).toBeCloseTo(6)
		expect(averageTimeline([subject]).at(-1).value).toBeCloseTo(6)
		// per il 6.5: scritto/orale -> (2/3)·(14+x)/3 + 4/3 = 6.5 -> x = 9.25; pratico -> (2/3)·7 + (1/3)·(4+x)/2 = 6.5 -> x = 7
		expect(requiredGrade(subject, 6.5).value).toBe(9.25)
		expect(requiredGrade(subject, 6.5, { practical: true }).value).toBe(7)
		// per il 7: con uno scritto servirebbe 11.5 (non basta), con un pratico esattamente 10
		expect(requiredGrade(subject, 7).value).toBeGreaterThan(10)
		expect(requiredGrade(subject, 7, { practical: true }).value).toBe(10)
	})

	it('etichette', () => {
		expect(averageLabel(8.2)).toBe('Ottimo')
		expect(averageLabel(5.8)).toBe('Insufficiente')
		expect(averageLabel(null)).toBe('Nessun voto')
	})
})
