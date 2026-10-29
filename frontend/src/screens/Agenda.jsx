import { useState } from 'react'
import { Icon } from './DashboardShared.jsx'

const weekDays = [
	{ label: 'LUN', day: 13 },
	{ label: 'MAR', day: 14, active: true },
	{ label: 'MER', day: 15 },
	{ label: 'GIO', day: 16 },
	{ label: 'VEN', day: 17 },
	{ label: 'SAB', day: 18 },
]

const monthData = [
	{ day: 24, muted: true },
	{ day: 25, muted: true },
	{ day: 26, muted: true },
	{ day: 27, muted: true },
	{ day: 28, muted: true },
	{ day: 29, muted: true },
	{ day: 1, active: true, hasDot: true },
	{ day: 2 },
	{ day: 3 },
	{ day: 4 },
	{ day: 5, hasDot: true },
	{ day: 6, hasDot: true },
	{ day: 7 },
	{ day: 8 },
	{ day: 9, hasDot: true },
	{ day: 10 },
	{ day: 11 },
	{ day: 12 },
	{ day: 13, hasDot: true },
	{ day: 14 },
	{ day: 15 },
	{ day: 16 },
	{ day: 17 },
	{ day: 18 },
	{ day: 19 },
	{ day: 20 },
	{ day: 21 },
	{ day: 22 },
]

const weekLessons = [
	{ time: '08:00 - 09:00', subject: 'FILOSOFIA', teacher: 'Prof. Castelli', room: 'Aula 302', note: 'VERIFICA SCRITTA: KANT E ILLUMINISMO', tone: 'danger' },
	{ time: '09:00 - 10:00', subject: 'MATEMATICA', teacher: 'Prof.ssa Bianchi', room: 'Aula 302', note: 'COMPITI: ESERCIZI PAG. 112', tone: 'blue' },
	{ time: '10:15 - 11:15', subject: 'FISICA', teacher: 'Prof. Rossi', room: 'Laboratorio 201', note: 'CAMBIO AULA / LAB 201', tone: 'amber' },
	{ time: '11:15 - 12:15', subject: 'ITALIANO', teacher: 'Prof. De Luca', room: 'Aula 302', note: 'Aula 302', tone: 'green' },
	{ time: '12:15 - 13:15', subject: 'SCIENZE MOTORIE', teacher: 'Prof. Barbierri', room: 'Palestra', note: 'Palestra', tone: 'neutral' },
]

const monthEntries = [
	{ day: 'Martedì 14 Ottobre', points: '5 ore di lezione', items: [
		{ time: '08:00 - 09:00', period: '1ª Ora', subject: 'FILOSOFIA', teacher: 'Prof. Castelli', room: 'Aula 302', note: 'VERIFICA SCRITTA: KANT E ILLUMINISMO', tone: 'danger' },
		{ time: '09:00 - 10:00', period: '2ª Ora', subject: 'MATEMATICA', teacher: 'Prof.ssa Bianchi', room: 'Aula 302', note: 'COMPITI: ESERCIZI PAG. 112', tone: 'blue' },
		{ time: '10:15 - 11:15', period: '3ª Ora', subject: 'FISICA', teacher: 'Prof. Rossi', room: 'Laboratorio 201', note: 'CAMBIO AULA / LAB 201', tone: 'amber', status: 'CAMBIO AULA / LAB 201' },
		{ time: '11:15 - 12:15', period: '4ª Ora', subject: 'ITALIANO', teacher: 'Prof. De Luca', room: 'Aula 302', note: 'Aula 302', tone: 'green' },
		{ time: '12:15 - 13:15', period: '5ª Ora', subject: 'SCIENZE MOTORIE', teacher: 'Prof. Barbierri', room: 'Palestra', note: 'Palestra', tone: 'neutral' },
	] },
]

