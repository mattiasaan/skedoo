import { createContext, useContext } from 'react'

/**
 * Stato condiviso dalle schermate della dashboard:
 * utente, classe, apertura dei dettagli (openDetail) e della dashboard di una materia (openSubject),
 * compiti completati/salvati.
 */
export const AppContext = createContext(null)

export function useApp() {
	const value = useContext(AppContext)
	if (!value) throw new Error('useApp va usato dentro DashboardShell')
	return value
}
