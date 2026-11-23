import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import DashboardShell from './screens/DashboardShell.jsx'
import Login from './screens/Login.jsx'
import SchoolSetup from './screens/SchoolSetup.jsx'
import { api, ApiError, UNAUTHORIZED_EVENT } from './lib/api.js'
import { classLabel, titleCase } from './lib/format.js'
import { legalDocFromHash } from './lib/legal.js'
import {
	clearSession, getClassId, getLastLogin, getOtherAccount, getStoredUser, getToken, isGalileiSchool, rememberLastLogin, sameAccount,
	saveOtherAccount, saveSession, saveUser, setClassId, swapAccounts,
} from './lib/session.js'
import { useToast } from './lib/toast.js'
import { refreshTokenIfStale } from './lib/tokenRefresh.js'

const LegalPage = lazy(() => import('./screens/LegalPage.jsx'))
import { clearApiCache } from './lib/useApi.js'

// Schermata da mostrare dopo il login: chi è del Galilei deve prima scegliere la classe.
function nextScreen(user) {
	return isGalileiSchool(user?.scuola) && !getClassId(user?.id) ? 'setup' : 'app'
}

// Genitore e studente vedono la stessa classe: il secondo account del Galilei la eredita dal primo
function inheritClass(user, from, classId) {
	if (!classId || getClassId(user?.id) || !isGalileiSchool(user?.scuola)) return
	if (user.scuola?.codice && from?.scuola?.codice && user.scuola.codice !== from.scuola.codice) return
	setClassId(user.id, classId)
}

// Il genitore su ClasseViva ha il nome dello studente: gli account si distinguono per tipo
function accountName(user) {
	if (user?.tipo) return `account ${user.tipo}`
	const name = titleCase(user?.nome?.split(' ')[0] ?? '') || user?.id
	return name ? `account di ${name}` : 'altro account'
}

/** Chiude una sessione sul server senza far uscire l'account attivo (token vecchi, doppioni). */
function closeSession(token) {
	if (token) api.logout(token).catch(() => {})
}

// Messaggio sulla schermata di login dopo un 401: la password cambiata su ClasseViva ha il suo
function expiredNotice(error) {
	return error?.code === 'credentials_changed' ? error.message : 'Sessione scaduta: accedi di nuovo.'
}

function App() {
	const toast = useToast()
	const [user, setUser] = useState(() => (getToken() ? getStoredUser() : null))
	const [screen, setScreen] = useState(() => (getToken() ? 'checking' : 'login'))
	const [classId, setClassIdState] = useState(() => getClassId(getStoredUser()?.id))
	const [loginNotice, setLoginNotice] = useState('')
	const [other, setOther] = useState(() => getOtherAccount()?.user ?? null)
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

	// `expired`: uscita non voluta (sessione scaduta), si ricorda chi era collegato per il prossimo accesso
	const resetToLogin = useCallback((notice = '', { expired = false } = {}) => {
		rememberLastLogin(expired ? getStoredUser() : null)
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
					resetToLogin(expiredNotice(error), { expired: true })
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

	// Qualsiasi richiesta con 401 (sessione chiusa, server riavviato, password cambiata) riporta al login
	useEffect(() => {
		const onUnauthorized = (event) => resetToLogin(expiredNotice(event.detail), { expired: true })
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

	// Passa a un account già salvato: lo controlla /auth/me nella schermata 'checking' (la sessione può essere scaduta)
	function activate(account) {
		clearApiCache()
		setUser(account.user)
		setClassIdState(getClassId(account.user.id))
		setOther(getOtherAccount()?.user ?? null)
		setLoginNotice('')
		setScreen('checking')
	}

	function handleSwitchAccount() {
		const account = swapAccounts()
		if (!account) return
		activate(account)
		toast(`Ora usi l'${accountName(account.user)}`, { tone: 'info' })
	}

	// Dalla schermata di login (sessione scaduta) si può tornare all'altro account senza password
	function handleUseOtherAccount() {
		const account = getOtherAccount()
		if (!account) return
		saveSession(account.token, account.user)
		saveOtherAccount(null)
		activate(account)
	}

	function handleLogin(token, loggedUser) {
		clearApiCache()
		rememberLastLogin(null)
		// rientrare con l'account che era in attesa: niente doppioni, la sessione vecchia si chiude
		const waiting = getOtherAccount()
		if (sameAccount(waiting?.user, loggedUser)) {
			closeSession(waiting.token)
			saveOtherAccount(null)
			setOther(null)
		}
		saveSession(token, loggedUser)
		setUser(loggedUser)
		setClassIdState(getClassId(loggedUser.id))
		setLoginNotice('')
		setScreen(nextScreen(loggedUser))
	}

	// Secondo account (studente <-> genitore): quello in uso va in attesa, il nuovo diventa attivo
	function handleAccountAdded(token, loggedUser) {
		const current = { token: getToken(), user: getStoredUser() ?? user }
		if (sameAccount(current.user, loggedUser)) {
			// ha rifatto il login con lo stesso account: si tiene solo il token nuovo
			closeSession(current.token)
			handleLogin(token, loggedUser)
			return
		}
		closeSession(getOtherAccount()?.token)
		saveOtherAccount(current.token ? current : null)
		inheritClass(loggedUser, current.user, classId)
		clearApiCache()
		saveSession(token, loggedUser)
		setUser(loggedUser)
		setOther(getOtherAccount()?.user ?? null)
		setClassIdState(getClassId(loggedUser.id))
		setScreen(nextScreen(loggedUser))
		toast(`Aggiunto l'${accountName(loggedUser)}: per tornare all'altro usa il Profilo`)
	}

	async function handleLogout() {
		const leaving = getStoredUser()
		try {
			await api.logout()
		} catch {
			// anche se il server non risponde, sul dispositivo la sessione va chiusa
		}
		const account = getOtherAccount()
		if (account) {
			// con due account si esce solo da quello in uso e si passa all'altro
			saveSession(account.token, account.user)
			saveOtherAccount(null)
			activate(account)
			toast(`Sei uscito dall'${accountName(leaving)}`, { tone: 'info' })
			return
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
		return (
			<Login
				key={loginNotice}
				notice={loginNotice}
				onLogin={handleLogin}
				onUseOther={other ? handleUseOtherAccount : undefined}
				other={other}
				remembered={getLastLogin()}
			/>
		)
	}

	if (screen === 'add-account') {
		return <Login adding current={user} onCancel={() => setScreen('app')} onLogin={handleAccountAdded} />
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
			// ogni account ha i suoi compiti completati, circolari lette e preferenze: cambiando account si riparte da zero
			key={user?.id}
			classId={isGalileiSchool(user?.scuola) ? classId : null}
			onAddAccount={() => setScreen('add-account')}
			onChangeClass={() => setScreen('change-class')}
			onLogout={handleLogout}
			onSwitchAccount={other ? handleSwitchAccount : undefined}
			otherAccount={other}
			user={user}
		/>
	)
}

export default App
