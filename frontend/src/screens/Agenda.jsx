import { Icon, LessonRow } from './DashboardShared.jsx'
import { lessons } from './DashboardData.js'

function Agenda() {
	return (
		<section className="alternate-view" aria-labelledby="agenda-heading">
			<div className="date-heading"><p>MARTEDÌ, 14 OTTOBRE</p><span>Liceo Scientifico A. Righi (4ª A)</span></div>
			<div className="alternate-title"><h2 id="agenda-heading">Agenda</h2><span>Oggi</span></div>
			<p className="alternate-caption">Le tue lezioni e i prossimi impegni</p>
			<div className="lesson-list agenda-list">{lessons.map((lesson) => <LessonRow key={lesson.time} lesson={lesson} />)}</div>
			<div className="agenda-event"><span className="agenda-event-time">14:30</span><div><strong>Allenamento pallavolo</strong><span>Palestra scolastica</span></div><Icon name="calendar" size={17} /></div>
		</section>
	)
}

export default Agenda