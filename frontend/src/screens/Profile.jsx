import { useMemo, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { ErrorMessage, LinkButton, SectionHeading, Skeleton, StateMessage } from '../components/ui.jsx'
import { useApp } from '../lib/appContext.js'
import { useAbsences, useDidactics } from '../lib/data.js'
import { flattenMaterials, materialType } from '../lib/didactics.js'
import { classLabel, dateKey, formatDateTime, initials, schoolDisplayName, schoolYear, teacherName, titleCase } from '../lib/format.js'
import { readJson, writeJson } from '../lib/session.js'
import { useToast } from '../lib/toast.js'
import { clearApiCache } from '../lib/useApi.js'

const PREVIEW_MATERIALS = 3

function ProfileCard() {
	const { user, classId } = useApp()
	const absences = useAbsences()
	const pending = absences.data?.riepilogo?.da_giustificare ?? 0
	const school = user?.scuola
	const schoolLine = [
		school ? `${schoolDisplayName(school)}${school.provincia ? ` (${school.provincia})` : ''}` : null,
		classId ? classLabel(classId).replace(/ª /, 'ª Sezione ') : null,
	].filter(Boolean).join(' • ')

	return (
		<article className="card profile-card">
			<div className="profile-card__avatar">
				<span className="avatar avatar--large">{initials(user?.nome, user?.cognome)}</span>
				<span className="profile-card__verified"><Icon name="check" size={13} strokeWidth={2.6} /></span>
			</div>
			<h1 id="profile-heading">{titleCase([user?.nome, user?.cognome].filter(Boolean).join(' ')) || 'Studente'}</h1>
			{schoolLine && <p className="profile-card__school">{schoolLine}</p>}
			<span className="profile-card__linked"><span className="live-dot" aria-hidden="true" />Account collegato a Spaggiari ClasseViva</span>
			<div className="profile-card__meta">
				<span>Cod. CV: <strong>{user?.id ?? '—'}</strong></span>
				<i aria-hidden="true">•</i>
				<span>A.S. {schoolYear()}</span>
				<i aria-hidden="true">•</i>
				{absences.data
					? <span className={pending ? 'tone-text--amber' : 'tone-text--good'}><span className="status-dot" aria-hidden="true" />{pending ? `${pending} da giustificare` : 'Stato Regolare'}</span>
					: <span>Stato in verifica</span>}
			</div>
		</article>
	)
}

function AttendanceSection() {
	const { navigate } = useApp()
	const absences = useAbsences()
	const events = absences.data?.eventi ?? []
	const summary = absences.data?.riepilogo
	const byType = (type) => events.filter((event) => event.tipo === type)
	const absent = byType('assenza')
	const justified = absent.filter((event) => event.giustificata).length
	const exitsPending = byType('uscita').filter((event) => !event.giustificata).length
	const latePending = byType('ritardo').filter((event) => !event.giustificata).length

	return (
		<section className="profile-section" aria-labelledby="attendance-heading">
			<SectionHeading aside={<LinkButton onClick={() => navigate('profilo/assenze')}>Dettagli</LinkButton>} icon="pulse" id="attendance-heading" title="Presenze & Assenze" />
			{absences.loading && <Skeleton height={130} lines={1} />}
			{absences.error && !absences.data && <ErrorMessage error={absences.error} onRetry={absences.reload} title="Presenze non disponibili" />}
			{summary && (
				<div className="attendance-grid">
					<article className="attendance-card">
						<div><span>Assenze</span><Icon name="calendar" size={16} /></div>
						<p><strong>{summary.assenze}</strong> gg</p>
						<small className={absent.length - justified ? 'attendance-card__tag attendance-card__tag--amber' : 'attendance-card__tag'}>
							{justified} giustif. • {absent.length - justified} da giust.
						</small>
					</article>
					<article className="attendance-card">
						<div><span>Ritardi</span><Icon name="clock" size={16} /></div>
						<p><strong>{summary.ritardi}</strong> {summary.ritardi === 1 ? 'volta' : 'volte'}</p>
						<small className={latePending ? 'attendance-card__tag attendance-card__tag--amber' : 'attendance-card__tag'}>
							{latePending ? `${latePending} da giustificare` : 'Entrate posticipate'}
						</small>
					</article>
					<article className="attendance-card">
						<div><span>Uscite</span><Icon name="logout" size={16} /></div>
						<p><strong>{summary.uscite}</strong> {summary.uscite === 1 ? 'volta' : 'volte'}</p>
						<small className={exitsPending ? 'attendance-card__tag attendance-card__tag--amber' : 'attendance-card__tag attendance-card__tag--blue'}>
							{exitsPending ? `${exitsPending} da giustificare` : 'Uscite anticipate'}
						</small>
					</article>
				</div>
			)}
		</section>
	)
}

function MaterialsSection() {
	const { navigate } = useApp()
	const didactics = useDidactics()
	const materials = useMemo(() => flattenMaterials(didactics.data), [didactics.data])
	const visible = materials.slice(0, PREVIEW_MATERIALS)

	return (
		<section className="profile-section" aria-labelledby="materials-heading">
			<SectionHeading
				aside={materials.length > PREVIEW_MATERIALS && (
					<LinkButton onClick={() => navigate('profilo/materiali')}>Vedi tutti ({materials.length})</LinkButton>
				)}
				icon="book"
				id="materials-heading"
				title="Didattica & Materiali Condivisi"
			/>
			{didactics.loading && <Skeleton height={68} lines={3} />}
			{didactics.error && !didactics.data && <ErrorMessage error={didactics.error} onRetry={didactics.reload} title="Materiali non disponibili" />}
			{didactics.data && (materials.length ? (
				<ul className="material-list">
					{visible.map((material) => {
						const type = materialType(material)
						return (
							<li className="material-card" key={material.key}>
								<span className={`icon-tile icon-tile--${type.tone}`}><Icon name={type.icon} size={18} /></span>
								<span className="material-card__copy">
									<strong title={material.nome}>{material.nome || 'Materiale senza titolo'}</strong>
									<small>
										{[material.teacher ? teacherName(material.teacher) : null, material.folder, material.condiviso_il ? formatDateTime(material.condiviso_il) : null]
											.filter(Boolean).join(' • ')}
									</small>
								</span>
							</li>
						)
					})}
				</ul>
			) : (
				<StateMessage icon="book" text="I docenti non hanno ancora condiviso materiali." title="Nessun materiale" />
			))}
		</section>
	)
}

function SettingsSection() {
	const { isGalilei, classId, onChangeClass, alertsOn, setAlertsOn } = useApp()
	const toast = useToast()
	const [lastSync, setLastSync] = useState(() => readJson('last-sync', null))

	function toggleAlerts(value) {
		setAlertsOn(value)
		toast(value ? 'Avvisi attivati' : 'Avvisi disattivati: la campanella non mostrerà il contatore', { tone: 'info' })
	}

	function syncNow() {
		const date = new Date()
		const now = `${dateKey(date)}T${date.toTimeString().slice(0, 5)}`
		// svuotando la cache ogni schermata richiede di nuovo i dati quando viene mostrata
		clearApiCache()
		setLastSync(now)
		writeJson('last-sync', now)
		toast('Dati in aggiornamento da ClasseViva')
	}

	const syncLabel = lastSync ? `Ultimo sync: ${formatDateTime(lastSync)}` : 'Aggiorna voti, agenda, assenze e bacheca'

	return (
		<section className="profile-section" aria-labelledby="settings-heading">
			<SectionHeading icon="gear" id="settings-heading" title="Impostazioni & Notifiche" />
			<div className="settings-card">
				<label className="settings-row">
					<span className="settings-row__icon settings-row__icon--plain"><Icon name="swap" size={19} /></span>
					<span className="settings-row__copy">
						<strong>Avvisi Cambi Orario &amp; Supplenze</strong>
						<small>Mostra il badge delle notifiche quando cambia l'orario o arriva una circolare</small>
					</span>
					<input checked={alertsOn} className="switch__input" onChange={(event) => toggleAlerts(event.target.checked)} type="checkbox" />
					<span className="switch" aria-hidden="true"><span /></span>
				</label>
				{isGalilei && (
					<button className="settings-row" onClick={onChangeClass} type="button">
						<span className="settings-row__icon"><Icon name="users" size={18} /></span>
						<span className="settings-row__copy">
							<strong>Classe: {classLabel(classId)}</strong>
							<small>Cambia la classe usata per orario e variazioni</small>
						</span>
						<Icon className="settings-row__chevron" name="chevron" size={18} />
					</button>
				)}
				<button className="settings-row" onClick={syncNow} type="button">
					<span className="settings-row__icon"><Icon name="refresh" size={18} /></span>
					<span className="settings-row__copy">
						<strong>Sincronizza Dati ClasseViva Ora</strong>
						<small>{syncLabel}</small>
					</span>
					<Icon className="settings-row__chevron" name="chevron" size={18} />
				</button>
			</div>
		</section>
	)
}

function Profile() {
	const { openDetail } = useApp()

	return (
		<div className="page page--profile" aria-labelledby="profile-heading">
			<div className="profile-layout">
				<div className="profile-layout__main">
					<ProfileCard />
					<AttendanceSection />
				</div>
				<div className="profile-layout__side">
					<MaterialsSection />
					<SettingsSection />
					<button className="logout-button" onClick={() => openDetail({ type: 'logout' })} type="button">
						<Icon name="logout" size={18} />
						Logout dal Profilo
					</button>
				</div>
			</div>
		</div>
	)
}

export default Profile
