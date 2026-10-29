import { Icon } from './DashboardShared.jsx'

const grades = [
	{ subject: 'Matematica', teacher: 'Prof.ssa Bianchi', grade: '8', tone: 'good' },
	{ subject: 'Fisica', teacher: 'Prof. Rossi', grade: '7½', tone: 'good' },
	{ subject: 'Italiano', teacher: 'Prof.ssa Verdi', grade: '6½', tone: 'average' },
	{ subject: 'Inglese', teacher: 'Prof. Smith', grade: '9', tone: 'excellent' },
	{ subject: 'Storia dell’arte', teacher: 'Prof. Conti', grade: '8½', tone: 'good' },
]

function Grades() {
	return (
		<section className="alternate-view" aria-labelledby="grades-heading">
			<div className="date-heading"><p>ANNO SCOLASTICO 2024/2025</p><span>Liceo Scientifico A. Righi (4ª A)</span></div>
			<div className="alternate-title"><h2 id="grades-heading">I tuoi Voti</h2><Icon name="trend" size={19} /></div>
			<article className="average-card"><span>MEDIA GENERALE</span><strong>7,8</strong><div><Icon name="chart" size={15} /> In linea con il trimestre scorso</div></article>
			<h3 className="list-subheading">Valutazioni recenti</h3>
			<div className="grades-list">{grades.map((grade) => <article className="grade-row" key={grade.subject}><div><strong>{grade.subject}</strong><span>{grade.teacher}</span></div><b className={`grade-value grade-value--${grade.tone}`}>{grade.grade}</b></article>)}</div>
		</section>
	)
}

export default Grades