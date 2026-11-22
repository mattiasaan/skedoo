import { api } from '../lib/api.js'
import { useApp } from '../lib/appContext.js'
import { materialType } from '../lib/didactics.js'
import { useDownload } from '../lib/useDownload.js'
import { Icon } from './Icon.jsx'

/** A destra della riga: l'icona dell'azione, oppure l'avanzamento mentre il file arriva. */
function DownloadState({ progress, icon }) {
	if (progress === undefined) return <Icon className="download-state__icon" name={icon} size={17} />
	return (
		<span className="download-state" role="status">
			<span aria-hidden="true" className="download-state__spinner" />
			{progress == null ? 'Download…' : `${Math.round(progress * 100)}%`}
		</span>
	)
}

/** Materiale della didattica: al tocco si scarica (file), si apre (link) o se ne legge il testo. */
export function MaterialCard({ material, details }) {
	const { openDetail } = useApp()
	const download = useDownload()
	const type = materialType(material)
	const key = `material-${material.id}`
	const progress = download.progress(key)
	const name = material.nome || 'Materiale senza titolo'

	function open() {
		download.start({
			key,
			name: material.nome,
			link: material.tipo === 'link',
			fetch: (onProgress) => api.material(material.id, { onProgress }),
			onText: (text) => openDetail({ type: 'text', kicker: 'Materiale', title: name, text }),
		})
	}

	return (
		<li>
			<button
				aria-busy={progress !== undefined}
				className="material-card material-card--action"
				disabled={material.id == null}
				onClick={open}
				type="button"
			>
				<span className={`icon-tile icon-tile--${type.tone}`}><Icon name={type.icon} size={18} /></span>
				<span className="material-card__copy">
					<span className="visually-hidden">{type.verb}: </span>
					<strong title={name}>{name}</strong>
					{details && <small>{details}</small>}
				</span>
				<DownloadState icon={type.action} progress={progress} />
			</button>
		</li>
	)
}

/** Allegato di una comunicazione della bacheca: al tocco si scarica. */
export function AttachmentButton({ item, attachment }) {
	const download = useDownload()
	const key = `board-${item.codice}-${item.id}-${attachment.numero}`
	const progress = download.progress(key)
	const name = attachment.nome || `Allegato ${attachment.numero}`

	return (
		<li>
			<button
				aria-busy={progress !== undefined}
				className="attachment-button"
				disabled={!item.codice || item.id == null}
				onClick={() => download.start({
					key,
					name: attachment.nome,
					fetch: (onProgress) => api.boardAttachment(item.codice, item.id, attachment.numero, { onProgress }),
				})}
				type="button"
			>
				<Icon name="file" size={16} />
				<span><span className="visually-hidden">Scarica </span>{name}</span>
				<DownloadState icon="download" progress={progress} />
			</button>
		</li>
	)
}
