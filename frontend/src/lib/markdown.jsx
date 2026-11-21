// Mini renderer Markdown per i documenti legali (src/legal/*.md).
// Produce elementi React, mai HTML grezzo: il testo non può iniettare markup.
// Supporta: titoli #/##/###, paragrafi, elenchi "- ", tabelle "| a | b |", citazioni "> ",
// separatori "---" e in linea **grassetto**, *corsivo*, `codice`, [link](url) e URL nudi.

const INLINE = /(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|https?:\/\/[^\s)]+[^\s).,;:])/g

function safeHref(href) {
	return /^(https?:|mailto:|#)/i.test(href) ? href : null
}

function inline(text, keyPrefix = '') {
	const nodes = []
	let last = 0
	let index = 0
	for (const match of text.matchAll(INLINE)) {
		if (match.index > last) nodes.push(text.slice(last, match.index))
		const key = `${keyPrefix}${index++}`
		const [whole, , bold, italic, code, label, href] = match
		if (bold !== undefined) nodes.push(<strong key={key}>{inline(bold, `${key}-`)}</strong>)
		else if (italic !== undefined) nodes.push(<em key={key}>{inline(italic, `${key}-`)}</em>)
		else if (code !== undefined) nodes.push(<code key={key}>{code}</code>)
		else {
			const target = safeHref(href ?? whole)
			const external = target && /^https?:/i.test(target)
			nodes.push(
				target ? (
					<a href={target} key={key} {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}>
						{label !== undefined ? inline(label, `${key}-`) : whole}
					</a>
				) : (
					label ?? whole
				),
			)
		}
		last = match.index + whole.length
	}
	if (last < text.length) nodes.push(text.slice(last))
	return nodes
}

function cells(row) {
	return row.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim())
}

/** Testo del titolo -> id per i link interni (es. "1. Titolare" -> "1-titolare"). */
export function slug(text) {
	return text
		.toLowerCase()
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '')
}

export function renderMarkdown(source) {
	const lines = source.replace(/\r\n?/g, '\n').split('\n')
	const blocks = []
	let i = 0
	const key = () => `b${blocks.length}`

	while (i < lines.length) {
		const line = lines[i]
		if (!line.trim()) {
			i++
			continue
		}

		const heading = /^(#{1,3})\s+(.*)$/.exec(line)
		if (heading) {
			const Tag = `h${heading[1].length}`
			blocks.push(<Tag id={slug(heading[2])} key={key()}>{inline(heading[2])}</Tag>)
			i++
			continue
		}

		if (/^-{3,}\s*$/.test(line)) {
			blocks.push(<hr key={key()} />)
			i++
			continue
		}

		if (line.startsWith('|')) {
			const rows = []
			while (i < lines.length && lines[i].startsWith('|')) rows.push(lines[i++])
			const [head, , ...body] = rows // la seconda riga è il separatore |---|
			blocks.push(
				<div className="legal-table" key={key()}>
					<table>
						<thead>
							<tr>{cells(head).map((cell, c) => <th key={c}>{inline(cell)}</th>)}</tr>
						</thead>
						<tbody>
							{body.map((row, r) => (
								<tr key={r}>{cells(row).map((cell, c) => <td key={c}>{inline(cell)}</td>)}</tr>
							))}
						</tbody>
					</table>
				</div>,
			)
			continue
		}

		if (/^-\s+/.test(line)) {
			const items = []
			while (i < lines.length && /^-\s+/.test(lines[i])) items.push(lines[i++].replace(/^-\s+/, ''))
			blocks.push(<ul key={key()}>{items.map((item, n) => <li key={n}>{inline(item)}</li>)}</ul>)
			continue
		}

		if (line.startsWith('>')) {
			const quoted = []
			while (i < lines.length && lines[i].startsWith('>')) quoted.push(lines[i++].replace(/^>\s?/, ''))
			blocks.push(<blockquote key={key()}>{renderMarkdown(quoted.join('\n'))}</blockquote>)
			continue
		}

		const paragraph = []
		while (i < lines.length && lines[i].trim() && !/^(#{1,3}\s|\||-\s|>|-{3,}\s*$)/.test(lines[i])) {
			paragraph.push(lines[i++].trim())
		}
		blocks.push(<p key={key()}>{inline(paragraph.join(' '))}</p>)
	}
	return blocks
}
