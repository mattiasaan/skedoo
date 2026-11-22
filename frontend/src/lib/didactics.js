// Materiali didattici: dalla struttura docente -> cartelle -> materiali a liste pronte da mostrare.
import { formatDateTime, teacherName } from './format.js'

// action: icona a destra, cioè cosa succede al tocco (scarica, apri il link, leggi il testo)
export const MATERIAL_TYPES = {
	file: { icon: 'file', tone: 'accent', label: 'File', action: 'download', verb: 'Scarica' },
	link: { icon: 'link', tone: 'blue', label: 'Link', action: 'external', verb: 'Apri il link' },
	text: { icon: 'clipboard', tone: 'amber', label: 'Testo', action: 'chevron', verb: 'Leggi' },
}

export function materialType(material) {
	return MATERIAL_TYPES[material.tipo] ?? MATERIAL_TYPES.file
}

/** Tutti i materiali, dal più recente, con docente e cartella. */
export function flattenMaterials(data) {
	return (data?.docenti ?? [])
		.flatMap((teacher) => teacher.cartelle.flatMap((folder) => folder.materiali.map((material) => ({
			...material,
			teacher: teacher.nome,
			folder: folder.nome,
			key: `${teacher.id}-${folder.id}-${material.id}`,
		}))))
		.sort((a, b) => String(b.condiviso_il ?? '').localeCompare(String(a.condiviso_il ?? '')))
}

/** Riga secondaria di un materiale di flattenMaterials: "Rossi Mario • Cartella • 12 ott". */
export function materialDetails(material, { teacher = true } = {}) {
	return [
		teacher && material.teacher ? teacherName(material.teacher) : null,
		material.folder,
		material.condiviso_il ? formatDateTime(material.condiviso_il) : null,
	].filter(Boolean).join(' • ')
}
