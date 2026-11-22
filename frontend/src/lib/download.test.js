import { describe, expect, it } from 'vitest'
import { downloadName, extensionOf, filenameFromDisposition, isWebUrl } from './download.js'

describe('download', () => {
	it('legge il nome dal Content-Disposition', () => {
		expect(filenameFromDisposition("attachment; filename=\"Circ. 12.pdf\"; filename*=UTF-8''Circ.%2012%20%E2%80%93%20gita.pdf")).toBe('Circ. 12 – gita.pdf')
		expect(filenameFromDisposition('attachment; filename="verifica.docx"')).toBe('verifica.docx')
		expect(filenameFromDisposition('attachment; filename=semplice.txt')).toBe('semplice.txt')
		expect(filenameFromDisposition("attachment; filename*=UTF-8''%E0%A4%A; filename=\"riserva.pdf\"")).toBe('riserva.pdf')
		expect(filenameFromDisposition('attachment')).toBeNull()
		expect(filenameFromDisposition(null)).toBeNull()
	})

	it('riconosce solo estensioni vere', () => {
		expect(extensionOf('Esercizi.PDF')).toBe('pdf')
		expect(extensionOf('archivio.7z')).toBe('7z')
		expect(extensionOf('Cap. 3')).toBeNull()
		expect(extensionOf('Lezione 3.12')).toBeNull()
		expect(extensionOf('senza estensione')).toBeNull()
	})

	it("sceglie il nome con cui salvare: quello dell'app con l'estensione giusta", () => {
		expect(downloadName('CIRC. N. 518 - Evento.pdf', 'circ518.pdf', 'application/pdf')).toBe('CIRC. N. 518 - Evento.pdf')
		expect(downloadName('Esercizi capitolo 3', 'es_cap3.docx', 'application/octet-stream')).toBe('Esercizi capitolo 3.docx')
		expect(downloadName('Slide lezione', null, 'application/pdf')).toBe('Slide lezione.pdf')
		expect(downloadName('Appunti', null, 'application/octet-stream')).toBe('Appunti')
		expect(downloadName('', 'dal-server.pdf', 'application/pdf')).toBe('dal-server.pdf')
		expect(downloadName(null, null, 'image/png')).toBe('file.png')
		expect(downloadName('Compiti 1/2: "ripasso"?', null, 'text/plain')).toBe('Compiti 1 2 ripasso.txt')
	})

	it('apre solo link web', () => {
		expect(isWebUrl('https://example.org/x')).toBe(true)
		expect(isWebUrl('http://example.org')).toBe(true)
		expect(isWebUrl('javascript:alert(1)')).toBe(false)
		expect(isWebUrl('data:text/html,ciao')).toBe(false)
		expect(isWebUrl('non un link')).toBe(false)
	})
})
