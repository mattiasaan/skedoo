import { dateKey, minutesOf, normalizeText, realTeachers } from './format.js'

const DAY_KEYS = ['domenica', 'lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato']

/** Lezioni (singole ore) della classe nel giorno della settimana di `date`. */
export function lessonsOfDay(schedule, date) {
	const key = DAY_KEYS[date.getDay()]
	return schedule?.giorni?.find((day) => day.giorno === key)?.lezioni ?? []
}

const CANCEL_FROM = {
	uscita_anticipata: 'Uscita anticipata',
	senza_lezioni_pomeridiane: 'Niente lezioni pomeridiane',
}

/** Variazioni del giorno (cambi aula, entrate posticipate, uscite anticipate) applicate alle singole ore. */
function applyChanges(lessons, changes) {
	return lessons.map((lesson) => {
		let roomChange = null
		let cancelled = null
		for (const change of changes) {
			if (change.ora == null || lesson.ora == null) continue
			// un cambio aula può durare più ore: `ore` le elenca tutte (le risposte più vecchie hanno solo `ora`)
			const hours = change.ore?.length ? change.ore : [change.ora]
			if (change.tipo === 'cambio_aula' && change.nuova_aula && hours.includes(lesson.ora)) roomChange = change.nuova_aula
			if (change.tipo === 'entrata_posticipata' && lesson.ora < change.ora) cancelled = 'Entrata posticipata'
			if (CANCEL_FROM[change.tipo] && lesson.ora >= change.ora) cancelled = CANCEL_FROM[change.tipo]
		}
		return { ...lesson, roomChange, cancelled }
	})
}

function sameBlock(first, second) {
	return first.materia === second.materia
		&& first.aula === second.aula
		&& first.roomChange === second.roomChange
		&& first.cancelled === second.cancelled
		&& first.docenti.join('|') === second.docenti.join('|')
}

/**
 * Lezioni del giorno pronte da mostrare: variazioni applicate e ore consecutive
 * della stessa materia unite in un blocco (es. 4ª–5ª ora di Informatica).
 */
export function buildDayLessons(schedule, date, changes = []) {
	const key = dateKey(date)
	const todayChanges = changes.filter((change) => !change.data || change.data === key)
	const lessons = applyChanges(lessonsOfDay(schedule, date), todayChanges)
	const blocks = []
	for (const lesson of lessons) {
		const previous = blocks.at(-1)
		if (previous && sameBlock(previous, lesson)) {
			previous.fine = lesson.fine
			previous.ore.push(lesson.ora)
			continue
		}
		blocks.push({ ...lesson, ore: [lesson.ora], id: `${key}-${lesson.inizio}` })
	}
	return blocks.map((block) => ({
		...block,
		teachers: realTeachers(block.docenti),
		room: block.roomChange ?? block.aula ?? null,
		date: key,
	}))
}

export function periodLabel(lesson) {
	const hours = (lesson.ore ?? []).filter((hour) => hour != null)
	if (!hours.length) return ''
	return hours.length === 1 ? `${hours[0]}ª Ora` : `${hours[0]}ª–${hours.at(-1)}ª Ora`
}

/** done | current | upcoming, in base all'ora attuale (solo per il giorno di oggi). */
export function lessonStatus(lesson, now, isToday) {
	if (!isToday) return 'upcoming'
	const start = minutesOf(lesson.inizio)
	const end = minutesOf(lesson.fine)
	if (end != null && now >= end) return 'done'
	if (start != null && now >= start) return 'current'
	return 'upcoming'
}

/**
 * Stato della giornata per la card "Prossima lezione":
 * lezione in corso, prossima lezione (con eventuale intervallo) oppure giornata finita.
 */
export function dayProgress(lessons, now) {
	const active = lessons.filter((lesson) => !lesson.cancelled)
	const current = active.find((lesson) => minutesOf(lesson.inizio) <= now && now < minutesOf(lesson.fine))
	if (current) {
		const start = minutesOf(current.inizio)
		const end = minutesOf(current.fine)
		return { mode: 'current', lesson: current, remaining: end - now, progress: (now - start) / (end - start) }
	}
	const nextIndex = active.findIndex((lesson) => minutesOf(lesson.inizio) > now)
	if (nextIndex >= 0) {
		const next = active[nextIndex]
		const start = minutesOf(next.inizio)
		const previous = active[nextIndex - 1]
		const gapStart = previous ? minutesOf(previous.fine) : Math.min(now, start - 30)
		const span = Math.max(1, start - gapStart)
		return {
			mode: previous ? 'break' : 'before',
			lesson: next,
			remaining: start - now,
			progress: Math.min(1, Math.max(0, (now - gapStart) / span)),
		}
	}
	return { mode: active.length ? 'finished' : 'empty', lesson: null, remaining: 0, progress: 1 }
}

// parole comuni a molte materie: da sole non bastano a dire che due nomi indicano la stessa materia
const GENERIC_WORDS = new Set(['lingua', 'letteratura', 'scienze', 'sperimentali', 'tecnologie', 'tecnol', 'discipline', 'educazione', 'laboratorio', 'storia'])

/** Gli eventi dell'agenda che riguardano la materia della lezione (es. verifica di Fisica). */
export function subjectMatches(lessonSubject, eventSubject) {
	const lesson = normalizeText(lessonSubject)
	const event = normalizeText(eventSubject)
	if (!lesson || !event) return false
	if (lesson === event || lesson.includes(event) || event.includes(lesson)) return true
	// "Scienze sperimentali (FISICA)" <-> "FISICA", "Lingua e letteratura italiana" <-> "ITALIANO"
	const meaningful = (text) => text.split(' ').filter((word) => word.length > 4 && !GENERIC_WORDS.has(word))
	const lessonWords = meaningful(lesson)
	const eventWords = meaningful(event)
	return lessonWords.some((word) => eventWords.some((other) => word.slice(0, 5) === other.slice(0, 5)))
}
