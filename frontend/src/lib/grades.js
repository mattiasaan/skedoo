import { titleCase } from './format.js'

// Stesse regole del backend (app/grades.py): media pesata, esclusi annullati, "non fa media", giudizi e pesi non positivi.
export function counted(grade) {
	return !grade.annullato && grade.fa_media !== false && grade.valore != null && (grade.peso == null || grade.peso > 0)
}

export function weightedAverage(grades) {
	const valid = grades.filter(counted)
	if (!valid.length) return null
	const total = valid.reduce((sum, grade) => sum + (grade.peso || 1), 0)
	return valid.reduce((sum, grade) => sum + grade.valore * (grade.peso || 1), 0) / total
}

export function isPractical(grade) {
	return /pratic/i.test(grade.tipo ?? '')
}

/**
 * Media di una materia. Con `practicalSplit` (scuole Galilei) i pratici valgono meno:
 * media di scritti e orali × 2/3 + media dei pratici × 1/3; se c'è un solo gruppo vale la sua media.
 * Dentro ogni gruppo restano i pesi di ClasseViva (a pesi uguali è la media semplice).
 */
export function subjectAverage(grades, practicalSplit = false) {
	if (!practicalSplit) return weightedAverage(grades)
	const theory = weightedAverage(grades.filter((grade) => !isPractical(grade)))
	const practical = weightedAverage(grades.filter(isPractical))
	if (theory == null || practical == null) return theory ?? practical
	return theory * (2 / 3) + practical * (1 / 3)
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

/**
 * Materie con soli i voti del periodo `pos` (null = tutto l'anno) e media ricalcolata.
 * `practicalSplit`: pratici a 1/3 (vedi subjectAverage); resta sulla materia per andamento e simulatore.
 */
export function subjectsForTerm(grades, pos, { practicalSplit = false } = {}) {
	return (grades?.materie ?? [])
		.map((subject) => {
			const voti = pos == null ? subject.voti : subject.voti.filter((grade) => grade.periodo_pos === pos)
			return { ...subject, voti, practicalSplit, media: subjectAverage(voti, practicalSplit), name: titleCase(subject.materia) }
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
			.map((subject) => subjectAverage(subject.voti.filter((grade) => grade.data <= date), subject.practicalSplit))
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
		.map((subject) => subjectAverage(subject.voti.filter((grade) => grade.data <= date), subject.practicalSplit))
		.filter((value) => value != null)
	return averages.length ? averages.reduce((sum, value) => sum + value, 0) / averages.length : null
}

/** Peso più frequente tra i voti (a parità, il più alto): è il peso "ordinario" del prossimo voto. */
export function usualWeight(grades) {
	const counts = new Map()
	for (const grade of grades) counts.set(grade.peso || 1, (counts.get(grade.peso || 1) ?? 0) + 1)
	let best = 1
	let bestCount = 0
	for (const [weight, count] of counts) {
		if (count > bestCount || (count === bestCount && weight > best)) [best, bestCount] = [weight, count]
	}
	return best
}

/**
 * Voto minimo (a passi di 0.25, da 1 a 10) per portare la media della materia a `target` con un
 * nuovo voto di peso ordinario; con `practical` il nuovo voto è un pratico (conta solo se la
 * materia usa practicalSplit). `value` > 10: non basta neanche un 10.
 * Il peso ordinario è il più frequente tra i voti dello stesso gruppo: ClasseViva non usa sempre
 * peso 1 (alcune scuole mandano 100 = 100%) e un nuovo voto da 1 contro voti da 100 non conterebbe nulla.
 * Si provano i voti uno per uno invece di invertire la formula: funziona con qualunque media.
 */
export function requiredGrade(subject, target, { practical = false } = {}) {
	const valid = subject.voti.filter(counted)
	const split = Boolean(subject.practicalSplit)
	const group = split ? valid.filter((grade) => isPractical(grade) === practical) : valid
	const peso = usualWeight(group.length ? group : valid)
	const tipo = split && practical ? 'Pratico' : 'Scritto'
	const reaches = (valore) => subjectAverage([...valid, { valore, peso, tipo }], split) >= target - 1e-9
	let value = 10.25
	for (let step = 4; step <= 40; step++) {
		if (reaches(step / 4)) {
			value = step / 4
			break
		}
	}
	return { value, count: valid.length }
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
