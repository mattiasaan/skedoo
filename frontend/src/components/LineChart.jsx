import { useId } from 'react'

const WIDTH = 600
const HEIGHT = 150
const PAD_X = 12
const PAD_TOP = 16
const PAD_BOTTOM = 14

/** Andamento dei voti/media: linea con area sfumata, ultimo punto evidenziato. */
export function LineChart({ points, min, max, label, threshold }) {
	const gradientId = useId()
	if (!points.length) return null

	const values = points.map((point) => point.value)
	const low = min ?? Math.max(1, Math.floor(Math.min(...values) - 0.5))
	const high = max ?? Math.min(10, Math.ceil(Math.max(...values) + 0.5))
	const span = Math.max(0.5, high - low)
	const x = (index) => (points.length === 1 ? WIDTH / 2 : PAD_X + (index / (points.length - 1)) * (WIDTH - PAD_X * 2))
	const y = (value) => PAD_TOP + (1 - (value - low) / span) * (HEIGHT - PAD_TOP - PAD_BOTTOM)
	const coords = points.map((point, index) => [x(index), y(point.value)])
	const line = coords.map(([px, py], index) => `${index ? 'L' : 'M'}${px.toFixed(1)} ${py.toFixed(1)}`).join(' ')
	const area = `${line} L${coords.at(-1)[0].toFixed(1)} ${HEIGHT} L${coords[0][0].toFixed(1)} ${HEIGHT} Z`
	const last = coords.at(-1)

	return (
		<svg className="line-chart" role="img" aria-label={label} viewBox={`0 0 ${WIDTH} ${HEIGHT}`}>
			<defs>
				<linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
					<stop offset="0%" stopColor="var(--accent)" stopOpacity="0.28" />
					<stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
				</linearGradient>
			</defs>
			{threshold != null && threshold > low && threshold < high && (
				<line className="line-chart__threshold" x1="0" x2={WIDTH} y1={y(threshold)} y2={y(threshold)} />
			)}
			<path d={area} fill={`url(#${gradientId})`} />
			<path className="line-chart__line" d={line} />
			{coords.slice(0, -1).map(([px, py], index) => (
				<circle className="line-chart__point" cx={px} cy={py} key={points[index].key ?? index} r="4.5">
					<title>{points[index].title}</title>
				</circle>
			))}
			<circle className="line-chart__last" cx={last[0]} cy={last[1]} r="6.5">
				<title>{points.at(-1).title}</title>
			</circle>
		</svg>
	)
}

export default LineChart
