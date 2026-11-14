import { useMemo, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { LineChart } from '../components/LineChart.jsx'
import { ErrorMessage, SectionHeading, Skeleton, StateMessage } from '../components/ui.jsx'
import { useApp } from '../lib/appContext.js'
import { useGrades } from '../lib/data.js'
import { useToast } from '../lib/toast.js'
import { classLabel, formatNumber, formatShortDate, monthName, parseDateKey, schoolYear, teacherShort } from '../lib/format.js'
import {
	averageLabel,
	averageTimeline,
	averageTrendLabel,
	currentTerm,
	generalAverage,
	gradeCounts,
	gradeTone,
	requiredGrade,
	subjectIcon,
	subjectsForTerm,
	termsOf,
} from '../lib/grades.js'

const YEAR = 'year'

function AverageCard({ subjects }) {
	const average = generalAverage(subjects)
	const counts = gradeCounts(subjects)
	const timeline = averageTimeline(subjects)
	const first = timeline[0]
	const middle = timeline[Math.floor((timeline.length - 1) / 2)]
	const last = timeline.at(-1)
	const delta = first && last ? last.value - first.value : null
	const firstMonth = first ? monthName(parseDateKey(first.date)).slice(0, 3) : ''
	const lastMonth = last ? monthName(parseDateKey(last.date)).slice(0, 3) : ''

	return (
		<article className="card average-card">
			<div className="average-card__top">
				<div>
					<p className="card-kicker">Media generale ponderata</p>
					<div className="average-card__value">
						<strong className={`tone-text--${gradeTone(average)}`}>{formatNumber(average)}</strong>
						<span className={`badge badge--pill badge--soft-case ${average != null && average < 6 ? 'badge--danger' : 'badge--accent'}`}>
							{averageTrendLabel(average)} {delta != null && delta >= 0 ? '↗' : delta != null ? '↘' : ''}
						</span>
					</div>
				</div>
				<span className="icon-tile"><Icon name="trend" size={18} /></span>
			</div>

			<dl className="average-card__counts">
				<div><dt>Totale</dt><dd>{counts.total} Voti</dd></div>
				<div><dt>Scritti</dt><dd>{counts.written} Prove</dd></div>
				<div><dt>Orali/Prat.</dt><dd>{counts.oral} Prove</dd></div>
			</dl>

			{timeline.length > 1 ? (
				<>
					<div className="average-card__chart-heading">
						<span>Andamento temporale ({firstMonth} - {lastMonth})</span>
						<strong className={delta < 0 ? 'tone-text--low' : 'tone-text--good'}>{delta >= 0 ? '+' : ''}{delta.toFixed(1)} p.ti</strong>
					</div>
					<LineChart
						label="Andamento della media generale"
						points={timeline.map((point) => ({ key: point.date, value: point.value, title: `${point.value.toFixed(2)} • ${point.date}` }))}
					/>
					<div className="average-card__chart-labels">
						<span>Inizio ({formatNumber(first.value)})</span>
						{timeline.length > 2 && <span>{monthName(parseDateKey(middle.date))} ({formatNumber(middle.value)})</span>}
						<strong>Oggi ({formatNumber(last.value)})</strong>
					</div>
				</>
			) : (
				<p className="card-hint">Il grafico dell'andamento compare dopo le prime valutazioni in giorni diversi.</p>
			)}
		</article>
	)
}

function Simulator({ subjects }) {
	const candidates = subjects.filter((subject) => subject.media != null)
	const lowest = [...candidates].sort((a, b) => a.media - b.media)[0]
	const [subjectName, setSubjectName] = useState(null)
	// obiettivo iniziale raggiungibile: la sufficienza se la materia più debole è sotto il 6
	const [target, setTarget] = useState(() => (lowest && lowest.media < 6 ? 6 : 7))
	const subject = candidates.find((item) => item.materia === subjectName) ?? lowest
	// su telefono parte chiuso: è lungo e non serve a ogni visita
	const [open, setOpen] = useState(() => window.matchMedia?.('(min-width: 600px)').matches ?? true)

	if (!subject) {
		return (
			<article className="card simulator-card">
				<StateMessage icon="chart" text="Il simulatore si attiva quando ci sono voti numerici." title="Simulatore non disponibile" />
			</article>
		)
	}

	const result = requiredGrade(subject, target)
	const needed = String(Number(result.value.toFixed(2)))
	// 2 decimali: con toFixed(1) 6.25 diventava "6.3" e 6.75 "6.8", diverso dal valore usato nel calcolo
	const targetLabel = String(Number(target.toFixed(2)))

	let message
	if (result.value <= 1) {
		message = <>La tua media è {formatNumber(subject.media, 2)}: resti sopra il <b>{targetLabel}</b> qualunque sia il prossimo voto.</>
	} else if (result.value > 10) {
		message = <>Con un solo voto non basta: anche un <b>10</b> lascerebbe la media sotto il <b>{targetLabel}</b>. Servono più prove positive.</>
	} else if (subject.media >= target) {
		message = <>Sei già sopra il <b>{targetLabel}</b>: per restarci ti serve almeno <b className="prediction__value">{needed}</b> nella prossima verifica.</>
	} else {
		message = <>Per raggiungere la media del <b>{targetLabel}</b> devi prendere almeno <b className="prediction__value">{needed}</b> nella prossima verifica!</>
	}

	return (
		<article className={`card simulator-card${open ? '' : ' simulator-card--closed'}`}>
			<button aria-controls="simulator-body" aria-expanded={open} className="simulator-card__heading" onClick={() => setOpen((value) => !value)} type="button">
				<span className="icon-tile"><Icon name="clipboard" size={18} /></span>
				<span>
					<strong className="simulator-card__title">Simulatore Media &amp; Obiettivo</strong>
					<small>{open ? 'Calcolo del prossimo voto necessario' : `${subject.name}: tocca per calcolare il voto necessario`}</small>
				</span>
				<Icon className="simulator-card__chevron" name="chevronDown" size={18} />
			</button>

			{open && <div id="simulator-body">
			<label className="field-label" htmlFor="simulator-subject">Seleziona materia da recuperare / migliorare</label>
			<div className="select-wrap">
				<select id="simulator-subject" onChange={(event) => setSubjectName(event.target.value)} value={subject.materia}>
					{candidates.map((item) => (
						<option key={item.materia} value={item.materia}>
							{item.name} (Media attuale: {formatNumber(item.media, 2)} - {averageLabel(item.media)})
						</option>
					))}
				</select>
				<Icon name="chevronDown" size={18} />
			</div>

			<div className="simulator-card__target">
				<label htmlFor="simulator-target">Media desiderata:</label>
				<output htmlFor="simulator-target">{targetLabel}</output>
			</div>
			<input
				className="range"
				id="simulator-target"
				max="9"
				min="6"
				onChange={(event) => setTarget(Number(event.target.value))}
				step="0.25"
				style={{ '--range-progress': `${((target - 6) / 3) * 100}%` }}
				type="range"
				value={target}
			/>
			<div className="simulator-card__scale"><span>6.0 (Sufficienza minima)</span><span>7.5</span><span>9.0 (Eccellenza)</span></div>

			<div className="prediction">
				<span className="icon-tile icon-tile--accent"><Icon name="flag" size={17} /></span>
				<div>
					<p className="card-kicker card-kicker--accent">Previsione calcolata</p>
					<p className="prediction__text">{message}</p>
					<small>Stima basata su {result.count} {result.count === 1 ? 'voto preesistente' : 'voti preesistenti'} e su un nuovo voto con peso ordinario 100%.</small>
				</div>
			</div>
			</div>}
		</article>
	)
}

function SubjectCard({ subject }) {
	const { openDetail } = useApp()
	const last = subject.voti.find((grade) => !grade.annullato) ?? subject.voti[0]
	const tone = gradeTone(subject.media)

	return (
		<button className={`subject-card subject-card--${tone}`} onClick={() => openDetail({ type: 'subject', name: subject.materia })} type="button">
			<span className="icon-tile"><Icon name={subjectIcon(subject.materia)} size={18} /></span>
			<span className="subject-card__copy">
				<strong>{subject.name}</strong>
				<span>{subject.docenti?.length ? teacherShort(subject.docenti[0]) : `${subject.voti.length} ${subject.voti.length === 1 ? 'voto' : 'voti'}`}</span>
				{last && (
					<small className="subject-card__last">
						Ultimo: <b>{last.voto}</b> ({[last.tipo, formatShortDate(parseDateKey(last.data))].filter(Boolean).join(' - ')})
					</small>
				)}
			</span>
			<span className="subject-card__score">
				<span className={`score-box score-box--${tone}`}>{formatNumber(subject.media)}</span>
				<small>{averageLabel(subject.media)}</small>
			</span>
		</button>
	)
}

function Comparison({ subjects }) {
	const rows = subjects.filter((subject) => subject.media != null)
	if (!rows.length) return null
	return (
		<section className="card comparison-card" aria-labelledby="comparison-heading">
			<h3 id="comparison-heading">Confronto Medie &amp; Soglia 6.0</h3>
			<p className="card-hint">Benchmark sufficienza ministeriale</p>
			<div className="comparison">
				<span className="comparison__threshold" aria-hidden="true" />
				{rows.map((subject) => (
					<div className="comparison__row" key={subject.materia}>
						<div className="comparison__label">
							<span>{subject.name}</span>
							<strong className={`tone-text--${gradeTone(subject.media)}`}>{formatNumber(subject.media)}</strong>
						</div>
						<div className="comparison__track">
							<span className={`comparison__fill comparison__fill--${gradeTone(subject.media)}`} style={{ width: `${Math.min(100, subject.media * 10)}%` }} />
						</div>
					</div>
				))}
			</div>
		</section>
	)
}

function Grades() {
	const { classId } = useApp()
	const toast = useToast()
	const grades = useGrades()

	async function sync() {
		const ok = await grades.reload()
		toast(ok ? 'Voti aggiornati da ClasseViva' : 'Aggiornamento non riuscito, riprova tra poco', { tone: ok ? 'success' : 'error' })
	}
	const terms = termsOf(grades.data)
	const [termChoice, setTermChoice] = useState(null)
	const term = termChoice ?? currentTerm(grades.data) ?? YEAR
	const subjects = useMemo(() => subjectsForTerm(grades.data, term === YEAR ? null : term), [grades.data, term])
	const subtitle = [`Anno Scolastico ${schoolYear()}`, classId ? classLabel(classId) : null].filter(Boolean).join(' • ')

	return (
		<div className="page page--grades">
			<header className="page-header page-header--stacked">
				<div>
					<h1>Valutazioni &amp; Medie</h1>
					<p className="page-header__subtitle">{subtitle}</p>
				</div>
				<button className={`sync-button${grades.refreshing ? ' sync-button--busy' : ''}`} disabled={grades.refreshing} onClick={sync} type="button">
					<Icon name="refresh" size={16} />
					{grades.refreshing ? 'Sincronizzo…' : 'Sincronizza'}
				</button>
			</header>

			<div className="segmented segmented--wide" role="group" aria-label="Periodo">
				{[...terms, { pos: YEAR, label: 'Tutto l\'anno' }].map((item) => (
					<button
						aria-pressed={term === item.pos}
						className={`segmented__button${term === item.pos ? ' segmented__button--active' : ''}`}
						key={item.pos}
						onClick={() => setTermChoice(item.pos)}
						type="button"
					>
						{item.label}
					</button>
				))}
			</div>

			{grades.loading && <Skeleton height={220} lines={2} />}
			{grades.error && !grades.data && <ErrorMessage error={grades.error} onRetry={grades.reload} title="Voti non disponibili" />}

			{grades.data && (subjects.length ? (
				<div className="grades-layout">
					<div className="grades-layout__overview">
						<AverageCard subjects={subjects} />
						<Simulator key={term} subjects={subjects} />
					</div>

					<section className="grades-layout__subjects" aria-labelledby="subjects-heading">
						<SectionHeading aside={<span className="section-heading__note">{subjects.length} {subjects.length === 1 ? 'Materia caricata' : 'Materie caricate'}</span>} id="subjects-heading" title="Dettaglio per Materia" />
						<div className="subject-list">
							{subjects.map((subject) => <SubjectCard key={subject.materia} subject={subject} />)}
						</div>
					</section>

					<Comparison subjects={subjects} />
				</div>
			) : (
				<StateMessage icon="chart" text="In questo periodo non ci sono ancora valutazioni registrate su ClasseViva." title="Nessun voto" />
			))}
		</div>
	)
}

export default Grades
