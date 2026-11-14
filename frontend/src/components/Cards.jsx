import { clickableProps } from '../lib/a11y.js'
import { useApp } from '../lib/appContext.js'
import { relativeDay, teacherShort } from '../lib/format.js'
import { periodLabel } from '../lib/schedule.js'
import { Icon } from './Icon.jsx'

const STATUS_BADGE = {
	done: { label: 'Completata', className: 'badge--neutral', icon: 'check' },
	current: { label: 'In corso', className: 'badge--accent', dot: true },
	upcoming: { label: 'In arrivo', className: 'badge--blue' },
}

/** Riga dell'orario di oggi (Home Galilei). */
export function LessonRow({ lesson, status }) {
	const { openDetail } = useApp()
	const badge = lesson.cancelled ? { label: 'Annullata', className: 'badge--danger' } : STATUS_BADGE[status]
	const teacher = lesson.teachers[0]

	return (
		<article
			className={`lesson-row lesson-row--${lesson.cancelled ? 'cancelled' : status}${lesson.roomChange ? ' lesson-row--changed' : ''}`}
			{...clickableProps(() => openDetail({ type: 'lesson', lesson }))}
			aria-label={`${lesson.materia}, ${lesson.inizio}–${lesson.fine}`}
		>
			<div className="lesson-row__time">
				<strong>{lesson.inizio}</strong>
				<span>{lesson.fine}</span>
			</div>
			<div className="lesson-row__copy">
				<strong>{lesson.materia}</strong>
				<span>
					{teacher ? teacherShort(teacher) : periodLabel(lesson)}
					{lesson.room && (
						<>
							<i aria-hidden="true">•</i>
							{lesson.roomChange
								? <b className="lesson-row__room-change"><Icon name="refresh" size={13} />{lesson.roomChange}</b>
								: lesson.room}
						</>
					)}
				</span>
			</div>
			{badge && (
				<span className={`badge badge--pill ${badge.className}`}>
					{badge.dot && <span className="badge-dot" aria-hidden="true" />}
					{badge.label}
					{badge.icon && <Icon name={badge.icon} size={12} strokeWidth={2.4} />}
				</span>
			)}
		</article>
	)
}

/** Card "Compiti & Verifiche" (VERIFICA rossa con segnalibro, COMPITI blu con "Completa"). */
export function TaskCard({ item }) {
	const { openDetail, doneTasks, toggleDone, savedTasks, toggleSaved } = useApp()
	const done = Boolean(doneTasks[item.key])
	const saved = Boolean(savedTasks[item.key])
	const due = relativeDay(item.date)
	const soon = due === 'Oggi' || due === 'Domani'
	const isHomework = item.kind === 'compito'

	return (
		<article className={`task-card${done ? ' task-card--done' : ''}`} {...clickableProps(() => openDetail({ type: 'event', item }))}>
			<div className="task-card__meta">
				<span className={`badge badge--${item.tone}`}>{item.label}</span>
				<span className={`task-card__due${soon ? ' task-card__due--soon' : ''}`}>
					<Icon name="calendar" size={14} />
					{due}
					{item.ora_inizio && ` • ${item.ora_inizio}`}
				</span>
			</div>
			<h3>{item.title}</h3>
			{item.description && <p>{item.description}</p>}
			<div className="task-card__footer">
				<span>{item.autore ? teacherShort(item.autore) : item.subject ?? 'Agenda di classe'}</span>
				{isHomework ? (
					<button
						aria-pressed={done}
						className={`task-toggle${done ? ' task-toggle--done' : ''}`}
						onClick={(event) => {
							event.stopPropagation()
							toggleDone(item.key)
						}}
						type="button"
					>
						<Icon name={done ? 'checkCircle' : 'square'} size={16} />
						{done ? 'Completato' : 'Completa'}
					</button>
				) : (
					<button
						aria-label={saved ? 'Rimuovi dai salvati' : 'Salva'}
						aria-pressed={saved}
						className={`bookmark-toggle${saved ? ' bookmark-toggle--saved' : ''}`}
						onClick={(event) => {
							event.stopPropagation()
							toggleSaved(item.key)
						}}
						type="button"
					>
						<Icon name="bookmark" size={18} />
					</button>
				)}
			</div>
		</article>
	)
}
