import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api.js'
import { useApp } from '../lib/appContext.js'
import { useGrades, useMonthAgenda, useUpcomingAgenda } from '../lib/data.js'
import { MAX_DOWNLOAD_MB } from '../lib/download.js'
import { formatDateTime, formatLongDate, formatNumber, parseDateKey, relativeDay, teacherName, titleCase } from '../lib/format.js'
import { averageLabel, counted, gradeTone, subjectIcon, subjectsForTerm, usualWeight } from '../lib/grades.js'
import { periodLabel, subjectMatches } from '../lib/schedule.js'
import { useApi } from '../lib/useApi.js'
import { AttachmentButton } from './Files.jsx'
import { Icon } from './Icon.jsx'
import { LineChart } from './LineChart.jsx'
import { ErrorMessage, Sheet, Skeleton, StateMessage } from './ui.jsx'

function Facts({ items }) {
	const visible = items.filter(([, value]) => value)
	if (!visible.length) return null
	return (
		<dl className="detail-facts">
			{visible.map(([label, value]) => (
				<div key={label}>
					<dt>{label}</dt>
					<dd>{value}</dd>
				</div>
			))}
		</dl>
	)
}

function RelatedButton({ icon, label, value, onClick, tone = 'neutral' }) {
	return (
		<button className={`related-link related-link--${tone}`} onClick={onClick} type="button">
			<Icon name={icon} size={17} />
			<span><small>{label}</small><strong>{value}</strong></span>
			<Icon name="chevron" size={17} />
		</button>
	)
}

// ---------- compito / verifica / evento ----------
function EventDetail({ item, onClose }) {
	const { openDetail, doneTasks, toggleDone, savedTasks, toggleSaved } = useApp()
	const date = parseDateKey(item.date)
	const done = Boolean(doneTasks[item.key])
	const saved = Boolean(savedTasks[item.key])
	const time = item.tutto_il_giorno || !item.ora_inizio ? 'Tutto il giorno' : `${item.ora_inizio}${item.ora_fine ? ` – ${item.ora_fine}` : ''}`

	return (
		<Sheet kicker={item.label} onClose={onClose} title={item.title} tone={item.tone}>
			<div className="detail-meta">
				<span><Icon name="calendar" size={15} />{date ? formatLongDate(date) : ''} ({relativeDay(item.date)})</span>
				<span><Icon name="clock" size={15} />{time}</span>
			</div>
			{item.description && <p className="detail-text">{item.description}</p>}
			<Facts items={[['Materia', item.subject], ['Inserito da', item.autore ? teacherName(item.autore) : null]]} />
			<div className="detail-actions">
				{item.kind === 'compito' ? (
					<button className={`task-toggle task-toggle--large${done ? ' task-toggle--done' : ''}`} onClick={() => toggleDone(item.key)} type="button">
						<Icon name={done ? 'checkCircle' : 'square'} size={18} />
						{done ? 'Segnato come completato' : 'Segna come completato'}
					</button>
				) : (
					<button className={`task-toggle task-toggle--large${saved ? ' task-toggle--done' : ''}`} onClick={() => toggleSaved(item.key)} type="button">
						<Icon name="bookmark" size={18} />
						{saved ? 'Salvato' : 'Salva per dopo'}
					</button>
				)}
			</div>
			{item.subject && (
				<RelatedButton icon={subjectIcon(item.subject)} label="Apri materia" onClick={() => openDetail({ type: 'subject', name: item.subject })} value={item.subject} />
			)}
		</Sheet>
	)
}

// ---------- lezione ----------
function LessonDetail({ lesson, onClose }) {
	const { openDetail } = useApp()
	const date = parseDateKey(lesson.date) ?? new Date()
	const agenda = useMonthAgenda(date)
	const related = agenda.items.filter((item) => item.date === lesson.date && subjectMatches(lesson.materia, item.subject))

	return (
		<Sheet kicker={periodLabel(lesson) || 'Lezione'} onClose={onClose} title={lesson.materia} tone={lesson.roomChange ? 'amber' : undefined}>
			<div className="detail-meta">
				<span><Icon name="calendar" size={15} />{formatLongDate(date)}</span>
				<span><Icon name="clock" size={15} />{lesson.inizio} – {lesson.fine}</span>
			</div>
			{lesson.cancelled && (
				<StateMessage icon="alert" text="Per la classe è prevista una variazione d'orario: questa ora non si svolge." title={lesson.cancelled} />
			)}
			{lesson.roomChange && (
				<div className="detail-callout detail-callout--amber">
					<Icon name="swap" size={18} />
					<p><strong>Cambio aula:</strong> la lezione si svolge in <b>{lesson.roomChange}</b>{lesson.aula ? ` invece di ${lesson.aula}` : ''}.</p>
				</div>
			)}
			<Facts
				items={[
					['Materia', lesson.materia_completa],
					['Aula', lesson.room],
					['Docenti', lesson.teachers.map(teacherName).join(', ')],
				]}
			/>
			{related.length > 0 && (
				<div className="detail-section">
					<h3>In agenda per questa lezione</h3>
					{related.map((item) => (
						<RelatedButton icon={item.kind === 'compito' ? 'clipboard' : 'calendar'} key={item.key} label={item.label} onClick={() => openDetail({ type: 'event', item })} tone={item.tone} value={item.description || item.title} />
					))}
				</div>
			)}
			<RelatedButton icon={subjectIcon(lesson.materia)} label="Voti e andamento" onClick={() => openDetail({ type: 'subject', name: lesson.materia })} value={lesson.materia} />
		</Sheet>
	)
}

