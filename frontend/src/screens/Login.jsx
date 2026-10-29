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
	const [showPassword, setShowPassword] = useState(false)
	const [notice, setNotice] = useState('')

	function handleSubmit(event) {
		event.preventDefault()
		setNotice('')
		onEnter()
	}

	return (
		<main className="login-page">
			<section className="login-content" aria-labelledby="welcome-title">
				<header className="login-heading">
					<div className="brand-mark" aria-hidden="true">
						<Icon name="cap" size={34} />
					</div>
					<h1 id="welcome-title">Bentornato!</h1>
					<p>Accedi al tuo registro elettronico ClasseViva</p>
					<div className="compatibility-badge">
						<Icon name="shield" size={17} />
						<span>Compatibile con Spaggiari ClasseViva &amp; Multi-Istituto</span>
					</div>
				</header>

				<form className="login-panel" onSubmit={handleSubmit}>
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
				</form>
			</section>

			<footer className="login-footer">
				<div className="privacy-note">
					<Icon name="shield" size={18} />
					<span>I tuoi dati rimangono crittografati solo sul tuo dispositivo</span>
				</div>
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
