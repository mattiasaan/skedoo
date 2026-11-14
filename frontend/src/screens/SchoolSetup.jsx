import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { AuthLayout } from '../components/AuthLayout.jsx'
import { Icon } from '../components/Icon.jsx'
import { ErrorMessage } from '../components/ui.jsx'
import { api } from '../lib/api.js'
import { classDisplayName, normalizeText, schoolYear, titleCase } from '../lib/format.js'
import { useApi } from '../lib/useApi.js'
import './Login.css'

function classTitle(option) {
	const name = classDisplayName(option.nome)
	const [number, ...section] = name.split(' ')
	return section.length ? `${number} Sezione ${section.join(' ')}` : name
}

function classSubtitle(option) {
	return [option.pomeriggio ? 'Con rientri pomeridiani' : 'Solo mattina', `A.S. ${schoolYear()}`].join(' • ')
}

function SchoolSetup({ initialClassId, onDone, onCancel }) {
	const classes = useApi('classes', api.classes)
	const [selectedId, setSelectedId] = useState(initialClassId ?? '')
	const [open, setOpen] = useState(false)
	const [query, setQuery] = useState('')
	const listId = useId()
	const wrapperRef = useRef(null)
	const searchRef = useRef(null)

	const options = useMemo(() => classes.data ?? [], [classes.data])
	const filtered = useMemo(() => {
		const needle = normalizeText(query).replace(/ /g, '')
		if (!needle) return options
		return options.filter((option) => normalizeText(`${option.id} ${option.nome} ${option.docente_coordinatore ?? ''}`).replace(/ /g, '').includes(needle))
	}, [options, query])
	const selected = options.find((option) => option.id === selectedId)

	useEffect(() => {
		if (!open) return undefined
		searchRef.current?.focus()
		const onPointer = (event) => {
			if (!wrapperRef.current?.contains(event.target)) setOpen(false)
		}
		document.addEventListener('pointerdown', onPointer)
		return () => document.removeEventListener('pointerdown', onPointer)
	}, [open])

	function choose(option) {
		setSelectedId(option.id)
		setOpen(false)
		setQuery('')
	}

	function handleSubmit(event) {
		event.preventDefault()
		if (selected) onDone(selected.id)
	}

	return (
		<AuthLayout subtitle="Accedi al tuo registro elettronico ClasseViva">
			<form className="auth-panel auth-panel--setup" onSubmit={handleSubmit} aria-labelledby="setup-title">
				<h2 className="auth-panel__title" id="setup-title">Seleziona la tua Scuola</h2>

				<div className="auth-field" ref={wrapperRef}>
					<span className="auth-label" id={`${listId}-label`}>Classe &amp; Indirizzo di Studio</span>
					<button
						aria-controls={listId}
						aria-expanded={open}
						aria-haspopup="listbox"
						aria-labelledby={`${listId}-label ${listId}-value`}
						className={`choice-control${open ? ' choice-control--open' : ''}`}
						disabled={classes.loading || !options.length}
						onClick={() => setOpen((value) => !value)}
						type="button"
					>
						<span className="choice-control__icon"><Icon name="users" size={18} /></span>
						<span className="choice-control__copy" id={`${listId}-value`}>
							<strong>{selected ? classTitle(selected) : classes.loading ? 'Caricamento classi…' : 'Scegli la tua classe'}</strong>
							<small>{selected ? classSubtitle(selected) : `Istituto G. Galilei • A.S. ${schoolYear()}`}</small>
						</span>
						<Icon className="choice-control__chevron" name="chevronDown" size={18} />
					</button>

					{open && (
						<div className="choice-popover">
							<div className="choice-search">
								<Icon name="search" size={16} />
								<input
									aria-label="Cerca classe"
									onChange={(event) => setQuery(event.target.value)}
									onKeyDown={(event) => {
										if (event.key === 'Escape') setOpen(false)
										if (event.key === 'Enter') {
											event.preventDefault()
											if (filtered[0]) choose(filtered[0])
										}
									}}
									placeholder="Cerca (es. 4A)"
									ref={searchRef}
									value={query}
								/>
							</div>
							<ul aria-label="Classi" className="choice-list" id={listId} role="listbox">
								{filtered.map((option) => (
									<li
										aria-selected={option.id === selectedId}
										className={`choice-option${option.id === selectedId ? ' choice-option--selected' : ''}`}
										key={option.id}
										onClick={() => choose(option)}
										onKeyDown={(event) => {
											if (event.key === 'Enter' || event.key === ' ') {
												event.preventDefault()
												choose(option)
											}
										}}
										role="option"
										tabIndex={0}
									>
										<strong>{classTitle(option)}</strong>
										{option.docente_coordinatore && <small>Coord. {titleCase(option.docente_coordinatore)}</small>}
										{option.id === selectedId && <Icon name="check" size={16} />}
									</li>
								))}
								{!filtered.length && <li className="choice-empty">Nessuna classe trovata</li>}
							</ul>
						</div>
					)}
				</div>

				{classes.error && <ErrorMessage error={classes.error} onRetry={classes.reload} title="Classi non disponibili" />}

				<button className="auth-submit" disabled={!selected} type="submit">
					<Icon name="check" size={18} />
					<span>Completa Configurazione ed Entra</span>
				</button>
				{onCancel && (
					<button className="auth-secondary" onClick={onCancel} type="button">Annulla</button>
				)}
			</form>
		</AuthLayout>
	)
}

export default SchoolSetup
