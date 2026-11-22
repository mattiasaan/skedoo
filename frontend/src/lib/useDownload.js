import { useCallback, useSyncExternalStore } from 'react'
import { downloadName, isWebUrl, saveFile } from './download.js'
import { useToast } from './toast.js'

// Download in corso, condivisi da tutte le schermate: lo stesso file non parte due volte e l'avanzamento
// resta visibile anche cambiando pagina (es. dalla dashboard della materia a Materiali).
const active = new Map() // chiave -> avanzamento 0..1, oppure null se la dimensione non è nota
const listeners = new Set()
let version = 0

function update(key, value) {
	if (value === undefined) active.delete(key)
	else active.set(key, value)
	version += 1
	listeners.forEach((listener) => listener())
}

function subscribe(listener) {
	listeners.add(listener)
	return () => listeners.delete(listener)
}

/**
 * download.start({ key, name, fetch, link, onText }):
 * - `fetch(onProgress)` chiama l'API (api.material / api.boardAttachment);
 * - `name` è il nome mostrato nell'app, usato per salvare il file;
 * - `link`: il materiale è un link, che si apre in una nuova scheda;
 * - `onText(testo)`: per i materiali di solo testo.
 * download.progress(key): undefined se non è in corso, altrimenti 0..1 o null.
 */
export function useDownload() {
	useSyncExternalStore(subscribe, () => version)
	const toast = useToast()

	const start = useCallback(async ({ key, name, fetch, link = false, onText }) => {
		if (active.has(key)) return
		// la scheda va aperta subito, al tocco: dopo l'attesa della rete il browser la bloccherebbe come popup
		const tab = link ? window.open('', '_blank') : null
		if (tab) tab.opener = null
		update(key, null)
		try {
			const result = await fetch((progress) => update(key, progress))
			if (result.kind === 'file') {
				saveFile(result.blob, downloadName(name, result.filename, result.blob.type))
				tab?.close()
				return
			}
			const data = result.data ?? {}
			if (data.tipo === 'link' && isWebUrl(data.url)) {
				if (tab) tab.location.href = data.url
				else window.open(data.url, '_blank', 'noopener')
				return
			}
			tab?.close()
			if (data.tipo === 'testo' && onText) onText(data.testo)
			else toast('Questo contenuto si apre solo dall\'app o dal sito ClasseViva', { tone: 'info' })
		} catch (error) {
			tab?.close()
			toast(error.message || 'Download non riuscito, riprova tra poco', { tone: 'error' })
		} finally {
			update(key, undefined)
		}
	}, [toast])

	const progress = useCallback((key) => (active.has(key) ? active.get(key) : undefined), [])
	return { start, progress }
}
