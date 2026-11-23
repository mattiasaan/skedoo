import { normalizeText } from './format.js'
import { subjectMatches } from './schedule.js'

// Registro di classe (GET /lezioni): le lezioni compaiono solo dopo la firma del docente,
// l'argomento può mancare oppure essere lunghissimo. Qui solo logica pura, testata in lessons.test.js.

/** Ore coperte da una firma: alla 2ª ora con durata 2 -> [2, 3]. */
export function hoursOf(entry) {
	if (!Number.isInteger(entry?.ora)) return []
	const duration = Number.isInteger(entry.durata) && entry.durata > 0 ? entry.durata : 1
	return Array.from({ length: duration }, (_, index) => entry.ora + index)
}

/** Argomenti distinti: lo stesso testo firmato per due ore (o dal docente in compresenza) compare una volta. */
export function uniqueTopics(entries) {
	const seen = new Set()
	const topics = []
	for (const entry of entries) {
		if (!entry?.argomento) continue
		const key = normalizeText(entry.argomento)
		if (seen.has(key)) continue
		seen.add(key)
		topics.push({ text: entry.argomento, teacher: entry.docente ?? null, type: entry.tipo ?? null })
	}
	return topics
}

/**
 * Argomenti di un blocco dell'orario del Galilei (ore consecutive della stessa materia).
 * Si abbinano per ora e materia; se la materia non combacia (nomi diversi tra PDF e registro, supplenze)
 * vale la sola lezione firmata in quelle ore, purché sia una e non una compresenza.
 */
export function topicsForBlock(register, block) {
	const hours = new Set(block?.ore ?? [])
	const sameHours = (register?.lezioni ?? []).filter((entry) => hoursOf(entry).some((hour) => hours.has(hour)))
	const sameSubject = sameHours.filter((entry) =>
		subjectMatches(block.materia, entry.materia) || subjectMatches(block.materia_completa, entry.materia))
	if (sameSubject.length) return uniqueTopics(sameSubject)
	const main = sameHours.filter((entry) => !entry.compresenza)
	return main.length === 1 ? uniqueTopics(main) : []
}

/**
 * Lezioni del giorno dal registro, per le scuole senza orario: ore consecutive della stessa materia e
 * docente diventano un blocco; le compresenze non fanno righe a sé ma il loro argomento va nel blocco.
 * Le righe hanno la stessa forma di quelle dell'orario (materia, ore, teachers, date), senza orari.
 */
export function registerBlocks(register) {
	const entries = register?.lezioni ?? []
	const blocks = []
	for (const entry of entries) {
		if (entry.compresenza) continue
		const hours = hoursOf(entry)
		const previous = blocks.at(-1)
		const continues = previous && hours.length && previous.ore.length
			&& previous.materia === entry.materia && previous.docente === entry.docente && previous.ore.at(-1) + 1 === hours[0]
		if (continues) {
			previous.ore.push(...hours)
			previous.entries.push(entry)
		} else {
			blocks.push({ materia: entry.materia, docente: entry.docente, ore: hours, entries: [entry] })
		}
	}
	return blocks.map((block, index) => {
		const covered = new Set(block.ore)
		const support = entries.filter((entry) => entry.compresenza && hoursOf(entry).some((hour) => covered.has(hour)))
		return {
			id: `${register.data}-${block.ore[0] ?? `n${index}`}-${index}`,
			materia: block.materia || 'Lezione',
			ore: block.ore,
			teachers: block.docente ? [block.docente] : [],
			date: register.data,
			inizio: null,
			fine: null,
			topics: uniqueTopics([...block.entries, ...support]),
		}
	})
}

/** Anteprima di una riga: gli argomenti uniti in un solo testo (la riga lo accorcia a due righe). */
export function topicPreview(topics) {
	return (topics ?? []).map((topic) => topic.text.replace(/\s+/g, ' ')).join(' • ') || null
}

/** Un testo da accorciare nel dettaglio, con "Mostra tutto". */
export function isLongTopic(text) {
	return text.length > 320 || text.split('\n').length > 6
}