// ---------- materia (voti) ----------
function SubjectDetail({ name, onClose }) {
	const { openDetail, isGalilei } = useApp()
	const grades = useGrades()
	const upcoming = useUpcomingAgenda()
	const subject = useMemo(
		() => subjectsForTerm(grades.data, null, { practicalSplit: isGalilei }).find((item) => subjectMatches(name, item.materia)),
		[grades.data, name, isGalilei],
	)
	const title = subject?.name ?? titleCase(name)
	const events = upcoming.items.filter((item) => subjectMatches(title, item.subject))
	const chronological = subject ? subject.voti.filter(counted).reverse() : []
	// il peso si mostra rispetto a quello ordinario della materia: ClasseViva può mandare 1 o 100 per lo stesso 100%
	const usual = usualWeight(chronological)

	return (
		<Sheet kicker="Dettaglio materia" onClose={onClose} title={title}>
			{grades.loading && <Skeleton height={64} lines={3} />}
			{grades.error && !grades.data && <ErrorMessage error={grades.error} onRetry={grades.reload} />}
			{grades.data && !subject && <StateMessage icon="chart" text="Non ci sono ancora voti registrati per questa materia." title="Nessun voto" />}
			{subject && (
				<>
					<div className={`subject-summary subject-summary--${gradeTone(subject.media)}`}>
						<div>
							<small>Media dell'anno</small>
							<strong>{formatNumber(subject.media)}</strong>
							<span>{averageLabel(subject.media)}</span>
						</div>
						<p>
							{subject.voti.length} {subject.voti.length === 1 ? 'valutazione' : 'valutazioni'}
							{subject.docenti?.length ? <><br />{subject.docenti.map(teacherName).join(', ')}</> : null}
						</p>
					</div>
					{chronological.length > 1 && (
						<div className="detail-chart">
							<LineChart
								label={`Andamento dei voti di ${title}`}
								max={10}
								min={Math.max(1, Math.floor(Math.min(...chronological.map((grade) => grade.valore))) - 1)}
								points={chronological.map((grade) => ({ key: grade.id, value: grade.valore, title: `${grade.voto} • ${grade.data}` }))}
								threshold={6}
							/>
						</div>
					)}
					<div className="detail-section">
						<h3>Tutti i voti</h3>
						<ul className="grade-list">
							{subject.voti.map((grade) => (
								<li className={`grade-list__item${grade.annullato || grade.fa_media === false ? ' grade-list__item--void' : ''}`} key={grade.id}>
									<span className={`grade-chip grade-chip--${gradeTone(grade.valore)}`}>{grade.voto || '—'}</span>
									<span>
										<strong>{grade.tipo ?? 'Valutazione'}{grade.annullato ? ' (annullato)' : grade.fa_media === false ? ' (non fa media)' : ''}</strong>
										<small>{relativeDay(grade.data)}{grade.peso != null && grade.peso > 0 && grade.peso !== usual ? ` • peso ${Math.round((grade.peso / usual) * 100)}%` : ''}</small>
										{grade.note && <em>{grade.note}</em>}
									</span>
								</li>
							))}
						</ul>
					</div>
				</>
			)}
			{events.length > 0 && (
				<div className="detail-section">
					<h3>Prossimi impegni</h3>
					{events.map((item) => (
						<RelatedButton icon={item.kind === 'compito' ? 'clipboard' : 'calendar'} key={item.key} label={`${item.label} • ${relativeDay(item.date)}`} onClick={() => openDetail({ type: 'event', item })} tone={item.tone} value={item.description || item.title} />
					))}
				</div>
			)}
		</Sheet>
	)
}

