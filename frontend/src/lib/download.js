// File scaricati da ClasseViva (allegati della bacheca, materiali della didattica): nome e salvataggio.

/** Limite del backend (MAX_DOWNLOAD_MB in backend/app/config.py): qui serve solo per i testi d'aiuto. */
export const MAX_DOWNLOAD_MB = 250

const EXTENSIONS = {
	'application/pdf': 'pdf',
	'application/zip': 'zip',
	'application/msword': 'doc',
	'application/vnd.ms-excel': 'xls',
	'application/vnd.ms-powerpoint': 'ppt',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
	'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
	'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
	'application/vnd.oasis.opendocument.text': 'odt',
	'audio/mpeg': 'mp3',
	'image/gif': 'gif',
	'image/jpeg': 'jpg',
	'image/png': 'png',
	'text/plain': 'txt',
	'video/mp4': 'mp4',
}

/** Nome dall'header Content-Disposition (filename* UTF-8 o filename), null se manca. */
export function filenameFromDisposition(header) {
	if (!header) return null
	const encoded = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header)
	if (encoded) {
		try {
			return decodeURIComponent(encoded[1].trim().replace(/^"|"$/g, '')) || null
		} catch {
			// codifica non valida: si prova con filename=
		}
	}
	const plain = /filename\s*=\s*(?:"([^"]*)"|([^;]+))/i.exec(header)
	return (plain?.[1] ?? plain?.[2])?.trim() || null
}

/** Estensione di un nome di file ("pdf"), solo se sembra davvero tale: "Cap. 3" o "Lezione 3.1" non ne hanno. */
export function extensionOf(name) {
	const match = /\.([a-z0-9]{2,5})$/i.exec(name ?? '')
	return match && /[a-z]/i.test(match[1]) ? match[1].toLowerCase() : null
}

// caratteri non ammessi nei nomi di file (Windows è il più restrittivo), oltre a quelli di controllo
const FORBIDDEN = new Set([...'\\/:*?"<>|'])

function cleanName(value) {
	const text = [...String(value ?? '')].map((char) => (FORBIDDEN.has(char) || char.charCodeAt(0) < 32 ? ' ' : char)).join('')
	return text.replace(/\s+/g, ' ').trim().slice(0, 180)
}

/**
 * Nome con cui salvare il file: quello mostrato nell'app (più leggibile), con l'estensione presa dal nome che
 * dà ClasseViva o dal tipo del file; se l'app non ha un nome, quello di ClasseViva.
 */
export function downloadName(listingName, serverName, mimeType) {
	const listing = cleanName(listingName)
	const server = cleanName(serverName)
	if (listing && extensionOf(listing)) return listing
	const extension = extensionOf(server) ?? EXTENSIONS[mimeType] ?? null
	const base = listing || server.replace(/\.[^.]*$/, '') || 'file'
	return extension ? `${base}.${extension}` : base
}

/** Solo indirizzi web: un link di un materiale non deve poter eseguire codice (javascript:, data:...). */
export function isWebUrl(value) {
	try {
		return ['http:', 'https:'].includes(new URL(value).protocol)
	} catch {
		return false
	}
}

/** Fa salvare il file dal browser. */
export function saveFile(blob, name) {
	const url = URL.createObjectURL(blob)
	const link = document.createElement('a')
	link.href = url
	link.download = name
	link.rel = 'noopener'
	document.body.append(link)
	link.click()
	link.remove()
	// alcuni browser leggono il blob dopo il click: lo si libera più tardi
	setTimeout(() => URL.revokeObjectURL(url), 60000)
}
