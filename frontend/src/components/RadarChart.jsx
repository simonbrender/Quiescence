import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'

function RadarChartComponent({ messaging, motion, market, size = 200 }) {
  const data = [
    {
      subject: 'Messaging',
      score: messaging,
      fullMark: 100,
    },
    {
      subject: 'Motion',
      score: motion,
      fullMark: 100,
    },
    {
      subject: 'Market',
      score: market,
      fullMark: 100,
    },
  ]

  // Determine color based on average score
  const avgScore = (messaging + motion + market) / 3
  const getColor = () => {
    if (avgScore >= 60) return '#34d399' // green-400
    if (avgScore >= 40) return '#fbbf24' // yellow-400
    return '#f87171' // red-400
  }

  const color = getColor()

  return (
    <div style={{ width: size, height: size, margin: '0 auto' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(6, 182, 212, 0.2)" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: 'rgba(255, 255, 255, 0.8)', fontSize: 11, fontWeight: 500 }}
            tickLine={{ stroke: 'rgba(6, 182, 212, 0.3)' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke={color}
            fill={color}
            fillOpacity={0.25}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default RadarChartComponent
