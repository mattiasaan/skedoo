import { titleCase } from './format.js'

// Stesse regole del backend (app/grades.py): media pesata, esclusi annullati, giudizi e pesi non positivi.
function counted(grade) {
	return !grade.annullato && grade.valore != null && (grade.peso == null || grade.peso > 0)
}

export function weightedAverage(grades) {
	const valid = grades.filter(counted)
	if (!valid.length) return null
	const total = valid.reduce((sum, grade) => sum + (grade.peso || 1), 0)
	return valid.reduce((sum, grade) => sum + grade.valore * (grade.peso || 1), 0) / total
}

export function generalAverage(subjects) {
	const averages = subjects.map((subject) => subject.media).filter((value) => value != null)
	return averages.length ? averages.reduce((sum, value) => sum + value, 0) / averages.length : null
}

/** Periodi presenti nei voti: [{ pos: 1, label: '1° Quadrimestre' }, ...] */
export function termsOf(grades) {
	const positions = new Set()
	for (const subject of grades?.materie ?? []) {
		for (const grade of subject.voti) if (grade.periodo_pos != null) positions.add(grade.periodo_pos)
	}
	const sorted = [...positions].sort((a, b) => a - b)
	// a inizio anno c'è solo il primo periodo: il secondo si mostra comunque (vuoto), come nel design
	const list = sorted.length > 1 ? sorted : [...new Set([...(sorted.length ? sorted : [1]), 2])]
	const name = list.length >= 3 ? 'Trimestre' : 'Quadrimestre'
	return list.map((pos) => ({ pos, label: `${pos}° ${name}` }))
}

/** Il periodo più recente che ha voti (quello in corso). */
export function currentTerm(grades) {
	let latest = null
	for (const subject of grades?.materie ?? []) {
		for (const grade of subject.voti) {
			if (grade.periodo_pos != null && (!latest || grade.data > latest.data)) latest = grade
		}
	}
	return latest?.periodo_pos ?? termsOf(grades)[0]?.pos ?? null
}

/** Materie con soli i voti del periodo `pos` (null = tutto l'anno) e media ricalcolata. */
export function subjectsForTerm(grades, pos) {
	return (grades?.materie ?? [])
		.map((subject) => {
			const voti = pos == null ? subject.voti : subject.voti.filter((grade) => grade.periodo_pos === pos)
			return { ...subject, voti, media: weightedAverage(voti), name: titleCase(subject.materia) }
		})
		.filter((subject) => subject.voti.length > 0)
}

export function allGrades(subjects) {
	return subjects
		.flatMap((subject) => subject.voti.map((grade) => ({ ...grade, subject: subject.name ?? titleCase(subject.materia) })))
		.sort((a, b) => (b.data ?? '').localeCompare(a.data ?? '') || b.id - a.id)
}

export function gradeCounts(subjects) {
	const grades = subjects.flatMap((subject) => subject.voti).filter((grade) => !grade.annullato)
	const written = grades.filter((grade) => /scritt|grafic/i.test(grade.tipo ?? '')).length
	const oral = grades.filter((grade) => /oral|pratic/i.test(grade.tipo ?? '')).length
	return { total: grades.length, written, oral }
}

/**
 * Andamento della media generale nel tempo: per ogni data con voti,
 * la media generale calcolata con i voti fino a quella data.
 */
export function averageTimeline(subjects, maxPoints = 10) {
	const dates = [...new Set(subjects.flatMap((subject) => subject.voti.filter(counted).map((grade) => grade.data)))].sort()
	const points = dates.map((date) => {
		const averages = subjects
			.map((subject) => weightedAverage(subject.voti.filter((grade) => grade.data <= date)))
			.filter((value) => value != null)
		return { date, value: averages.reduce((sum, value) => sum + value, 0) / averages.length }
	})
	if (points.length <= maxPoints) return points
	// tiene il primo, l'ultimo e punti distribuiti in mezzo
	const step = (points.length - 1) / (maxPoints - 1)
	return Array.from({ length: maxPoints }, (_, index) => points[Math.round(index * step)])
}

/** Media generale alla data indicata (per "+0.2 questo mese"). */
export function averageAt(subjects, date) {
	const averages = subjects
		.map((subject) => weightedAverage(subject.voti.filter((grade) => grade.data <= date)))
		.filter((value) => value != null)
	return averages.length ? averages.reduce((sum, value) => sum + value, 0) / averages.length : null
}

/** Voto minimo (a passi di 0.25) per portare la media della materia a `target` con un voto di peso 1. */
export function requiredGrade(subject, target) {
	const valid = subject.voti.filter(counted)
	const weight = valid.reduce((sum, grade) => sum + (grade.peso || 1), 0)
	const sum = valid.reduce((total, grade) => total + grade.valore * (grade.peso || 1), 0)
	const needed = target * (weight + 1) - sum
	return { value: Math.ceil(needed * 4) / 4, count: valid.length }
}

export function averageLabel(value) {
	if (value == null) return 'Nessun voto'
	if (value >= 8) return 'Ottimo'
	if (value >= 7) return 'Buono'
	if (value >= 6) return 'Sufficiente'
	return 'Insufficiente'
}

export function averageTrendLabel(value) {
	if (value == null) return 'In attesa dei voti'
	if (value >= 8) return 'Ottimo andamento'
	if (value >= 7) return 'Buon andamento'
	if (value >= 6) return 'Andamento sufficiente'
	return 'Da migliorare'
}

export function gradeTone(value) {
	if (value == null) return 'neutral'
	return value >= 6 ? 'good' : 'low'
}

const SUBJECT_ICONS = [
	[/matemat/, 'sigma'],
	[/motori|sport/, 'run'],
	[/fisic/, 'bolt'],
	[/filosof/, 'bulb'],
	[/inglese|tedesco|francese|spagnolo|english|deutsch/, 'globe'],
	[/informat|tecnolog|tic\b/, 'code'],
	[/scienz|chimic|biolog|natural/, 'flask'],
	[/arte|disegno/, 'palette'],
	[/storia|geograf/, 'landmark'],
]

export function subjectIcon(name) {
	const key = String(name ?? '').toLowerCase()
	return SUBJECT_ICONS.find(([pattern]) => pattern.test(key))?.[1] ?? 'book'
}
