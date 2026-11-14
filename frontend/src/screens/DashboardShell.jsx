import { useCallback, useEffect, useMemo, useState } from 'react'
import { BottomNav, Sidebar } from '../components/AppNav.jsx'
import { DetailHost } from '../components/Details.jsx'
import { ErrorBoundary } from '../components/ErrorBoundary.jsx'
import { NotificationsMenu } from '../components/NotificationsMenu.jsx'
import { boardKey } from '../lib/agenda.js'
import { AppContext } from '../lib/appContext.js'
import { usePersistentFlags } from '../lib/data.js'
import { initials, schoolDisplayName } from '../lib/format.js'
import { parseRoute } from '../lib/routes.js'
import { readJson, writeJson } from '../lib/session.js'
import { useToast } from '../lib/toast.js'
import Agenda from './Agenda.jsx'
import Grades from './Grades.jsx'
import Home from './Home.jsx'
import Profile from './Profile.jsx'
import AbsencesPage from './subpages/AbsencesPage.jsx'
import BoardPage from './subpages/BoardPage.jsx'
import MaterialsPage from './subpages/MaterialsPage.jsx'
import TasksPage from './subpages/TasksPage.jsx'
import '../styles/dashboard/index.css'

const SCREENS = {
	home: Home,
	agenda: Agenda,
	voti: Grades,
	profilo: Profile,
	'home/compiti': TasksPage,
	'home/bacheca': BoardPage,
	'profilo/assenze': AbsencesPage,
	'profilo/materiali': MaterialsPage,
}

/** Navigazione tramite hash (#voti, #profilo/assenze): "indietro" e refresh funzionano. */
function useHashRoute() {
	const [route, setRoute] = useState(() => parseRoute())
	useEffect(() => {
		const onHash = () => {
			setRoute(parseRoute())
			window.scrollTo({ top: 0 })
		}
		window.addEventListener('hashchange', onHash)
		return () => window.removeEventListener('hashchange', onHash)
	}, [])
	const navigate = useCallback((path) => {
		if (window.location.hash === `#${path}`) window.scrollTo({ top: 0, behavior: 'smooth' })
		else window.location.hash = path
	}, [])
	return [route, navigate]
}

/** Compiti completati e verifiche salvate (sul dispositivo), con toast e "Annulla". */
function useTaskFlags(toast) {
	const [doneTasks, setDone] = usePersistentFlags('tasks-done')
	const [savedTasks, setSaved] = usePersistentFlags('tasks-saved')

	const toggleDone = useCallback((key) => {
		const wasDone = Boolean(doneTasks[key])
		setDone(key, !wasDone)
		toast(wasDone ? 'Compito di nuovo da fare' : 'Compito completato', {
			action: { label: 'Annulla', onClick: () => setDone(key, wasDone) },
		})
	}, [doneTasks, setDone, toast])

	const toggleSaved = useCallback((key) => {
		const wasSaved = Boolean(savedTasks[key])
		setSaved(key, !wasSaved)
		toast(wasSaved ? 'Rimosso dai salvati' : 'Salvato: lo ritrovi in Compiti & Verifiche', {
			action: { label: 'Annulla', onClick: () => setSaved(key, wasSaved) },
		})
	}, [savedTasks, setSaved, toast])

	return useMemo(() => ({ doneTasks, toggleDone, savedTasks, toggleSaved }), [doneTasks, toggleDone, savedTasks, toggleSaved])
}

function DashboardShell({ user, classId, onLogout, onChangeClass }) {
	const toast = useToast()
	const [route, navigate] = useHashRoute()
	const [detail, setDetail] = useState(null)
	const tasks = useTaskFlags(toast)
	const [boardRead, setBoardRead] = usePersistentFlags('board-read')
	const [alertsOn, setAlertsOnState] = useState(() => readJson('pref-alerts', true))
	const isGalilei = Boolean(classId)

	// ClasseViva segna come letta una circolare quando la si apre, ma l'elenco in cache non lo sa ancora
	const isBoardRead = useCallback((item) => Boolean(item.letto || boardRead[boardKey(item)]), [boardRead])
	const markBoardRead = useCallback((item) => {
		if (!boardRead[boardKey(item)]) setBoardRead(boardKey(item), true)
	}, [boardRead, setBoardRead])

	const setAlertsOn = useCallback((value) => {
		setAlertsOnState(value)
		writeJson('pref-alerts', value)
	}, [])

	const context = useMemo(() => ({
		user,
		classId,
		isGalilei,
		navigate,
		openDetail: setDetail,
		...tasks,
		isBoardRead,
		markBoardRead,
		alertsOn,
		setAlertsOn,
		onLogout,
		onChangeClass,
	}), [user, classId, isGalilei, navigate, tasks, isBoardRead, markBoardRead, alertsOn, setAlertsOn, onLogout, onChangeClass])

	const Screen = SCREENS[route.path] ?? Home
	const school = schoolDisplayName(user?.scuola)
	const richHeader = route.path === 'home' && !isGalilei

	return (
		<AppContext.Provider value={context}>
			<div className="app-shell">
				<Sidebar activeTab={route.tab} />

				<div className="app-main">
					<header className={`topbar${richHeader ? ' topbar--rich' : ''}`}>
						{richHeader ? (
							<div className="topbar__identity">
								<span className="avatar avatar--small avatar--online">{initials(user?.nome, user?.cognome)}</span>
								<div>
									<div className="topbar__title-row">
										<strong className="topbar__brand">Skedoo</strong>
										<span className="badge badge--accent">CV Synced</span>
									</div>
									<small><span aria-hidden="true" className="live-dot" />{school || 'ClasseViva'}</small>
								</div>
							</div>
						) : (
							<a className="topbar__brand" href="#home" onClick={(event) => { event.preventDefault(); navigate('home') }}>Skedoo</a>
						)}
						<NotificationsMenu />
					</header>

					<main className="content" id="content">
						<ErrorBoundary resetKey={route.path}>
							<Screen />
						</ErrorBoundary>
					</main>
				</div>

				<BottomNav activeTab={route.tab} />
				<DetailHost detail={detail} onClose={() => setDetail(null)} />
			</div>
		</AppContext.Provider>
	)
}

export default DashboardShell
