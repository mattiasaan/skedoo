/** Rende cliccabile con tastiera un elemento non-button (card che contiene altri pulsanti). */
export function clickableProps(onActivate) {
	if (!onActivate) return {}
	return {
		role: 'button',
		tabIndex: 0,
		onClick: onActivate,
		onKeyDown: (event) => {
			if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
				event.preventDefault()
				onActivate()
			}
		},
	}
}
