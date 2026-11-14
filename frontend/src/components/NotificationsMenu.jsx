import { useEffect, useMemo, useRef, useState } from 'react'
import { boardKey } from '../lib/agenda.js'
import { useApp } from '../lib/appContext.js'
import { useBoard, useChanges } from '../lib/data.js'
import { dateKey, formatDateTime } from '../lib/format.js'
import { readJson, writeJson } from '../lib/session.js'
import { Icon } from './Icon.jsx'

const MAX_BOARD_ITEMS = 6

/** Campanella in alto: variazioni d'orario di oggi e circolari non lette. */
export function NotificationsMenu() {
	const { classId, openDetail, navigate, isBoardRead, alertsOn } = useApp()
	const changes = useChanges(classId)
	const board = useBoard()
	const [open, setOpen] = useState(false)
	const [seen, setSeen] = useState(() => readJson('notifications-seen', {}))
	const rootRef = useRef(null)

	const todayChanges = useMemo(() => (changes.data ?? []).filter((change) => change.data === dateKey()), [changes.data])
	const items = useMemo(() => [
		...todayChanges.map((change) => ({ id: `change-${change.id}`, kind: 'change', title: 'Variazione orario', text: change.testo })),
		...(board.data?.elementi ?? [])
			.filter((item) => !isBoardRead(item))
			.slice(0, MAX_BOARD_ITEMS)
			.map((item) => ({ id: `board-${boardKey(item)}`, kind: 'board', title: item.categoria || 'Circolare', text: item.titolo, when: item.pubblicato_il, item })),
	], [todayChanges, board.data, isBoardRead])

	// preferenza "Avvisi" del Profilo: se spenta, niente contatore sulla campanella
	const unseen = alertsOn ? items.filter((item) => !seen[item.id]).length : 0

	useEffect(() => {
		if (!open) return undefined
		const onPointer = (event) => {
			if (!rootRef.current?.contains(event.target)) setOpen(false)
		}
		const onKey = (event) => {
			if (event.key === 'Escape') setOpen(false)
		}
		document.addEventListener('pointerdown', onPointer)
		document.addEventListener('keydown', onKey)
		return () => {
			document.removeEventListener('pointerdown', onPointer)
			document.removeEventListener('keydown', onKey)
		}
	}, [open])

	function toggle() {
		if (!open) {
			const next = Object.fromEntries(items.map((item) => [item.id, true]))
			setSeen(next)
			writeJson('notifications-seen', next)
		}
		setOpen(!open)
	}

	function select(item) {
		setOpen(false)
		if (item.kind === 'board') openDetail({ type: 'board', item: item.item })
		else openDetail({ type: 'changes', changes: todayChanges })
	}

	return (
		<div className="notifications" ref={rootRef}>
			<button
				aria-expanded={open}
				aria-label={`Notifiche${unseen ? ` (${unseen} nuove)` : ''}`}
				className={`icon-button notifications__button${open ? ' notifications__button--active' : ''}`}
				onClick={toggle}
				type="button"
			>
				<Icon name="bell" size={19} />
				{unseen > 0 && <span className="notifications__count">{Math.min(unseen, 9)}</span>}
			</button>
			{open && (
				<div aria-label="Notifiche" className="notifications__popover" role="region">
					<strong className="notifications__title">Notifiche</strong>
					{items.length ? (
						<ul>
							{items.map((item) => (
								<li key={item.id}>
									<button onClick={() => select(item)} type="button">
										<span className={`notifications__icon notifications__icon--${item.kind}`}>
											<Icon name={item.kind === 'board' ? 'megaphone' : 'swap'} size={16} />
										</span>
										<span>
											<small>{item.title}{item.when ? ` • ${formatDateTime(item.when)}` : ''}</small>
											<b>{item.text}</b>
										</span>
									</button>
								</li>
							))}
						</ul>
					) : <p className="notifications__empty">Nessuna novità: sei in pari!</p>}
					<button
						className="notifications__all"
						onClick={() => {
							setOpen(false)
							navigate('home/bacheca')
						}}
						type="button"
					>
						Vai alla bacheca <Icon name="chevron" size={15} />
					</button>
				</div>
			)}
		</div>
	)
}

export default NotificationsMenu
