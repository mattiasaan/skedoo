import { useMemo, useState } from 'react'
import { LessonRow } from '../../components/Cards.jsx'
import { Icon } from '../../components/Icon.jsx'
import { ErrorMessage, SectionHeading, Skeleton, StateMessage } from '../../components/ui.jsx'
import { clickableProps } from '../../lib/a11y.js'
import { useApp } from '../../lib/appContext.js'
import { useChanges, useLessons, useNow, usePersistentFlags, useSchedule } from '../../lib/data.js'
import { addDays, classDisplayName, classLabel, dateKey, formatDuration, formatKickerDate, nowMinutes, relativeDay, schoolDisplayName, teacherShort, weekdayName } from '../../lib/format.js'
import { topicPreview, topicsForBlock } from '../../lib/lessons.js'
import { buildDayLessons, dayProgress, lessonStatus, periodLabel } from '../../lib/schedule.js'
import { useToast } from '../../lib/toast.js'
import { TasksSection } from './TasksSection.jsx'

/** Prossimo giorno (entro una settimana) in cui la classe ha lezione. */
function nextSchoolDay(schedule, from) {
	for (let offset = 1; offset <= 7; offset += 1) {
		const day = addDays(from, offset)
		const lessons = buildDayLessons(schedule, day)
		if (lessons.length) return { date: day, lessons }
	}
	return null
}

const CHANGE_LABELS = {
	entrata_posticipata: 'Entrata posticipata',
	uscita_anticipata: 'Uscita anticipata',
	senza_lezioni_pomeridiane: 'Niente lezioni pomeridiane',
}

function changeMessage(change, lessons) {
	if (change.tipo === 'cambio_aula') {
		const lesson = lessons.find((item) => item.ore.includes(change.ora))
		const when = change.orario ? ` (${change.orario})` : change.ora ? ` (${change.ora}ª ora)` : ''
		return (
			<>
				<b>Cambio aula</b> — {lesson ? lesson.materia : 'Lezione'}{when} spostata in <u>{change.nuova_aula}</u>.
			</>
		)
	}
	const label = CHANGE_LABELS[change.tipo] ?? 'Variazione'
	return <><b>{label}</b> — {change.testo}</>
}

function ChangeAlert({ changes, lessons }) {
	const { openDetail } = useApp()
	const toast = useToast()
	const [dismissed, dismiss] = usePersistentFlags('changes-dismissed')
	const visible = changes.filter((change) => !dismissed[`${change.data}-${change.id}`])
	if (!visible.length) return null
	const [first] = visible

	function hide() {
		const keys = visible.map((change) => `${change.data}-${change.id}`)
		keys.forEach((key) => dismiss(key, true))
		toast('Avviso nascosto: le variazioni restano nell\'orario', {
			tone: 'info',
			action: { label: 'Annulla', onClick: () => keys.forEach((key) => dismiss(key, false)) },
		})
	}

	return (
		<aside className="change-alert" aria-label="Variazione orario" {...clickableProps(() => openDetail({ type: 'changes', changes }))}>
			<span className="change-alert__icon"><Icon name="bell" size={19} /></span>
			<div className="change-alert__copy">
				<div className="change-alert__meta">
					<span className="badge badge--amber badge--pill">Variazione orario</span>
					<span>Oggi</span>
				</div>
				<p>{changeMessage(first, lessons)}</p>
				{visible.length > 1 && <span className="change-alert__more">+{visible.length - 1} {visible.length === 2 ? 'altra variazione' : 'altre variazioni'}</span>}
			</div>
			<button
				aria-label="Nascondi avviso"
				className="change-alert__close"
				onClick={(event) => {
					event.stopPropagation()
					hide()
				}}
				type="button"
			>
				<Icon name="close" size={17} />
			</button>
		</aside>
	)
}

function NextLessonCard({ progress, upcomingDay }) {
	const { openDetail } = useApp()
	const isLive = progress.mode === 'current' || progress.mode === 'break' || progress.mode === 'before'
	const lesson = isLive ? progress.lesson : upcomingDay?.lessons[0]

	if (!lesson) {
		return <StateMessage icon="calendar" text="Non ci sono lezioni in programma nei prossimi giorni." title="Nessuna lezione in arrivo" />
	}

	const kicker = progress.mode === 'current' ? 'Lezione in corso' : 'Prossima lezione'
	const pill = progress.mode === 'current'
		? `Termina tra ${formatDuration(progress.remaining)}`
		: isLive
			? `Inizia tra ${formatDuration(progress.remaining)}`
			: relativeDay(dateKey(upcomingDay.date))
	const footer = progress.mode === 'current'
		? ['Lezione in corso', `${formatDuration(progress.remaining)} rimanenti`]
		: progress.mode === 'break'
			? ['Intervallo in corso', `${formatDuration(progress.remaining)} rimanenti`]
			: progress.mode === 'before'
				? ['Prima campanella', `tra ${formatDuration(progress.remaining)}`]
				: null

	return (
		<section className="home-section" aria-labelledby="next-lesson-heading">
			<SectionHeading aside={<span className="badge badge--accent badge--pill badge--soft-case">{pill}</span>} id="next-lesson-heading" kicker title={kicker} />
			<article className={`next-lesson${lesson.roomChange ? ' next-lesson--changed' : ''}`} {...clickableProps(() => openDetail({ type: 'lesson', lesson }))}>
				<div className="next-lesson__top">
					<span className="next-lesson__period">{periodLabel(lesson) || 'Lezione'}{!isLive && upcomingDay ? ` • ${weekdayName(upcomingDay.date)}` : ''}</span>
					{lesson.room && (
						<span className="room-pill">
							<Icon name={lesson.roomChange ? 'swap' : 'building'} size={15} />
							<span>{lesson.room}</span>
						</span>
					)}
				</div>
				<h3>{lesson.materia}</h3>
				<div className="next-lesson__details">
					{lesson.teachers[0] && <span><Icon name="person" size={16} />{teacherShort(lesson.teachers[0])}</span>}
					<strong><Icon name="clock" size={16} />{lesson.inizio} – {lesson.fine}</strong>
				</div>
				{footer && (
					<div className="next-lesson__progress">
						<div><span>{footer[0]}</span><strong>{footer[1]}</strong></div>
						<div className="progress-track" role="progressbar" aria-label={footer[0]} aria-valuemax={100} aria-valuemin={0} aria-valuenow={Math.round(progress.progress * 100)}>
							<span style={{ width: `${Math.round(progress.progress * 100)}%` }} />
						</div>
					</div>
				)}
			</article>
		</section>
	)
}

