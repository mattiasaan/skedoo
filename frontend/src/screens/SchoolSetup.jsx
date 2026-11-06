import { useEffect, useState } from 'react'
import { classPicker } from './api/classPicker'
import './Login.css'

function Icon({ name, size = 20 }) {
	const shared = {
		width: size,
		height: size,
		viewBox: '0 0 24 24',
		fill: 'none',
		stroke: 'currentColor',
		strokeWidth: 1.8,
		strokeLinecap: 'round',
		strokeLinejoin: 'round',
		'aria-hidden': true,
	}

	if (name === 'cap') {
		return (
			<svg {...shared}>
				<path d="m2 9 10-5 10 5-10 5L2 9Z" />
				<path d="M6 11v5c3.5 2.7 8.5 2.7 12 0v-5M22 9v6" />
			</svg>
		)
	}

	if (name === 'school') {
		return (
			<svg {...shared}>
				<path d="m3 10 9-6 9 6-9 5-9-5Z" />
				<path d="M6 12v5l6 3 6-3v-5M21 10v6" />
			</svg>
		)
	}

	if (name === 'chevronDown') {
		return (
			<svg {...shared}>
				<path d="m6 9 6 6 6-6" />
			</svg>
		)
	}

	if (name === 'check') {
		return (
			<svg {...shared}>
				<path d="m5 12 4 4L19 6" />
			</svg>
		)
	}

	return null
}

function SchoolSetup({ onEnter }) {
	const [classes, setClasses] = useState([])
	const [selectedClassId, setSelectedClassId] = useState('')
	const [isOpen, setIsOpen] = useState(false)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState(null)

	useEffect(() => {
		async function fetchClasses() {
			try {
				const data = await classPicker()
				setClasses(data)
				if (data.length > 0) {
					setSelectedClassId(data[0].id)
				}
			} catch (err) {
				setError(err.message)
			} finally {
				setLoading(false)
			}
		}

		fetchClasses()
	}, [])

	const schoolClass = classes.find((option) => option.id === selectedClassId) || {
		nome: loading ? 'Caricamento classi...' : 'Nessuna classe disponibile',
		docente_coordinatore: ''
	}

	function handleSubmit(event) {
		event.preventDefault()
		localStorage.setItem('selectedClassId', selectedClassId)
		onEnter()
	}

	return (
		<main className="login-page login-page--setup">
			<section className="login-content" aria-labelledby="welcome-title">
				<header className="login-heading login-heading--setup">
					<div className="brand-mark" aria-hidden="true">
						<Icon name="cap" size={34} />
					</div>
					<h1 id="welcome-title">Bentornato!</h1>
					<p>Accedi al tuo registro elettronico ClasseViva</p>
				</header>

				<form className="login-panel setup-panel" onSubmit={handleSubmit}>
					<div className="setup-panel-heading">
						<h2>Seleziona la tua Classe</h2>
					</div>

					{error && <p style={{ color: '#ff6b6b', fontSize: '14px', marginBottom: '10px' }}>{error}</p>}

					<div className="setup-fields" style={{ position: 'relative' }}>
						<div 
							className="choice-control choice-control--single" 
							onClick={() => !loading && classes.length > 0 && setIsOpen(!isOpen)}
							style={{ cursor: 'pointer' }}
						>
							<Icon name="school" />
							<span className="choice-copy">
								<strong>{schoolClass.nome}</strong>
								<small>{schoolClass.docente_coordinatore ? `Coordinatore: ${schoolClass.docente_coordinatore}` : 'Seleziona una sezione'}</small>
							</span>
							<Icon name="chevronDown" size={17} />
						</div>

						{/* Menu a tendina personalizzato con colori in palette */}
						{isOpen && (
							<ul style={{
								position: 'absolute',
								top: '100%',
								left: 0,
								right: 0,
								marginTop: '8px',
								background: 'rgba(13, 22, 23, 0.95)',
								backdropFilter: 'blur(10px)',
								border: '1px solid rgba(26, 43, 44, 0.8)',
								borderRadius: '12px',
								listStyle: 'none',
								padding: '6px',
								zIndex: 1000,
								maxHeight: '220px',
								overflowY: 'auto',
								boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)'
							}}>
								{classes.map((option) => {
									const isSelected = option.id === selectedClassId;
									return (
										<li
											key={option.id}
											onClick={() => {
												setSelectedClassId(option.id)
												setIsOpen(false)
											}}
											style={{
												padding: '10px 14px',
												borderRadius: '8px',
												cursor: 'pointer',
												color: '#ffffff',
												background: isSelected ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
												border: isSelected ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid transparent',
												display: 'flex',
												flexDirection: 'column',
												gap: '3px',
												marginBottom: '4px',
												transition: 'all 0.2s ease'
											}}
											onMouseEnter={(e) => {
												if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
											}}
											onMouseLeave={(e) => {
												if (!isSelected) e.currentTarget.style.background = 'transparent'
											}}
										>
											<strong style={{ fontSize: '14px', color: isSelected ? '#10b981' : '#ffffff' }}>
												{option.nome}
											</strong>
											{option.docente_coordinatore && (
												<small style={{ color: '#94a3b8', fontSize: '12px' }}>
													Coordinatore: {option.docente_coordinatore}
												</small>
											)}
										</li>
									);
								})}
							</ul>
						)}
					</div>

					<button className="submit-button setup-submit" type="submit" disabled={loading || classes.length === 0}>
						<Icon name="check" size={17} />
						<span>Completa Configurazione ed Entra</span>
					</button>
				</form>
			</section>

			<footer className="login-footer">
				<nav className="footer-links" aria-label="Link informativi">
					<a href="mailto:privacy@skedoo.app?subject=Informativa%20Privacy">Informativa Privacy</a>
					<span aria-hidden="true">•</span>
					<a href="mailto:supporto@skedoo.app">Supporto Tecnico</a>
					<span aria-hidden="true">•</span>
					<a href="https://web.spaggiari.eu/">Info ClasseViva</a>
				</nav>
				<p className="copyright">
					SKEDOO APPS © 2025 · NON AFFILIATO UFFICIALMENTE A<br />
					GRUPPO SPAGGIARI PARMA
				</p>
			</footer>
		</main>
	)
}

export default SchoolSetup