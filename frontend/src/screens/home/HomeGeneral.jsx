import { useMemo, useState } from 'react'
import { LessonRow } from '../../components/Cards.jsx'
import { Icon } from '../../components/Icon.jsx'
import { ErrorMessage, LinkButton, SectionHeading, Skeleton } from '../../components/ui.jsx'
import { boardKey } from '../../lib/agenda.js'
import { useApp } from '../../lib/appContext.js'
import { useAbsences, useBoard, useGrades, useLessons, usePersistentFlags } from '../../lib/data.js'
import { addDays, dateKey, formatDateTime, formatKickerDate, formatNumber, relativeDay, schoolDisplayName, teacherShort, titleCase } from '../../lib/format.js'
import { useToast } from '../../lib/toast.js'
import { allGrades, averageAt, currentTerm, generalAverage, gradeTone, subjectsForTerm, termsOf } from '../../lib/grades.js'
import { registerBlocks, topicPreview } from '../../lib/lessons.js'
import { TasksSection } from './TasksSection.jsx'

/** "Circolare n. 142 — Disposizioni..." -> grassetto sulla prima parte, come nel design. */
function boardTitle(item) {
	const [head, ...rest] = String(item.titolo ?? '').split(/\s[—–-]\s/)
	if (rest.length) return <><b>{head}</b> — {rest.join(' — ')}</>
	return <><b>{item.categoria || 'Comunicazione'}</b> — {item.titolo}</>
}

function BoardCard() {
	const { openDetail, navigate, isBoardRead } = useApp()
	const toast = useToast()
	const board = useBoard()
	const [dismissed, dismiss] = usePersistentFlags('board-dismissed')
	const items = board.data?.elementi ?? []
	// prima la più recente da leggere, altrimenti l'ultima pubblicata
	const item = items.find((entry) => !isBoardRead(entry) && !dismissed[boardKey(entry)])
		?? items.find((entry) => !dismissed[boardKey(entry)])
	const unread = items.filter((entry) => !isBoardRead(entry)).length

	function hide() {
		dismiss(boardKey(item), true)
		toast('Circolare nascosta dalla Home', { tone: 'info', action: { label: 'Annulla', onClick: () => dismiss(boardKey(item), false) } })
	}

	if (board.loading) return <Skeleton height={130} lines={1} />
	if (board.error && !board.data) return <ErrorMessage error={board.error} onRetry={board.reload} title="Bacheca non disponibile" />
	if (!item) return null

	return (
		<aside className="board-card" aria-label="Ultima circolare">
			<span className="board-card__icon"><Icon name="megaphone" size={20} /></span>
			<div className="board-card__copy">
				<div className="board-card__meta">
					<span className="badge badge--accent">Bacheca circolari</span>
					{item.pubblicato_il && <span>{formatDateTime(item.pubblicato_il)}</span>}
				</div>
				<p>{boardTitle(item)}</p>
				<button className="board-card__read" onClick={() => openDetail({ type: 'board', item })} type="button">
					Leggi <Icon name="chevron" size={15} />
				</button>
				<button className="board-card__count" onClick={() => navigate('home/bacheca')} type="button">
					{unread > 1 ? `${unread} comunicazioni da leggere` : 'Tutta la bacheca'} <Icon name="chevron" size={13} />
				</button>
			</div>
			<button aria-label="Nascondi circolare" className="change-alert__close" onClick={hide} type="button">
				<Icon name="close" size={17} />
			</button>
		</aside>
	)
}

const RECENT_LESSONS = 3

/**
 * Lezioni di oggi dal registro di ClasseViva (le altre scuole non hanno l'orario): compaiono man mano che i
 * docenti firmano, con l'argomento se l'hanno scritto. Si vedono le ultime ore, le precedenti a richiesta;
 * senza lezioni firmate (mattina presto, festivi) o se il registro non risponde la sezione non occupa spazio.
 */
function TodayLessons() {
	const today = dateKey(new Date())
	const register = useLessons(today)
	const blocks = useMemo(() => (register.data ? registerBlocks(register.data) : []), [register.data])
	const [showEarlier, setShowEarlier] = useState(false)
	if (!blocks.length) return null

	const hidden = showEarlier ? 0 : Math.max(0, blocks.length - RECENT_LESSONS)
	const hours = blocks.reduce((sum, block) => sum + Math.max(1, block.ore.length), 0)

	return (
		<section className="home-section" aria-labelledby="today-lessons-heading">
			<SectionHeading
				aside={<span className="section-heading__note">{hours} {hours === 1 ? 'ora firmata' : 'ore firmate'}</span>}
				icon="book"
				id="today-lessons-heading"
				title="Lezioni di oggi"
			/>
			<div className="lesson-list">
				{blocks.length > RECENT_LESSONS && (
					<button aria-expanded={showEarlier} className="show-more" onClick={() => setShowEarlier((value) => !value)} type="button">
						<Icon name={showEarlier ? 'chevronDown' : 'clock'} size={15} />
						{showEarlier ? 'Mostra solo le ultime lezioni' : `Mostra ${hidden === 1 ? 'la lezione precedente' : `le ${hidden} lezioni precedenti`}`}
					</button>
				)}
				{blocks.slice(hidden).map((block) => <LessonRow key={block.id} lesson={block} topic={topicPreview(block.topics)} />)}
			</div>
		</section>
	)
}

