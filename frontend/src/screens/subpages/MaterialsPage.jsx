import { useMemo, useState } from 'react'
import { Icon } from '../../components/Icon.jsx'
import { ErrorMessage, SearchField, Skeleton, StateMessage, SubPageHeader } from '../../components/ui.jsx'
import { useApp } from '../../lib/appContext.js'
import { useDidactics } from '../../lib/data.js'
import { materialType } from '../../lib/didactics.js'
import { formatDateTime, normalizeText, teacherName } from '../../lib/format.js'

/** Materiali condivisi dai docenti, raggruppati per docente e cartella ("Vedi tutti" del Profilo). */
function MaterialsPage() {
	const { navigate } = useApp()
	const didactics = useDidactics()
	const [query, setQuery] = useState('')
	const needle = normalizeText(query)

	const teachers = useMemo(() => (didactics.data?.docenti ?? [])
		.map((teacher) => ({
			...teacher,
			cartelle: teacher.cartelle
				.map((folder) => ({
					...folder,
					materiali: folder.materiali.filter((material) =>
						!needle || normalizeText(`${material.nome} ${folder.nome} ${teacher.nome}`).includes(needle)),
				}))
				.filter((folder) => folder.materiali.length),
		}))
		.filter((teacher) => teacher.cartelle.length), [didactics.data, needle])
	const total = teachers.reduce((sum, teacher) => sum + teacher.cartelle.reduce((count, folder) => count + folder.materiali.length, 0), 0)

	return (
		<div className="page page--subpage">
			<SubPageHeader backLabel="Profilo" onBack={() => navigate('profilo')} subtitle="Condivisi dai docenti su ClasseViva" title="Didattica & Materiali" />

			<SearchField label="Cerca materiali" onChange={setQuery} placeholder="Cerca per nome, cartella o docente" value={query} />

			{didactics.loading && <Skeleton height={64} lines={4} />}
			{didactics.error && !didactics.data && <ErrorMessage error={didactics.error} onRetry={didactics.reload} title="Materiali non disponibili" />}
			{didactics.data && !total && (
				<StateMessage icon="book" text={query ? 'Nessun materiale corrisponde alla ricerca.' : 'I docenti non hanno ancora condiviso materiali.'} title="Nessun materiale" />
			)}

			{teachers.map((teacher) => (
				<section aria-label={teacher.nome ?? 'Docente'} className="day-group" key={teacher.id ?? teacher.nome}>
					<h2 className="day-group__title">
						<span>{teacher.nome ? teacherName(teacher.nome) : 'Docente'}</span>
						<small>{teacher.cartelle.length} {teacher.cartelle.length === 1 ? 'cartella' : 'cartelle'}</small>
					</h2>
					{teacher.cartelle.map((folder) => (
						<div className="folder" key={folder.id ?? folder.nome}>
							<p className="folder__name"><Icon name="book" size={15} />{folder.nome || 'Senza cartella'}</p>
							<ul className="material-list">
								{folder.materiali.map((material) => {
									const type = materialType(material)
									return (
										<li className="material-card" key={material.id ?? material.nome}>
											<span className={`icon-tile icon-tile--${type.tone}`}><Icon name={type.icon} size={18} /></span>
											<span className="material-card__copy">
												<strong title={material.nome}>{material.nome || 'Materiale senza titolo'}</strong>
												<small>{[type.label, material.condiviso_il ? formatDateTime(material.condiviso_il) : null].filter(Boolean).join(' • ')}</small>
											</span>
										</li>
									)
								})}
							</ul>
						</div>
					))}
				</section>
			))}

			{didactics.data && total > 0 && (
				<p className="detail-hint">Per aprire o scaricare un materiale usa l'app o il sito ClasseViva.</p>
			)}
		</div>
	)
}

export default MaterialsPage
