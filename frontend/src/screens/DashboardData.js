export const lessons = [
	{ time: '08:00', end: '09:30', subject: 'INGLESE', teacher: 'Prof. Smith', room: 'Aula 104', state: 'COMPLETATA', tone: 'complete' },
	{ time: '09:30', end: '10:30', subject: 'FISICA', teacher: 'Prof. Rossi', room: 'Laboratorio 201', state: 'IN CORSO', tone: 'current' },
	{ time: '11:45', end: '13:00', subject: 'STORIA DELL’ARTE', teacher: 'Prof. Conti', room: 'Aula 302', state: 'IN ARRIVO', tone: 'upcoming' },
]

export const assignments = [
	{ id: 'philosophy', kind: 'VERIFICA', due: 'Giovedì', title: 'Verifica di Filosofia', description: 'Kant e la Critica della Ragion Pura. Studio argomenti da pag. 80 a 124.', teacher: 'Prof. Castelli', tone: 'test' },
	{ id: 'math', kind: 'COMPITI', due: 'Domani', title: 'Esercizi Matematica', description: 'Studio limiti notevoli ed svolgimento esercizi numero 214, 215, 218.', teacher: 'Prof.ssa Bianchi', tone: 'homework', actionable: true },
	{ id: 'english', kind: 'COMPITI', due: 'Venerdì', title: 'English Literature', description: 'Read and annotate the assigned pages from the textbook.', teacher: 'Prof. Smith', tone: 'homework', actionable: true },
	{ id: 'history', kind: 'VERIFICA', due: 'Lunedì', title: 'Interrogazione di Storia', description: 'Ripassare il programma della Rivoluzione francese.', teacher: 'Prof. Conti', tone: 'test' },
]