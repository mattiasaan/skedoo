import { useState } from 'react'
import Agenda from './Agenda.jsx'
import Grades from './Grades.jsx'
import Home from './Home.jsx'
import Profile from './Profile.jsx'
import { Icon } from './DashboardShared.jsx'
import './Dashboard.css'

const navigationItems = [
	{ id: 'home', label: 'Home', icon: 'home' },
	{ id: 'agenda', label: 'Agenda', icon: 'calendar' },
	{ id: 'grades', label: 'Voti', icon: 'chart' },
	{ id: 'profile', label: 'Profilo', icon: 'person' },
]

function DashboardShell({ onLogout }) {
	const [activeTab, setActiveTab] = useState('home')
	const [notificationsOpen, setNotificationsOpen] = useState(false)
	const [completedTasks, setCompletedTasks] = useState({})
	const [savedTasks, setSavedTasks] = useState({})

	function toggleItem(setItems, id) {
		setItems((items) => ({ ...items, [id]: !items[id] }))
	}

	return (
		<main className="dashboard-shell">
			<header className="dashboard-header">
				<a className="dashboard-brand" href="#home" onClick={(event) => { event.preventDefault(); setActiveTab('home') }}>Skedoo</a>
				<button
					aria-expanded={notificationsOpen}
					aria-label={notificationsOpen ? 'Chiudi notifiche' : 'Apri notifiche'}
					className={`notification-button${notificationsOpen ? ' notification-button--active' : ''}`}
					onClick={() => setNotificationsOpen((open) => !open)}
					type="button"
				>
					<Icon name="bell" size={18} />
					<span className="notification-count">3</span>
				</button>
			</header>

			{notificationsOpen && (
				<aside className="notifications-popover" aria-label="Notifiche recenti">
					<strong>Notifiche</strong>
					<p>Variazione di orario per la lezione di Fisica.</p>
					<p>Nuovi compiti assegnati in Matematica.</p>
				</aside>
			)}

			<div className="dashboard-content">
				{activeTab === 'home' && <Home completedTasks={completedTasks} savedTasks={savedTasks} onComplete={(id) => toggleItem(setCompletedTasks, id)} onSave={(id) => toggleItem(setSavedTasks, id)} />}
				{activeTab === 'agenda' && <Agenda />}
				{activeTab === 'grades' && <Grades />}
				{activeTab === 'profile' && <Profile onLogout={onLogout} />}
			</div>

			<nav className="dashboard-nav" aria-label="Navigazione principale">
				{navigationItems.map((item) => (
					<button
						aria-current={activeTab === item.id ? 'page' : undefined}
						className={`dashboard-nav-item${activeTab === item.id ? ' dashboard-nav-item--active' : ''}`}
						key={item.id}
						onClick={() => { setActiveTab(item.id); setNotificationsOpen(false) }}
						type="button"
					>
						<Icon name={item.icon} size={19} />
						<span>{item.label}</span>
					</button>
				))}
			</nav>
		</main>
	)
}

export default DashboardShell