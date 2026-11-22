import { useEffect, useRef } from 'react'
import { Icon } from './Icon.jsx'

/** Titolo di sezione: "Orario di Oggi ............ 5 ore previste" */
export function SectionHeading({ id, icon, title, aside, kicker = false }) {
	return (
		<div className={`section-heading${kicker ? ' section-heading--kicker' : ''}`}>
			<h2 id={id}>
				{kicker && <span className="live-dot" aria-hidden="true" />}
				{icon && <Icon name={icon} size={18} />}
				{title}
			</h2>
			{aside}
		</div>
	)
}

/** Intestazione delle sottoschermate (Compiti, Bacheca, Presenze, Materiali) con il ritorno alla schermata madre. */
export function SubPageHeader({ title, subtitle, backLabel, onBack, actions }) {
	return (
		<header className="subpage-header">
			<button className="subpage-header__back" onClick={onBack} type="button">
				<Icon name="chevronLeft" size={18} />
				{backLabel}
			</button>
			<div className="subpage-header__row">
				<div>
					<h1>{title}</h1>
					{subtitle && <p className="page-header__subtitle">{subtitle}</p>}
				</div>
				{actions}
			</div>
		</header>
	)
}

/** Filtri a schede (Tutti / Compiti / Verifiche...). */
export function FilterTabs({ label, options, value, onChange }) {
	return (
		<div aria-label={label} className="filter-tabs" role="group">
			{options.map((option) => (
				<button
					aria-pressed={value === option.id}
					className={`filter-tabs__button${value === option.id ? ' filter-tabs__button--active' : ''}`}
					key={option.id}
					onClick={() => onChange(option.id)}
					type="button"
				>
					{option.label}
					{option.count != null && <span className="filter-tabs__count">{option.count}</span>}
				</button>
			))}
		</div>
	)
}

export function SearchField({ label, value, onChange, placeholder }) {
	return (
		<label className="search-field">
			<Icon name="search" size={17} />
			<span className="visually-hidden">{label}</span>
			<input onChange={(event) => onChange(event.target.value)} placeholder={placeholder} type="search" value={value} />
		</label>
	)
}

export function LinkButton({ children, onClick }) {
	return (
		<button className="link-button" onClick={onClick} type="button">
			{children}
			<Icon name="chevron" size={15} />
		</button>
	)
}

/** Riga che porta a un altro dettaglio: icona, etichetta piccola, testo e freccia. */
export function RelatedLink({ icon, label, value, onClick, tone = 'neutral' }) {
	return (
		<button className={`related-link related-link--${tone}`} onClick={onClick} type="button">
			<Icon name={icon} size={17} />
			<span><small>{label}</small><strong>{value}</strong></span>
			<Icon name="chevron" size={17} />
		</button>
	)
}

/** Blocchi grigi mentre i dati arrivano. */
export function Skeleton({ lines = 3, height = 72 }) {
	return (
		<div className="skeleton-list" aria-busy="true" aria-label="Caricamento in corso">
			{Array.from({ length: lines }, (_, index) => <span className="skeleton" key={index} style={{ height }} />)}
		</div>
	)
}

/** Messaggio per stato vuoto o errore, con eventuale pulsante "Riprova". */
export function StateMessage({ icon = 'calendar', title, text, onRetry, tone = 'neutral' }) {
	return (
		<div className={`state-message state-message--${tone}`} role={tone === 'error' ? 'alert' : undefined}>
			<span className="state-message__icon"><Icon name={tone === 'error' ? 'alert' : icon} size={18} /></span>
			<div>
				{title && <strong>{title}</strong>}
				{text && <p>{text}</p>}
			</div>
			{onRetry && (
				<button className="state-message__retry" onClick={onRetry} type="button">
					<Icon name="refresh" size={14} />
					Riprova
				</button>
			)}
		</div>
	)
}

export function ErrorMessage({ error, onRetry, title = 'Dati non disponibili' }) {
	return <StateMessage onRetry={onRetry} text={error?.message} title={title} tone="error" />
}

/** Pannello di dettaglio: bottom sheet su telefono, finestra centrata su schermi larghi. */
export function Sheet({ title, kicker, onClose, children, tone }) {
	const panelRef = useRef(null)
	const closeRef = useRef(onClose)

	useEffect(() => {
		closeRef.current = onClose
	}, [onClose])

	useEffect(() => {
		const previous = document.activeElement
		panelRef.current?.focus()
		const onKey = (event) => {
			if (event.key === 'Escape') closeRef.current()
		}
		document.addEventListener('keydown', onKey)
		document.body.classList.add('no-scroll')
		return () => {
			document.removeEventListener('keydown', onKey)
			document.body.classList.remove('no-scroll')
			previous?.focus?.()
		}
	}, [])

	return (
		<div className="sheet-backdrop" onClick={onClose}>
			<section
				aria-label={title}
				aria-modal="true"
				className={`sheet${tone ? ` sheet--${tone}` : ''}`}
				onClick={(event) => event.stopPropagation()}
				ref={panelRef}
				role="dialog"
				tabIndex={-1}
			>
				<header className="sheet__header">
					<div>
						{kicker && <p className="sheet__kicker">{kicker}</p>}
						<h2>{title}</h2>
					</div>
					<button aria-label="Chiudi" className="icon-button" onClick={onClose} type="button">
						<Icon name="close" size={18} />
					</button>
				</header>
				<div className="sheet__body">{children}</div>
			</section>
		</div>
	)
}
