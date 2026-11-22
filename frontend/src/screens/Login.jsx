import { useState } from 'react'
import { AuthLayout } from '../components/AuthLayout.jsx'
import { Icon } from '../components/Icon.jsx'
import { api } from '../lib/api.js'
import '../styles/auth.css'

// `remembered`: l'utente uscito per sessione scaduta ({ id, nome }), con lo username già inserito
function Login({ onLogin, notice: initialNotice, remembered }) {
	const [username, setUsername] = useState(remembered?.id ?? '')
	const [password, setPassword] = useState('')
	const [showPassword, setShowPassword] = useState(false)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState(null)
	const [notice, setNotice] = useState(initialNotice ?? '')
	const [returning, setReturning] = useState(Boolean(remembered?.id))

	function switchAccount() {
		setReturning(false)
		setUsername('')
		setPassword('')
		document.getElementById('username')?.focus()
	}

	async function handleSubmit(event) {
		event.preventDefault()
		if (loading) return
		setLoading(true)
		setError(null)
		setNotice('')
		try {
			const data = await api.login(username.trim(), password)
			onLogin(data.access_token, data.utente)
		} catch (e) {
			setError(e.message)
			setLoading(false)
		}
	}

	return (
		<AuthLayout
			subtitle="Accedi al tuo registro elettronico ClasseViva"
			badge={(
				<div className="compat-badge">
					<Icon name="shield" size={16} />
					<span>Compatibile con Spaggiari ClasseViva &amp; Multi-Istituto</span>
				</div>
			)}
		>
			<form className="auth-panel" onSubmit={handleSubmit} aria-labelledby="credentials-title" noValidate>
				<h2 className="auth-panel__title auth-panel__title--divided" id="credentials-title">
					{returning && remembered?.nome ? `Ciao ${remembered.nome}!` : 'Credenziali Personali'}
				</h2>

				<div className="auth-field">
					<div className="auth-label-row">
						<label className="auth-label" htmlFor="username">Codice Personale o Email</label>
						{returning && (
							<button className="auth-text-button" onClick={switchAccount} type="button">
								Non sei tu?
							</button>
						)}
					</div>
					<div className="input-wrap">
						<Icon name="person" size={20} />
						<input
							autoCapitalize="none"
							autoComplete="username"
							autoCorrect="off"
							id="username"
							name="username"
							onChange={(event) => setUsername(event.target.value)}
							placeholder="es. S1234567X o mario.rossi@studenti"
							required
							spellCheck="false"
							value={username}
						/>
					</div>
				</div>

				<div className="auth-field">
					<div className="auth-label-row">
						<label className="auth-label" htmlFor="password">Password</label>
						<button
							className="auth-text-button"
							onClick={() => setNotice('forgot')}
							type="button"
						>
							Password dimenticata?
						</button>
					</div>
					<div className="input-wrap">
						<Icon name="lock" size={20} />
						<input
							autoComplete="current-password"
							autoFocus={returning}
							id="password"
							name="password"
							onChange={(event) => setPassword(event.target.value)}
							placeholder="••••••••••••"
							required
							type={showPassword ? 'text' : 'password'}
							value={password}
						/>
						<button
							aria-label={showPassword ? 'Nascondi password' : 'Mostra password'}
							aria-pressed={showPassword}
							className="input-wrap__action"
							onClick={() => setShowPassword((visible) => !visible)}
							type="button"
						>
							<Icon name={showPassword ? 'eyeOff' : 'eye'} size={20} />
						</button>
					</div>
				</div>

				{notice === 'forgot' && (
					<p className="auth-notice" role="status">
						La password è quella di ClasseViva: puoi reimpostarla da{' '}
						<a href="https://web.spaggiari.eu/" rel="noreferrer" target="_blank">web.spaggiari.eu</a>{' '}
						con «Hai dimenticato la password?».
					</p>
				)}
				{notice && notice !== 'forgot' && <p className="auth-notice" role="status">{notice}</p>}
				{error && (
					<p className="auth-notice auth-notice--error" role="alert">
						<Icon name="alert" size={16} />
						{error}
					</p>
				)}

				<button className="auth-submit" disabled={loading || !username.trim() || !password} type="submit">
					{loading ? <span className="spinner" aria-hidden="true" /> : null}
					<span>{loading ? 'Accesso in corso…' : 'Accedi con ClasseViva'}</span>
					{!loading && <Icon name="arrow" size={22} />}
				</button>
				<p className="auth-consent">
					Accedendo accetti i <a href="#termini">Termini di servizio</a> e dichiari di aver letto l'
					<a href="#privacy">Informativa privacy</a>. La password serve solo a collegarti a ClasseViva e non viene salvata.
				</p>
			</form>
		</AuthLayout>
	)
}

export default Login
