import { describe, expect, it } from 'vitest'
import { toAgendaItem } from './agenda.js'
import { personKey, subjectAgenda, subjectMaterials, subjectOverview, weeklySlots } from './subject.js'

const lesson = (ora, inizio, fine, materia, docenti = ['ROSSI Mario'], aula = 'AULA B1') => ({ ora, inizio, fine, materia, docenti, aula })

const SCHEDULE = {
	giorni: [
		{ giorno: 'lunedi', etichetta: 'Lunedì', lezioni: [
			lesson(1, '08:10', '09:00', 'Italiano', ['BIANCHI Anna']),
			lesson(2, '09:00', '09:50', 'Scienze sperimentali (FISICA)', ['VERDI Luca', 'PNRR (301)']),
			lesson(3, '09:50', '10:40', 'Scienze sperimentali (FISICA)', ['VERDI Luca', 'PNRR (301)']),
			lesson(5, '11:45', '12:35', 'Scienze sperimentali (FISICA)', ['VERDI Luca']),
		] },
		{ giorno: 'giovedi', etichetta: 'Giovedì', lezioni: [lesson(4, '10:40', '11:30', 'Storia', ['BIANCHI Anna'], 'AULA C2')] },
	],
}

const DIDACTICS = {
	docenti: [
		{ id: 'T1', nome: 'BIANCHI ANNA', cartelle: [
			{ id: 1, nome: 'Italiano', materiali: [{ id: 11, nome: 'Dante', tipo: 'file', condiviso_il: '2026-11-10T10:00:00+01:00' }] },
			{ id: 2, nome: 'Storia', materiali: [{ id: 12, nome: 'Rivoluzione francese', tipo: 'file', condiviso_il: '2026-11-12T10:00:00+01:00' }] },
			{ id: 3, nome: 'Materiale vario', materiali: [{ id: 13, nome: 'Calendario', tipo: 'link', condiviso_il: '2026-11-01T10:00:00+01:00' }] },
		] },
		{ id: 'T2', nome: 'VERDI LUCA', cartelle: [
			{ id: 4, nome: 'Esercizi', materiali: [{ id: 21, nome: 'Moto rettilineo', tipo: 'file', condiviso_il: '2026-11-15T10:00:00+01:00' }] },
		] },
	],
}

const GRADES = {
	materie: [
		{ materia_id: 1, materia: 'FISICA', docenti: ['VERDI LUCA'], voti: [
			{ id: 1, data: '2026-11-03', voto: '7', valore: 7, tipo: 'Scritto', peso: 1, annullato: false },
			{ id: 2, data: '2026-10-20', voto: '5', valore: 5, tipo: 'Orale', peso: 1, annullato: false },
		] },
		{ materia_id: 2, materia: 'ITALIANO', docenti: ['BIANCHI ANNA'], voti: [{ id: 3, data: '2026-10-10', voto: '8', valore: 8, peso: 1, annullato: false }] },
		{ materia_id: 3, materia: 'STORIA', docenti: ['BIANCHI ANNA'], voti: [{ id: 4, data: '2026-10-11', voto: '6', valore: 6, peso: 1, annullato: false }] },
	],
}

const AGENDA = [
	toAgendaItem({ id: 1, tipo: 'annotazione', materia: 'FISICA', testo: 'Verifica sul moto', autore: 'VERDI LUCA' }, '2026-11-26'),
	toAgendaItem({ id: 2, tipo: 'compito', materia: 'FISICA', testo: 'Es. 3 pag. 40', autore: 'VERDI LUCA' }, '2026-11-24'),
	toAgendaItem({ id: 3, tipo: 'annotazione', materia: null, testo: 'Verifica di fisica rimandata', autore: 'ROSSI MARIO' }, '2026-11-25'),
	toAgendaItem({ id: 4, tipo: 'annotazione', materia: null, testo: 'Uscita didattica', autore: 'ROSSI MARIO' }, '2026-11-25'),
	toAgendaItem({ id: 5, tipo: 'compito', materia: 'ITALIANO', testo: 'Leggere il canto V' }, '2026-11-24'),
]

describe('dashboard della materia', () => {
	it('riconosce la stessa persona scritta in modi diversi', () => {
		expect(personKey('ROSSI MARIO')).toBe(personKey('Mario Rossi'))
		expect(personKey('DE LUCA Anna')).toBe(personKey('de luca anna'))
	})

	it("raggruppa l'agenda: verifiche (anche senza materia, dal testo) e il resto, in ordine di data", () => {
		const { tests, others } = subjectAgenda(AGENDA, ['Scienze sperimentali (FISICA)', 'FISICA'])
		expect(tests.map((item) => item.id)).toEqual([3, 1])
		expect(others.map((item) => item.id)).toEqual([2])
	})

	it('unisce le ore consecutive della settimana', () => {
		expect(weeklySlots(SCHEDULE, ['Scienze sperimentali (FISICA)'])).toEqual([
			{ key: 'lunedi-09:00', day: 'Lunedì', hours: [2, 3], inizio: '09:00', fine: '10:40', room: 'AULA B1' },
			{ key: 'lunedi-11:45', day: 'Lunedì', hours: [5], inizio: '11:45', fine: '12:35', room: 'AULA B1' },
		])
	})

	it("un docente con più materie: le cartelle di un'altra materia non si mostrano", () => {
		const teachers = new Set([personKey('BIANCHI ANNA')])
		const italian = subjectMaterials(DIDACTICS, ['ITALIANO'], { teachers, otherSubjects: ['STORIA', 'FISICA'] })
		expect(italian.map((material) => material.nome)).toEqual(['Dante', 'Calendario'])
		const history = subjectMaterials(DIDACTICS, ['STORIA'], { teachers, otherSubjects: ['ITALIANO', 'FISICA'] })
		expect(history.map((material) => material.nome)).toEqual(['Rivoluzione francese', 'Calendario'])
	})

	it('senza docenti noti guarda solo il nome della cartella', () => {
		expect(subjectMaterials(DIDACTICS, ['STORIA']).map((material) => material.nome)).toEqual(['Rivoluzione francese'])
	})

	it("mette insieme voti, agenda, orario e materiali partendo dal nome dell'orario", () => {
		const view = subjectOverview({
			name: 'Scienze sperimentali (FISICA)',
			grades: GRADES,
			agendaItems: AGENDA,
			didactics: DIDACTICS,
			schedule: SCHEDULE,
		})
		expect(view.title).toBe('Fisica')
		expect(view.subject.media).toBe(6)
		expect(view.tests).toHaveLength(2)
		expect(view.slots).toHaveLength(2)
		expect(view.teacherNames).toEqual(['VERDI LUCA'])
		expect(view.materials.map((material) => material.nome)).toEqual(['Moto rettilineo'])
		// ROSSI MARIO ha scritto una verifica di fisica senza materia: non diventa un docente di Fisica
		expect([...view.teachers]).toEqual([personKey('VERDI LUCA')])
	})

	it('funziona anche senza dati (mentre arrivano o per una materia senza voti)', () => {
		const view = subjectOverview({ name: 'Filosofia' })
		expect(view).toMatchObject({ subject: null, title: 'Filosofia', tests: [], others: [], slots: [], teacherNames: [], materials: [] })
	})
})
