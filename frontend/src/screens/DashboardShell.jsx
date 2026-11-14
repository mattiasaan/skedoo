import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { DetailHost } from '../components/Details.jsx'
import { Icon } from '../components/Icon.jsx'
import { AppContext } from '../lib/appContext.js'
import { useBoard, useChanges, usePersistentFlags } from '../lib/data.js'
import { classLabel, dateKey, formatDateTime, initials, schoolDisplayName, titleCase } from '../lib/format.js'
import { readJson, writeJson } from '../lib/session.js'
import Agenda from './Agenda.jsx'
import Grades from './Grades.jsx'
import Home from './Home.jsx'
import Profile from './Profile.jsx'
import './Dashboard.css'

const TABS = [
	{ id: 'home', label: 'Home', icon: 'grid' },
	{ id: 'agenda', label: 'Agenda', icon: 'calendar' },
	{ id: 'voti', label: 'Voti', icon: 'chart' },
	{ id: 'profilo', label: 'Profilo', icon: 'person' },
]

function tabFromHash() {
	const hash = window.location.hash.replace('#', '')
	return TABS.some((tab) => tab.id === hash) ? hash : 'home'
}

/** Notifiche: variazioni d'orario di oggi + circolari non lette. */
function useNotifications(classId) {
	const changes = useChanges(classId)
	const board = useBoard()
	const [seen, setSeen] = useState(() => readJson('notifications-seen', {}))

	const items = useMemo(() => {
		const today = dateKey()
		const changeItems = (changes.data ?? [])
			.filter((change) => change.data === today)
			.map((change) => ({ id: `change-${change.id}`, kind: 'change', title: 'Variazione orario', text: change.testo, change }))
		const boardItems = (board.data?.elementi ?? [])
			.filter((item) => !item.letto)
			.slice(0, 6)
			.map((item) => ({ id: `board-${item.codice}-${item.id}`, kind: 'board', title: item.categoria || 'Circolare', text: item.titolo, when: item.pubblicato_il, item }))
		return [...changeItems, ...boardItems]
	}, [changes.data, board.data])

	// preferenza "Avvisi cambi orario" del Profilo: se spenta niente contatore sulla campanella
	const alertsOn = readJson('pref-alerts', true)
	const unseen = alertsOn ? items.filter((item) => !seen[item.id]).length : 0
	const markAllSeen = useCallback(() => {
		const next = Object.fromEntries(items.map((item) => [item.id, true]))
		setSeen(next)
		writeJson('notifications-seen', next)
	}, [items])

	return { items, unseen, markAllSeen, changes: changes.data ?? [] }
}

