// Date, nomi e numeri nel formato mostrato dall'app.

const WEEKDAYS = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato']
const MONTHS = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

export function dateKey(date = new Date()) {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	return `${year}-${month}-${day}`
}

export function parseDateKey(key) {
	if (!key) return null
	const [year, month, day] = key.slice(0, 10).split('-').map(Number)
	if (!year || !month || !day) return null
	return new Date(year, month - 1, day, 12)
}

export function addDays(date, days) {
	const result = new Date(date)
	result.setDate(result.getDate() + days)
	return result
}

export function startOfWeek(date) {
	const result = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12)
	result.setDate(result.getDate() - ((result.getDay() + 6) % 7))
	return result
}

export function isSameDay(first, second) {
	return Boolean(first && second) && dateKey(first) === dateKey(second)
}

export function weekdayName(date) {
	return WEEKDAYS[date.getDay()]
}

export function weekdayShort(date) {
	return WEEKDAYS[date.getDay()].slice(0, 3).toUpperCase()
}

export function monthName(date) {
	return MONTHS[date.getMonth()]
}

/** "Martedì 14 Ottobre" */
export function formatLongDate(date) {
	return `${weekdayName(date)} ${date.getDate()} ${monthName(date)}`
}

/** "MARTEDÌ, 14 OTTOBRE" */
export function formatKickerDate(date) {
	return `${weekdayName(date)}, ${date.getDate()} ${monthName(date)}`.toUpperCase()
}

/** "14 ott" */
export function formatShortDate(date) {
	return `${date.getDate()} ${monthName(date).slice(0, 3).toLowerCase()}`
}

/** "Oggi", "Domani", "Ieri", "Giovedì" (entro la settimana) o "14 ott". */
export function relativeDay(key, today = new Date()) {
	const date = parseDateKey(key)
	if (!date) return ''
	const base = parseDateKey(dateKey(today))
	const diff = Math.round((date - base) / 86400000)
	if (diff === 0) return 'Oggi'
	if (diff === 1) return 'Domani'
	if (diff === -1) return 'Ieri'
	if (diff > 1 && diff < 7) return weekdayName(date)
	return formatShortDate(date)
}

/** "2026-10-14T11:30:00+02:00" -> "Oggi, 11:30" */
export function formatDateTime(value, today = new Date()) {
	if (!value) return ''
	const day = relativeDay(value.slice(0, 10), today)
	const time = value.length >= 16 ? value.slice(11, 16) : ''
	return time && time !== '00:00' ? `${day}, ${time}` : day
}

/** Anno scolastico corrente: da settembre si passa al successivo. */
export function schoolYear(date = new Date()) {
	const start = date.getMonth() >= 8 ? date.getFullYear() : date.getFullYear() - 1
	return `${start}/${start + 1}`
}

export function minutesOf(time) {
	const [hours, minutes] = String(time ?? '').split(':').map(Number)
	return Number.isFinite(hours) && Number.isFinite(minutes) ? hours * 60 + minutes : null
}

export function nowMinutes(date = new Date()) {
	return date.getHours() * 60 + date.getMinutes()
}

/** "15 min", "1 h 20 min" */
export function formatDuration(minutes) {
	const value = Math.max(0, Math.round(minutes))
	if (value < 60) return `${value} min`
	const hours = Math.floor(value / 60)
	const rest = value % 60
	return rest ? `${hours} h ${rest} min` : `${hours} h`
}

// ---------- testi ----------
const ROMAN = /^(ii|iii|iv|vi|vii|viii|ix)$/
const LOWER_WORDS = new Set(['di', 'e', 'del', 'della', 'dei', 'delle', 'da', 'a', 'in', 'con', 'per', 'la', 'il', 'lo', 'le', 'gli'])

export function titleCase(value) {
	return String(value ?? '')
		.toLowerCase()
		.split(/(\s+|-|')/)
		.map((word, index) => {
			if (ROMAN.test(word)) return word.toUpperCase()
			return index > 0 && LOWER_WORDS.has(word) ? word : word.charAt(0).toUpperCase() + word.slice(1)
		})
		.join('')
		.trim()
}

/** "BIANCHI ANNA" / "ROSSI Mario" -> "Prof. Bianchi Anna" */
export function teacherName(value) {
	const clean = String(value ?? '').trim()
	if (!clean) return ''
	return `Prof. ${titleCase(clean)}`
}

/** Solo il cognome, per le card: "DE SANTIS Paolo" -> "Prof. De Santis", "ROSSI MARIO" -> "Prof. Moretti" */
export function teacherShort(value) {
	const words = String(value ?? '').trim().split(/\s+/).filter(Boolean)
	if (!words.length) return ''
	const isUpper = (word) => word.length > 1 && word === word.toUpperCase() && /\p{L}/u.test(word)
	let surname = []
	for (const word of words) {
		if (!isUpper(word)) break
		surname.push(word)
	}
	if (!surname.length || surname.length === words.length) surname = [words[0]]
	return `Prof. ${titleCase(surname.join(' '))}`
}

/** Docenti veri dall'elenco dell'orario (l'OCR a volte aggiunge progetti come "PNRR ... (301)"). */
export function realTeachers(list = []) {
	return list.filter((name) => name && !/\d|\(|PNRR/i.test(name))
}

export function initials(first, last) {
	return `${String(first ?? '').trim().charAt(0)}${String(last ?? '').trim().charAt(0)}`.toUpperCase() || 'S'
}

/** '"G. GALILEI"' -> 'G. Galilei' */
export function schoolDisplayName(school) {
	if (!school) return ''
	const dedication = String(school.dedica ?? '').replace(/["“”]/g, '').trim()
	const name = titleCase(school.nome ?? '')
	// le iniziali ("G.") restano maiuscole, il resto diventa "Galilei"
	const dedicationText = dedication.split(/\s+/).map((word) => (/^[A-Z]\.$/i.test(word) ? word.toUpperCase() : titleCase(word))).join(' ')
	return [name, dedicationText].filter(Boolean).join(' ')
}

/** "1 A" -> "1ª A" */
export function classDisplayName(name) {
	const match = String(name ?? '').trim().match(/^(\d+)\s*(.*)$/)
	return match ? `${match[1]}ª ${match[2]}`.trim() : String(name ?? '')
}

/** Id della classe ("4A") -> "4ª A" */
export function classLabel(classId) {
	return classId ? classDisplayName(String(classId).replace(/^(\d+)\s*/, '$1 ')) : ''
}

export function normalizeText(value) {
	return String(value ?? '')
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, ' ')
		.trim()
}

/** Numero con un decimale come nel design: 7.8 */
export function formatNumber(value, digits = 1) {
	return Number.isFinite(value) ? value.toFixed(digits) : '—'
}
