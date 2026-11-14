import { createContext, useContext } from 'react'

/**
 * Messaggi brevi in basso ("Compito completato", "Dati aggiornati"...).
 * toast(testo, { tone: 'success' | 'error' | 'info', action: { label, onClick }, duration })
 */
export const ToastContext = createContext(() => {})

export function useToast() {
	return useContext(ToastContext)
}