function HomeGalilei() {
	const { user, classId } = useApp()
	const now = useNow(30000)
	const schedule = useSchedule(classId)
	const changes = useChanges(classId)
	const todayKey = dateKey(now)
	const minutes = nowMinutes(now)
	const [showDone, setShowDone] = useState(false)

	const todayChanges = useMemo(() => (changes.data ?? []).filter((change) => change.data === todayKey), [changes.data, todayKey])
	const todayLessons = useMemo(() => buildDayLessons(schedule.data, now, todayChanges), [schedule.data, now, todayChanges])
	const progress = dayProgress(todayLessons, minutes)
	const needsNextDay = progress.mode === 'finished' || progress.mode === 'empty'
	const upcomingDay = useMemo(() => (needsNextDay ? nextSchoolDay(schedule.data, now) : null), [needsNextDay, schedule.data, now])

	const listLessons = todayLessons.length ? todayLessons : upcomingDay?.lessons ?? []
	const listIsToday = todayLessons.length > 0
	// argomenti scritti dai docenti: esistono solo per le ore di oggi già iniziate
	const register = useLessons(listIsToday ? todayKey : null)
	const hours = listLessons.filter((lesson) => !lesson.cancelled).reduce((sum, lesson) => sum + lesson.ore.length, 0)
	// le ore già svolte si nascondono finché ne restano altre: meno scorrimento per arrivare a quelle che servono
	const withStatus = listLessons.map((lesson) => ({ lesson, status: lessonStatus(lesson, minutes, listIsToday) }))
	const doneCount = withStatus.filter((item) => item.status === 'done').length
	const canHideDone = doneCount > 0 && doneCount < withStatus.length
	const visibleLessons = canHideDone && !showDone ? withStatus.filter((item) => item.status !== 'done') : withStatus
	const school = schoolDisplayName(user?.scuola)
	const className = schedule.data?.nome ? classDisplayName(schedule.data.nome) : classLabel(classId)

	return (
		<div className="page page--home">
			<header className="page-intro">
				<p className="page-intro__kicker">{formatKickerDate(now)}</p>
				<p className="page-intro__line">{school ? `${school} (${className})` : className}</p>
			</header>

			<div className="home-grid">
				<div className="home-grid__main">
					<ChangeAlert changes={todayChanges} lessons={todayLessons} />

					{schedule.loading && <Skeleton height={190} lines={1} />}
					{schedule.error && !schedule.data && <ErrorMessage error={schedule.error} onRetry={schedule.reload} title="Orario non disponibile" />}
					{schedule.data && <NextLessonCard progress={progress} upcomingDay={upcomingDay} />}

					<section className="home-section" aria-labelledby="today-heading">
						<SectionHeading
							aside={<span className="section-heading__note">{hours} {hours === 1 ? 'ora prevista' : 'ore previste'}</span>}
							id="today-heading"
							title={listIsToday || !upcomingDay ? 'Orario di Oggi' : `Orario di ${weekdayName(upcomingDay.date)}`}
						/>
						{schedule.loading && <Skeleton height={76} lines={3} />}
						{schedule.data && (listLessons.length ? (
							<div className="lesson-list">
								{canHideDone && (
									<button aria-expanded={showDone} className="show-more" onClick={() => setShowDone((value) => !value)} type="button">
										<Icon name={showDone ? 'chevronDown' : 'checkCircle'} size={15} />
										{showDone ? 'Nascondi le ore già svolte' : `Mostra ${doneCount === 1 ? "l'ora già svolta" : `le ${doneCount} ore già svolte`}`}
									</button>
								)}
								{visibleLessons.map(({ lesson, status }) => (
									<LessonRow
										key={lesson.id}
										lesson={lesson}
										status={status}
										topic={status !== 'upcoming' && !lesson.cancelled ? topicPreview(topicsForBlock(register.data, lesson)) : null}
									/>
								))}
							</div>
						) : <StateMessage icon="calendar" text="Per questa classe non ci sono lezioni in orario." title="Nessuna lezione" />)}
					</section>
				</div>

				<div className="home-grid__side">
					<TasksSection />
				</div>
			</div>
		</div>
	)
}

export default HomeGalilei
