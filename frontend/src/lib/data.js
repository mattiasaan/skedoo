import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import { flattenAgenda, monthRange, upcomingRange } from './agenda.js'
import { readJson, writeJson } from './session.js'
import { useApi } from './useApi.js'

// Ogni hook ha una chiave di cache: due schermate che chiedono gli stessi dati fanno una sola richiesta.

export function useSchedule(classId) {
	return useApi(classId ? `schedule:${classId}` : null, () => api.schedule(classId))
}

/** Variazioni della classe (cambi aula, entrate/uscite). Se il file della bacheca manca, nessuna variazione. */
export function useChanges(classId) {
	return useApi(classId ? `changes:${classId}` : null, () =>
		api.changes(classId).catch((error) => {
			if (error.status === 503) return []
			throw error
		}),
	)
}

export function useUpcomingAgenda() {
	const range = upcomingRange()
	const result = useApi(`agenda:${range.da}:${range.a}`, () => api.agenda(range.da, range.a))
	const items = useMemo(() => flattenAgenda(result.data), [result.data])
	return { ...result, items }
}

export function useMonthAgenda(date) {
	const range = monthRange(date)
	const result = useApi(`agenda:${range.da}:${range.a}`, () => api.agenda(range.da, range.a))
	const items = useMemo(() => flattenAgenda(result.data), [result.data])
	return { ...result, items, range }
}

export const useGrades = () => useApi('grades', api.grades)
export const useAbsences = () => useApi('absences', api.absences)
export const useBoard = () => useApi('board', api.board)
export const useDidactics = () => useApi('didactics', api.didactics)

/** Ora corrente aggiornata ogni `interval` ms (per lezione in corso, countdown...). */
export function useNow(interval = 30000) {
	const [now, setNow] = useState(() => new Date())
	useEffect(() => {
		const timer = setInterval(() => setNow(new Date()), interval)
		return () => clearInterval(timer)
	}, [interval])
	return now
}

/** Insieme di id salvato sul dispositivo (compiti completati, verifiche salvate, avvisi chiusi). */
export function usePersistentFlags(key) {
	const [flags, setFlags] = useState(() => readJson(key, {}))
	const toggle = useCallback((id, value) => {
		setFlags((current) => {
			const next = { ...current, [id]: value ?? !current[id] }
			if (!next[id]) delete next[id]
			writeJson(key, next)
			return next
		})
	}, [key])
	return [flags, toggle]
}
