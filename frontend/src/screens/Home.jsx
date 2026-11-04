import { useState } from 'react'
import { AssignmentCard, Icon, LessonRow } from './DashboardShared.jsx'
import { assignments, lessons } from './DashboardData.js'
import { getAssignmentAgendaItem, getLessonAgendaItem, agendaEvents } from './AgendaData.js'

function Home({ completedTasks, savedTasks, onComplete, onSave, onNavigateToAgenda, onOpenAgendaItem }) {
	const [noticeVisible, setNoticeVisible] = useState(true)
	const currentLessons = lessons.filter((lesson) => lesson.tone === 'current')
	const currentLesson = currentLessons[0]
	const remainingLessonCount = currentLessons.length
	const recentAssignments = assignments.slice(0, 4)

	return (
		<>
			<div className="date-heading">
				<p>MARTEDÌ, 14 OTTOBRE</p>
				<span>Liceo Scientifico A. Righi (4ª A)</span>
			</div>

			{noticeVisible && (
				<aside
					className="schedule-alert schedule-alert--clickable"
					aria-label="Dettagli variazione orario"
					onClick={() => onOpenAgendaItem(agendaEvents[0])}
					onKeyDown={(event) => {
						if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
							event.preventDefault()
							onOpenAgendaItem(agendaEvents[0])
						}
					}}
					role="link"
					tabIndex={0}
				>
					<div className="alert-icon"><Icon name="alert" size={19} /></div>
					<div className="alert-copy">
						<div className="alert-meta"><strong>VARIAZIONE ORARIO</strong><span>10 min fa</span></div>
						<p><b>Prof. Rossi assente</b> — Aula 204 spostata in <u>201</u> per il laboratorio di Fisica (3ª ora).</p>
					</div>
					<button aria-label="Chiudi avviso" className="icon-button alert-close" onClick={(event) => { event.stopPropagation(); setNoticeVisible(false) }} type="button"><Icon name="close" size={16} /></button>
				</aside>
			)}

			<section className="next-lesson-section" aria-labelledby="next-lesson-title">
				<div className="section-kicker-row">
					<h2 id="next-lesson-title"><span className="live-dot" />LEZIONE ATTUALE</h2>
				</div>
				{currentLesson ? (
					<article
						className="featured-lesson featured-lesson--clickable"
						onClick={() => onOpenAgendaItem(getLessonAgendaItem({ ...currentLesson, date: '2025-10-14' }))}
						onKeyDown={(event) => {
							if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
								event.preventDefault()
								onOpenAgendaItem(getLessonAgendaItem({ ...currentLesson, date: '2025-10-14' }))
							}
						}}
						role="link"
						tabIndex={0}
					>
						<div className="featured-topline">
							<span>{currentLesson.period ?? 'LEZIONE'}</span>
							<span className="room-pill"><Icon name="room" size={13} />{currentLesson.room}</span>
						</div>
						<h3>{currentLesson.subject}</h3>
						<div className="featured-details">
							<span><Icon name="person" size={16} />{currentLesson.teacher}</span>
							<strong><Icon name="clock" size={16} />{currentLesson.time} – {currentLesson.end}</strong>
						</div>
						<div className="progress-track" role="progressbar" aria-label="Lezione in corso" aria-valuenow="72" aria-valuemin="0" aria-valuemax="100"><span /></div>
					</article>
				) : <p className="agenda-empty-state">Nessuna lezione in corso al momento.</p>}
			</section>

			<section className="schedule-section" aria-labelledby="today-heading">
				<div className="content-section-heading">
					<h2 id="today-heading">Orario di Oggi</h2>
					<div className="schedule-heading-actions">
						<span>{remainingLessonCount} {remainingLessonCount === 1 ? 'ora rimanente' : 'ore rimanenti'}</span>
						<button className="agenda-shortcut" onClick={onNavigateToAgenda} type="button">
							<Icon name="calendar" size={14} />
							Agenda
						</button>
					</div>
				</div>
				<div className="lesson-list">
					{currentLessons.length
						? currentLessons.map((lesson) => <LessonRow key={lesson.time} lesson={lesson} onOpen={() => onOpenAgendaItem(getLessonAgendaItem({ ...lesson, date: '2025-10-14' }))} />)
						: <p className="agenda-empty-state">Nessuna lezione in corso al momento.</p>}
				</div>
			</section>

			<section className="assignments-section" aria-labelledby="assignments-heading">
				<div className="content-section-heading assignments-heading">
					<h2 id="assignments-heading"><Icon name="task" size={17} />Compiti &amp; Verifiche</h2>
					<button className="view-all-button" onClick={onNavigateToAgenda} type="button">
						Vedi tutti <Icon name="chevron" size={15} />
					</button>
				</div>
				<div className="assignment-list">
					{recentAssignments.map((assignment) => (
						<AssignmentCard
							assignment={assignment}
							completed={Boolean(completedTasks[assignment.id])}
							onComplete={() => onComplete(assignment.id)}
							onOpen={() => onOpenAgendaItem(getAssignmentAgendaItem(assignment))}
							onSave={() => onSave(assignment.id)}
							saved={Boolean(savedTasks[assignment.id])}
							key={assignment.id}
						/>
					))}
				</div>
			</section>
		</>
	)
}

export default Home