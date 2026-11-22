import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import DashboardShell from './screens/DashboardShell.jsx'
import Login from './screens/Login.jsx'
import SchoolSetup from './screens/SchoolSetup.jsx'
import { api, ApiError, UNAUTHORIZED_EVENT } from './lib/api.js'
import { classLabel } from './lib/format.js'
import { legalDocFromHash } from './lib/legal.js'
import { clearSession, getClassId, getStoredUser, getToken, isGalileiSchool, saveSession, saveUser, setClassId } from './lib/session.js'
import { useToast } from './lib/toast.js'
import { refreshTokenIfStale } from './lib/tokenRefresh.js'

const LegalPage = lazy(() => import('./screens/LegalPage.jsx'))
import { clearApiCache } from './lib/useApi.js'

// Schermata da mostrare dopo il login: chi è del Galilei deve prima scegliere la classe.
function nextScreen(user) {
	return isGalileiSchool(user?.scuola) && !getClassId(user?.id) ? 'setup' : 'app'
}

function App() {
	const toast = useToast()
	const [user, setUser] = useState(() => (getToken() ? getStoredUser() : null))
	const [screen, setScreen] = useState(() => (getToken() ? 'checking' : 'login'))
	const [classId, setClassIdState] = useState(() => getClassId(getStoredUser()?.id))
	const [loginNotice, setLoginNotice] = useState('')
	const [legalDoc, setLegalDoc] = useState(() => legalDocFromHash())
	const returnHash = useRef('')

	// #privacy, #cookie e #termini si aprono sopra qualsiasi schermata, anche senza login
	useEffect(() => {
		let previous = window.location.hash
		const onHash = () => {
			const doc = legalDocFromHash()
			if (doc && !legalDocFromHash(previous)) returnHash.current = previous
			previous = window.location.hash
			setLegalDoc(doc)
		}
		window.addEventListener('hashchange', onHash)
		return () => window.removeEventListener('hashchange', onHash)
	}, [])

	function closeLegal() {
		window.location.hash = returnHash.current.replace(/^#/, '') || 'home'
	}

	const resetToLogin = useCallback((notice = '') => {
		clearSession()
		clearApiCache()
		setUser(null)
		setLoginNotice(notice)
		setScreen('login')
	}, [])

	// All'avvio: il token salvato è ancora valido? (il server perde le sessioni quando si riavvia)
	useEffect(() => {
		if (screen !== 'checking') return
		let cancelled = false
		api.me()
			.then((me) => {
				if (cancelled) return
				saveUser(me)
				setUser(me)
				setClassIdState(getClassId(me.id))
				setScreen(nextScreen(me))
				refreshTokenIfStale()
			})
			.catch((error) => {
				if (cancelled) return
				if (error instanceof ApiError && error.status === 401) {
					resetToLogin('Sessione scaduta: accedi di nuovo.')
				} else if (getStoredUser()) {
					// server irraggiungibile: si entra comunque, le schermate mostrano l'errore con "Riprova"
					setScreen(nextScreen(getStoredUser()))
				} else {
					resetToLogin(error.message)
				}
			})
		return () => {
			cancelled = true
		}
	}, [screen, resetToLogin])

	// Qualsiasi richiesta con 401 (sessione chiusa, server riavviato) riporta al login
	useEffect(() => {
		const onUnauthorized = () => resetToLogin('Sessione scaduta: accedi di nuovo.')
		window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
		return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
	}, [resetToLogin])

	// Con l'app aperta (o quando la PWA torna in primo piano) il token si rinnova da solo:
	// si esce solo dopo 7 giorni senza usarla
	const loggedIn = screen !== 'login' && screen !== 'checking'
	useEffect(() => {
		if (!loggedIn) return
		const onVisible = () => {
			if (document.visibilityState === 'visible') refreshTokenIfStale()
		}
		const timer = window.setInterval(refreshTokenIfStale, 60 * 60 * 1000)
		document.addEventListener('visibilitychange', onVisible)
		return () => {
			window.clearInterval(timer)
			document.removeEventListener('visibilitychange', onVisible)
		}
	}, [loggedIn])

	function handleLogin(token, loggedUser) {
		clearApiCache()
		saveSession(token, loggedUser)
		setUser(loggedUser)
		setClassIdState(getClassId(loggedUser.id))
		setLoginNotice('')
		setScreen(nextScreen(loggedUser))
	}

	async function handleLogout() {
		try {
			await api.logout()
		} catch {
			// anche se il server non risponde, sul dispositivo la sessione va chiusa
		}
		resetToLogin()
		toast('Sei uscito da Skedoo', { tone: 'info' })
	}

	function handleClassChosen(id) {
		const changed = screen === 'change-class' && id !== classId
		setClassId(user?.id, id)
		setClassIdState(id)
		setScreen('app')
		// orario e variazioni hanno la classe nella chiave di cache: non serve svuotare nulla
		if (changed) toast(`Classe impostata: ${classLabel(id)}`)
	}

	if (legalDoc) {
		return (
			<Suspense fallback={null}>
				<LegalPage doc={legalDoc} onClose={closeLegal} />
			</Suspense>
		)
	}

	if (screen === 'checking') {
		return (
			<main className="boot-screen" aria-busy="true">
				<span className="boot-screen__logo">Skedoo</span>
				<span className="boot-screen__bar" />
			</main>
		)
	}

	if (screen === 'login') {
		return <Login key={loginNotice} notice={loginNotice} onLogin={handleLogin} />
	}

	if (screen === 'setup' || screen === 'change-class') {
		return (
			<SchoolSetup
				initialClassId={classId}
				onCancel={screen === 'change-class' ? () => setScreen('app') : undefined}
				onDone={handleClassChosen}
			/>
		)
	}

	return (
		<DashboardShell
			classId={isGalileiSchool(user?.scuola) ? classId : null}
			onChangeClass={() => setScreen('change-class')}
			onLogout={handleLogout}
			user={user}
		/>
	)
}

export default App
