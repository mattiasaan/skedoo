import { useState } from 'react'
import { Icon } from './DashboardShared.jsx'
import { logout } from './api/logout'

const materials = [
    { name: 'Dispensa_Meccanica_Quantisti...', teacher: 'Prof. Rossi', size: '2.4 MB', tone: 'green', type: 'Documento' },
    { name: 'Schema_Illuminismo_Kant.pdf', teacher: 'Prof. Castelli', size: '1.1 MB', tone: 'blue', type: 'PDF' },
    { name: 'Simulazione_Verifica_Matemati...', teacher: 'Prof.ssa Bianchi', size: '850 KB', tone: 'green', type: 'Documento' },
]

function Profile({ onLogout }) {
    const [notificationsEnabled, setNotificationsEnabled] = useState(true)
    const [showSyncNotice, setShowSyncNotice] = useState(false)
    const [loading, setLoading] = useState(false)

    async function handleLogout() {
        try {
            setLoading(true)
            await logout() // Chiama l'endpoint di logout e pulisce il localStorage
        } catch (e) {
            console.error("Errore durante il logout dal server:", e.message)
            // Fallback di sicurezza locale in caso di errore di rete
            localStorage.removeItem("token")
            localStorage.removeItem("utente")
            localStorage.removeItem("selectedClassId")
        } finally {
            setLoading(false)
            if (onLogout) {
                onLogout() // Riporta l'utente alla schermata di Login tramite App.jsx
            }
        }
    }

    return (
        <section className="alternate-view profile-view" aria-labelledby="profile-heading">
            <div className="date-heading"><p>IL TUO ACCOUNT</p><span>Informazioni personali e preferenze</span></div>

            <article className="student-profile-card">
                <div className="student-avatar-wrap">
                    <div className="student-avatar">AM</div>
                    <span className="avatar-check"><Icon name="check" size={12} /></span>
                </div>
                <h2 id="profile-heading">Alex Moretti</h2>
                <p>Liceo Scientifico A. Righi (RM) · 4ª Sezione A</p>
                <span className="account-connected"><i />Account collegato a Spaggiari ClasseViva</span>
                <div className="student-meta"><span>Cod. CV: <strong>8849201</strong></span><i />A.S. 2024/2025<i /><span className="regular-status"><i />Stato Regolare</span></div>
            </article>

            <section className="profile-section" aria-labelledby="attendance-heading">
                <div className="profile-section-heading">
                    <h3 id="attendance-heading"><Icon name="clock" size={18} />Quadro Presenze &amp; Assenze</h3>
                    <span className="profile-period">I quadrimestre</span>
                </div>
                <div className="attendance-grid">
                    <article className="attendance-card"><div><span>Assenze</span><Icon name="calendar" size={15} /></div><p><strong>4</strong> gg</p><small>3 giustif. · 1 da giust.</small></article>
                    <article className="attendance-card"><div><span>Ritardi</span><Icon name="clock" size={15} /></div><p><strong>2</strong> volte</p><small>Entrate posticipate</small></article>
                    <article className="attendance-card"><div><span>Uscite</span><Icon name="logout" size={15} /></div><p><strong>1</strong> volta</p><small>Con firma genitore</small></article>
                </div>
            </section>

            <section className="profile-section" aria-labelledby="materials-heading">
                <div className="profile-section-heading">
                    <h3 id="materials-heading"><Icon name="task" size={18} />Didattica &amp; Materiali Condivisi</h3>
                    <span className="materials-total">Vedi tutti (12)</span>
                </div>
                <div className="material-list">
                    {materials.map((material) => (
                        <article className="material-card" key={material.name}>
                            <span className={`material-file-icon material-file-icon--${material.tone}`}><Icon name="task" size={18} /></span>
                            <div><strong>{material.name}</strong><span>{material.teacher} · {material.size}</span></div>
                            <span aria-hidden="true" className="material-download" title={`${material.type} · download non disponibile in modalità demo`}><Icon name="download" size={17} /></span>
                        </article>
                    ))}
                </div>
            </section>

            <section className="profile-section" aria-labelledby="preferences-heading">
                <div className="profile-section-heading"><h3 id="preferences-heading"><Icon name="bell" size={18} />Impostazioni &amp; Notifiche</h3></div>
                <div className="profile-settings">
                    <label className="profile-setting">
                        <Icon name="alert" size={18} />
                        <span><strong>Avvisi Cambi Orario &amp; Supplenze</strong><small>Ricevi alert push istantanei quando varia la didattica</small></span>
                        <input checked={notificationsEnabled} onChange={(event) => setNotificationsEnabled(event.target.checked)} type="checkbox" />
                        <i className="profile-switch" aria-hidden="true"><span /></i>
                    </label>
                    <button className="profile-sync-row" onClick={() => setShowSyncNotice(true)} type="button">
                        <span className="profile-sync-icon"><Icon name="trend" size={17} /></span>
                        <span><strong>Sincronizza Dati ClasseViva Ora</strong><small>Ultimo sync: Oggi, alle 13:42</small></span>
                        <Icon name="chevron" size={17} />
                    </button>
                    {showSyncNotice && <p className="profile-sync-notice" role="status">Sincronizzazione non disponibile: collega il registro per aggiornare i dati.</p>}
                </div>
            </section>

            <button 
                className="logout-button profile-logout" 
                onClick={handleLogout} 
                type="button"
                disabled={loading}
            >
                <Icon name="logout" size={17} />
                {loading ? 'Disconnessione in corso...' : 'Logout dal Profilo'}
            </button>
        </section>
    )
}

export default Profile