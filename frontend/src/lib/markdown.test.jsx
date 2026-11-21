import { readFileSync } from 'node:fs'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { renderMarkdown } from './markdown.jsx'

const html = (source) => renderToStaticMarkup(<>{renderMarkdown(source)}</>)

describe('renderMarkdown', () => {
	it('rende titoli, elenchi, tabelle e formattazione in linea', () => {
		const out = html('# Titolo\n\nTesto **forte** e *corsivo*.\n\n- uno\n- due\n\n| A | B |\n|---|---|\n| 1 | 2 |')
		expect(out).toContain('<h1 id="titolo">Titolo</h1>')
		expect(out).toContain('<strong>forte</strong>')
		expect(out).toContain('<em>corsivo</em>')
		expect(out).toContain('<li>due</li>')
		expect(out).toContain('<td>2</td>')
	})

	it('non permette HTML né link javascript:', () => {
		const out = html('<img src=x onerror=alert(1)> [clic](javascript:alert(1))')
		expect(out).not.toContain('<img')
		expect(out).not.toContain('href="javascript')
		expect(out).toContain('&lt;img')
	})

	it('apre i link esterni in una nuova scheda e lascia interni quelli con #', () => {
		const out = html('[privacy](#privacy) e https://www.garanteprivacy.it.')
		expect(out).toContain('<a href="#privacy">privacy</a>')
		expect(out).toContain('href="https://www.garanteprivacy.it" target="_blank" rel="noreferrer"')
	})

	it.each(['privacy', 'cookie', 'termini'])('rende il documento %s', (doc) => {
		const out = html(readFileSync(new URL(`../legal/${doc}.md`, import.meta.url), 'utf8'))
		expect(out).toContain('<h1')
		expect(out).not.toMatch(/\*\*|\]\(/)
	})
})
