// Dashboard di una materia: cosa le appartiene tra agenda, orario e materiali della didattica.
// I nomi non coincidono tra le fonti ("Scienze sperimentali (FISICA)" nell'orario, "FISICA" su ClasseViva):
// ogni funzione riceve tutti i nomi noti della materia e accetta un elemento se corrisponde a uno di questi.
import { flattenMaterials } from './didactics.js'
import { normalizeText, realTeachers, titleCase } from './format.js'
import { subjectsForTerm } from './grades.js'
import { subjectMatches } from './schedule.js'

export function matchesAny(names, value) {
	return names.some((name) => subjectMatches(name, value))
}

/** "ROSSI MARIO", "Rossi Mario" e "Mario Rossi" sono la stessa persona. */
export function personKey(value) {
	return normalizeText(value).split(' ').filter(Boolean).sort().join(' ')
}

/** Docenti della materia come li scrive l'orario ("FESSLER Stefano"), senza progetti come "PNRR (301)". */
export function scheduleTeachers(schedule, names) {
	const list = (schedule?.giorni ?? []).flatMap((day) => day.lezioni
		.filter((lesson) => matchesAny(names, lesson.materia))
		.flatMap((lesson) => realTeachers(lesson.docenti)))
	return [...new Set(list)]
}

/**
 * Docenti della materia (chiavi di personKey): da ClasseViva (voti), dall'orario e da chi ha scritto in agenda
 * i suoi eventi. Solo eventi con la materia indicata: una nota senza materia può scriverla qualunque docente.
 */
export function subjectTeachers(names, { subject, schedule, items = [] } = {}) {
	const authors = items.filter((item) => item.subject).map((item) => item.autore)
	const values = [...(subject?.docenti ?? []), ...scheduleTeachers(schedule, names), ...authors]
	return new Set(values.map(personKey).filter(Boolean))
}

/**
 * Materiali della materia, dal più recente: quelli dei suoi docenti.
 * Un docente può insegnare più materie (es. Italiano e Storia): una sua cartella col nome di un'altra materia
 * (`otherSubjects`) e non di questa non si mostra. Senza docenti noti si guarda solo il nome della cartella.
 */
export function subjectMaterials(didactics, names, { teachers = new Set(), otherSubjects = [] } = {}) {
	return flattenMaterials(didactics).filter((material) => {
		const ownFolder = Boolean(material.folder) && matchesAny(names, material.folder)
		if (!teachers.size) return ownFolder
		if (!teachers.has(personKey(material.teacher))) return false
		return ownFolder || !material.folder || !matchesAny(otherSubjects, material.folder)
	})
}

/** Quando c'è la materia nella settimana: ore consecutive unite ("Lunedì, 2ª–3ª ora, 09:00–10:50"). */
export function weeklySlots(schedule, names) {
	return (schedule?.giorni ?? []).flatMap((day) => {
		const blocks = []
		for (const lesson of day.lezioni) {
			if (!matchesAny(names, lesson.materia)) continue
			const previous = blocks.at(-1)
			if (previous && lesson.ora != null && previous.hours.at(-1) === lesson.ora - 1) {
				previous.hours.push(lesson.ora)
				previous.fine = lesson.fine
				continue
			}
			blocks.push({
				key: `${day.giorno}-${lesson.inizio}`,
				day: day.etichetta,
				hours: lesson.ora != null ? [lesson.ora] : [],
				inizio: lesson.inizio,
				fine: lesson.fine,
				room: lesson.aula ?? null,
			})
		}
		return blocks
	})
}

/**
 * Eventi dell'agenda della materia in ordine di data, con le verifiche a parte.
 * Le verifiche senza materia (annotazioni del tipo "verifica di fisica giovedì") si riconoscono dal testo.
 */
export function subjectAgenda(items, names) {
	const related = items
		.filter((item) => (item.subject
			? matchesAny(names, item.subject)
			: item.kind === 'verifica' && matchesAny(names, item.description)))
		.sort((a, b) => a.date.localeCompare(b.date) || String(a.ora_inizio ?? '').localeCompare(String(b.ora_inizio ?? '')))
	return {
		tests: related.filter((item) => item.kind === 'verifica'),
		others: related.filter((item) => item.kind !== 'verifica'),
	}
}

/**
 * Tutto quello che mostra la dashboard della materia `name` (il nome con cui la si apre, es. dall'orario).
 * `grades`, `didactics`, `schedule`: risposte dell'API (anche undefined mentre arrivano); `agendaItems`: da flattenAgenda.
 */
export function subjectOverview({ name, grades, agendaItems = [], didactics, schedule, practicalSplit = false }) {
	const subjects = subjectsForTerm(grades, null, { practicalSplit })
	const subject = subjects.find((item) => subjectMatches(name, item.materia)) ?? null
	// tutti i nomi noti della materia: quello con cui la si apre e quello di ClasseViva
	const names = [name, subject?.materia].filter(Boolean)
	const { tests, others } = subjectAgenda(agendaItems, names)
	const teachers = subjectTeachers(names, { subject, schedule, items: [...tests, ...others] })
	return {
		subject,
		title: subject?.name ?? titleCase(name),
		tests,
		others,
		slots: weeklySlots(schedule, names),
		teachers,
		teacherNames: subject?.docenti?.length ? realTeachers(subject.docenti) : scheduleTeachers(schedule, names),
		materials: subjectMaterials(didactics, names, {
			teachers,
			otherSubjects: subjects.filter((item) => item !== subject).map((item) => item.materia),
		}),
	}
}
