import { useMemo, useState } from 'react'
import { Icon } from '../../components/Icon.jsx'
import { ErrorMessage, FilterTabs, SearchField, Skeleton, StateMessage, SubPageHeader } from '../../components/ui.jsx'
import { boardKey } from '../../lib/agenda.js'
import { useApp } from '../../lib/appContext.js'
import { useBoard } from '../../lib/data.js'
import { useToast } from '../../lib/toast.js'
import { formatDateTime, normalizeText } from '../../lib/format.js'

/** Tutte le comunicazioni della bacheca ClasseViva, con ricerca e filtro "da leggere". */
function BoardPage() {
	const { navigate, openDetail, isBoardRead } = useApp()
	const toast = useToast()
	const board = useBoard()
	const [filter, setFilter] = useState('all')
	const [query, setQuery] = useState('')

	async function refresh() {
		const ok = await board.reload()
		toast(ok ? 'Bacheca aggiornata' : 'Aggiornamento non riuscito, riprova tra poco', { tone: ok ? 'success' : 'error' })
	}

	const items = useMemo(
		() => [...(board.data?.elementi ?? [])].sort((a, b) => String(b.pubblicato_il ?? '').localeCompare(String(a.pubblicato_il ?? ''))),
		[board.data],
	)
	const unread = items.filter((item) => !isBoardRead(item)).length
	const needle = normalizeText(query)
	const visible = items.filter((item) =>
		(filter === 'all' || !isBoardRead(item))
		&& (!needle || normalizeText(`${item.titolo} ${item.categoria}`).includes(needle)))

	return (
		<div className="page page--subpage">
			<SubPageHeader
				actions={(
					<button className={`sync-button${board.refreshing ? ' sync-button--busy' : ''}`} disabled={board.refreshing} onClick={refresh} type="button">
						<Icon name="refresh" size={16} />
						Aggiorna
					</button>
				)}
				backLabel="Home"
				onBack={() => navigate('home')}
				subtitle="Circolari e comunicazioni della scuola"
				title="Bacheca"
			/>

			<div className="subpage-toolbar">
				<FilterTabs
					label="Stato"
					onChange={setFilter}
					options={[{ id: 'all', label: 'Tutte', count: items.length }, { id: 'unread', label: 'Da leggere', count: unread }]}
					value={filter}
				/>
				<SearchField label="Cerca nella bacheca" onChange={setQuery} placeholder="Cerca per titolo o categoria" value={query} />
			</div>

			{board.loading && <Skeleton height={76} lines={4} />}
			{board.error && !board.data && <ErrorMessage error={board.error} onRetry={board.reload} title="Bacheca non disponibile" />}
			{board.data && !visible.length && (
				<StateMessage
					icon="megaphone"
					text={query ? 'Nessuna comunicazione corrisponde alla ricerca.' : 'Hai letto tutte le comunicazioni.'}
					title={query ? 'Nessun risultato' : 'Tutto letto'}
				/>
			)}

			<ul className="board-list">
				{visible.map((item) => {
					const read = isBoardRead(item)
					return (
						<li key={boardKey(item)}>
							<button className={`board-row${read ? '' : ' board-row--unread'}`} onClick={() => openDetail({ type: 'board', item })} type="button">
								<span className="board-row__icon"><Icon name="megaphone" size={18} /></span>
								<span className="board-row__copy">
									<span className="board-row__meta">
										<span className="badge badge--accent">{item.categoria || 'Comunicazione'}</span>
										{item.pubblicato_il && <small>{formatDateTime(item.pubblicato_il)}</small>}
									</span>
									<strong>{item.titolo || 'Comunicazione senza titolo'}</strong>
									{item.allegati?.length > 0 && (
										<small className="board-row__attachments">
											<Icon name="file" size={13} />
											{item.allegati.length} {item.allegati.length === 1 ? 'allegato' : 'allegati'}
										</small>
									)}
								</span>
								{!read && <span className="board-row__dot" aria-label="Da leggere" />}
								<Icon name="chevron" size={17} />
							</button>
						</li>
					)
				})}
			</ul>
		</div>
	)
}

export default BoardPage
