import { Icon } from './DashboardShared.jsx'

function Profile({ onLogout }) {
	return (
		<section className="alternate-view" aria-labelledby="profile-heading">
			<div className="date-heading"><p>IL TUO ACCOUNT</p><span>Informazioni personali e preferenze</span></div>
			<div className="profile-card"><div className="profile-avatar">MR</div><div><h2 id="profile-heading">Marco Rossi</h2><p>Studente · 4ª Sezione A</p></div></div>
			<div className="profile-details"><span>Istituto</span><strong>Liceo Scientifico A. Righi</strong><span>Indirizzo</span><strong>Scienze Applicate</strong><span>Anno scolastico</span><strong>2024/2025</strong></div>
			<button className="logout-button" onClick={onLogout} type="button"><Icon name="logout" size={17} />Esci dall’account</button>
		</section>
	)
}

export default Profile