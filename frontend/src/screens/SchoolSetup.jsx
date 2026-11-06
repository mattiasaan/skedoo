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
						<h2>Seleziona la tua Scuola</h2>
					</div>

					<div className="setup-fields">
						<div className="choice-control choice-control--single">
							<Icon name="school" />
							<span className="choice-copy">
								<strong>{schoolClass.name}</strong>
								<small>{schoolClass.details}</small>
							</span>
							<Icon name="chevronDown" size={17} />
							<select
								aria-label="Seleziona scuola e sezione"
								id="school-class"
								value={selectedClass}
								onChange={(event) => setSelectedClass(event.target.value)}
							>
								{classes.map((option) => (
									<option key={option.id} value={option.id}>
										{option.name}
									</option>
								))}
							</select>
						</div>
					</div>

					<button className="submit-button setup-submit" type="submit">
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
