"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"

export function RevenueBowtieDiagram() {
  const [hoveredVector, setHoveredVector] = useState<string | null>(null)

  return (
    <div className="relative">
      <Card className="glass-card p-12 border-0">
        {/* SVG Bowtie Diagram */}
        <svg viewBox="0 0 1200 600" className="w-full h-auto">
          <defs>
            {/* Gradient Definitions */}
            <linearGradient id="cyanGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(6, 182, 212, 0.8)" />
              <stop offset="100%" stopColor="rgba(6, 182, 212, 0.3)" />
            </linearGradient>

            {/* Glow Filter */}
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Center Circle - Revenue Architecture Core */}
          <circle
            cx="600"
            cy="300"
            r="80"
            fill="none"
            stroke="url(#cyanGradient)"
            strokeWidth="3"
            filter="url(#glow)"
            className="animate-pulse-glow"
          />
          <text x="600" y="295" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">
            REVENUE
          </text>
          <text x="600" y="315" textAnchor="middle" fill="var(--color-celerio-cyan-bright)" fontSize="14">
            ARCHITECTURE
          </text>

          {/* Left Side - Messaging Vectors */}
          <g
            onMouseEnter={() => setHoveredVector("messaging")}
            onMouseLeave={() => setHoveredVector(null)}
            className="cursor-pointer transition-all"
          >
            <path
              d="M 200 200 L 520 270 L 520 330 L 200 400 Z"
              fill={hoveredVector === "messaging" ? "rgba(6, 182, 212, 0.3)" : "rgba(6, 182, 212, 0.15)"}
              stroke="var(--color-celerio-cyan)"
              strokeWidth="2"
              filter="url(#glow)"
              className="transition-all duration-300"
            />
            <text x="280" y="240" fill="white" fontSize="18" fontWeight="bold">
              MESSAGING
            </text>
            <text x="280" y="265" fill="var(--color-celerio-cyan-bright)" fontSize="13">
              Strategic Narrative
            </text>
            <text x="280" y="285" fill="white" fontSize="12" opacity="0.7">
              Value Transport
            </text>
            <text x="280" y="305" fill="white" fontSize="12" opacity="0.7">
              SPICED Framework
            </text>
            <text x="280" y="325" fill="white" fontSize="12" opacity="0.7">
              Positioning
            </text>
          </g>

          {/* Top - Motion Vectors */}
          <g
            onMouseEnter={() => setHoveredVector("motion")}
            onMouseLeave={() => setHoveredVector(null)}
            className="cursor-pointer transition-all"
          >
            <path
              d="M 400 100 L 560 220 L 640 220 L 800 100 L 640 100 L 560 100 Z"
              fill={hoveredVector === "motion" ? "rgba(6, 182, 212, 0.3)" : "rgba(6, 182, 212, 0.15)"}
              stroke="var(--color-celerio-cyan)"
              strokeWidth="2"
              filter="url(#glow)"
              className="transition-all duration-300"
            />
            <text x="600" y="140" textAnchor="middle" fill="white" fontSize="18" fontWeight="bold">
              MOTION
            </text>
            <text x="600" y="165" textAnchor="middle" fill="var(--color-celerio-cyan-bright)" fontSize="13">
              Sales Velocity Physics
            </text>
            <text x="500" y="190" fill="white" fontSize="11" opacity="0.7">
              Acquisition Leakage
            </text>
            <text x="650" y="190" fill="white" fontSize="11" opacity="0.7">
              RevOps Audit
            </text>
          </g>

          {/* Right Side - Market Vectors */}
          <g
            onMouseEnter={() => setHoveredVector("market")}
            onMouseLeave={() => setHoveredVector(null)}
            className="cursor-pointer transition-all"
          >
            <path
              d="M 680 270 L 1000 200 L 1000 400 L 680 330 Z"
              fill={hoveredVector === "market" ? "rgba(6, 182, 212, 0.3)" : "rgba(6, 182, 212, 0.15)"}
              stroke="var(--color-celerio-cyan)"
              strokeWidth="2"
              filter="url(#glow)"
              className="transition-all duration-300"
            />
            <text x="800" y="240" fill="white" fontSize="18" fontWeight="bold">
              MARKET
            </text>
            <text x="800" y="265" fill="var(--color-celerio-cyan-bright)" fontSize="13">
              PMF Quantification
            </text>
            <text x="800" y="285" fill="white" fontSize="12" opacity="0.7">
              Sean Ellis Protocol
            </text>
            <text x="800" y="305" fill="white" fontSize="12" opacity="0.7">
              AI Unit Economics
            </text>
            <text x="800" y="325" fill="white" fontSize="12" opacity="0.7">
              ICP Matrix
            </text>
          </g>

          {/* Bottom - Output Indicators */}
          <g>
            <text x="300" y="480" fill="white" fontSize="13" opacity="0.6">
              ← Input Signals
            </text>
            <text x="900" y="480" textAnchor="end" fill="white" fontSize="13" opacity="0.6">
              Output Levers →
            </text>
          </g>

          {/* Connecting Lines with Animation */}
          <line
            x1="520"
            y1="300"
            x2="680"
            y2="300"
            stroke="var(--color-celerio-cyan)"
            strokeWidth="2"
            strokeDasharray="5,5"
            opacity="0.5"
          >
            <animate attributeName="stroke-dashoffset" from="0" to="10" dur="1s" repeatCount="indefinite" />
          </line>
        </svg>

        {/* Interactive Legend */}
        {hoveredVector && (
          <div className="mt-8 p-6 glass-card rounded-lg border-2" style={{ borderColor: "var(--color-celerio-cyan)" }}>
            <h4 className="text-xl font-bold text-white mb-2">
              {hoveredVector === "messaging" && "Messaging Vectors"}
              {hoveredVector === "motion" && "Motion Vectors"}
              {hoveredVector === "market" && "Market Vectors"}
            </h4>
            <p className="text-white/70">
              {hoveredVector === "messaging" &&
                "How your story lands in market. We diagnose narrative drift, positioning confusion, and value transport failures."}
              {hoveredVector === "motion" &&
                "Your revenue engine's physics. We identify acquisition leakage, sales velocity bottlenecks, and expansion stagnation."}
              {hoveredVector === "market" &&
                "Your product-market fit reality. We quantify PMF, analyze unit economics, and validate ICP alignment."}
            </p>
          </div>
        )}
      </Card>
    </div>
  )
}
