"use client"

import { Card } from "@/components/ui/card"
import { TrendingUp, Zap, Target } from "lucide-react"

export function VectorArchitecture() {
  const vectors = [
    {
      title: "Messaging Vectors",
      icon: Target,
      color: "var(--color-celerio-cyan)",
      image: "/images/3m-20revenue-20architecture-20blueprint-20-20layers.jpg",
      layers: [
        { name: "Strategic Narrative", desc: "Old Game vs. New Game positioning" },
        { name: "Narrative Vehicle", desc: "Value transport mechanism" },
        { name: "SPICED Framework", desc: "Customer voice integration" },
        { name: "Positioning", desc: "Trust narrative architecture" },
      ],
    },
    {
      title: "Motion Vectors",
      icon: Zap,
      color: "var(--color-celerio-cyan-bright)",
      image: "/images/3m-20revenue-20architecture-20blueprint-20-20layers.jpg",
      layers: [
        { name: "Acquisition Leakage", desc: "Top-of-funnel hemorrhaging" },
        { name: "Sales Velocity Physics", desc: "Revenue Bowtie mechanics" },
        { name: "Win Rate Optimization", desc: "Cycle length & AI bottleneck analysis" },
        { name: "Impact Gap", desc: "Expansion stagnation diagnosis" },
      ],
    },
    {
      title: "Market Vectors",
      icon: TrendingUp,
      color: "var(--color-celerio-gold)",
      image: "/images/3m-20revenue-20architecture-20blueprint-20-20layers.jpg",
      layers: [
        { name: "Product-Market Fit", desc: "PMF quantification via Sean Ellis" },
        { name: "Protocol & Drift", desc: "Market signal detection" },
        { name: "Operational Foundation", desc: "Unit economic sustainability" },
        { name: "AI Unit Economics", desc: "Gross margin trap avoidance" },
      ],
    },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="text-center mb-12">
        <h2 className="text-5xl font-bold text-white mb-4">
          Three-Vector <span style={{ color: "var(--color-celerio-cyan-bright)" }}>Diagnostic System</span>
        </h2>
        <p className="text-xl text-white/70 max-w-3xl mx-auto">
          Each vector contains proprietary frameworks that detect invisible revenue leaks
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {vectors.map((vector, index) => (
          <Card
            key={vector.title}
            className="glass-card border-2 p-8 group hover:scale-[1.02] transition-all duration-500"
            style={{ borderColor: "var(--color-celerio-glass-border)" }}
          >
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div
                    className="w-14 h-14 rounded-full glass-card flex items-center justify-center border-2"
                    style={{ borderColor: vector.color }}
                  >
                    <vector.icon className="w-7 h-7" style={{ color: vector.color }} />
                  </div>
                  <div>
                    <h3 className="text-3xl font-bold text-white">{vector.title}</h3>
                    <p className="text-white/60">Layer {index + 1} of 3</p>
                  </div>
                </div>

                <div className="space-y-4 pl-4 border-l-2" style={{ borderColor: vector.color }}>
                  {vector.layers.map((layer, i) => (
                    <div key={i} className="space-y-1">
                      <h4 className="text-lg font-semibold text-white">{layer.name}</h4>
                      <p className="text-white/60 text-sm">{layer.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative">
                <div
                  className="absolute inset-0 rounded-lg blur-2xl opacity-30"
                  style={{ background: `radial-gradient(circle, ${vector.color} 0%, transparent 70%)` }}
                />
                <img
                  src={vector.image || "/placeholder.svg"}
                  alt={vector.title}
                  className="relative rounded-lg w-full h-auto border-2 group-hover:scale-105 transition-transform duration-500"
                  style={{ borderColor: vector.color }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
