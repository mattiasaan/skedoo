import { Icon } from './Icon.jsx'

/** Cornice comune di Login (passo 1) e configurazione classe (passo 2). */
export function AuthLayout({ title = 'Bentornato!', subtitle, badge, children }) {
	return (
		<main className="auth-page">
			<div className="auth-page__inner">
				<header className="auth-heading">
					<div className="brand-mark" aria-hidden="true">
						<Icon name="cap" size={32} />
					</div>
					<h1 id="auth-title">{title}</h1>
					{subtitle && <p>{subtitle}</p>}
					{badge}
				</header>

				{children}
			</div>

			<footer className="auth-footer">
				<nav className="auth-footer__links" aria-label="Link informativi">
					<a href="#privacy">Privacy</a>
					<span aria-hidden="true">•</span>
					<a href="#cookie">Cookie</a>
					<span aria-hidden="true">•</span>
					<a href="#termini">Termini di servizio</a>
				</nav>
				<p className="auth-footer__copyright">
					SKEDOO APPS © {new Date().getFullYear()} • NON AFFILIATO UFFICIALMENTE A GRUPPO SPAGGIARI PARMA
				</p>
			</footer>
		</main>
	)
}

export default AuthLayout