function DashboardShell({ user, classId, onLogout, onChangeClass }) {
	const [tab, setTab] = useState(tabFromHash)
	const [detail, setDetail] = useState(null)
	const [notificationsOpen, setNotificationsOpen] = useState(false)
	const [doneTasks, toggleDone] = usePersistentFlags('tasks-done')
	const [savedTasks, toggleSaved] = usePersistentFlags('tasks-saved')
	const notifications = useNotifications(classId)
	const popoverRef = useRef(null)
	const isGalilei = Boolean(classId)

	// La tab vive nell'hash dell'URL: il tasto "indietro" e il refresh funzionano.
	useEffect(() => {
		const onHash = () => setTab(tabFromHash())
		window.addEventListener('hashchange', onHash)
		return () => window.removeEventListener('hashchange', onHash)
	}, [])

	useEffect(() => {
		if (!notificationsOpen) return undefined
		const onPointer = (event) => {
			if (!popoverRef.current?.contains(event.target)) setNotificationsOpen(false)
		}
		const onKey = (event) => {
			if (event.key === 'Escape') setNotificationsOpen(false)
		}
		document.addEventListener('pointerdown', onPointer)
		document.addEventListener('keydown', onKey)
		return () => {
			document.removeEventListener('pointerdown', onPointer)
			document.removeEventListener('keydown', onKey)
		}
	}, [notificationsOpen])

	const navigate = useCallback((id) => {
		setNotificationsOpen(false)
		if (window.location.hash !== `#${id}`) window.location.hash = id
		setTab(id)
		window.scrollTo({ top: 0 })
	}, [])

	const openDetail = useCallback((value) => {
		setNotificationsOpen(false)
		setDetail(value)
	}, [])

	const context = useMemo(() => ({
		user,
		classId,
		isGalilei,
		navigate,
		openDetail,
		doneTasks,
		toggleDone,
		savedTasks,
		toggleSaved,
		onLogout,
		onChangeClass,
	}), [user, classId, isGalilei, navigate, openDetail, doneTasks, toggleDone, savedTasks, toggleSaved, onLogout, onChangeClass])

	const school = schoolDisplayName(user?.scuola)
	const className = classId ? classLabel(classId) : null
	const richHeader = tab === 'home' && !isGalilei

	function toggleNotifications() {
		setNotificationsOpen((open) => {
			if (!open) notifications.markAllSeen()
			return !open
		})
	}

	function openNotification(item) {
		if (item.kind === 'board') openDetail({ type: 'board', item: item.item })
		else openDetail({ type: 'changes', changes: notifications.changes.filter((change) => change.data === dateKey()) })
	}

	return (
		<AppContext.Provider value={context}>
			<div className="app-shell">
				<aside className="sidebar" aria-label="Navigazione">
					<a className="sidebar__brand" href="#home" onClick={(event) => { event.preventDefault(); navigate('home') }}>
						<span className="sidebar__logo"><Icon name="cap" size={20} /></span>
						Skedoo
					</a>
					<nav className="sidebar__nav">
						{TABS.map((item) => (
							<button
								aria-current={tab === item.id ? 'page' : undefined}
								className={`sidebar__item${tab === item.id ? ' sidebar__item--active' : ''}`}
								key={item.id}
								onClick={() => navigate(item.id)}
								type="button"
							>
								<Icon name={item.icon} size={20} />
								{item.label}
							</button>
						))}
					</nav>
					<button className="sidebar__user" onClick={() => navigate('profilo')} type="button">
						<span className="avatar avatar--small">{initials(user?.nome, user?.cognome)}</span>
						<span>
							<strong>{titleCase([user?.nome, user?.cognome].filter(Boolean).join(' ')) || 'Studente'}</strong>
							<small>{[school, className].filter(Boolean).join(' • ') || 'ClasseViva'}</small>
						</span>
					</button>
				</aside>

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
									<small><span className="live-dot" aria-hidden="true" />{school || 'ClasseViva'}</small>
								</div>
							</div>
						) : (
							<a className="topbar__brand" href="#home" onClick={(event) => { event.preventDefault(); navigate('home') }}>Skedoo</a>
						)}

						<div className="notifications" ref={popoverRef}>
							<button
								aria-expanded={notificationsOpen}
								aria-label={`Notifiche${notifications.unseen ? ` (${notifications.unseen} nuove)` : ''}`}
								className={`icon-button notifications__button${notificationsOpen ? ' notifications__button--active' : ''}`}
								onClick={toggleNotifications}
								type="button"
							>
								<Icon name="bell" size={19} />
								{notifications.unseen > 0 && <span className="notifications__count">{Math.min(notifications.unseen, 9)}</span>}
							</button>
							{notificationsOpen && (
								<div className="notifications__popover" role="region" aria-label="Notifiche">
									<strong className="notifications__title">Notifiche</strong>
									{notifications.items.length ? (
										<ul>
											{notifications.items.map((item) => (
												<li key={item.id}>
													<button onClick={() => openNotification(item)} type="button">
														<span className={`notifications__icon notifications__icon--${item.kind}`}>
															<Icon name={item.kind === 'board' ? 'megaphone' : 'swap'} size={16} />
														</span>
														<span>
															<small>{item.title}{item.when ? ` • ${formatDateTime(item.when)}` : ''}</small>
															<b>{item.text}</b>
														</span>
													</button>
												</li>
											))}
										</ul>
									) : <p className="notifications__empty">Nessuna novità: sei in pari!</p>}
								</div>
							)}
						</div>
					</header>

					<main className="content" id="content">
						{tab === 'home' && <Home />}
						{tab === 'agenda' && <Agenda />}
						{tab === 'voti' && <Grades />}
						{tab === 'profilo' && <Profile />}
					</main>
				</div>

				<nav className="bottom-nav" aria-label="Navigazione principale">
					{TABS.map((item) => (
						<button
							aria-current={tab === item.id ? 'page' : undefined}
							className={`bottom-nav__item${tab === item.id ? ' bottom-nav__item--active' : ''}`}
							key={item.id}
							onClick={() => navigate(item.id)}
							type="button"
						>
							<Icon name={item.icon} size={21} />
							<span>{item.label}</span>
						</button>
					))}
				</nav>

				<DetailHost detail={detail} onClose={() => setDetail(null)} />
			</div>
		</AppContext.Provider>
	)
}

export default DashboardShell
