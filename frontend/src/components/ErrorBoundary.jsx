import { Component } from 'react'
import { Icon } from './Icon.jsx'

/** Se una schermata va in errore mostra un messaggio invece di una pagina bianca. */
export class ErrorBoundary extends Component {
	constructor(props) {
		super(props)
		this.state = { error: null }
	}

	static getDerivedStateFromError(error) {
		return { error }
	}

	componentDidCatch(error, info) {
		console.error('Errore nella schermata', error, info.componentStack)
	}

	componentDidUpdate(previous) {
		// cambiando schermata si riprova
		if (this.state.error && previous.resetKey !== this.props.resetKey) this.setState({ error: null })
	}

	render() {
		if (!this.state.error) return this.props.children
		return (
			<div className="crash-screen" role="alert">
				<span className="crash-screen__icon"><Icon name="alert" size={26} /></span>
				<h1>Qualcosa è andato storto</h1>
				<p>Questa schermata non è riuscita a caricarsi. Puoi riprovare o tornare alla Home.</p>
				<div className="crash-screen__actions">
					<button className="crash-screen__primary" onClick={() => this.setState({ error: null })} type="button">
						<Icon name="refresh" size={16} />
						Riprova
					</button>
					<button className="crash-screen__secondary" onClick={() => window.location.assign('#home')} type="button">Vai alla Home</button>
				</div>
			</div>
		)
	}
}

export default ErrorBoundary
