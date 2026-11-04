export const subjects = [
	{
		name: 'Matematica', teacher: 'Prof.ssa Bianchi', teachers: ['Prof.ssa Bianchi'], average: '8,2', previous: '8,5', type: 'Scritto', tone: 'good', icon: 'chart',
		rooms: ['Aula 302'], weeklyHours: 5,
		grades: [
			{ id: 'math-grade-1', date: '2025-09-18', value: 7.5, type: 'Scritto', description: 'Equazioni e disequazioni' },
			{ id: 'math-grade-2', date: '2025-10-02', value: 8.5, type: 'Orale', description: 'Funzioni e dominio' },
			{ id: 'math-grade-3', date: '2025-10-14', value: 8.5, type: 'Scritto', description: 'Limiti notevoli' },
		],
		assignments: [
			{ id: 'math-homework', type: 'task', date: '2025-10-15', due: '15 ottobre', title: 'Esercizi sui limiti', description: 'Svolgere gli esercizi 214, 215 e 218.', teacher: 'Prof.ssa Bianchi', subject: 'Matematica', tone: 'blue' },
		],
		events: [
			{ id: 'math-test', type: 'event', date: '2025-10-22', due: '22 ottobre', title: 'Verifica di Matematica', description: 'Verifica scritta su limiti e continuità.', teacher: 'Prof.ssa Bianchi', subject: 'Matematica', tone: 'danger' },
			{ id: 'math-oral', type: 'event', date: '2025-10-28', due: '28 ottobre', title: 'Interrogazione di Matematica', description: 'Ripasso delle funzioni e dei limiti.', teacher: 'Prof.ssa Bianchi', subject: 'Matematica', tone: 'amber' },
		],
	},
	{
		name: 'Fisica', teacher: 'Prof. Rossi', teachers: ['Prof. Rossi'], average: '5,8', previous: '5,5', type: 'Orale', tone: 'low', icon: 'alert',
		rooms: ['Laboratorio 201', 'Aula 302'], weeklyHours: 3,
		grades: [
			{ id: 'physics-grade-1', date: '2025-09-22', value: 5.5, type: 'Orale', description: 'Grandezze e misure' },
			{ id: 'physics-grade-2', date: '2025-10-09', value: 6, type: 'Scritto', description: 'Moto rettilineo' },
		],
		assignments: [
			{ id: 'physics-homework', type: 'task', date: '2025-10-17', due: '17 ottobre', title: 'Problemi sul moto', description: 'Completare gli esercizi assegnati sul moto rettilineo.', teacher: 'Prof. Rossi', subject: 'Fisica', tone: 'blue' },
		],
		events: [
			{ id: 'physics-test', type: 'event', date: '2025-10-24', due: '24 ottobre', title: 'Verifica di Fisica', description: 'Verifica su moto rettilineo e accelerazione.', teacher: 'Prof. Rossi', subject: 'Fisica', tone: 'danger' },
		],
	},
	{
		name: 'Italiano', teacher: 'Prof. De Luca', teachers: ['Prof. De Luca'], average: '7,5', previous: '7,0', type: 'Orale', tone: 'good', icon: 'bookmark',
		rooms: ['Aula 302'], weeklyHours: 4,
		grades: [{ id: 'italian-grade-1', date: '2025-10-07', value: 7.5, type: 'Orale', description: 'Letteratura italiana' }],
		assignments: [], events: [],
	},
	{
		name: 'Filosofia', teacher: 'Prof. Castelli', teachers: ['Prof. Castelli'], average: '8,0', previous: '8,0', type: 'Orale', tone: 'good', icon: 'person',
		rooms: ['Aula 302'], weeklyHours: 2,
		grades: [{ id: 'philosophy-grade-1', date: '2025-10-06', value: 8, type: 'Orale', description: 'Kant e illuminismo' }],
		assignments: [], events: [
			{ id: 'philosophy-test', type: 'event', date: '2025-10-16', due: '16 ottobre', title: 'Verifica di Filosofia', description: 'Kant e la Critica della Ragion Pura.', teacher: 'Prof. Castelli', subject: 'Filosofia', tone: 'danger' },
		],
	},
]

function getSubjectOverview(subject) {
	return {
		id: `subject-${subject.name.toLowerCase()}`,
		type: 'subject',
		date: '2025-10-14',
		returnView: 'Voti',
		returnTab: 'grades',
		title: subject.name,
		subject: subject.name,
		teacher: subject.teacher,
		teachers: subject.teachers ?? [subject.teacher],
		rooms: subject.rooms ?? [],
		weeklyHours: subject.weeklyHours,
		description: `Riepilogo di ${subject.name}, con andamento dei voti, compiti e prossimi eventi.`,
		average: subject.average,
		previous: subject.previous,
		gradeType: subject.type,
		grades: subject.grades ?? [],
		assignments: subject.assignments ?? [],
		events: subject.events ?? [],
		tone: subject.tone === 'low' ? 'danger' : 'green',
	}
}

export function getSubjectAgendaItem(subject) {
	return getSubjectOverview(subject)
}

function normalizeSubjectName(name) {
	return name?.normalize('NFD').replace(/\p{Diacritic}/gu, '').trim().toLocaleLowerCase('it-IT') ?? ''
}

export function getSubjectAgendaItemByName(name, sourceItem = {}) {
	const subject = subjects.find((item) => normalizeSubjectName(item.name) === normalizeSubjectName(name))
	if (subject) {
		const overview = getSubjectOverview(subject)
		return sourceItem.returnView
			? { ...overview, returnView: sourceItem.returnView, returnTab: 'agenda' }
			: { ...overview, returnView: 'Home', returnTab: 'home' }
	}

	const title = name || sourceItem.subject || 'Materia'
	return {
		id: `subject-${normalizeSubjectName(title).replaceAll(' ', '-')}`,
		type: 'subject',
		date: sourceItem.date ?? '2025-10-14',
		returnView: sourceItem.returnView ?? 'Home',
		returnTab: sourceItem.returnView ? 'agenda' : 'home',
		title,
		subject: title,
		teacher: sourceItem.teacher,
		teachers: sourceItem.teacher ? [sourceItem.teacher] : [],
		rooms: sourceItem.room ? [sourceItem.room] : [],
		description: `Riepilogo di ${title}, con andamento dei voti, compiti e prossimi eventi.`,
		average: '—',
		grades: [],
		assignments: [],
		events: [],
	}
}
