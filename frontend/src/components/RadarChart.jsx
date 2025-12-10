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
    if (avgScore >= 60) return '#22c55e' // green
    if (avgScore >= 40) return '#eab308' // yellow
    return '#ef4444' // red
  }

  return (
    <div style={{ width: size, height: size, margin: '0 auto' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#1e293b" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            tickLine={{ stroke: '#475569' }}
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
            stroke={getColor()}
            fill={getColor()}
            fillOpacity={0.3}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default RadarChartComponent



