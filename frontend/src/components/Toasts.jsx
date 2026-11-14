import { useCallback, useEffect, useRef, useState } from 'react'
import { ToastContext } from '../lib/toast.js'
import { Icon } from './Icon.jsx'

const ICONS = { success: 'checkCircle', error: 'alert', info: 'bell', offline: 'globe' }
const MAX_VISIBLE = 3

/** Fornisce toast() alle schermate e mostra i messaggi in una regione "live" letta dagli screen reader. */
export function ToastProvider({ children }) {
	const [toasts, setToasts] = useState([])
	const timers = useRef(new Map())
	const nextId = useRef(0)

	const dismiss = useCallback((id) => {
		clearTimeout(timers.current.get(id))
		timers.current.delete(id)
		setToasts((list) => list.filter((toast) => toast.id !== id))
	}, [])

	const show = useCallback((message, { tone = 'success', action, duration = 3500, id: fixedId } = {}) => {
		nextId.current += 1
		const id = fixedId ?? `toast-${nextId.current}`
		clearTimeout(timers.current.get(id))
		setToasts((list) => [...list.filter((toast) => toast.id !== id), { id, message, tone, action }].slice(-MAX_VISIBLE))
		if (duration > 0) timers.current.set(id, setTimeout(() => dismiss(id), duration))
		return id
	}, [dismiss])

	useEffect(() => {
		const pending = timers.current
		return () => pending.forEach((timer) => clearTimeout(timer))
	}, [])

	// avviso persistente quando manca la rete
	useEffect(() => {
		const offline = () => show('Sei offline: i dati mostrati potrebbero non essere aggiornati.', { tone: 'offline', duration: 0, id: 'offline' })
		const online = () => {
			dismiss('offline')
			show('Connessione ristabilita', { tone: 'info' })
		}
		if (!navigator.onLine) offline()
		window.addEventListener('offline', offline)
		window.addEventListener('online', online)
		return () => {
			window.removeEventListener('offline', offline)
			window.removeEventListener('online', online)
		}
	}, [show, dismiss])

	return (
		<ToastContext.Provider value={show}>
			{children}
			<div aria-live="polite" className="toasts" role="status">
				{toasts.map((toast) => (
					<div className={`toast toast--${toast.tone}`} key={toast.id}>
						<Icon name={ICONS[toast.tone] ?? 'bell'} size={17} />
						<span>{toast.message}</span>
						{toast.action && (
							<button
								className="toast__action"
								onClick={() => {
									toast.action.onClick()
									dismiss(toast.id)
								}}
								type="button"
							>
								{toast.action.label}
							</button>
						)}
						<button aria-label="Chiudi messaggio" className="toast__close" onClick={() => dismiss(toast.id)} type="button">
							<Icon name="close" size={14} />
						</button>
					</div>
				))}
			</div>
		</ToastContext.Provider>
	)
}

export default ToastProvider
