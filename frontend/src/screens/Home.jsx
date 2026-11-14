import { useApp } from '../lib/appContext.js'
import HomeGalilei from './home/HomeGalilei.jsx'
import HomeGeneral from './home/HomeGeneral.jsx'

/**
 * Due varianti della Home:
 * - Galilei di Bolzano (classe scelta): orario di oggi, prossima lezione, variazioni;
 * - altre scuole: bacheca, panoramica voti, presenze (non abbiamo l'orario).
 */
function Home() {
	const { isGalilei } = useApp()
	return isGalilei ? <HomeGalilei /> : <HomeGeneral />
}

export default Home
