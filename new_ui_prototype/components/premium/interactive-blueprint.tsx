"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import Image from "next/image"

interface VectorData {
  id: string
  title: string
  subtitle: string
  metrics: {
    label: string
    value: string
    status: "healthy" | "warning" | "critical"
  }[]
  insights: string[]
}

const vectorData: Record<string, VectorData> = {
  messaging: {
    id: "messaging",
    title: "MESSAGING VECTORS",
    subtitle: "Value Transport & Positioning",
    metrics: [
      { label: "Narrative Consistency", value: "85/100", status: "healthy" },
      { label: "Value Prop Clarity", value: "67%", status: "warning" },
      { label: "Positioning Drift", value: "-23%", status: "critical" },
    ],
    insights: [
      "Strategic Narrative → Old Game vs. New Game transition detected",
      "SPICED Framework alignment: 78% (Target: 90%+)",
      "Trust Narrative requires repositioning to emphasize fractional model",
    ],
  },
  motion: {
    id: "motion",
    title: "MOTION VECTORS",
    subtitle: "Sales Velocity Physics",
    metrics: [
      { label: "Sales Velocity", value: "Stalled", status: "critical" },
      { label: "Win Rate", value: "34%", status: "warning" },
      { label: "Cycle Length", value: "47 days", status: "warning" },
    ],
    insights: [
      "MOL Illusion detected: 43% of pipeline non-viable",
      "Acquisition Leakage: $847K/quarter lost to friction",
      "RevOps Audit reveals 7 critical bottlenecks in sales process",
    ],
  },
  market: {
    id: "market",
    title: "MARKET VECTORS",
    subtitle: "PMF Quantification & Unit Economics",
    metrics: [
      { label: "PMF Score", value: "32%", status: "critical" },
      { label: "Unit Economics", value: "$0.73", status: "warning" },
      { label: "ICP Alignment", value: "81%", status: "healthy" },
    ],
    insights: [
      "Product-Market Fit: Drift detected in mid-market segment",
      "Sean Ellis Protocol: 32% 'very disappointed' (Target: 40%+)",
      "AI Unit Economics: Gross margin trap identified",
    ],
  },
}

export function InteractiveBlueprint() {
  const [selectedVector, setSelectedVector] = useState<string | null>(null)
  const [hoveredLayer, setHoveredLayer] = useState<string | null>(null)

  const selectedData = selectedVector ? vectorData[selectedVector] : null

  return (
    <div className="space-y-8">
      {/* Main Blueprint Visual */}
      <Card className="relative overflow-hidden border-0 bg-transparent">
        {/* 3D Layered Blueprint with Clickable Hotspots */}
        <div className="relative">
          <Image
            src="/images/3m-20revenue-20architecture-20blueprint.jpg"
            alt="3M Revenue Architecture Blueprint"
            width={1408}
            height={792}
            className="w-full h-auto"
            priority
          />

          {/* Interactive Hotspots */}
          {/* Messaging Vector Hotspot - Top Left Layer */}
          <button
            onClick={() => setSelectedVector("messaging")}
            onMouseEnter={() => setHoveredLayer("messaging")}
            onMouseLeave={() => setHoveredLayer(null)}
            className="absolute top-[20%] left-[5%] w-[35%] h-[15%] bg-cyan-400/10 hover:bg-cyan-400/30 transition-all duration-300 border-2 border-cyan-400/50 hover:border-cyan-400 rounded-lg backdrop-blur-sm"
            style={{
              boxShadow: hoveredLayer === "messaging" ? "0 0 40px rgba(6, 182, 212, 0.6)" : "none",
            }}
          >
            <span className="sr-only">Messaging Vectors</span>
          </button>

          {/* Motion Vector Hotspot - Middle Layer */}
          <button
            onClick={() => setSelectedVector("motion")}
            onMouseEnter={() => setHoveredLayer("motion")}
            onMouseLeave={() => setHoveredLayer(null)}
            className="absolute top-[40%] left-[15%] w-[70%] h-[20%] bg-cyan-400/10 hover:bg-cyan-400/30 transition-all duration-300 border-2 border-cyan-400/50 hover:border-cyan-400 rounded-lg backdrop-blur-sm"
            style={{
              boxShadow: hoveredLayer === "motion" ? "0 0 40px rgba(6, 182, 212, 0.6)" : "none",
            }}
          >
            <span className="sr-only">Motion Vectors</span>
          </button>

          {/* Market Vector Hotspot - Bottom Layer */}
          <button
            onClick={() => setSelectedVector("market")}
            onMouseEnter={() => setHoveredLayer("market")}
            onMouseLeave={() => setHoveredLayer(null)}
            className="absolute top-[65%] left-[15%] w-[70%] h-[18%] bg-cyan-400/10 hover:bg-cyan-400/30 transition-all duration-300 border-2 border-cyan-400/50 hover:border-cyan-400 rounded-lg backdrop-blur-sm"
            style={{
              boxShadow: hoveredLayer === "market" ? "0 0 40px rgba(6, 182, 212, 0.6)" : "none",
            }}
          >
            <span className="sr-only">Market Vectors</span>
          </button>

          {/* Hover Indicator */}
          {hoveredLayer && (
            <div className="absolute top-4 right-4 glass-card px-4 py-2 rounded-lg animate-in fade-in duration-200">
              <p className="text-sm text-cyan-400 font-semibold">
                Click to explore{" "}
                {hoveredLayer === "messaging" ? "Messaging" : hoveredLayer === "motion" ? "Motion" : "Market"} Vectors
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Selected Vector Details */}
      {selectedData && (
        <Card className="glass-card border-2 border-cyan-400/50 p-8 animate-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-3xl font-bold text-white mb-2">{selectedData.title}</h3>
              <p className="text-cyan-400 text-lg">{selectedData.subtitle}</p>
            </div>
            <button
              onClick={() => setSelectedVector(null)}
              className="text-white/60 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {selectedData.metrics.map((metric) => (
              <div
                key={metric.label}
                className="p-4 rounded-lg border-2"
                style={{
                  backgroundColor: "rgba(6, 182, 212, 0.05)",
                  borderColor:
                    metric.status === "healthy"
                      ? "rgba(34, 197, 94, 0.5)"
                      : metric.status === "warning"
                        ? "rgba(234, 179, 8, 0.5)"
                        : "rgba(239, 68, 68, 0.5)",
                }}
              >
                <p className="text-white/60 text-sm mb-1">{metric.label}</p>
                <p
                  className="text-3xl font-bold"
                  style={{
                    color:
                      metric.status === "healthy"
                        ? "rgb(34, 197, 94)"
                        : metric.status === "warning"
                          ? "rgb(234, 179, 8)"
                          : "rgb(239, 68, 68)",
                  }}
                >
                  {metric.value}
                </p>
              </div>
            ))}
          </div>

          {/* Insights */}
          <div className="space-y-3">
            <h4 className="text-xl font-semibold text-white mb-4">Key Insights</h4>
            {selectedData.insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 flex-shrink-0" />
                <p className="text-white/80 leading-relaxed">{insight}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
