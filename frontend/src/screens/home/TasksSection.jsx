import { TaskCard } from '../../components/Cards.jsx'
import { ErrorMessage, LinkButton, SectionHeading, Skeleton, StateMessage } from '../../components/ui.jsx'
import { useApp } from '../../lib/appContext.js'
import { useUpcomingAgenda } from '../../lib/data.js'

/** "Compiti & Verifiche": prossimi compiti e verifiche dall'agenda ClasseViva. */
export function TasksSection({ limit = 3 }) {
	const { navigate } = useApp()
	const agenda = useUpcomingAgenda()
	const tasks = agenda.items.filter((item) => item.kind === 'compito' || item.kind === 'verifica').slice(0, limit)

	return (
		<section className="home-section home-section--tasks" aria-labelledby="tasks-heading">
			<SectionHeading
				aside={<LinkButton onClick={() => navigate('home/compiti')}>Vedi tutti</LinkButton>}
				icon="clipboard"
				id="tasks-heading"
				title="Compiti & Verifiche"
			/>
			{agenda.loading && <Skeleton height={150} lines={2} />}
			{agenda.error && !agenda.data && <ErrorMessage error={agenda.error} onRetry={agenda.reload} title="Agenda non disponibile" />}
			{agenda.data && (tasks.length ? (
				<div className="task-list">
					{tasks.map((item) => <TaskCard item={item} key={item.key} />)}
				</div>
			) : (
				<StateMessage icon="checkCircle" text="Nelle prossime due settimane non ci sono compiti o verifiche in agenda." title="Tutto in ordine" />
			))}
		</section>
	)
}

export default TasksSection