// ---------- circolare ----------
function BoardDetail({ item, onClose }) {
	const { markBoardRead } = useApp()
	const detail = useApi(item.codice && item.id ? `board:${item.codice}:${item.id}` : null, () => api.boardItem(item.codice, item.id))
	const loaded = Boolean(detail.data)

	// aprendola, ClasseViva la segna come letta: si aggiorna subito anche il contatore delle notifiche
	useEffect(() => {
		if (loaded) markBoardRead(item)
	}, [loaded, item, markBoardRead])

	return (
		<Sheet kicker={item.categoria || 'Bacheca'} onClose={onClose} title={item.titolo || 'Comunicazione'}>
			<div className="detail-meta">
				{item.pubblicato_il && <span><Icon name="calendar" size={15} />{formatDateTime(item.pubblicato_il)}</span>}
				{item.valido_a && <span><Icon name="clock" size={15} />Valida fino al {formatLongDate(parseDateKey(item.valido_a))}</span>}
			</div>
			{detail.loading && <Skeleton height={18} lines={4} />}
			{detail.error && <ErrorMessage error={detail.error} onRetry={detail.reload} title="Testo non disponibile" />}
			{detail.data && <p className="detail-text">{detail.data.testo || (item.allegati?.length ? 'Questa comunicazione non ha un testo: il contenuto è negli allegati.' : 'Questa comunicazione non ha un testo.')}</p>}
			{item.allegati?.length > 0 && (
				<div className="detail-section">
					<h3>Allegati</h3>
					<ul className="attachment-list">
						{item.allegati.map((attachment) => <AttachmentButton attachment={attachment} item={item} key={attachment.numero} />)}
					</ul>
					<p className="detail-hint">Tocca un allegato per scaricarlo. I file oltre {MAX_DOWNLOAD_MB} MB si scaricano solo dall'app o dal sito ClasseViva.</p>
				</div>
			)}
		</Sheet>
	)
}

// ---------- materiale di solo testo (didattica) ----------
function TextDetail({ kicker, title, text, onClose }) {
	return (
		<Sheet kicker={kicker} onClose={onClose} title={title}>
			<p className="detail-text detail-text--first">{text}</p>
		</Sheet>
	)
}

// ---------- variazioni del giorno ----------
function ChangesDetail({ changes, onClose }) {
	return (
		<Sheet kicker="Variazioni orario" onClose={onClose} title="Modifiche di oggi" tone="amber">
			<ul className="changes-list">
				{changes.map((change) => (
					<li key={change.id}>
						<span className="changes-list__icon"><Icon name={change.tipo === 'cambio_aula' ? 'swap' : 'clock'} size={17} /></span>
						<span>
							<strong>{change.ora ? `${change.ora}ª ora` : 'Variazione'}{change.orario ? ` • ${change.orario}` : ''}</strong>
							<small>{change.testo}</small>
						</span>
					</li>
				))}
			</ul>
		</Sheet>
	)
}

// ---------- conferma logout ----------
function LogoutDetail({ onClose }) {
	const { onLogout } = useApp()
	const [leaving, setLeaving] = useState(false)

	return (
		<Sheet kicker="Account" onClose={onClose} title="Vuoi uscire da Skedoo?" tone="danger">
			<p className="detail-text">
				Su questo dispositivo verranno cancellati la sessione e i dati in memoria. Classe scelta, compiti completati e
				preferenze restano salvati per il prossimo accesso.
			</p>
			<div className="confirm-actions">
				<button className="confirm-actions__cancel" disabled={leaving} onClick={onClose} type="button">Annulla</button>
				<button
					className="confirm-actions__danger"
					disabled={leaving}
					onClick={() => {
						setLeaving(true)
						onLogout()
					}}
					type="button"
				>
					<Icon name="logout" size={17} />
					{leaving ? 'Uscita in corso…' : 'Esci'}
				</button>
			</div>
		</Sheet>
	)
}

/** Mostra il dettaglio richiesto con openDetail({ type, ... }). */
export function DetailHost({ detail, onClose }) {
	if (!detail) return null
	switch (detail.type) {
		case 'event':
			return <EventDetail item={detail.item} onClose={onClose} />
		case 'lesson':
			return <LessonDetail lesson={detail.lesson} onClose={onClose} />
		case 'subject':
			return <SubjectDetail name={detail.name} onClose={onClose} />
		case 'text':
			return <TextDetail kicker={detail.kicker} onClose={onClose} text={detail.text} title={detail.title} />
		case 'board':
			return <BoardDetail item={detail.item} onClose={onClose} />
		case 'logout':
			return <LogoutDetail onClose={onClose} />
		case 'changes':
			return <ChangesDetail changes={detail.changes} onClose={onClose} />
		default:
			return null
	}
}
