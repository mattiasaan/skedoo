import { useState } from 'react'
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

	if (name === 'shield') {
		return (
			<svg {...shared}>
				<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
				<path d="m9 12 2 2 4-4" />
			</svg>
		)
	}

	if (name === 'user') {
		return (
			<svg {...shared}>
				<circle cx="12" cy="8" r="4" />
				<path d="M5 21v-2a7 7 0 0 1 14 0v2" />
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

	if (name === 'people') {
		return (
			<svg {...shared}>
				<circle cx="9" cy="8" r="3" />
				<path d="M3 19v-1a6 6 0 0 1 12 0v1H3ZM16 5.5a3 3 0 0 1 0 5.8M18 14a5 5 0 0 1 3 4.5" />
			</svg>
		)
	}

	if (name === 'layers') {
		return (
			<svg {...shared}>
				<rect x="8" y="8" width="12" height="12" rx="2" />
				<path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
			</svg>
		)
	}

	if (name === 'chevrons') {
		return (
			<svg {...shared}>
				<path d="m7 9 5-5 5 5M7 15l5 5 5-5" />
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

	if (name === 'lock') {
		return (
			<svg {...shared}>
				<rect x="4" y="10" width="16" height="11" rx="2" />
				<path d="M8 10V7a4 4 0 0 1 7.8-1.2M12 14v3" />
			</svg>
		)
	}

	if (name === 'eye') {
		return (
			<svg {...shared}>
				<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
				<circle cx="12" cy="12" r="3" />
			</svg>
		)
	}

	if (name === 'eyeOff') {
		return (
			<svg {...shared}>
				<path d="m3 3 18 18M10.6 10.6a2 2 0 0 0 2.8 2.8" />
				<path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a16 16 0 0 1-3.1 3.8M6.2 6.2C3.5 8 2 12 2 12s3.6 7 10 7a10.8 10.8 0 0 0 4.1-.8" />
			</svg>
		)
	}

	if (name === 'arrow') {
		return (
			<svg {...shared}>
				<path d="M5 12h14M13 6l6 6-6 6" />
			</svg>
		)
	}

	return (
		<svg {...shared}>
			<rect x="4" y="10" width="16" height="11" rx="2" />
			<path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
		</svg>
	)
}

function Login({ onEnter }) {
	const [currentStep, setCurrentStep] = useState(1)
	const [showPassword, setShowPassword] = useState(false)
	const [notice, setNotice] = useState('')
	const [selectedSchool, setSelectedSchool] = useState('righi')
	const [selectedClass, setSelectedClass] = useState('4a')
	const [multiInstitute, setMultiInstitute] = useState(true)

	const schools = [
		{ id: 'righi', name: 'Liceo Scientifico A. Righi', details: 'Roma (RM) • Cod. Mecc. RMPS28000X' },
		{ id: 'galilei', name: 'Istituto Galileo Galilei', details: 'Roma (RM) • Istituto scolastico' },
	]
	const classes = [
		{ id: '4a', name: '5ª Sezione J', details: 'Scienze Applicate • A.S. 2024/2025' },
		{ id: '4b', name: '4ª Sezione B', details: 'Scienze Applicate • A.S. 2024/2025' },
		{ id: '3a', name: '3ª Sezione A', details: 'Scienze Applicate • A.S. 2024/2025' },
	]
	const school = schools.find((option) => option.id === selectedSchool)
	const schoolClass = classes.find((option) => option.id === selectedClass)

	function handleSubmit(event) {
		event.preventDefault()
		setNotice('')
		setCurrentStep(2)
	}

	function handleComplete(event) {
		event.preventDefault()
		onEnter()
	}

	return (
		<main className={`login-page${currentStep === 2 ? ' login-page--setup' : ''}`}>
			<section className="login-content" aria-labelledby="welcome-title">
				<header className={`login-heading${currentStep === 2 ? ' login-heading--setup' : ''}`}>
					<div className="brand-mark" aria-hidden="true">
						<Icon name="cap" size={34} />
					</div>
					<h1 id="welcome-title">Bentornato!</h1>
					<p>Accedi al tuo registro elettronico ClasseViva</p>
					{currentStep === 1 && (
						<div className="compatibility-badge">
							<Icon name="shield" size={17} />
							<span>Compatibile con Spaggiari ClasseViva &amp; Multi-Istituto</span>
						</div>
					)}
				</header>

				<form className={`login-panel${currentStep === 2 ? ' setup-panel' : ''}`} onSubmit={currentStep === 1 ? handleSubmit : handleComplete}>
					{currentStep === 1 ? (
						<>
							<div className="panel-heading">
								<span className="step-indicator">1</span>
								<h2>Credenziali Personali</h2>
								<span className="step-label">Passo 1 di 2</span>
							</div>

							<div className="form-fields">
								<label className="field-label" htmlFor="username">
									Codice Personale o Email
								</label>
								<div className="input-wrap">
									<Icon name="user" />
									<input
										autoComplete="username"
										id="username"
										name="username"
										placeholder="es. S1234567X o mario.rossi@studenti"
										required
									/>
								</div>

								<div className="password-label-row">
									<label className="field-label" htmlFor="password">Password</label>
									<button
										className="forgot-link"
										onClick={() => setNotice('Per recuperare la password, contatta il supporto del tuo istituto.')}
										type="button"
									>
										Password dimenticata?
									</button>
								</div>
								<div className="input-wrap">
									<Icon name="lock" />
									<input
										autoComplete="current-password"
										id="password"
										name="password"
										placeholder="Inserisci la password"
										required
										type={showPassword ? 'text' : 'password'}
									/>
									<button
										aria-label={showPassword ? 'Nascondi password' : 'Mostra password'}
										aria-pressed={showPassword}
										className="visibility-toggle"
										onClick={() => setShowPassword((visible) => !visible)}
										title={showPassword ? 'Nascondi password' : 'Mostra password'}
										type="button"
									>
										<Icon name={showPassword ? 'eyeOff' : 'eye'} />
									</button>
								</div>
							</div>

							{notice && <p className="form-notice" role="status">{notice}</p>}

							<button className="submit-button" type="submit">
								<span>Accedi con ClasseViva</span>
								<Icon name="arrow" size={22} />
							</button>
						</>
					) : (
						<>
							<div className="setup-panel-heading">
								<div>
									<p className="setup-eyebrow">Configurazione scuola &amp; classe</p>
									<h2>Seleziona la tua Scuola</h2>
								</div>
								<span className="step-label">Passo 2 di 2</span>
							</div>

							<div className="setup-fields">
								<label className="setup-field-label" htmlFor="school">
									Istituto Scolastico Principale
								</label>
								<div className="choice-control">
									<Icon name="school" />
									<span className="choice-copy">
										<strong>{school.name}</strong>
										<small>{school.details}</small>
									</span>
									<Icon name="chevrons" size={17} />
									<select
										aria-label="Istituto Scolastico Principale"
										id="school"
										value={selectedSchool}
										onChange={(event) => setSelectedSchool(event.target.value)}
									>
										{schools.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}
									</select>
								</div>

								<label className="setup-field-label" htmlFor="school-class">
									Classe &amp; Indirizzo di Studio
								</label>
								<div className="choice-control">
									<Icon name="people" />
									<span className="choice-copy">
										<strong>{schoolClass.name}</strong>
										<small>{schoolClass.details}</small>
									</span>
									<Icon name="chevronDown" size={17} />
									<select
										aria-label="Classe e indirizzo di studio"
										id="school-class"
										value={selectedClass}
										onChange={(event) => setSelectedClass(event.target.value)}
									>
										{classes.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}
									</select>
								</div>

								<label className="multi-institute-control">
									<Icon name="layers" />
									<span className="choice-copy">
										<strong>Attiva Multi-Istituto</strong>
										<small>Gestisci fratelli o scuole diverse</small>
									</span>
									<input
										checked={multiInstitute}
										className="switch-input"
										onChange={(event) => setMultiInstitute(event.target.checked)}
										type="checkbox"
									/>
									<span className="switch-track" aria-hidden="true"><span /></span>
								</label>
							</div>

							{notice && <p className="form-notice setup-notice" role="status">{notice}</p>}

							<button className="submit-button setup-submit" type="submit">
								<Icon name="check" size={17} />
								<span>Completa Configurazione ed Entra</span>
							</button>
						</>
					)}
				</form>
			</section>

			<footer className="login-footer">
				{currentStep === 1 && (
					<div className="privacy-note">
						<Icon name="secure" size={18} />
						<span>I tuoi dati rimangono crittografati solo sul tuo dispositivo</span>
					</div>
				)}
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

export default Login
