import { assignments } from './DashboardData.js'

export const agendaLessons = [
	{ id: 'lesson-philosophy', date: '2025-10-14', time: '08:00 - 09:00', period: '1ª Ora', subject: 'FILOSOFIA', teacher: 'Prof. Castelli', room: 'Aula 302', note: 'VERIFICA SCRITTA: KANT E ILLUMINISMO', tone: 'danger', status: 'complete', relatedId: 'philosophy' },
	{ id: 'lesson-math', date: '2025-10-14', time: '09:00 - 10:00', period: '2ª Ora', subject: 'MATEMATICA', teacher: 'Prof.ssa Bianchi', room: 'Aula 302', note: 'COMPITI: ESERCIZI PAG. 112', tone: 'blue', status: 'complete', relatedId: 'math' },
	{ id: 'lesson-physics', date: '2025-10-14', time: '10:15 - 11:15', period: '3ª Ora', subject: 'FISICA', teacher: 'Prof. Rossi', room: 'Laboratorio 201', note: 'CAMBIO AULA / LAB 201', tone: 'amber', status: 'current', relatedId: 'room-change' },
	{ id: 'lesson-italian', date: '2025-10-14', time: '11:15 - 12:15', period: '4ª Ora', subject: 'ITALIANO', teacher: 'Prof. De Luca', room: 'Aula 302', note: 'Lezione in aula 302', tone: 'green', status: 'upcoming' },
	{ id: 'lesson-pe', date: '2025-10-14', time: '12:15 - 13:15', period: '5ª Ora', subject: 'SCIENZE MOTORIE', teacher: 'Prof. Barbieri', room: 'Palestra', note: 'Lezione in palestra', tone: 'neutral', status: 'upcoming' },
]

const assignmentDates = {
	philosophy: '2025-10-16',
	math: '2025-10-15',
	english: '2025-10-17',
	history: '2025-10-20',
}

export const agendaTasks = assignments.map((assignment) => ({
	...assignment,
	id: `task-${assignment.id}`,
	sourceId: assignment.id,
	type: assignment.kind === 'VERIFICA' ? 'event' : 'task',
	date: assignmentDates[assignment.id],
	title: assignment.title,
	description: assignment.description,
	subject: assignment.title.replace(/^(Verifica di |Esercizi |Interrogazione di )/, ''),
}))

export const agendaEvents = [
	{
		id: 'room-change',
		type: 'event',
		date: '2025-10-14',
		time: '10:15 - 11:15',
		title: 'Cambio aula per Fisica',
		subject: 'FISICA',
		teacher: 'Prof. Rossi',
		room: 'Laboratorio 201',
		description: 'La lezione si svolge nel Laboratorio 201 al posto dell’aula prevista.',
		tone: 'amber',
	},
]

export function getAgendaDateKey(date) {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	return `${year}-${month}-${day}`
}

export function getAgendaItemDate(item) {
	return new Date(`${item.date}T12:00:00`)
}

export function getAgendaItemsForDate(date) {
	const dateKey = getAgendaDateKey(date)
	return [
		...agendaLessons.filter((item) => item.date === dateKey).map(getLessonAgendaItem),
		...agendaTasks.filter((item) => item.date === dateKey),
		...agendaEvents.filter((item) => item.date === dateKey),
	].sort((first, second) => {
		const firstTime = first.time?.slice(0, 5) ?? '23:59'
		const secondTime = second.time?.slice(0, 5) ?? '23:59'
		return firstTime.localeCompare(secondTime)
	})
}

export function getLessonAgendaItem(lesson) {
	return {
		...lesson,
		id: lesson.id ?? `lesson-${lesson.subject.toLowerCase().replaceAll(' ', '-')}`,
		type: 'lesson',
		title: lesson.subject,
		time: lesson.end ? `${lesson.time} - ${lesson.end}` : lesson.time,
		date: lesson.date ?? '2025-10-14',
		description: lesson.description ?? `Lezione di ${lesson.subject} con ${lesson.teacher}.`,
	}
}

export function getAssignmentAgendaItem(assignment) {
	return {
		...assignment,
		id: `task-${assignment.id}`,
		sourceId: assignment.id,
		type: assignment.kind === 'VERIFICA' ? 'event' : 'task',
		date: assignmentDates[assignment.id] ?? '2025-10-14',
		subject: assignment.title.replace(/^(Verifica di |Esercizi |Interrogazione di )/, ''),
	}
}

export function getRelatedAgendaItem(lesson) {
	if (lesson.relatedId === 'room-change') {
		return agendaEvents[0]
	}

	if (!lesson.relatedId) {
		return null
	}

	return agendaTasks.find((item) => item.sourceId === lesson.relatedId) ?? null
}

export function getLessonsForDate(date) {
	const dateKey = getAgendaDateKey(date)
	const statusPriority = { current: 0, upcoming: 1, complete: 2 }

	return agendaLessons
		.filter((lesson) => lesson.date === dateKey)
		.sort((first, second) => (statusPriority[first.status] ?? 1) - (statusPriority[second.status] ?? 1))
		.map(getLessonAgendaItem)
}
