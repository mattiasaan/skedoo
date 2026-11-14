import { useMemo, useState } from 'react'
import { TaskCard } from '../../components/Cards.jsx'
import { ErrorMessage, FilterTabs, Skeleton, StateMessage, SubPageHeader } from '../../components/ui.jsx'
import { useApp } from '../../lib/appContext.js'
import { useUpcomingAgenda } from '../../lib/data.js'
import { formatLongDate, parseDateKey, relativeDay } from '../../lib/format.js'

const DAYS = 30

/** Tutti i compiti e le verifiche dei prossimi 30 giorni ("Vedi tutti" della Home). */
function TasksPage() {
	const { navigate, doneTasks, savedTasks } = useApp()
	const agenda = useUpcomingAgenda(DAYS)
	const [filter, setFilter] = useState('all')
	const [hideDone, setHideDone] = useState(false)

	const tasks = useMemo(() => agenda.items.filter((item) => item.kind === 'compito' || item.kind === 'verifica'), [agenda.items])
	const filters = [
		{ id: 'all', label: 'Tutti', count: tasks.length, match: () => true },
		{ id: 'compito', label: 'Compiti', count: tasks.filter((item) => item.kind === 'compito').length, match: (item) => item.kind === 'compito' },
		{ id: 'verifica', label: 'Verifiche', count: tasks.filter((item) => item.kind === 'verifica').length, match: (item) => item.kind === 'verifica' },
		{ id: 'saved', label: 'Salvati', count: tasks.filter((item) => savedTasks[item.key]).length, match: (item) => savedTasks[item.key] },
	]
	const active = filters.find((option) => option.id === filter) ?? filters[0]
	const visible = tasks.filter((item) => active.match(item) && !(hideDone && doneTasks[item.key]))
	const doneCount = tasks.filter((item) => doneTasks[item.key]).length

	const groups = []
	for (const item of visible) {
		const group = groups.at(-1)
		if (group?.date === item.date) group.items.push(item)
		else groups.push({ date: item.date, items: [item] })
	}

	return (
		<div className="page page--subpage">
			<SubPageHeader
				backLabel="Home"
				onBack={() => navigate('home')}
				subtitle={`Prossimi ${DAYS} giorni dall'agenda ClasseViva`}
				title="Compiti & Verifiche"
			/>

			<div className="subpage-toolbar">
				<FilterTabs label="Tipo" onChange={setFilter} options={filters} value={filter} />
				{doneCount > 0 && (
					<label className="check-toggle">
						<input checked={hideDone} onChange={(event) => setHideDone(event.target.checked)} type="checkbox" />
						Nascondi completati ({doneCount})
					</label>
				)}
			</div>

			{agenda.loading && <Skeleton height={130} lines={3} />}
			{agenda.error && !agenda.data && <ErrorMessage error={agenda.error} onRetry={agenda.reload} title="Agenda non disponibile" />}
			{agenda.data && !groups.length && (
				<StateMessage
					icon="checkCircle"
					text={filter === 'saved' ? 'Usa il segnalibro su una verifica per ritrovarla qui.' : 'Niente in agenda per questo filtro.'}
					title="Nessun elemento"
				/>
			)}

			{groups.map((group) => (
				<section aria-label={formatLongDate(parseDateKey(group.date))} className="day-group" key={group.date}>
					<h2 className="day-group__title">
						<span>{relativeDay(group.date)}</span>
						<small>{formatLongDate(parseDateKey(group.date))}</small>
					</h2>
					<div className="task-list">
						{group.items.map((item) => <TaskCard item={item} key={item.key} />)}
					</div>
				</section>
			))}
		</div>
	)
}

export default TasksPage
