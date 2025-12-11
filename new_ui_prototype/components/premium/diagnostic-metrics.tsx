"use client"

import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

interface DiagnosticMetricsProps {
  isUnlocked: boolean
}

export function DiagnosticMetrics({ isUnlocked }: DiagnosticMetricsProps) {
  const metrics = [
    {
      vector: "Messaging",
      score: 67,
      status: "Warning",
      findings: [
        "Narrative drift detected across 3 channels",
        "Positioning misalignment: -23% vs. competitors",
        "Value prop clarity: 4.2/10 (Industry avg: 7.1)",
      ],
    },
    {
      vector: "Motion",
      score: 42,
      status: "Critical",
      findings: [
        "Sales velocity: 47 days (Target: 28 days)",
        "Acquisition leakage: $847K/quarter",
        "Win rate compression: -15% YoY",
      ],
    },
    {
      vector: "Market",
      score: 78,
      status: "Healthy",
      findings: [
        'PMF Score: 42% "Very Disappointed"',
        "Unit economics: $0.73 LTV/CAC (Strong)",
        "ICP alignment: 81% match rate",
      ],
    },
  ]

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-5xl font-bold text-white mb-4">
          Your <span style={{ color: "var(--color-celerio-cyan-bright)" }}>Diagnostic Preview</span>
        </h2>
        <p className="text-xl text-white/70">Real-time scoring across all three vectors</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metrics.map((metric) => (
          <Card
            key={metric.vector}
            className="glass-card border-2 p-6 space-y-4"
            style={{ borderColor: "var(--color-celerio-glass-border)" }}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">{metric.vector}</h3>
              <Badge
                className={`
                  ${metric.status === "Critical" ? "bg-red-500/20 text-red-300 border-red-500/50" : ""}
                  ${metric.status === "Warning" ? "bg-yellow-500/20 text-yellow-300 border-yellow-500/50" : ""}
                  ${metric.status === "Healthy" ? "bg-green-500/20 text-green-300 border-green-500/50" : ""}
                  border
                `}
              >
                {metric.status}
              </Badge>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/70">Vector Score</span>
                <span className="text-2xl font-bold text-white">{metric.score}</span>
              </div>
              <Progress value={metric.score} className="h-2 bg-white/10" />
            </div>

            <div className={`space-y-2 ${!isUnlocked && "blur-sm select-none"}`}>
              <h4 className="text-sm font-semibold text-white/80">Key Findings:</h4>
              <ul className="space-y-1.5">
                {metric.findings.map((finding, i) => (
                  <li key={i} className="text-xs text-white/60 leading-relaxed">
                    • {finding}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
