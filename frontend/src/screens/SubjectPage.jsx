import { useMemo, useState } from 'react'
import { MaterialCard } from '../components/Files.jsx'
import { Icon } from '../components/Icon.jsx'
import { LineChart } from '../components/LineChart.jsx'
import { ErrorMessage, LinkButton, RelatedLink, SectionHeading, Skeleton, StateMessage, SubPageHeader } from '../components/ui.jsx'
import { useApp } from '../lib/appContext.js'
import { useDidactics, useGrades, useSchedule, useUpcomingAgenda } from '../lib/data.js'
import { materialDetails } from '../lib/didactics.js'
import { formatNumber, formatShortDate, parseDateKey, relativeDay, teacherName, weekdayName } from '../lib/format.js'
import { averageLabel, counted, gradeTone, subjectIcon, usualWeight } from '../lib/grades.js'
import { TABS } from '../lib/routes.js'
import { periodLabel } from '../lib/schedule.js'
import { subjectOverview } from '../lib/subject.js'

const AGENDA_DAYS = 30
const RECENT_GRADES = 5
const RECENT_MATERIALS = 5

/** Sotto "Giovedì" la data, sotto "3 dic" il giorno della settimana: mai la stessa informazione due volte. */
function testHint(key) {
	const date = parseDateKey(key)
	return /^\d/.test(relativeDay(key)) ? weekdayName(date) : formatShortDate(date)
}

function StatTile({ label, value, hint, tone = 'neutral' }) {
	return (
		<div className={`subject-stat subject-stat--${tone}`}>
			<small>{label}</small>
			<strong>{value}</strong>
			{hint && <span>{hint}</span>}
		</div>
	)
}

function AgendaSection({ agenda, tests, others }) {
	const { openDetail } = useApp()
	const items = [...tests, ...others]
	return (
		<section aria-labelledby="subject-agenda" className="subject-section">
			<SectionHeading aside={<span className="badge badge--pill badge--soft-case">Prossimi {AGENDA_DAYS} giorni</span>} icon="calendar" id="subject-agenda" title="Verifiche e agenda" />
			{agenda.loading && <Skeleton height={56} lines={2} />}
			{agenda.error && !agenda.data && <ErrorMessage error={agenda.error} onRetry={agenda.reload} title="Agenda non disponibile" />}
			{agenda.data && !items.length && (
				<StateMessage icon="calendar" text={`Nessuna verifica, compito o evento nei prossimi ${AGENDA_DAYS} giorni.`} title="Niente in vista" />
			)}
			{items.length > 0 && (
				<div className="subject-section__list">
					{items.map((item) => (
						<RelatedLink
							icon={item.kind === 'compito' ? 'clipboard' : item.kind === 'verifica' ? 'flag' : 'calendar'}
							key={item.key}
							label={`${item.label} • ${relativeDay(item.date)}${item.ora_inizio && !item.tutto_il_giorno ? `, ${item.ora_inizio}` : ''}`}
							onClick={() => openDetail({ type: 'event', item })}
							tone={item.tone}
							value={item.description || item.title}
						/>
					))}
				</div>
			)}
		</section>
	)
}

