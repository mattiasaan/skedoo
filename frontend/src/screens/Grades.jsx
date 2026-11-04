import { useState } from 'react'
import { Icon } from './DashboardShared.jsx'
import { getSubjectAgendaItem, subjects } from './SubjectData.js'

const terms = [
	{ id: 'first', label: '1° Quadrimestre', average: '7,8', change: '+0,7 p.ti' },
	{ id: 'second', label: '2° Quadrimestre', average: '—', change: 'In attesa dei voti' },
	{ id: 'year', label: 'Tutto l’anno', average: '7,8', change: '+0,7 p.ti' },
]

function getGradeAgendaItem(subject) {
	return {
		type: 'grade',
		id: `grade-${subject.name.toLowerCase()}`,
		date: '2025-10-14',
		returnView: 'Voti',
		returnTab: 'grades',
		title: `Voto di ${subject.name}`,
		subject: subject.name,
		teacher: subject.teacher,
		grade: subject.average,
		gradeDate: 'Ultima valutazione',
		gradeType: subject.type,
		previous: subject.previous,
		tone: subject.tone,
		description: `Valutazione più recente di ${subject.name}.`,
	}
}

function Grades({ onOpenItem }) {
	const [termId, setTermId] = useState('first')
	const [subjectName, setSubjectName] = useState('Fisica')
	const [targetAverage, setTargetAverage] = useState(7)
	const [notice, setNotice] = useState('')
	const selectedTerm = terms.find((term) => term.id === termId) ?? terms[0]
	const selectedSubject = subjects.find((subject) => subject.name === subjectName) ?? subjects[0]
	const requiredMark = Math.ceil((targetAverage * 2 - Number(selectedSubject.average.replace(',', '.'))) * 2) / 2
	const canReachTarget = requiredMark <= 10
	const hasTermGrades = termId !== 'second'

	return (
		<section className="alternate-view grades-view" aria-labelledby="grades-heading">
			<div className="grades-page-heading">
				<div>
					<p className="agenda-kicker">ANNO SCOLASTICO 2024/2025 · 4° SCIENTIFICO</p>
					<h2 id="grades-heading">Valutazioni &amp; Medie</h2>
				</div>
				<button className="grades-sync" onClick={() => setNotice('La sincronizzazione richiede il collegamento al registro.')} type="button">
					<Icon name="trend" size={15} />
					Sincronizza
				</button>
			</div>
			{notice && <p className="grades-notice" role="status">{notice}</p>}

			<div className="term-tabs" aria-label="Periodo scolastico">
				{terms.map((term) => (
					<button
						aria-pressed={termId === term.id}
						className={`term-tab${termId === term.id ? ' term-tab--active' : ''}`}
						key={term.id}
						onClick={() => setTermId(term.id)}
						type="button"
					>
						{term.label}
					</button>
				))}
			</div>

			<div className="grades-overview">
				<article className="average-card">
					<div className="grades-card-heading">
						<span>MEDIA GENERALE PONDERATA</span>
						<span className="grades-trend-icon"><Icon name="trend" size={17} /></span>
					</div>
					<div className="average-value-row">
						<strong>{selectedTerm.average}</strong>
						<span className="average-status">Ottimo andamento</span>
					</div>
					<div className="grade-counts">
						<span><small>Totale</small><strong>14 Voti</strong></span>
						<span><small>Scritto</small><strong>8 Prove</strong></span>
						<span><small>Orali/Prat.</small><strong>6 Prove</strong></span>
					</div>
					<div className="grade-chart-heading">
						<span>Andamento temporale (Set - Nov)</span>
						<strong>{selectedTerm.change}</strong>
					</div>
					<svg className="grade-chart" viewBox="0 0 640 150" role="img" aria-label="Grafico della media in crescita da settembre a oggi">
						<defs>
							<linearGradient id="grade-chart-fill" x1="0" x2="0" y1="0" y2="1">
								<stop offset="0%" stopColor="#10bd89" stopOpacity=".24" />
								<stop offset="100%" stopColor="#10bd89" stopOpacity="0" />
							</linearGradient>
						</defs>
						<path d="M12 105 L85 101 L158 96 L231 105 L304 81 L377 69 L450 61 L523 45 L596 19 L596 145 L12 145 Z" fill="url(#grade-chart-fill)" />
						<path d="M12 105 L85 101 L158 96 L231 105 L304 81 L377 69 L450 61 L523 45 L596 19" fill="none" stroke="#20d9a2" strokeWidth="3" />
						{[[12, 105], [85, 101], [158, 96], [231, 105], [304, 81], [377, 69], [450, 61], [523, 45], [596, 19]].map(([x, y]) => (
							<circle cx={x} cy={y} fill="#101a1d" key={`${x}-${y}`} r="5" stroke="#20d9a2" strokeWidth="2" />
						))}
						<circle cx="596" cy="19" r="7" fill="#20d9a2" stroke="#effff9" strokeWidth="3" />
					</svg>
					<div className="grade-chart-labels"><span>Inizio (7,1)</span><span>Ottobre (7,4)</span><strong>Oggi (7,8)</strong></div>
				</article>

				{hasTermGrades ? <article className="simulator-card">
					<div className="simulator-heading">
						<span className="simulator-icon"><Icon name="chart" size={17} /></span>
						<div><h3>Simulatore Media &amp; Obiettivo</h3><p>Una stima del prossimo voto necessario</p></div>
					</div>
					<label className="simulator-label" htmlFor="simulator-subject">Seleziona materia da recuperare / migliorare</label>
					<select id="simulator-subject" value={subjectName} onChange={(event) => setSubjectName(event.target.value)}>
						{subjects.map((subject) => <option key={subject.name} value={subject.name}>{subject.name} (media attuale: {subject.average})</option>)}
					</select>
					<div className="target-row"><label htmlFor="target-average">Media desiderata</label><output htmlFor="target-average">{targetAverage.toFixed(1).replace('.', ',')}</output></div>
					<input
						aria-label="Media desiderata"
						className="target-slider"
						id="target-average"
						max="9"
						min="6"
						onChange={(event) => setTargetAverage(Number(event.target.value))}
						step="0.5"
						type="range"
						value={targetAverage}
					/>
					<div className="slider-labels"><span>6,0 · Sufficienza minima</span><span>9,0 · Eccellenza</span></div>
					<div className="prediction-card">
						<span className="prediction-icon"><Icon name="flag" size={16} /></span>
						<div>
							<strong>Previsione calcolata</strong>
							<p>{canReachTarget
								? `Per raggiungere la media ${targetAverage.toFixed(1).replace('.', ',')} in ${selectedSubject.name}, punta ad almeno ${requiredMark.toFixed(1).replace('.', ',')} nel prossimo voto.`
								: `Per raggiungere la media ${targetAverage.toFixed(1).replace('.', ',')} in ${selectedSubject.name}, servirebbe un voto superiore a 10.`}</p>
							<small>Stima indicativa basata sulla media attuale.</small>
						</div>
					</div>
				</article> : (
					<article className="simulator-card simulator-empty">
						<span className="simulator-icon"><Icon name="chart" size={17} /></span>
						<h3>Simulatore non disponibile</h3>
						<p>I voti del secondo quadrimestre non sono ancora stati caricati.</p>
					</article>
				)}
			</div>

			<section className="subject-grades" aria-labelledby="subject-grades-heading">
				<div className="content-section-heading">
					<h3 id="subject-grades-heading">Dettaglio per Materia</h3>
					<span>{hasTermGrades ? '4 materie caricate' : '0 voti'}</span>
				</div>
				{hasTermGrades ? (
					<div className="subject-grade-list">
						{subjects.map((subject) => (
							<article
								className={`subject-grade subject-grade--${subject.tone}`}
								key={subject.name}
								onClick={() => onOpenItem(getSubjectAgendaItem(subject))}
								onKeyDown={(event) => {
									if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
										event.preventDefault()
										onOpenItem(getSubjectAgendaItem(subject))
									}
								}}
								role="link"
								tabIndex={0}
							>
								<span className="subject-grade-icon"><Icon name={subject.icon} size={17} /></span>
								<div className="subject-grade-copy">
									<strong>{subject.name}</strong>
									<span>{subject.teacher}</span>
									<small>Ultimo: <b>{subject.previous}</b> ({subject.type})</small>
								</div>
								<div className="subject-grade-score">
									<button
										aria-label={`Apri voto ${subject.average} di ${subject.name}`}
										onClick={(event) => {
											event.stopPropagation()
											onOpenItem(getGradeAgendaItem(subject))
										}}
										type="button"
									>{subject.average}</button>
									<span>{subject.tone === 'low' ? 'Insufficiente' : 'Ottimo'}</span>
								</div>
							</article>
						))}
					</div>
				) : <p className="grades-empty-state">I voti del secondo quadrimestre non sono ancora disponibili.</p>}
			</section>

			<section className="comparison-card" aria-labelledby="comparison-heading">
				<div className="comparison-heading"><div><h3 id="comparison-heading">Confronto Medie &amp; Soglia 6,0</h3><p>Benchmark di sufficienza ministeriale</p></div><span>Media</span></div>
				{hasTermGrades
					? subjects.map((subject) => (
						<div className="comparison-row" key={subject.name}>
							<span>{subject.name}</span>
							<div className="comparison-track"><i className={`comparison-fill comparison-fill--${subject.tone}`} style={{ width: `${Number(subject.average.replace(',', '.')) * 10}%` }} /></div>
							<strong>{subject.average}</strong>
						</div>
					))
					: <p className="grades-empty-state">Nessun dato da confrontare.</p>}
			</section>
		</section>
	)
}

export default Grades
