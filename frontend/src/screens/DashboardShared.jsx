const iconPaths = {
	alert: <><path d="M12 3 2.8 19a1.5 1.5 0 0 0 1.3 2.2h15.8a1.5 1.5 0 0 0 1.3-2.2L12 3Z" /><path d="M12 9v4m0 4h.01" /></>,
	arrow: <><path d="M5 12h14m-6-6 6 6-6 6" /></>,
	bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 12a2 2 0 0 0 4 0" /></>,
	bookmark: <><path d="M6 4.8A1.8 1.8 0 0 1 7.8 3h8.4A1.8 1.8 0 0 1 18 4.8V21l-6-4-6 4V4.8Z" /></>,
	book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21V5.5Z" /><path d="M4 17.5A2.5 2.5 0 0 1 6.5 15H20M8 7h8" /></>,
	calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
	chart: <><path d="M4 20V10m8 10V4m8 16v-7" /></>,
	check: <><path d="m5 12 4 4L19 6" /></>,
	chevron: <><path d="m9 18 6-6-6-6" /></>,
	clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
	close: <><path d="m18 6-12 12M6 6l12 12" /></>,
	download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5m-5 5V3" /></>,
	flag: <><path d="M5 21V5m0 0c5-4 9 4 14 0v10c-5 4-9-4-14 0" /></>,
	grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
	home: <><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z" /></>,
	logout: <><path d="M10 17l5-5-5-5m5 5H3" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /></>,
	person: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-1a7 7 0 0 1 14 0v1" /></>,
	room: <><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M9 21v-5h6v5M9 7h.01M15 7h.01M9 11h.01M15 11h.01" /></>,
	task: <><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4.5h6M8 11l2 2 5-5" /></>,
	trend: <><path d="m3 17 6-6 4 4 8-9m-6 0h6v6" /></>,
}

export function Icon({ name, size = 18 }) {
	return (
		<svg
			aria-hidden="true"
			fill="none"
			height={size}
			stroke="currentColor"
			strokeLinecap="round"
			strokeLinejoin="round"
			strokeWidth="1.8"
			viewBox="0 0 24 24"
			width={size}
		>
			{iconPaths[name]}
		</svg>
	)
}

export function LessonRow({ lesson, onOpen }) {
	return (
		<article
			className={`lesson-row lesson-row--${lesson.tone}${onOpen ? ' lesson-row--clickable' : ''}`}
			onClick={onOpen}
			onKeyDown={(event) => {
				if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
					event.preventDefault()
					onOpen?.()
				}
			}}
			role={onOpen ? 'link' : undefined}
			tabIndex={onOpen ? 0 : undefined}
		>
			<div className="lesson-time"><strong>{lesson.time}</strong><span>{lesson.end}</span></div>
			<div className="lesson-divider" />
			<div className="lesson-copy">
				<strong>{lesson.subject}</strong>
				<span>{lesson.teacher} · {lesson.room}</span>
			</div>
		</article>
	)
}

export function AssignmentCard({ assignment, completed, saved, onComplete, onSave, onOpen }) {
	return (
		<article
			className={`assignment-card${completed ? ' assignment-card--completed' : ''}`}
			onClick={onOpen}
			onKeyDown={(event) => {
				if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
					event.preventDefault()
					onOpen?.()
				}
			}}
			role="link"
			tabIndex={0}
		>
			<div className="assignment-meta">
				<span className={`assignment-kind assignment-kind--${assignment.tone}`}>{assignment.kind}</span>
				<span className={assignment.due === 'Domani' ? 'assignment-due assignment-due--soon' : 'assignment-due'}>
					<Icon name="calendar" size={14} />{assignment.due}
				</span>
			</div>
			<h3>{assignment.title}</h3>
			<p>{assignment.description}</p>
			<div className="assignment-bottom">
				<span>{assignment.teacher}</span>
				{assignment.actionable ? (
					<button className={`task-action${completed ? ' task-action--done' : ''}`} onClick={(event) => { event.stopPropagation(); onComplete() }} type="button">
						<Icon name={completed ? 'check' : 'grid'} size={15} />
						{completed ? 'Completato' : 'Completa'}
					</button>
				) : (
					<button
						aria-label={saved ? 'Rimuovi dai salvati' : 'Salva compito'}
						aria-pressed={saved}
						className={`bookmark-button${saved ? ' bookmark-button--saved' : ''}`}
						onClick={(event) => { event.stopPropagation(); onSave() }}
						title={saved ? 'Rimuovi dai salvati' : 'Salva compito'}
						type="button"
					>
						<Icon name="bookmark" size={17} />
					</button>
				)}
			</div>
		</article>
	)
}