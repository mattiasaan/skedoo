import { useApp } from '../lib/appContext.js'
import { classLabel, initials, schoolDisplayName, titleCase } from '../lib/format.js'
import { TABS } from '../lib/routes.js'
import { Icon } from './Icon.jsx'

/** Barra laterale (desktop, da 1024px). */
export function Sidebar({ activeTab }) {
	const { user, classId, navigate } = useApp()
	const details = [schoolDisplayName(user?.scuola), classId ? classLabel(classId) : null].filter(Boolean).join(' • ')

	return (
		<aside aria-label="Navigazione" className="sidebar">
			<a className="sidebar__brand" href="#home" onClick={(event) => { event.preventDefault(); navigate('home') }}>
				<span className="sidebar__logo"><Icon name="cap" size={20} /></span>
				Skedoo
			</a>
			<nav className="sidebar__nav">
				{TABS.map((item) => (
					<button
						aria-current={activeTab === item.id ? 'page' : undefined}
						className={`sidebar__item${activeTab === item.id ? ' sidebar__item--active' : ''}`}
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
					<small>{details || 'ClasseViva'}</small>
				</span>
			</button>
		</aside>
	)
}

/** Barra in basso (telefono e tablet). */
export function BottomNav({ activeTab }) {
	const { navigate } = useApp()
	return (
		<nav aria-label="Navigazione principale" className="bottom-nav">
			{TABS.map((item) => (
				<button
					aria-current={activeTab === item.id ? 'page' : undefined}
					className={`bottom-nav__item${activeTab === item.id ? ' bottom-nav__item--active' : ''}`}
					key={item.id}
					onClick={() => navigate(item.id)}
					type="button"
				>
					<Icon name={item.icon} size={20} />
					<span>{item.label}</span>
				</button>
			))}
		</nav>
	)
}