function GradesSection({ grades, subject, title }) {
	const [showAll, setShowAll] = useState(false)
	const chronological = subject ? subject.voti.filter(counted).reverse() : []
	// il peso si mostra rispetto a quello ordinario della materia: ClasseViva può mandare 1 o 100 per lo stesso 100%
	const usual = usualWeight(chronological)
	const list = subject ? (showAll ? subject.voti : subject.voti.slice(0, RECENT_GRADES)) : []

	return (
		<section aria-labelledby="subject-grades" className="subject-section">
			<SectionHeading icon="chart" id="subject-grades" title="Voti" />
			{grades.loading && <Skeleton height={64} lines={2} />}
			{grades.error && !grades.data && <ErrorMessage error={grades.error} onRetry={grades.reload} title="Voti non disponibili" />}
			{grades.data && !subject && <StateMessage icon="chart" text="Non ci sono ancora voti registrati per questa materia." title="Nessun voto" />}
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
			{list.length > 0 && (
				<ul className="grade-list">
					{list.map((grade) => (
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
			)}
			{subject && subject.voti.length > RECENT_GRADES && (
				<button aria-expanded={showAll} className="show-more" onClick={() => setShowAll((value) => !value)} type="button">
					<Icon className={`show-more__chevron${showAll ? ' show-more__chevron--up' : ''}`} name="chevronDown" size={15} />
					{showAll ? 'Mostra solo gli ultimi voti' : `Mostra tutti i voti (${subject.voti.length})`}
				</button>
			)}
		</section>
	)
}

function MaterialsSection({ didactics, materials, multipleTeachers }) {
	const { navigate } = useApp()
	return (
		<section aria-labelledby="subject-materials" className="subject-section">
			<SectionHeading
				aside={materials.length > RECENT_MATERIALS && <LinkButton onClick={() => navigate('profilo/materiali')}>Tutti i materiali</LinkButton>}
				icon="book"
				id="subject-materials"
				title="Materiali recenti"
			/>
			{didactics.loading && <Skeleton height={64} lines={2} />}
			{didactics.error && !didactics.data && <ErrorMessage error={didactics.error} onRetry={didactics.reload} title="Materiali non disponibili" />}
			{didactics.data && !materials.length && (
				<StateMessage icon="book" text="I docenti di questa materia non hanno ancora condiviso materiali in Didattica." title="Nessun materiale" />
			)}
			{materials.length > 0 && (
				<ul className="material-list">
					{materials.slice(0, RECENT_MATERIALS).map((material) => (
						<MaterialCard details={materialDetails(material, { teacher: multipleTeachers })} key={material.key} material={material} />
					))}
				</ul>
			)}
		</section>
	)
}

/** Dashboard di una materia: verifiche e agenda, voti, materiali recenti e (Galilei) le ore in orario. */
function SubjectPage({ route }) {
	const { navigate, classId, isGalilei } = useApp()
	const name = route?.subject ?? ''
	const grades = useGrades()
	const agenda = useUpcomingAgenda(AGENDA_DAYS)
	const didactics = useDidactics()
	const schedule = useSchedule(classId)

	const { subject, title, tests, others, slots, teachers, teacherNames, materials } = useMemo(() => subjectOverview({
		name,
		grades: grades.data,
		agendaItems: agenda.items,
		didactics: didactics.data,
		schedule: schedule.data,
		practicalSplit: isGalilei,
	}), [name, grades.data, agenda.items, didactics.data, schedule.data, isGalilei])
	const subtitle = teacherNames.slice(0, 3).map(teacherName).join(', ')
	const nextTest = tests[0]
	const lastGrade = subject?.voti.find((grade) => !grade.annullato)
	const backTab = TABS.find((tab) => tab.id === route?.tab) ?? TABS[0]
	// se la materia è sempre nella stessa aula la si scrive una volta sola
	const rooms = new Set(slots.map((slot) => slot.room))
	const sameRoom = rooms.size === 1 ? slots[0].room : null

	return (
		<div className="page page--subpage subject-page">
			<SubPageHeader
				actions={<span className="icon-tile icon-tile--accent"><Icon name={subjectIcon(title)} size={20} /></span>}
				backLabel={backTab.label}
				onBack={() => navigate(backTab.id)}
				subtitle={subtitle || 'Panoramica della materia'}
				title={title}
			/>

			<div className="subject-stats">
				<StatTile
					hint={subject ? averageLabel(subject.media) : grades.loading ? 'Caricamento…' : 'Nessun voto'}
					label="Media dell'anno"
					tone={subject?.media != null ? gradeTone(subject.media) : 'neutral'}
					value={formatNumber(subject?.media)}
				/>
				<StatTile
					hint={nextTest ? testHint(nextTest.date) : `Nei prossimi ${AGENDA_DAYS} giorni`}
					label="Prossima verifica"
					tone={nextTest ? 'danger' : 'neutral'}
					value={nextTest ? relativeDay(nextTest.date) : agenda.loading ? '…' : 'Nessuna'}
				/>
				<StatTile
					hint={lastGrade ? `Ultimo: ${lastGrade.voto} (${formatShortDate(parseDateKey(lastGrade.data))})` : 'Ancora nessuna'}
					label="Valutazioni"
					value={subject ? subject.voti.length : grades.loading ? '…' : 0}
				/>
			</div>

			{isGalilei && slots.length > 0 && (
				<section aria-labelledby="subject-schedule" className="subject-section">
					<SectionHeading
						aside={sameRoom && <span className="badge badge--pill badge--soft-case">{sameRoom}</span>}
						icon="clock"
						id="subject-schedule"
						title="In orario"
					/>
					<ul className="subject-slots">
						{slots.map((slot) => (
							<li key={slot.key} title={slot.day}>
								<strong>{slot.day.slice(0, 3)} <b>{periodLabel({ ore: slot.hours }).replace(/ Ora$/, '')}</b></strong>
								<span>{[`${slot.inizio}–${slot.fine}`, sameRoom ? null : slot.room].filter(Boolean).join(' • ')}</span>
							</li>
						))}
					</ul>
				</section>
			)}

			<div className="subject-page__grid">
				<div className="subject-page__column">
					<AgendaSection agenda={agenda} others={others} tests={tests} />
					<MaterialsSection didactics={didactics} materials={materials} multipleTeachers={teachers.size > 1} />
				</div>
				<div className="subject-page__column">
					<GradesSection grades={grades} subject={subject} title={title} />
				</div>
			</div>
		</div>
	)
}

export default SubjectPage
