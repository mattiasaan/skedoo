import { useState } from 'react'
import { AssignmentCard, Icon, LessonRow } from './DashboardShared.jsx'
import { assignments, lessons } from './DashboardData.js'

function Home({ completedTasks, savedTasks, onComplete, onSave }) {
	const [noticeVisible, setNoticeVisible] = useState(true)
	const [showAllAssignments, setShowAllAssignments] = useState(false)
	const shownAssignments = showAllAssignments ? assignments : assignments.slice(0, 2)

	return (
		<>
			<div className="date-heading">
				<p>MARTEDÌ, 14 OTTOBRE</p>
				<span>Liceo Scientifico A. Righi (4ª A)</span>
			</div>

			{noticeVisible && (
				<aside className="schedule-alert" aria-label="Avviso variazione orario">
					<div className="alert-icon"><Icon name="alert" size={19} /></div>
					<div className="alert-copy">
						<div className="alert-meta"><strong>VARIAZIONE ORARIO</strong><span>10 min fa</span></div>
						<p><b>Prof. Rossi assente</b> — Aula 204 spostata in <u>201</u> per il laboratorio di Fisica (3ª ora).</p>
					</div>
					<button aria-label="Chiudi avviso" className="icon-button alert-close" onClick={() => setNoticeVisible(false)} type="button"><Icon name="close" size={16} /></button>
				</aside>
			)}

			<section className="next-lesson-section" aria-labelledby="next-lesson-title">
				<div className="section-kicker-row">
					<h2 id="next-lesson-title"><span className="live-dot" />PROSSIMA LEZIONE</h2>
					<span className="countdown-pill">Inizia tra 15 min</span>
				</div>
				<article className="featured-lesson">
					<div className="featured-topline">
						<span>3ª ORA ACCADEMICA</span>
						<span className="room-pill"><Icon name="room" size={13} />AULA 302</span>
					</div>
					<h3>MATEMATICA</h3>
					<div className="featured-details">
						<span><Icon name="person" size={16} />Prof.ssa Bianchi</span>
						<strong><Icon name="clock" size={16} />10:30 – 11:45</strong>
					</div>
					<div className="lesson-progress-copy"><span>Intervallo in corso</span><span>15 min rimanenti</span></div>
					<div className="progress-track" role="progressbar" aria-label="Intervallo rimanente" aria-valuenow="72" aria-valuemin="0" aria-valuemax="100"><span /></div>
				</article>
			</section>

			<section className="schedule-section" aria-labelledby="today-heading">
				<div className="content-section-heading">
					<h2 id="today-heading">Orario di Oggi</h2>
					<span>5 ore previste</span>
				</div>
				<div className="lesson-list">{lessons.map((lesson) => <LessonRow key={lesson.time} lesson={lesson} />)}</div>
			</section>

			<section className="assignments-section" aria-labelledby="assignments-heading">
				<div className="content-section-heading assignments-heading">
					<h2 id="assignments-heading"><Icon name="task" size={17} />Compiti &amp; Verifiche</h2>
					<button className="view-all-button" onClick={() => setShowAllAssignments((visible) => !visible)} type="button">
						{showAllAssignments ? 'Mostra meno' : 'Vedi tutti'} <Icon name="chevron" size={15} />
					</button>
				</div>
				<div className="assignment-list">
					{shownAssignments.map((assignment) => (
						<AssignmentCard
							assignment={assignment}
							completed={Boolean(completedTasks[assignment.id])}
							onComplete={() => onComplete(assignment.id)}
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