"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingDown, AlertTriangle, CheckCircle } from "lucide-react"

interface DiagnosticCard {
  vector: string
  title: string
  value: string
  status: "healthy" | "warning" | "critical"
  statusLabel: string
  chart: "line" | "bars" | "radar"
  metrics?: { label: string; value: string }[]
}

const diagnosticData: DiagnosticCard[] = [
  {
    vector: "MARKET VECTOR",
    title: "Market Viability",
    value: "32%",
    status: "critical",
    statusLabel: "Drift Detected",
    chart: "line",
    metrics: [
      { label: "PMF Score", value: "32%" },
      { label: "Sean Ellis", value: "Below 40%" },
    ],
  },
  {
    vector: "MOTION VECTOR",
    title: "Sales Physics",
    value: "Stalled",
    status: "warning",
    statusLabel: "MOL Illusion Detected",
    chart: "bars",
    metrics: [
      { label: "Win Rate", value: "34%" },
      { label: "Cycle Length", value: "47d" },
    ],
  },
  {
    vector: "MESSAGING VECTOR",
    title: "Strategic Narrative",
    value: "85",
    status: "healthy",
    statusLabel: "High Consistency",
    chart: "radar",
    metrics: [
      { label: "Positioning", value: "Strong" },
      { label: "Clarity", value: "Good" },
    ],
  },
]

export function DiagnosticCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {diagnosticData.map((card) => (
        <Card
          key={card.vector}
          className="relative overflow-hidden border-2 bg-[#0A1628] p-6 space-y-4 hover:scale-[1.02] transition-transform duration-300"
          style={{
            borderColor: "rgba(6, 182, 212, 0.2)",
            boxShadow: "0 4px 24px rgba(0, 0, 0, 0.4)",
          }}
        >
          {/* Vector Label */}
          <div className="flex items-center justify-between">
            <p className="text-xs font-mono text-cyan-400/80 tracking-wider">{card.vector}</p>
            {card.status === "healthy" && <CheckCircle className="w-4 h-4 text-green-400" />}
            {card.status === "warning" && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
            {card.status === "critical" && <TrendingDown className="w-4 h-4 text-red-400" />}
          </div>

          {/* Title */}
          <h3 className="text-2xl font-bold text-white">{card.title}</h3>

          {/* Main Value */}
          <div className="py-4">
            <p
              className="text-5xl font-bold"
              style={{
                color:
                  card.status === "healthy"
                    ? "rgb(34, 197, 94)"
                    : card.status === "warning"
                      ? "rgb(234, 179, 8)"
                      : "rgb(239, 68, 68)",
              }}
            >
              {card.value}
              {card.title.includes("Narrative") && <span className="text-2xl text-white/40">{" /100"}</span>}
            </p>
          </div>

          {/* Status Badge */}
          <Badge
            className="border"
            style={{
              backgroundColor:
                card.status === "healthy"
                  ? "rgba(34, 197, 94, 0.15)"
                  : card.status === "warning"
                    ? "rgba(234, 179, 8, 0.15)"
                    : "rgba(239, 68, 68, 0.15)",
              borderColor:
                card.status === "healthy"
                  ? "rgba(34, 197, 94, 0.5)"
                  : card.status === "warning"
                    ? "rgba(234, 179, 8, 0.5)"
                    : "rgba(239, 68, 68, 0.5)",
              color:
                card.status === "healthy"
                  ? "rgb(34, 197, 94)"
                  : card.status === "warning"
                    ? "rgb(234, 179, 8)"
                    : "rgb(239, 68, 68)",
            }}
          >
            {card.statusLabel}
          </Badge>

          {/* Chart Visualization */}
          <div className="pt-4">
            {card.chart === "line" && (
              <svg viewBox="0 0 200 60" className="w-full h-16">
                <path
                  d="M 0 50 L 40 35 L 80 40 L 120 25 L 160 30 L 200 50"
                  fill="none"
                  stroke="rgb(239, 68, 68)"
                  strokeWidth="2"
                  opacity="0.8"
                />
                <path
                  d="M 0 50 L 40 35 L 80 40 L 120 25 L 160 30 L 200 50 L 200 60 L 0 60 Z"
                  fill="url(#redGradient)"
                  opacity="0.2"
                />
                <defs>
                  <linearGradient id="redGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="rgb(239, 68, 68)" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="rgb(239, 68, 68)" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            )}

            {card.chart === "bars" && (
              <div className="flex items-end justify-between h-16 gap-2">
                {[70, 50, 30, 20].map((height, idx) => (
                  <div
                    key={idx}
                    className="flex-1 rounded-t"
                    style={{
                      height: `${height}%`,
                      backgroundColor: "rgb(234, 179, 8)",
                      opacity: 1 - idx * 0.15,
                    }}
                  />
                ))}
              </div>
            )}

            {card.chart === "radar" && (
              <svg viewBox="0 0 120 120" className="w-full h-20">
                <defs>
                  <linearGradient id="greenGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="rgb(34, 197, 94)" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="rgb(34, 197, 94)" stopOpacity="0.1" />
                  </linearGradient>
                </defs>
                {/* Pentagon background */}
                <path
                  d="M 60 10 L 105 40 L 90 95 L 30 95 L 15 40 Z"
                  fill="none"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="1"
                />
                {/* Data pentagon */}
                <path
                  d="M 60 20 L 95 45 L 85 85 L 35 85 L 25 45 Z"
                  fill="url(#greenGradient)"
                  stroke="rgb(34, 197, 94)"
                  strokeWidth="2"
                  opacity="0.8"
                />
              </svg>
            )}
          </div>

          {/* Additional Metrics */}
          {card.metrics && (
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/10">
              {card.metrics.map((metric) => (
                <div key={metric.label} className="space-y-1">
                  <p className="text-xs text-white/50">{metric.label}</p>
                  <p className="text-sm font-semibold text-white">{metric.value}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      ))}
    </div>
  )
}
