import { useEffect, useMemo, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { LEGAL_DOCS } from '../lib/legal.js'
import { renderMarkdown } from '../lib/markdown.jsx'
import '../styles/legal.css'

/** Pagina di un documento legale (informativa, cookie, termini). */
export function LegalPage({ doc, onClose }) {
	const { title, load } = LEGAL_DOCS[doc]
	const [loaded, setLoaded] = useState({ doc: null, text: '', failed: false })

	useEffect(() => {
		let cancelled = false
		load()
			.then((module) => !cancelled && setLoaded({ doc, text: module.default, failed: false }))
			.catch(() => !cancelled && setLoaded({ doc, text: '', failed: true }))
		window.scrollTo(0, 0)
		document.title = `${title} · Skedoo`
		return () => {
			cancelled = true
			document.title = 'Skedoo'
		}
	}, [doc, load, title])

	const ready = loaded.doc === doc
	const content = useMemo(() => (ready ? renderMarkdown(loaded.text) : null), [ready, loaded.text])

	return (
		<main className="legal-page">
			<div className="legal-page__inner">
				<button className="legal-page__back" onClick={onClose} type="button">
					<Icon name="chevronLeft" size={18} />
					Torna a Skedoo
				</button>

				<article className="legal-doc" aria-busy={!ready}>
					{!ready && <p className="legal-doc__status">Caricamento…</p>}
					{ready && loaded.failed && (
						<p className="legal-doc__status">Impossibile caricare il documento. Controlla la connessione e riprova.</p>
					)}
					{content}
				</article>

				<nav className="legal-page__nav" aria-label="Documenti legali">
					{Object.entries(LEGAL_DOCS).map(([id, item]) => (
						<a aria-current={id === doc ? 'page' : undefined} href={`#${id}`} key={id}>
							{item.title}
						</a>
					))}
				</nav>
			</div>
		</main>
	)
}

export default LegalPage
