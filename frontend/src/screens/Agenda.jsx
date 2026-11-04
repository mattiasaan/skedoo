import { useState } from 'react'
import { Icon } from './DashboardShared.jsx'
import { getAgendaDateKey, getAgendaItemDate, getAgendaItemsForDate, getLessonsForDate, getRelatedAgendaItem } from './AgendaData.js'
import { getSubjectAgendaItemByName } from './SubjectData.js'

const views = [
	{ id: 'today', label: 'Oggi' },
	{ id: 'week', label: 'Settimana' },
	{ id: 'month', label: 'Mese' },
]

const monthWeekdays = ['DOM', 'LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB']

function getWeekDays(date) {
	const monday = new Date(date)
	monday.setDate(date.getDate() - ((date.getDay() + 6) % 7))

	return Array.from({ length: 6 }, (_, index) => {
		const day = new Date(monday)
		day.setDate(monday.getDate() + index)
		return {
			date: day,
			label: new Intl.DateTimeFormat('it-IT', { weekday: 'short' }).format(day).replace('.', '').slice(0, 3).toUpperCase(),
		}
	})
}

function getMonthDays(date) {
	const firstDay = new Date(date.getFullYear(), date.getMonth(), 1)
	const leadingDays = firstDay.getDay()
	const dayCount = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
	const cellCount = Math.ceil((leadingDays + dayCount) / 7) * 7

	return Array.from({ length: cellCount }, (_, index) => new Date(date.getFullYear(), date.getMonth(), index - leadingDays + 1))
}