function GradesOverview() {
	const { navigate, openSubject } = useApp()
	const grades = useGrades()
	const term = currentTerm(grades.data)
	const termLabel = termsOf(grades.data).find((item) => item.pos === term)?.label
	const subjects = useMemo(() => subjectsForTerm(grades.data, term), [grades.data, term])
	const average = generalAverage(subjects)
	const monthAgo = averageAt(subjects, dateKey(addDays(new Date(), -30)))
	const delta = average != null && monthAgo != null ? average - monthAgo : null
	const last = allGrades(subjects)[0]
	const lastTeacher = last ? subjects.find((subject) => subject.name === last.subject)?.docenti?.[0] : null

	return (
		<section className="home-section" aria-labelledby="grades-overview-heading">
			<SectionHeading aside={termLabel && <span className="badge badge--accent badge--pill badge--soft-case">{termLabel}</span>} id="grades-overview-heading" kicker title="Panoramica valutazioni" />
			{grades.loading && <Skeleton height={150} lines={1} />}
			{grades.error && !grades.data && <ErrorMessage error={grades.error} onRetry={grades.reload} title="Voti non disponibili" />}
			{grades.data && (
				<div className="overview-grid">
					<button className="overview-card" onClick={() => navigate('voti')} type="button">
						<span className="overview-card__label">Media generale <Icon name="trend" size={16} /></span>
						<span className={`overview-card__value overview-card__value--${gradeTone(average)}`}>
							{formatNumber(average)}<small> / 10</small>
						</span>
						<span className="overview-card__footer">
							{delta == null ? 'Nessun confronto disponibile' : `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} questo mese ${delta >= 0 ? '↗' : '↘'}`}
						</span>
					</button>
					<button className="overview-card" disabled={!last} onClick={() => last && openSubject(last.subject)} type="button">
						<span className="overview-card__label">
							Ultimo voto
							{last && <span className="badge">{relativeDay(last.data)}</span>}
						</span>
						{last ? (
							<>
								<span className="overview-card__last">
									<strong>{last.subject}</strong>
									<span className={`grade-chip grade-chip--${gradeTone(last.valore)}`}>{last.voto}</span>
								</span>
								<span className="overview-card__sub">{[last.tipo, last.note].filter(Boolean).join(' • ') || 'Valutazione'}</span>
								<span className="overview-card__footer overview-card__footer--muted">
									{lastTeacher ? teacherShort(lastTeacher) : 'ClasseViva'}
								</span>
							</>
						) : <span className="overview-card__sub">Ancora nessun voto in questo periodo.</span>}
					</button>
				</div>
			)}
		</section>
	)
}

function AttendanceCard() {
	const { navigate } = useApp()
	const absences = useAbsences()
	const summary = absences.data?.riepilogo
	const events = absences.data?.eventi ?? []
	const absenceEvents = events.filter((event) => event.tipo === 'assenza')
	const justified = absenceEvents.filter((event) => event.giustificata).length

	return (
		<section className="home-section" aria-labelledby="attendance-heading">
			<SectionHeading aside={<LinkButton onClick={() => navigate('profilo/assenze')}>Vedi dettagli</LinkButton>} icon="pulse" id="attendance-heading" title="Presenze & Registro" />
			{absences.loading && <Skeleton height={120} lines={1} />}
			{absences.error && !absences.data && <ErrorMessage error={absences.error} onRetry={absences.reload} title="Presenze non disponibili" />}
			{summary && (
				<div className="attendance-strip">
					<div>
						<span>Assenze</span>
						<p><strong>{summary.assenze}</strong> gg</p>
						<small>{justified} giustif. • {absenceEvents.length - justified} da giust.</small>
					</div>
					<div>
						<span>Ritardi</span>
						<p><strong>{summary.ritardi}</strong> {summary.ritardi === 1 ? 'volta' : 'volte'}</p>
						<small>Entrate posticipate</small>
					</div>
					<div>
						<span>Giustif.</span>
						<p className={summary.da_giustificare ? 'is-warning' : 'is-good'}><strong>{summary.da_giustificare}</strong> pend.</p>
						{summary.da_giustificare
							? <span className="badge badge--amber"><Icon name="alert" size={12} />Da giust.</span>
							: <span className="badge badge--accent"><Icon name="check" size={12} strokeWidth={2.4} />In regola</span>}
					</div>
				</div>
			)}
		</section>
	)
}

function HomeGeneral() {
	const { user } = useApp()
	const school = schoolDisplayName(user?.scuola)
	const city = user?.scuola?.citta ? ` • ${titleCase(user.scuola.citta)}` : ''

	return (
		<div className="page page--home">
			<header className="page-intro">
				<p className="page-intro__kicker">{formatKickerDate(new Date())}</p>
				<h1 className="page-intro__title">Ciao, {user?.nome ? titleCase(user.nome.split(' ')[0]) : 'studente'}! <span aria-hidden="true">👋</span></h1>
				{school && <p className="page-intro__line">{school}{city}</p>}
			</header>

			<div className="home-grid">
				<div className="home-grid__main">
					<BoardCard />
					<TodayLessons />
					<GradesOverview />
					<AttendanceCard />
				</div>
				<div className="home-grid__side">
					<TasksSection />
				</div>
			</div>
		</div>
	)
}

export default HomeGeneral