function Agenda() {
	const [view, setView] = useState('week')
	const selectedMonth = monthEntries[0]

	return (
		<section className="alternate-view" aria-labelledby="agenda-heading">
			<div className="agenda-header">
				<div>
					<p className="agenda-kicker">ORARIO E AGENDA</p>
					<h2 id="agenda-heading">{view === 'week' ? 'Agenda' : 'Mese'}</h2>
				</div>
				<div className="agenda-view-toggle" aria-label="Modalità vista agenda">
					<button type="button" className={`agenda-view-toggle__button${view === 'week' ? ' agenda-view-toggle__button--active' : ''}`} onClick={() => setView('week')}>Settimana</button>
					<button type="button" className={`agenda-view-toggle__button${view === 'month' ? ' agenda-view-toggle__button--active' : ''}`} onClick={() => setView('month')}>Mese</button>
				</div>
			</div>

			{view === 'week' ? (
				<>
					<div className="week-days" aria-label="Giorni della settimana">
						{weekDays.map((day) => (
							<button type="button" key={day.label} className={`week-day${day.active ? ' week-day--active' : ''}`}>
								<span>{day.label}</span>
								<strong>{day.day}</strong>
								{day.active && <i aria-hidden="true" />}
							</button>
						))}
					</div>

					<div className="agenda-summary">
						<span className="agenda-summary__dot" aria-hidden="true" />
						<strong>Martedì 14 Ottobre</strong>
						<span>5 ore di lezione</span>
					</div>

					<div className="agenda-list">
						{weekLessons.map((lesson) => (
							<article key={`${lesson.time}-${lesson.subject}`} className="agenda-entry agenda-entry--accent-default">
								<div className="agenda-entry__header">
									<div className="agenda-entry__time-block">
										<span>{lesson.time}</span>
										<small>{lesson.subject === 'FISICA' ? '3ª Ora' : lesson.subject === 'SCIENZE MOTORIE' ? '5ª Ora' : `${weekLessons.indexOf(lesson) + 1}ª Ora`}</small>
									</div>
									<span className="agenda-entry__room">{lesson.room}</span>
								</div>
								<h3>{lesson.subject}</h3>
								<p className="agenda-entry__teacher">{lesson.teacher}</p>
								<div className={`agenda-entry__note agenda-entry__note--${lesson.tone}`}>
									<Icon name="calendar" size={15} />
									<span>{lesson.note}</span>
									<Icon name="chevron" size={16} />
								</div>
							</article>
						))}
					</div>
				</>
			) : (
				<>
					<div className="calendar-month-wrapper">
						<div className="calendar-month-header">
							<h3>October 2023</h3>
							<div className="calendar-nav" aria-label="Naviga mese">
								<button type="button" aria-label="Mese precedente">‹</button>
								<button type="button" aria-label="Mese successivo">›</button>
							</div>
						</div>

						<div className="calendar-weekdays" aria-label="Settimana del mese">
							<span>SUN</span>
							<span>MON</span>
							<span>TUE</span>
							<span>WED</span>
							<span>THU</span>
							<span>FRI</span>
							<span>SAT</span>
						</div>

						<div className="month-calendar" aria-label="Calendario mensile">
							{monthData.map((day, index) => (
								<button type="button" key={`${day.day}-${index}`} className={`month-day${day.active ? ' month-day--active' : ''}${day.muted ? ' month-day--muted' : ''}`}>
									<span>{day.day}</span>
									{day.hasDot && <i aria-hidden="true" />}
								</button>
							))}
						</div>
					</div>

					<div className="calendar-legend">
						<span><i className="legend-dot legend-dot--tests" aria-hidden="true" />Tests</span>
						<span><i className="legend-dot legend-dot--deadlines" aria-hidden="true" />Deadlines</span>
						<span><i className="legend-dot legend-dot--holidays" aria-hidden="true" />Holidays</span>
						<span><i className="legend-dot legend-dot--assemblies" aria-hidden="true" />Assemblies</span>
					</div>
				</>
			)}
		</section>
	)
}

export default Agenda