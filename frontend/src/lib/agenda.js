import { addDays, dateKey, startOfWeek, titleCase } from './format.js'

const TEST_PATTERN = /\b(verific|compito in classe|interrogaz|test\b|prova (scritta|orale|pratica)|simulazione)/i

const KINDS = {
	verifica: { label: 'VERIFICA', tone: 'danger', title: 'Verifica' },
	compito: { label: 'COMPITI', tone: 'blue', title: 'Compiti' },
	evento: { label: 'EVENTO', tone: 'amber', title: 'Evento' },
	annotazione: { label: 'NOTA', tone: 'neutral', title: 'Annotazione' },
}

function kindOf(event) {
	if (TEST_PATTERN.test(event.testo ?? '')) return 'verifica'
	if (event.tipo === 'compito') return 'compito'
	if (event.tipo === 'annotazione') return 'annotazione'
	return 'evento'
}

/** Evento dell'agenda ClasseViva -> elemento pronto per le card (titolo, colore, etichetta). */
export function toAgendaItem(event, date) {
	const kind = kindOf(event)
	const meta = KINDS[kind]
	const subject = event.materia ? titleCase(event.materia) : null
	return {
		...event,
		key: `agenda-${event.id}-${date}`,
		date,
		kind,
		label: meta.label,
		tone: meta.tone,
		subject,
		title: subject ? `${meta.title} di ${subject}` : event.testo?.split(/[.\n]/)[0]?.slice(0, 60) || meta.title,
		description: event.testo ?? '',
	}
}

export function flattenAgenda(agenda) {
	return (agenda?.giorni ?? []).flatMap((day) => day.eventi.map((event) => toAgendaItem(event, day.data)))
}

/** Intervallo da chiedere al backend per il mese di `date`: dal lunedì della prima settimana alla domenica dell'ultima. */
export function monthRange(date) {
	const first = new Date(date.getFullYear(), date.getMonth(), 1, 12)
	const last = new Date(date.getFullYear(), date.getMonth() + 1, 0, 12)
	const start = startOfWeek(first)
	const end = addDays(startOfWeek(last), 6)
	return { da: dateKey(start), a: dateKey(end), start, end }
}

/** Da oggi per `days` giorni (oggi compreso). */
export function upcomingRange(today = new Date(), days = 14) {
	return { da: dateKey(today), a: dateKey(addDays(today, days - 1)) }
}

/** Chiave stabile di una comunicazione della bacheca (per letta/nascosta). */
export function boardKey(item) {
	return `${item.codice}-${item.id}`
}
