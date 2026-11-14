import { useRef, useState } from 'react'

const THRESHOLD = 56 // px di trascinamento per cambiare pagina
const WHEEL_THRESHOLD = 70 // deltaX accumulato dal trackpad
const WHEEL_COOLDOWN = 450 // ms: uno swipe del trackpad genera decine di eventi, ne conta uno solo

/**
 * Scorrimento orizzontale per calendari: dito, trascinamento col mouse e swipe del trackpad.
 * Restituisce gli handler da spargere sul contenitore e lo spostamento corrente (`offset`)
 * per far seguire il dito al contenuto. Lo scroll verticale della pagina resta libero
 * (serve `touch-action: pan-y` nel CSS).
 */
export function useSwipe({ onPrev, onNext }) {
	const [offset, setOffset] = useState(0)
	const [dragging, setDragging] = useState(false)
	const start = useRef(null)
	const swiped = useRef(false)
	const wheel = useRef({ total: 0, lockedUntil: 0 })

	function finish(dx) {
		start.current = null
		setDragging(false)
		setOffset(0)
		if (Math.abs(dx) < THRESHOLD) return
		swiped.current = true
		if (dx < 0) onNext()
		else onPrev()
	}

	const handlers = {
		onPointerDown(event) {
			if (event.pointerType === 'mouse' && event.button !== 0) return
			start.current = { x: event.clientX, y: event.clientY, horizontal: null }
			swiped.current = false
		},
		onPointerMove(event) {
			const origin = start.current
			if (!origin) return
			const dx = event.clientX - origin.x
			const dy = event.clientY - origin.y
			// si decide la direzione al primo movimento apprezzabile: se è verticale si lascia scorrere la pagina
			if (origin.horizontal == null && Math.hypot(dx, dy) > 8) origin.horizontal = Math.abs(dx) > Math.abs(dy)
			if (!origin.horizontal) return
			setDragging(true)
			setOffset(dx)
		},
		onPointerUp(event) {
			const origin = start.current
			if (!origin) return
			finish(origin.horizontal ? event.clientX - origin.x : 0)
		},
		onPointerCancel() {
			if (start.current) finish(0)
		},
		onPointerLeave(event) {
			const origin = start.current
			if (origin && event.pointerType === 'mouse') finish(origin.horizontal ? event.clientX - origin.x : 0)
		},
		// dopo uno swipe il rilascio non deve contare come tocco sul giorno sotto il dito
		onClickCapture(event) {
			if (!swiped.current) return
			swiped.current = false
			event.preventDefault()
			event.stopPropagation()
		},
		onWheel(event) {
			if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return
			const state = wheel.current
			const now = Date.now()
			if (now < state.lockedUntil) return
			state.total += event.deltaX
			if (Math.abs(state.total) < WHEEL_THRESHOLD) return
			if (state.total > 0) onNext()
			else onPrev()
			state.total = 0
			state.lockedUntil = now + WHEEL_COOLDOWN
		},
		onDragStart(event) {
			event.preventDefault()
		},
	}

	return { handlers, offset, dragging }
}