function formatSelectedDate(date) {
	const formatted = new Intl.DateTimeFormat('it-IT', { weekday: 'long', day: 'numeric', month: 'long' }).format(date)
	return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

function formatTime(time) {
	return time?.replace(' - ', ' – ') ?? 'Orario da definire'
}

function formatGrade(value) {
	const numericValue = Number(typeof value === 'string' ? value.replace(',', '.') : value)
	return Number.isFinite(numericValue) ? numericValue.toFixed(1).replace('.', ',').replace(',0', '') : value ?? '—'
}

function formatSubjectDate(date) {
	return date ? formatSelectedDate(getAgendaItemDate({ date })) : 'Data non disponibile'
}

function getGradeChartPoints(grades) {
	if (!grades.length) return []

	return grades.map((grade, index) => {
		const value = Number(typeof grade.value === 'string' ? grade.value.replace(',', '.') : grade.value)
		const x = grades.length === 1 ? 304 : 12 + (index / (grades.length - 1)) * 584
		const y = 130 - ((Math.min(10, Math.max(1, value)) - 1) / 9) * 105
		return { ...grade, x, y, value }
	}).filter((grade) => Number.isFinite(grade.value))
}

function SubjectScheduleCard({ item, onOpen }) {
	const isAssignment = item.type === 'task'
	const dateLabel = item.due ?? formatSubjectDate(item.date)

	return (
		<button className={`subject-agenda-card subject-agenda-card--${isAssignment ? 'task' : 'event'}`} onClick={() => onOpen(item)} type="button">
			<span className="subject-agenda-card__icon"><Icon name={isAssignment ? 'task' : 'calendar'} size={17} /></span>
			<span className="subject-agenda-card__content">
				<strong>{item.title}</strong>
				<small>{dateLabel}{item.description ? ` · ${item.description}` : ''}</small>
			</span>
			<Icon name="chevron" size={17} />
		</button>
	)
}

function SubjectDashboard({ item, onOpenItem }) {
	const teachers = item.teachers ?? (item.teacher ? [item.teacher] : [])
	const rooms = item.rooms ?? (item.room ? [item.room] : [])
	const grades = [...(item.grades ?? [])].sort((a, b) => String(a.date ?? '').localeCompare(String(b.date ?? '')))
	const chartPoints = getGradeChartPoints(grades)
	const linePath = chartPoints.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x} ${point.y}`).join(' ')
	const areaPath = chartPoints.length ? `${linePath} L${chartPoints.at(-1).x} 145 L${chartPoints[0].x} 145 Z` : ''
	const recentGrades = [...grades].reverse()

	function openScheduleItem(scheduleItem) {
		onOpenItem({
			...scheduleItem,
			subject: scheduleItem.subject ?? item.title,
			returnItem: item,
			returnView: item.returnView ?? 'Voti',
			returnTab: item.returnTab ?? 'grades',
		})
	}

	return (
		<div className="subject-dashboard">
			<header className="subject-dashboard__header">
				<p className="agenda-kicker">DETTAGLIO MATERIA</p>
				<h1>{item.title}</h1>
				<p>{item.description}</p>
			</header>

			<section className="subject-dashboard-card subject-intro-card" aria-labelledby="subject-intro-heading">
				<div className="subject-dashboard-card__heading">
					<span className="subject-dashboard-card__icon"><Icon name="book" size={18} /></span>
					<div><p className="agenda-kicker">LA TUA MATERIA</p><h2 id="subject-intro-heading">Informazioni</h2></div>
				</div>
				<dl className="subject-info-grid">
					<div><dt>Docenti</dt><dd>{teachers.length ? teachers.join(', ') : 'Non disponibile'}</dd></div>
					<div><dt>Aule</dt><dd>{rooms.length ? rooms.join(', ') : 'Non disponibile'}</dd></div>
					<div><dt>Ore a settimana</dt><dd>{item.weeklyHours != null ? `${item.weeklyHours} ${item.weeklyHours === 1 ? 'ora' : 'ore'}` : 'Non disponibile'}</dd></div>
				</dl>
			</section>

			<section className="subject-dashboard-card subject-progress-card" aria-labelledby="subject-progress-heading">
				<div className="subject-dashboard-card__heading">
					<span className="subject-dashboard-card__icon"><Icon name="chart" size={18} /></span>
					<div><p className="agenda-kicker">IL TUO ANDAMENTO</p><h2 id="subject-progress-heading">Voti e media</h2></div>
				</div>
				<div className="subject-average">
					<span>MEDIA GENERALE</span>
					<strong>{item.average ?? '—'}</strong>
					<small>{grades.length} {grades.length === 1 ? 'valutazione registrata' : 'valutazioni registrate'}</small>
				</div>
				{chartPoints.length > 0 ? (
					<div className="subject-grade-chart-wrap">
						<svg className="subject-grade-chart" viewBox="0 0 608 150" role="img" aria-label={`Andamento dei voti di ${item.title}`}>
							<defs>
								<linearGradient id="subject-grade-fill" x1="0" x2="0" y1="0" y2="1">
									<stop offset="0%" stopColor="#10bd89" stopOpacity=".25" />
									<stop offset="100%" stopColor="#10bd89" stopOpacity="0" />
								</linearGradient>
							</defs>
							<path d="M12 25H596M12 77H596M12 130H596" className="subject-grade-chart__grid" />
							{areaPath && <path d={areaPath} fill="url(#subject-grade-fill)" />}
							{linePath && <path d={linePath} className="subject-grade-chart__line" />}
							{chartPoints.map((point) => <circle key={point.id ?? `${point.date}-${point.x}`} cx={point.x} cy={point.y} r="5" className="subject-grade-chart__point"><title>{`${formatGrade(point.value)} · ${point.date}`}</title></circle>)}
						</svg>
						<div className="subject-grade-chart__labels"><span>1</span><span>6</span><span>10</span></div>
					</div>
				) : <p className="subject-dashboard-empty">Il grafico sarà disponibile quando saranno registrati i voti.</p>}
				<div className="subject-grades-list">
					<h3>Elenco voti</h3>
					{recentGrades.length ? recentGrades.map((grade) => (
						<div className="subject-grade-row" key={grade.id ?? `${grade.date}-${grade.type}`}>
							<span className="subject-grade-row__score">{formatGrade(grade.value)}</span>
							<span className="subject-grade-row__details"><strong>{grade.type ?? 'Valutazione'}{grade.description ? ` · ${grade.description}` : ''}</strong><small>{formatSubjectDate(grade.date)}</small></span>
						</div>
					)) : <p className="subject-dashboard-empty">Non ci sono ancora voti da mostrare.</p>}
				</div>
			</section>

			<section className="subject-dashboard-card" aria-labelledby="subject-tasks-heading">
				<div className="subject-dashboard-card__heading">
					<span className="subject-dashboard-card__icon subject-dashboard-card__icon--blue"><Icon name="task" size={18} /></span>
					<div><p className="agenda-kicker">DA COMPLETARE</p><h2 id="subject-tasks-heading">Compiti</h2></div>
					<span className="subject-section-count">{item.assignments?.length ?? 0}</span>
				</div>
				<div className="subject-agenda-list">
					{item.assignments?.length
						? item.assignments.map((task) => <SubjectScheduleCard item={task} key={task.id} onOpen={openScheduleItem} />)
						: <p className="subject-dashboard-empty">Non ci sono compiti da fare per questa materia.</p>}
				</div>
			</section>

			<section className="subject-dashboard-card" aria-labelledby="subject-events-heading">
				<div className="subject-dashboard-card__heading">
					<span className="subject-dashboard-card__icon subject-dashboard-card__icon--amber"><Icon name="calendar" size={18} /></span>
					<div><p className="agenda-kicker">DATE IMPORTANTI</p><h2 id="subject-events-heading">Verifiche e interrogazioni</h2></div>
					<span className="subject-section-count">{item.events?.length ?? 0}</span>
				</div>
				<div className="subject-agenda-list">
					{item.events?.length
						? item.events.map((event) => <SubjectScheduleCard item={event} key={event.id} onOpen={openScheduleItem} />)
						: <p className="subject-dashboard-empty">Non sono previste verifiche o interrogazioni.</p>}
				</div>
			</section>
		</div>
	)
}

function EventDetail({ item, onBack, onOpenItem }) {
	const isLesson = item.type === 'lesson'
	const isTask = item.type === 'task'
	const isSubject = item.type === 'subject'
	const isGrade = item.type === 'grade'
	const kindLabel = isLesson ? 'LEZIONE' : isTask ? 'COMPITO' : isSubject ? 'MATERIA' : isGrade ? 'VALUTAZIONE' : 'EVENTO'
	const date = getAgendaItemDate(item)
	const relatedItem = isLesson ? getRelatedAgendaItem(item) : null

	if (isSubject) {
		return (
			<section className="agenda-detail subject-detail" aria-label={`Dettaglio materia ${item.title}`}>
				<button className="agenda-back-button" onClick={() => onBack(null, item)} type="button">
					<Icon name="arrow" size={17} />
					Torna a {item.returnItem?.title ?? item.returnView ?? 'Voti'}
				</button>
				<SubjectDashboard item={item} onOpenItem={onOpenItem} />
			</section>
		)
	}

	return (
		<section className="agenda-detail" aria-labelledby="agenda-detail-heading">
			<button className="agenda-back-button" onClick={() => onBack(null, item)} type="button">
				<Icon name="arrow" size={17} />
				Torna a {item.returnItem?.title ?? item.returnView ?? (isLesson ? 'Oggi' : 'Agenda')}
			</button>
			<article className={`agenda-detail-card agenda-detail-card--${item.tone ?? (isLesson || isSubject ? 'green' : 'blue')}`}>
				<div className="agenda-detail-meta">
					<span className={`assignment-kind${isTask ? ' assignment-kind--homework' : ' assignment-kind--test'}`}>{kindLabel}</span>
					<span><Icon name="calendar" size={15} />{formatSelectedDate(date)}</span>
				</div>
				{item.time && <p className="agenda-detail-time"><Icon name="clock" size={16} />{formatTime(item.time)}</p>}
				<h2 id="agenda-detail-heading">{item.title}</h2>
				{item.subject && <p className="agenda-detail-subject">{item.subject}</p>}
				<p className="agenda-detail-description">{item.description}</p>
				{isGrade && (
					<div className={`detail-grade-card detail-grade-card--${item.tone}`}>
						<span>VOTO</span>
						<strong>{item.grade}</strong>
						<small>{item.gradeType} · {item.teacher}</small>
					</div>
				)}
				<dl className="agenda-detail-facts">
					{item.teacher && <div><dt>Docente</dt><dd>{item.teacher}</dd></div>}
					{item.room && <div><dt>Aula</dt><dd>{item.room}</dd></div>}
					{item.due && <div><dt>Scadenza</dt><dd>{item.due}</dd></div>}
					{item.period && <div><dt>Ora</dt><dd>{item.period}</dd></div>}
					{item.gradeDate && <div><dt>Data valutazione</dt><dd>{item.gradeDate}</dd></div>}
				</dl>
					{!isSubject && item.subject && (
						<button
							className="agenda-related-link"
							onClick={() => onOpenItem({
								...getSubjectAgendaItemByName(item.subject, item),
								returnItem: item,
								returnView: item.returnView ?? 'Agenda',
								returnTab: 'agenda',
							})}
							type="button"
						>
							<Icon name="book" size={16} />
							<span>Apri materia<strong>{item.subject}</strong></span>
							<Icon name="chevron" size={17} />
						</button>
					)}
					{relatedItem && (
					<button className="agenda-related-link" onClick={() => onBack({ ...relatedItem, returnView: item.returnView })} type="button">
						<Icon name="task" size={16} />
						<span>{relatedItem.type === 'event' ? 'Apri evento collegato' : 'Apri compito collegato'}<strong>{relatedItem.title}</strong></span>
						<Icon name="chevron" size={17} />
					</button>
				)}
			</article>
		</section>
	)
}

function AgendaItemCard({ item, onOpen, isComplete }) {
	const typeLabel = item.type === 'lesson' ? item.period : item.type === 'task' ? 'COMPITO' : item.type === 'grade' ? 'VOTO' : 'EVENTO'
	const time = item.time ? formatTime(item.time) : item.due

	return (
		<button className={`agenda-item-card agenda-item-card--${item.tone ?? 'neutral'}${isComplete ? ' agenda-item-card--complete' : ''}`} onClick={() => onOpen(item)} type="button">
			<span className="agenda-item-card__time">{time}</span>
			<span className="agenda-item-card__copy">
				<strong>{item.title}</strong>
				<small>{typeLabel}{item.teacher ? ` · ${item.teacher}` : ''}</small>
			</span>
			<Icon name="chevron" size={17} />
		</button>
	)
}

function Agenda({ selectedItem, onOpenItem, onClearItem }) {
	const [view, setView] = useState('today')
	const [selectedDate, setSelectedDate] = useState(new Date(2025, 9, 14))
	const weekDays = getWeekDays(selectedDate)
	const monthDays = getMonthDays(selectedDate)
	const formattedMonth = new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric' }).format(selectedDate)
	const monthLabel = formattedMonth.charAt(0).toUpperCase() + formattedMonth.slice(1)
	const selectedDayItems = getAgendaItemsForDate(selectedDate)
	const scheduledLessons = getLessonsForDate(selectedDate)
	const hasItems = (date) => getAgendaItemsForDate(date).some((item) => item.type !== 'lesson')
	const isItemComplete = (item) => item.status === 'complete' || item.date < getAgendaDateKey(selectedDate)

	function changeMonth(offset) {
		setSelectedDate((date) => new Date(date.getFullYear(), date.getMonth() + offset, 1))
	}

	function showItem(item) {
		onOpenItem({ ...item, returnView: views.find((itemView) => itemView.id === view)?.label ?? 'Programma' })
	}

	if (selectedItem) {
		return <EventDetail item={selectedItem} onBack={(relatedItem, sourceItem) => {
			if (relatedItem) {
				onOpenItem(relatedItem)
			} else if (sourceItem?.returnItem) {
				onOpenItem(sourceItem.returnItem)
			} else {
				onClearItem(sourceItem ?? selectedItem)
			}
		}} onOpenItem={onOpenItem} />
	}

	return (
		<section className="alternate-view" aria-labelledby="agenda-heading">
			<div className="agenda-header">
				<div>
					<p className="agenda-kicker">{view === 'today' ? 'ORARIO SCOLASTICO' : 'ORARIO E AGENDA'}</p>
					<h2 id="agenda-heading">{view === 'today' ? 'Oggi' : 'Orario &amp; Agenda'}</h2>
				</div>
				<div className="agenda-view-toggle" aria-label="Modalità vista agenda">
					{views.map((item) => (
						<button
							aria-pressed={view === item.id}
							type="button"
							key={item.id}
							className={`agenda-view-toggle__button${view === item.id ? ' agenda-view-toggle__button--active' : ''}`}
							onClick={() => setView(item.id)}
						>
							{item.label}
						</button>
					))}
				</div>
			</div>

			{view !== 'month' && (
				<>
					{view === 'week' && <div className="agenda-date-line"><Icon name="calendar" size={17} /><strong>{monthLabel}</strong><i />Trimestre 1</div>}
					{view === 'week' && (
						<div className="week-days" aria-label="Giorni della settimana">
							{weekDays.map((day) => (
								<button
									aria-pressed={day.date.toDateString() === selectedDate.toDateString()}
									type="button"
									key={day.date.toISOString()}
									className={`week-day${day.date.toDateString() === selectedDate.toDateString() ? ' week-day--active' : ''}`}
									onClick={() => setSelectedDate(day.date)}
								>
									<span>{day.label}</span>
									<strong>{day.date.getDate()}</strong>
									{hasItems(day.date) && <i aria-hidden="true" />}
								</button>
							))}
						</div>
					)}
				</>
			)}

			{view === 'today' && (
				<>
					<h3 className="agenda-day-heading">{formatSelectedDate(selectedDate)}</h3>
					{scheduledLessons.length ? (
						<div className="agenda-list">
							{scheduledLessons.map((lesson) => {
								const relatedItem = getRelatedAgendaItem(lesson)
								const isComplete = lesson.status === 'complete'
								const lessonItem = { ...lesson, type: 'lesson', returnView: 'Oggi' }
								return (
									<article
										key={lesson.id}
										className={`agenda-entry agenda-entry--accent-${lesson.tone}${isComplete ? ' agenda-entry--complete' : lesson.status === 'current' ? ' agenda-entry--current' : ''}`}
										onClick={() => showItem(lessonItem)}
										onKeyDown={(event) => {
											if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
												event.preventDefault()
												showItem(lessonItem)
											}
										}}
										role="link"
										tabIndex={0}
									>
										<div className="agenda-entry__header">
											<div className="agenda-entry__time-block"><span>{lesson.time}</span><small>{lesson.period}</small></div>
											<span className="agenda-entry__room">{lesson.room}</span>
										</div>
										<h3>{lesson.subject}</h3>
										<p className="agenda-entry__teacher">{lesson.teacher}</p>
										{relatedItem && (
											<button className={`agenda-entry__note agenda-entry__note--${lesson.tone}`} onClick={(event) => { event.stopPropagation(); showItem(relatedItem) }} type="button">
												<Icon name={relatedItem.type === 'event' ? 'alert' : 'task'} size={15} />
												<span>{lesson.note}</span>
												<Icon name="chevron" size={16} />
											</button>
										)}
									</article>
								)
							})}
						</div>
					) : <p className="agenda-empty-state">Nessuna lezione in programma per questa giornata.</p>}
				</>
			)}

			{view === 'week' && (
				<>
					<div className="agenda-summary">
						<span className="agenda-summary__dot" aria-hidden="true" />
						<strong>{formatSelectedDate(selectedDate)}</strong>
						<span>{selectedDayItems.length} elementi</span>
					</div>
					<div className="agenda-items-list">
						{selectedDayItems.length
							? selectedDayItems.map((item) => <AgendaItemCard item={item} isComplete={isItemComplete(item)} key={item.id} onOpen={showItem} />)
							: <p className="agenda-empty-state">Nessun evento o compito in programma per questa giornata.</p>}
					</div>
				</>
			)}

			{view === 'month' && (
				<>
					<div className="calendar-month-wrapper">
						<div className="calendar-month-header">
							<h3>{monthLabel}</h3>
							<div className="calendar-nav" aria-label="Naviga mese">
								<button type="button" aria-label="Mese precedente" onClick={() => changeMonth(-1)}>‹</button>
								<button type="button" aria-label="Mese successivo" onClick={() => changeMonth(1)}>›</button>
							</div>
						</div>

						<div className="calendar-weekdays" aria-label="Settimana del mese">
							{monthWeekdays.map((day) => <span key={day}>{day}</span>)}
						</div>

						<div className="month-calendar" aria-label="Calendario mensile">
							{monthDays.map((day) => (
								<button
									aria-label={formatSelectedDate(day)}
									aria-pressed={day.toDateString() === selectedDate.toDateString()}
									type="button"
									key={day.toISOString()}
									className={`month-day${day.getMonth() !== selectedDate.getMonth() ? ' month-day--muted' : ''}${day.toDateString() === selectedDate.toDateString() ? ' month-day--active' : ''}`}
									onClick={() => setSelectedDate(day)}
								>
									<span>{day.getDate()}</span>
									{hasItems(day) && <i aria-hidden="true" />}
								</button>
							))}
						</div>
					</div>

					<div className="calendar-legend">
						<span><i className="legend-dot legend-dot--tests" aria-hidden="true" />Lezioni</span>
						<span><i className="legend-dot legend-dot--deadlines" aria-hidden="true" />Compiti</span>
						<span><i className="legend-dot legend-dot--holidays" aria-hidden="true" />Eventi</span>
					</div>

					<div className="agenda-month-items">
						<div className="agenda-summary"><span className="agenda-summary__dot" aria-hidden="true" /><strong>{formatSelectedDate(selectedDate)}</strong><span>{selectedDayItems.length} elementi</span></div>
						<div className="agenda-items-list">
							{selectedDayItems.length
								? selectedDayItems.map((item) => <AgendaItemCard item={item} isComplete={isItemComplete(item)} key={item.id} onOpen={showItem} />)
								: <p className="agenda-empty-state">Nessun evento o compito in programma per questa giornata.</p>}
						</div>
					</div>
				</>
			)}
		</section>
	)
}

export default Agenda
