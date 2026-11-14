import { createContext, useContext } from 'react'

/**
 * Stato condiviso dalle schermate della dashboard:
 * utente, classe, apertura dei dettagli e compiti completati/salvati.
 */
export const AppContext = createContext(null)

export function useApp() {
	const value = useContext(AppContext)
	if (!value) throw new Error('useApp va usato dentro DashboardShell')
	return value
}
