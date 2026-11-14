import { useState } from 'react'
import { Icon } from '../../components/Icon.jsx'
import { ErrorMessage, FilterTabs, Skeleton, StateMessage, SubPageHeader } from '../../components/ui.jsx'
import { useApp } from '../../lib/appContext.js'
import { useAbsences } from '../../lib/data.js'
import { formatLongDate, monthName, parseDateKey, schoolYear } from '../../lib/format.js'

const TYPES = {
	assenza: { label: 'Assenza', icon: 'calendar', tone: 'danger' },
	ritardo: { label: 'Ritardo', icon: 'clock', tone: 'amber' },
	uscita: { label: 'Uscita anticipata', icon: 'logout', tone: 'blue' },
	altro: { label: 'Evento', icon: 'alert', tone: 'neutral' },
}

function eventDetail(event) {
	if (event.tipo === 'assenza') return 'Giornata intera'
	if (event.ora) return event.tipo === 'ritardo' ? `Entrata alla ${event.ora}ª ora` : `Uscita alla ${event.ora}ª ora`
	return ''
}

/** Elenco completo di assenze, ritardi e uscite dell'anno ("Vedi dettagli" di Presenze). */
function AbsencesPage() {
	const { navigate } = useApp()
	const absences = useAbsences()
	const [filter, setFilter] = useState('all')
	const events = absences.data?.eventi ?? []
	const summary = absences.data?.riepilogo

	const count = (match) => events.filter(match).length
	const filters = [
		{ id: 'all', label: 'Tutti', count: events.length, match: () => true },
		{ id: 'assenza', label: 'Assenze', count: count((event) => event.tipo === 'assenza'), match: (event) => event.tipo === 'assenza' },
		{ id: 'ritardo', label: 'Ritardi', count: count((event) => event.tipo === 'ritardo'), match: (event) => event.tipo === 'ritardo' },
		{ id: 'uscita', label: 'Uscite', count: count((event) => event.tipo === 'uscita'), match: (event) => event.tipo === 'uscita' },
		{ id: 'pending', label: 'Da giustificare', count: count((event) => !event.giustificata), match: (event) => !event.giustificata },
	]
	const active = filters.find((option) => option.id === filter) ?? filters[0]
	const visible = events.filter(active.match)

	// raggruppati per mese (gli eventi arrivano già dal più recente)
	const months = []
	for (const event of visible) {
		const date = parseDateKey(event.data)
		const key = date ? `${date.getFullYear()}-${date.getMonth()}` : 'senza-data'
		const label = date ? `${monthName(date)} ${date.getFullYear()}` : 'Senza data'
		const group = months.at(-1)
		if (group?.key === key) group.events.push(event)
		else months.push({ key, label, events: [event] })
	}

	return (
		<div className="page page--subpage">
			<SubPageHeader backLabel="Profilo" onBack={() => navigate('profilo')} subtitle={`Anno scolastico ${schoolYear()}`} title="Presenze & Assenze" />

			{absences.loading && <Skeleton height={70} lines={4} />}
			{absences.error && !absences.data && <ErrorMessage error={absences.error} onRetry={absences.reload} title="Presenze non disponibili" />}

			{summary && (
				<>
					<div className="stat-chips">
						<span className="stat-chip"><strong>{summary.assenze}</strong> assenze</span>
						<span className="stat-chip"><strong>{summary.ritardi}</strong> ritardi</span>
						<span className="stat-chip"><strong>{summary.uscite}</strong> uscite</span>
						<span className={`stat-chip${summary.da_giustificare ? ' stat-chip--amber' : ' stat-chip--good'}`}>
							<strong>{summary.da_giustificare}</strong> da giustificare
						</span>
					</div>
					<FilterTabs label="Tipo di evento" onChange={setFilter} options={filters} value={filter} />
				</>
			)}

			{absences.data && !visible.length && (
				<StateMessage icon="checkCircle" text="Nessun evento per questo filtro." title={filter === 'pending' ? 'Tutto giustificato' : 'Nessun evento'} />
			)}

			{months.map((month) => (
				<section aria-label={month.label} className="day-group" key={month.key}>
					<h2 className="day-group__title"><span>{month.label}</span><small>{month.events.length} {month.events.length === 1 ? 'evento' : 'eventi'}</small></h2>
					<ul className="absence-list">
						{month.events.map((event) => {
							const type = TYPES[event.tipo] ?? TYPES.altro
							const date = parseDateKey(event.data)
							return (
								<li className={`absence-row absence-row--${type.tone}`} key={`${event.id}-${event.data}`}>
									<span className="absence-row__icon"><Icon name={type.icon} size={17} /></span>
									<span className="absence-row__copy">
										<strong>{type.label}</strong>
										<small>{[date ? formatLongDate(date) : null, eventDetail(event)].filter(Boolean).join(' • ')}</small>
										{event.motivo && <em>{event.motivo}</em>}
									</span>
									<span className={`badge ${event.giustificata ? 'badge--accent' : 'badge--amber'}`}>
										{event.giustificata ? (event.tipo === 'ritardo' ? 'Giustificato' : 'Giustificata') : 'Da giustificare'}
									</span>
								</li>
							)
						})}
					</ul>
				</section>
			))}
		</div>
	)
}

export default AbsencesPage
