import { useMemo, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { ErrorMessage, Skeleton, StateMessage } from '../components/ui.jsx'
import { clickableProps } from '../lib/a11y.js'
import { useApp } from '../lib/appContext.js'
import { useChanges, useMonthAgenda, useSchedule } from '../lib/data.js'
import { addDays, dateKey, formatLongDate, isSameDay, monthName, schoolYear, startOfWeek, teacherName, teacherShort, weekdayShort } from '../lib/format.js'
import { buildDayLessons, periodLabel, subjectMatches } from '../lib/schedule.js'

const VIEWS = [
	{ id: 'week', label: 'Settimana' },
	{ id: 'month', label: 'Mese' },
]
const MONTH_WEEKDAYS = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM']
const TONE_ORDER = ['danger', 'blue', 'amber', 'neutral']

function initialDate() {
	const today = new Date()
	// la domenica non c'è scuola: si apre direttamente il lunedì
	return today.getDay() === 0 ? addDays(today, 1) : today
}

function lessonTone(lesson, related) {
	if (lesson.cancelled) return 'muted'
	if (lesson.roomChange) return 'amber'
	if (related.some((item) => item.kind === 'verifica')) return 'danger'
	if (related.some((item) => item.kind === 'compito')) return 'blue'
	return 'green'
}

function AgendaLessonCard({ lesson, related }) {
	const { openDetail } = useApp()
	const tone = lessonTone(lesson, related)
	const teacher = lesson.teachers[0]

	return (
		<article className={`agenda-lesson agenda-lesson--${tone}`} {...clickableProps(() => openDetail({ type: 'lesson', lesson }))}>
			<div className="agenda-lesson__top">
				<span className="agenda-lesson__time">
					<strong>{lesson.inizio} - {lesson.fine}</strong>
					{periodLabel(lesson) && <><i aria-hidden="true">•</i>{periodLabel(lesson)}</>}
				</span>
				{lesson.cancelled ? (
					<span className="badge badge--danger">{lesson.cancelled}</span>
				) : lesson.roomChange ? (
					<span className="badge badge--amber"><Icon name="swap" size={13} />Cambio aula / {lesson.roomChange}</span>
				) : lesson.room ? (
					<span className="agenda-lesson__room">{lesson.room}</span>
				) : null}
			</div>
			<div className="agenda-lesson__main">
				<h3>{lesson.materia}</h3>
				{teacher && <span>{teacherShort(teacher)}</span>}
			</div>
			{lesson.roomChange && <p className="agenda-lesson__where">{lesson.roomChange}</p>}
			{related.map((item) => (
				<button
					className={`agenda-note agenda-note--${item.tone}`}
					key={item.key}
					onClick={(event) => {
						event.stopPropagation()
						openDetail({ type: 'event', item })
					}}
					type="button"
				>
					<Icon name={item.kind === 'compito' ? 'clipboard' : 'calendar'} size={16} />
					<span><b>{item.label}:</b> {item.description || item.title}</span>
					<Icon name="chevron" size={16} />
				</button>
			))}
		</article>
	)
}

function AgendaItemCard({ item }) {
	const { openDetail, doneTasks } = useApp()
	const time = item.tutto_il_giorno || !item.ora_inizio ? 'Tutto il giorno' : `${item.ora_inizio}${item.ora_fine ? ` - ${item.ora_fine}` : ''}`

	return (
		<button className={`agenda-item agenda-item--${item.tone}${doneTasks[item.key] ? ' agenda-item--done' : ''}`} onClick={() => openDetail({ type: 'event', item })} type="button">
			<span className="agenda-item__top">
				<span className={`badge badge--${item.tone}`}>{item.label}</span>
				<span>{time}</span>
			</span>
			<strong>{item.title}</strong>
			{item.description && <span className="agenda-item__text">{item.description}</span>}
			{item.autore && <small>{teacherName(item.autore)}</small>}
		</button>
	)
}

function DayView({ date, lessons, items, agenda, isGalilei }) {
	const matched = new Set()
	const lessonCards = lessons.map((lesson) => {
		const related = items.filter((item) => item.kind !== 'annotazione' && subjectMatches(lesson.materia, item.subject))
		related.forEach((item) => matched.add(item.key))
		return { lesson, related }
	})
	const others = items.filter((item) => !matched.has(item.key))
	const hours = lessons.filter((lesson) => !lesson.cancelled).reduce((sum, lesson) => sum + lesson.ore.length, 0)
	const pill = isGalilei && lessons.length
		? `${hours} ${hours === 1 ? 'ora' : 'ore'} di lezione`
		: `${items.length} ${items.length === 1 ? 'impegno' : 'impegni'}`

	return (
		<section className="day-view" aria-labelledby="day-heading">
			<div className="day-view__heading">
				<h3 id="day-heading"><span className="live-dot" aria-hidden="true" />{formatLongDate(date)}</h3>
				<span className="day-view__pill">{pill}</span>
			</div>

			{lessonCards.length > 0 && (
				<div className="agenda-list">
					{lessonCards.map(({ lesson, related }) => <AgendaLessonCard key={lesson.id} lesson={lesson} related={related} />)}
				</div>
			)}

			{agenda.loading && <Skeleton height={86} lines={2} />}
			{agenda.error && !agenda.data && (
				<ErrorMessage
					error={agenda.error}
					onRetry={agenda.reload}
					title={agenda.error.code === 'date_out_of_range' ? 'Fuori dall\'anno scolastico' : 'Agenda non disponibile'}
				/>
			)}

			{others.length > 0 && (
				<>
					{lessonCards.length > 0 && <h4 className="day-view__subheading">Altri impegni</h4>}
					<div className="agenda-list">
						{others.map((item) => <AgendaItemCard item={item} key={item.key} />)}
					</div>
				</>
			)}

			{!lessonCards.length && !others.length && agenda.data && (
				<StateMessage
					icon="calendar"
					text={isGalilei ? 'Nessuna lezione né impegno in agenda per questa giornata.' : 'Nessun compito, verifica o evento in agenda per questa giornata.'}
					title="Giornata libera"
				/>
			)}
		</section>
	)
}

function Agenda() {
	const { classId, isGalilei } = useApp()
	const [view, setView] = useState('week')
	const [selected, setSelected] = useState(initialDate)
	const agenda = useMonthAgenda(selected)
	const schedule = useSchedule(classId)
	const changes = useChanges(classId)
	const today = new Date()

	const itemsByDay = useMemo(() => {
		const map = new Map()
		for (const item of agenda.items) {
			if (!map.has(item.date)) map.set(item.date, [])
			map.get(item.date).push(item)
		}
		return map
	}, [agenda.items])

	const dotsFor = (date) => {
		const key = dateKey(date)
		const tones = new Set((itemsByDay.get(key) ?? []).map((item) => item.tone))
		if ((changes.data ?? []).some((change) => change.data === key)) tones.add('amber')
		return TONE_ORDER.filter((tone) => tones.has(tone)).slice(0, 3)
	}

	const selectedKey = dateKey(selected)
	const dayLessons = useMemo(() => buildDayLessons(schedule.data, selected, changes.data ?? []), [schedule.data, selected, changes.data])
	const dayItems = itemsByDay.get(selectedKey) ?? []

	const weekStart = startOfWeek(selected)
	const weekDays = Array.from({ length: 6 }, (_, index) => addDays(weekStart, index))
	const monthCells = useMemo(() => {
		const start = startOfWeek(new Date(selected.getFullYear(), selected.getMonth(), 1, 12))
		const lastDay = new Date(selected.getFullYear(), selected.getMonth() + 1, 0, 12)
		const end = addDays(startOfWeek(lastDay), 6)
		const cells = []
		for (let day = start; day <= end; day = addDays(day, 1)) cells.push(day)
		return cells
	}, [selected])

	function shiftWeek(offset) {
		setSelected((date) => addDays(date, offset * 7))
	}

	function shiftMonth(offset) {
		setSelected((date) => {
			const target = new Date(date.getFullYear(), date.getMonth() + offset, 1, 12)
			return target.getMonth() === today.getMonth() && target.getFullYear() === today.getFullYear() ? new Date() : target
		})
	}

	const monthLabel = `${monthName(selected)} ${selected.getFullYear()}`

	return (
		<div className="page page--agenda">
			<header className="page-header">
				<h1>Orario &amp; Agenda</h1>
				<div className="segmented" role="group" aria-label="Vista">
					{VIEWS.map((item) => (
						<button
							aria-pressed={view === item.id}
							className={`segmented__button${view === item.id ? ' segmented__button--active' : ''}`}
							key={item.id}
							onClick={() => setView(item.id)}
							type="button"
						>
							{item.label}
						</button>
					))}
				</div>
			</header>

			<div className="agenda-toolbar">
				<p className="agenda-toolbar__date">
					<Icon name="calendar" size={18} />
					<strong>{monthLabel}</strong>
					<i aria-hidden="true" className="agenda-toolbar__year">•</i>
					<span className="agenda-toolbar__year">A.S. {schoolYear(selected)}</span>
				</p>
				<div className="agenda-toolbar__nav">
					{!isSameDay(selected, today) && (
						<button className="chip-button" onClick={() => setSelected(new Date())} type="button">Oggi</button>
					)}
					<button aria-label={view === 'week' ? 'Settimana precedente' : 'Mese precedente'} className="icon-button icon-button--small" onClick={() => (view === 'week' ? shiftWeek(-1) : shiftMonth(-1))} type="button">
						<Icon name="chevronLeft" size={17} />
					</button>
					<button aria-label={view === 'week' ? 'Settimana successiva' : 'Mese successivo'} className="icon-button icon-button--small" onClick={() => (view === 'week' ? shiftWeek(1) : shiftMonth(1))} type="button">
						<Icon name="chevron" size={17} />
					</button>
				</div>
			</div>

			<div className={`agenda-layout agenda-layout--${view}`}>
				{view === 'week' ? (
					<div className="week-strip" role="group" aria-label="Giorni della settimana">
						{weekDays.map((day) => {
							const active = isSameDay(day, selected)
							return (
								<button
									aria-label={formatLongDate(day)}
									aria-pressed={active}
									className={`week-day${active ? ' week-day--active' : ''}${isSameDay(day, today) ? ' week-day--today' : ''}`}
									key={dateKey(day)}
									onClick={() => setSelected(day)}
									type="button"
								>
									<span>{weekdayShort(day)}</span>
									<strong>{day.getDate()}</strong>
									<span className="dots" aria-hidden="true">
										{dotsFor(day).map((tone) => <i className={`dot dot--${tone}`} key={tone} />)}
									</span>
								</button>
							)
						})}
					</div>
				) : (
					<div className="month-card">
						<div className="month-grid month-grid--labels" aria-hidden="true">
							{MONTH_WEEKDAYS.map((label) => <span key={label}>{label}</span>)}
						</div>
						<div className="month-grid" role="group" aria-label={monthLabel}>
							{monthCells.map((day) => {
								const active = isSameDay(day, selected)
								const outside = day.getMonth() !== selected.getMonth()
								return (
									<button
										aria-label={formatLongDate(day)}
										aria-pressed={active}
										className={`month-day${active ? ' month-day--active' : ''}${outside ? ' month-day--outside' : ''}${isSameDay(day, today) ? ' month-day--today' : ''}`}
										key={dateKey(day)}
										onClick={() => setSelected(day)}
										type="button"
									>
										<span>{day.getDate()}</span>
										<span className="dots" aria-hidden="true">
											{dotsFor(day).map((tone) => <i className={`dot dot--${tone}`} key={tone} />)}
										</span>
									</button>
								)
							})}
						</div>
						<div className="month-legend" aria-hidden="true">
							<span><i className="dot dot--danger" />Verifiche</span>
							<span><i className="dot dot--blue" />Compiti</span>
							<span><i className="dot dot--amber" />Eventi e variazioni</span>
						</div>
					</div>
				)}

				{schedule.error && !schedule.data && <ErrorMessage error={schedule.error} onRetry={schedule.reload} title="Orario non disponibile" />}
				<DayView agenda={agenda} date={selected} isGalilei={isGalilei} items={dayItems} lessons={dayLessons} />
			</div>
		</div>
	)
}

export default Agenda
