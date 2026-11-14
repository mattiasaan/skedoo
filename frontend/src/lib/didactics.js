// Materiali didattici: dalla struttura docente -> cartelle -> materiali a liste pronte da mostrare.

export const MATERIAL_TYPES = {
	file: { icon: 'file', tone: 'accent', label: 'File' },
	link: { icon: 'link', tone: 'blue', label: 'Link' },
	text: { icon: 'clipboard', tone: 'amber', label: 'Testo' },
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
