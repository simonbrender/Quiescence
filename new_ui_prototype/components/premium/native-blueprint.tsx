"use client"

import type React from "react"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  FileText,
  Users,
  MessageSquare,
  Filter,
  Megaphone,
  Package,
  TrendingUp,
  Settings,
  Cpu,
  Grid3x3,
  X,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Zap,
} from "lucide-react"

type StatusType = "healthy" | "warning" | "critical"

interface AgentSolution {
  agentName: string
  action: string
  estimatedImpact: string
  deployTime: string
}

interface BlueprintElement {
  id: string
  label: string
  sublabel?: string
  icon: React.ReactNode
  status: StatusType // Added status to element
  findings: {
    title: string
    status: StatusType
    description: string
    metrics: { label: string; value: string }[]
    solution: AgentSolution // Added solution to findings
  }
}

const messagingElements: BlueprintElement[] = [
  {
    id: "strategic-narrative",
    label: "Strategic",
    sublabel: "Narrative",
    icon: <FileText className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Strategic Narrative Analysis",
      status: "warning",
      description:
        "Narrative positioning shows drift from ideal state. Old Game vs. New Game transition needs refinement.",
      metrics: [
        { label: "Clarity Score", value: "73/100" },
        { label: "Consistency", value: "85%" },
        { label: "Differentiation", value: "62%" },
      ],
      solution: {
        agentName: "Narrative Architect Agent",
        action: "Rewrite strategic narrative using SPICED framework analysis",
        estimatedImpact: "+18% message clarity, +$340K pipeline",
        deployTime: "3 days",
      },
    },
  },
  {
    id: "old-vs-new",
    label: "Old Game vs.",
    sublabel: "New Game",
    icon: <Users className="w-6 h-6" />,
    status: "healthy",
    findings: {
      title: "Old Game vs. New Game Framework",
      status: "healthy",
      description:
        "Transformation story well-articulated. Contrast between legacy approach and modern solution is clear.",
      metrics: [
        { label: "Contrast Clarity", value: "89/100" },
        { label: "Resonance", value: "91%" },
      ],
      solution: {
        agentName: "Maintain Current State",
        action: "Continue monitoring narrative performance",
        estimatedImpact: "Sustained messaging effectiveness",
        deployTime: "N/A",
      },
    },
  },
  {
    id: "narrative-vehicle",
    label: "NARRATIVE VEHICLE",
    sublabel: "(Value Transport)",
    icon: <MessageSquare className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Narrative Vehicle Assessment",
      status: "warning",
      description:
        "Value transport mechanism needs optimization. Message not consistently landing with target personas.",
      metrics: [
        { label: "Message Retention", value: "67%" },
        { label: "Value Comprehension", value: "71%" },
      ],
      solution: {
        agentName: "Value Transport Agent",
        action: "Deploy persona-specific messaging optimization",
        estimatedImpact: "+24% retention, +$520K qualified pipeline",
        deployTime: "5 days",
      },
    },
  },
  {
    id: "spiced-framework",
    label: "SPICED Framework",
    sublabel: "(Customer Voice)",
    icon: <Filter className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "SPICED Framework Alignment",
      status: "warning",
      description: "Customer discovery reveals gaps in pain articulation and decision criteria alignment.",
      metrics: [
        { label: "Situation Clarity", value: "78%" },
        { label: "Pain Articulation", value: "65%" },
        { label: "Impact Mapping", value: "71%" },
      ],
      solution: {
        agentName: "Discovery Agent",
        action: "Implement automated SPICED analysis on all sales conversations",
        estimatedImpact: "+31% win rate improvement",
        deployTime: "2 days",
      },
    },
  },
  {
    id: "positioning",
    label: "Positioning",
    sublabel: "(Trust Narrative)",
    icon: <Megaphone className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "Positioning & Trust Narrative",
      status: "critical",
      description:
        "Significant positioning drift detected. Trust narrative requires immediate repositioning to emphasize fractional expertise model.",
      metrics: [
        { label: "Position Strength", value: "58%" },
        { label: "Trust Indicators", value: "64%" },
        { label: "Category Authority", value: "51%" },
      ],
      solution: {
        agentName: "Positioning Agent",
        action: "Deploy fractional expertise narrative + category creation campaign",
        estimatedImpact: "+$1.2M ARR from improved positioning",
        deployTime: "7 days",
      },
    },
  },
]

const motionElements: BlueprintElement[] = [
  {
    id: "acquisition-leakage",
    label: "Acquisition",
    sublabel: "Leakage",
    icon: <TrendingUp className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "Acquisition Leakage Analysis",
      status: "critical",
      description:
        "Significant revenue leakage identified in top-of-funnel. $847K/quarter lost to preventable friction.",
      metrics: [
        { label: "Leakage Rate", value: "34%" },
        { label: "Quarterly Loss", value: "$847K" },
        { label: "Recovery Potential", value: "$2.5M ARR" },
      ],
      solution: {
        agentName: "Funnel Recovery Agent",
        action: "Deploy friction detection + automated lead nurture sequences",
        estimatedImpact: "$2.5M ARR recovery, -34% leakage",
        deployTime: "4 days",
      },
    },
  },
  {
    id: "mol-illusion",
    label: "MQL",
    sublabel: "Illusion",
    icon: <Users className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "MQL Illusion Detection",
      status: "critical",
      description: "43% of pipeline classified as non-viable. Lead quality scoring mechanism requires overhaul.",
      metrics: [
        { label: "Non-Viable Pipeline", value: "43%" },
        { label: "False Positive Rate", value: "38%" },
        { label: "Wasted Effort", value: "127 hrs/mo" },
      ],
      solution: {
        agentName: "Lead Scoring Agent",
        action: "Replace legacy MQL model with AI intent scoring + behavioral signals",
        estimatedImpact: "127 hrs/mo saved, +$890K qualified pipeline",
        deployTime: "3 days",
      },
    },
  },
  {
    id: "bowtie-model",
    label: "Revenue Architecture",
    sublabel: "Bowtie Model",
    icon: <Settings className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Revenue Bowtie Physics",
      status: "warning",
      description: "Win Rate × Cycle Length × AI Bottleneck equation reveals structural constraints in sales velocity.",
      metrics: [
        { label: "Win Rate", value: "34%" },
        { label: "Cycle Length", value: "47 days" },
        { label: "AI Bottleneck", value: "2.3x" },
        { label: "Sales Velocity", value: "Stalled" },
      ],
      solution: {
        agentName: "Revenue Physics Agent",
        action: "Deploy bowtie optimization: compress cycles + remove AI bottlenecks",
        estimatedImpact: "47→29 days cycle, +$3.4M ARR",
        deployTime: "10 days",
      },
    },
  },
  {
    id: "impact-gap",
    label: "Impact",
    sublabel: "Gap",
    icon: <TrendingUp className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Impact Gap Measurement",
      status: "warning",
      description: "Expected vs. actual business impact shows 47% realization gap.",
      metrics: [
        { label: "Expected Impact", value: "$3.2M" },
        { label: "Realized Impact", value: "$1.7M" },
        { label: "Gap", value: "47%" },
      ],
      solution: {
        agentName: "Value Realization Agent",
        action: "Deploy post-sale impact tracking + customer success playbooks",
        estimatedImpact: "$1.5M additional realized value",
        deployTime: "6 days",
      },
    },
  },
  {
    id: "expansion-stagnation",
    label: "Expansion",
    sublabel: "Stagnation",
    icon: <TrendingUp className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "Expansion Stagnation Analysis",
      status: "critical",
      description: "Net Revenue Retention below healthy threshold. Expansion motion stalled at 103% NRR.",
      metrics: [
        { label: "NRR", value: "103%" },
        { label: "Expansion Rate", value: "8%" },
        { label: "Target Gap", value: "-17%" },
      ],
      solution: {
        agentName: "Expansion Engine Agent",
        action: "Activate upsell triggers + usage-based expansion playbooks",
        estimatedImpact: "103%→125% NRR, +$2.1M expansion ARR",
        deployTime: "8 days",
      },
    },
  },
]

const marketElements: BlueprintElement[] = [
  {
    id: "pmf-quantification",
    label: "Product-Market Fit",
    sublabel: "(PMF) Quantification",
    icon: <Package className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "Product-Market Fit Quantification",
      status: "critical",
      description:
        "Sean Ellis Protocol reveals 32% 'very disappointed' score. Significant drift detected in mid-market segment.",
      metrics: [
        { label: "PMF Score", value: "32%" },
        { label: "Target", value: "40%+" },
        { label: "Segment Drift", value: "Mid-Market" },
      ],
      solution: {
        agentName: "PMF Recovery Agent",
        action: "Deploy segment-specific feature roadmap + customer feedback loops",
        estimatedImpact: "32%→42% PMF score, +$1.8M retention",
        deployTime: "12 days",
      },
    },
  },
  {
    id: "sean-ellis",
    label: "Sean Ellis",
    sublabel: "Protocol & Drift",
    icon: <TrendingUp className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Sean Ellis Protocol Analysis",
      status: "warning",
      description:
        "Product satisfaction trending downward in core segments. Drift indicators suggest feature-market misalignment.",
      metrics: [
        { label: "Very Disappointed", value: "32%" },
        { label: "Somewhat Disappointed", value: "41%" },
        { label: "Drift Velocity", value: "-7% QoQ" },
      ],
      solution: {
        agentName: "Drift Detection Agent",
        action: "Implement continuous PMF monitoring + early warning system",
        estimatedImpact: "Stop 7% QoQ drift, protect $2.3M ARR",
        deployTime: "5 days",
      },
    },
  },
  {
    id: "operational-foundation",
    label: "OPERATIONAL",
    sublabel: "FOUNDATION",
    icon: <Settings className="w-6 h-6" />,
    status: "warning",
    findings: {
      title: "Operational Foundation (Unit Economic Sustainability)",
      status: "warning",
      description: "Unit economics show structural challenges. Current CAC:LTV ratio below sustainable threshold.",
      metrics: [
        { label: "CAC", value: "$47K" },
        { label: "LTV", value: "$134K" },
        { label: "Ratio", value: "2.9:1" },
        { label: "Target", value: "3:1+" },
      ],
      solution: {
        agentName: "Unit Economics Agent",
        action: "Optimize acquisition channels + increase LTV through retention plays",
        estimatedImpact: "2.9:1→3.8:1 ratio, +$4.2M efficiency",
        deployTime: "14 days",
      },
    },
  },
  {
    id: "ai-unit-economics",
    label: "AI Unit Economics",
    sublabel: "(Gross Margin Trap)",
    icon: <Cpu className="w-6 h-6" />,
    status: "critical",
    findings: {
      title: "AI Unit Economics Analysis",
      status: "critical",
      description: "Gross margin trap identified. AI compute costs eroding profitability at scale.",
      metrics: [
        { label: "Gross Margin", value: "42%" },
        { label: "AI Cost/User", value: "$23" },
        { label: "Margin Compression", value: "-18% YoY" },
      ],
      solution: {
        agentName: "Margin Optimization Agent",
        action: "Deploy compute optimization + tiered pricing based on AI usage",
        estimatedImpact: "42%→67% margin, +$3.1M gross profit",
        deployTime: "9 days",
      },
    },
  },
  {
    id: "segmentation-icp",
    label: "Segmentation",
    sublabel: "& ICP Matrix",
    icon: <Grid3x3 className="w-6 h-6" />,
    status: "healthy",
    findings: {
      title: "Segmentation & ICP Matrix",
      status: "healthy",
      description: "ICP definition and segmentation strategy well-defined. Strong alignment with go-to-market motion.",
      metrics: [
        { label: "ICP Alignment", value: "81%" },
        { label: "Segment Clarity", value: "87%" },
        { label: "TAM Accuracy", value: "89%" },
      ],
      solution: {
        agentName: "Maintain Current State",
        action: "Continue quarterly ICP refinement process",
        estimatedImpact: "Sustained targeting effectiveness",
        deployTime: "N/A",
      },
    },
  },
]

function StatusBadge({ status }: { status: StatusType }) {
  if (status === "healthy") {
    return (
      <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-green-500/90 border-2 border-green-400 flex items-center justify-center shadow-[0_0_12px_rgba(34,197,94,0.6)]">
        <CheckCircle2 className="w-3.5 h-3.5 text-white" />
      </div>
    )
  }
  if (status === "warning") {
    return (
      <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-yellow-500/90 border-2 border-yellow-400 flex items-center justify-center shadow-[0_0_12px_rgba(234,179,8,0.6)] animate-pulse">
        <AlertCircle className="w-3.5 h-3.5 text-white" />
      </div>
    )
  }
  return (
    <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500/90 border-2 border-red-400 flex items-center justify-center shadow-[0_0_12px_rgba(239,68,68,0.6)] animate-pulse">
      <AlertTriangle className="w-3.5 h-3.5 text-white" />
    </div>
  )
}

export function NativeBlueprint() {
  const [selectedElement, setSelectedElement] = useState<BlueprintElement | null>(null)
  const [isDeploying, setIsDeploying] = useState(false)

  const handleDeploy = (solution: AgentSolution) => {
    setIsDeploying(true)
    // Simulate deployment
    setTimeout(() => {
      setIsDeploying(false)
      setSelectedElement(null)
      // Show success notification
      alert(`✓ ${solution.agentName} deployed successfully!\nEstimated impact: ${solution.estimatedImpact}`)
    }, 2000)
  }

  return (
    <div className="relative">
      {/* 3D Blueprint Container */}
      <div className="relative" style={{ perspective: "2000px", perspectiveOrigin: "50% 30%" }}>
        {/* Top Layer - Messaging Vectors */}
        <div
          className="relative mb-16"
          style={{
            transform: "rotateX(8deg) translateZ(100px)",
            transformStyle: "preserve-3d",
          }}
        >
          <div className="blueprint-layer-top px-8 py-12 rounded-2xl relative overflow-hidden">
            {/* Glowing border effect */}
            <div className="absolute inset-0 rounded-2xl border-2 border-cyan-400/60 glow-border-cyan" />
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-transparent to-blue-500/10 rounded-2xl" />

            {/* Layer Title */}
            <div className="relative z-10 mb-8">
              <h3 className="text-3xl font-bold text-white mb-1">MESSAGING VECTORS</h3>
              <p className="text-cyan-400 text-sm">Value Transport & Positioning</p>
            </div>

            {/* Elements Flow */}
            <div className="relative z-10 flex items-center justify-between gap-4">
              {messagingElements.map((element, idx) => (
                <div key={element.id} className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedElement(element)}
                    className="relative group flex flex-col items-center gap-2 p-4 rounded-xl glass-card border-2 border-cyan-400/40 hover:border-cyan-400 hover:scale-105 transition-all duration-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.4)]"
                  >
                    <StatusBadge status={element.status} />
                    <div className="w-14 h-14 rounded-full bg-cyan-400/10 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-400/20 transition-colors">
                      {element.icon}
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-semibold text-white">{element.label}</div>
                      {element.sublabel && <div className="text-xs text-white/60">{element.sublabel}</div>}
                    </div>
                  </button>

                  {idx < messagingElements.length - 1 && <div className="arrow-connector" />}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Layer - Motion Vectors */}
        <div
          className="relative mb-16"
          style={{
            transform: "rotateX(8deg) translateZ(0px)",
            transformStyle: "preserve-3d",
          }}
        >
          <div className="blueprint-layer-middle px-8 py-12 rounded-2xl relative overflow-hidden">
            <div className="absolute inset-0 rounded-2xl border-2 border-cyan-400/60 glow-border-cyan" />
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/15 via-transparent to-blue-500/10 rounded-2xl" />

            {/* Layer Title */}
            <div className="relative z-10 mb-8">
              <h3 className="text-3xl font-bold text-white mb-1">MOTION VECTORS</h3>
              <p className="text-cyan-400 text-sm">Sales Velocity Physics & Revenue Operations</p>
            </div>

            {/* Bowtie Model Center */}
            <div className="relative z-10">
              <div className="flex items-center gap-4 mb-6">
                {/* Left side - inputs */}
                <div className="flex flex-col gap-3 flex-1">
                  <button
                    onClick={() => setSelectedElement(motionElements[0])}
                    className="relative glass-card p-4 rounded-lg border-2 border-cyan-400/40 hover:border-cyan-400 transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                  >
                    <StatusBadge status={motionElements[0].status} />
                    <div className="flex items-center gap-3">
                      <div className="text-cyan-400">{motionElements[0].icon}</div>
                      <div className="text-left">
                        <div className="text-sm font-semibold text-white">{motionElements[0].label}</div>
                        <div className="text-xs text-white/60">{motionElements[0].sublabel}</div>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedElement(motionElements[1])}
                    className="relative glass-card p-4 rounded-lg border-2 border-cyan-400/40 hover:border-cyan-400 transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                  >
                    <StatusBadge status={motionElements[1].status} />
                    <div className="flex items-center gap-3">
                      <div className="text-cyan-400">{motionElements[1].icon}</div>
                      <div className="text-left">
                        <div className="text-sm font-semibold text-white italic">{motionElements[1].label}</div>
                        <div className="text-xs text-white/60 italic">{motionElements[1].sublabel}</div>
                      </div>
                    </div>
                  </button>
                </div>

                {/* Center - Bowtie */}
                <button
                  onClick={() => setSelectedElement(motionElements[2])}
                  className="relative glass-card p-8 rounded-2xl border-2 border-cyan-400/60 hover:border-cyan-400 transition-all hover:shadow-[0_0_40px_rgba(6,182,212,0.5)] hover:scale-105"
                >
                  <StatusBadge status={motionElements[2].status} />
                  <div className="text-center">
                    <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-cyan-400/10 flex items-center justify-center text-cyan-400">
                      {motionElements[2].icon}
                    </div>
                    <div className="text-base font-bold text-white">{motionElements[2].label}</div>
                    <div className="text-xs text-cyan-400 mt-1">{motionElements[2].sublabel}</div>
                    <div className="text-xs text-white/50 mt-3">Win Rate × Cycle Length</div>
                    <div className="text-xs text-white/50">÷ AI Bottleneck = Sales Velocity</div>
                  </div>
                </button>

                {/* Right side - outputs */}
                <div className="flex flex-col gap-3 flex-1">
                  <button
                    onClick={() => setSelectedElement(motionElements[3])}
                    className="relative glass-card p-4 rounded-lg border-2 border-cyan-400/40 hover:border-cyan-400 transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                  >
                    <StatusBadge status={motionElements[3].status} />
                    <div className="flex items-center gap-3">
                      <div className="text-cyan-400">{motionElements[3].icon}</div>
                      <div className="text-left">
                        <div className="text-sm font-semibold text-white">{motionElements[3].label}</div>
                        <div className="text-xs text-white/60">{motionElements[3].sublabel}</div>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setSelectedElement(motionElements[4])}
                    className="relative glass-card p-4 rounded-lg border-2 border-cyan-400/40 hover:border-cyan-400 transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
                  >
                    <StatusBadge status={motionElements[4].status} />
                    <div className="flex items-center gap-3">
                      <div className="text-cyan-400">{motionElements[4].icon}</div>
                      <div className="text-left">
                        <div className="text-sm font-semibold text-white">{motionElements[4].label}</div>
                        <div className="text-xs text-white/60">{motionElements[4].sublabel}</div>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* RevOps Audit Badge */}
              <div className="text-center">
                <div className="inline-flex items-center gap-2 glass-card px-4 py-2 rounded-lg border border-cyan-400/40">
                  <Settings className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-white font-medium">REVOPS AUDIT</span>
                  <span className="text-xs text-white/60">(Single Source of Truth)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Layer - Market Vectors */}
        <div
          className="relative"
          style={{
            transform: "rotateX(8deg) translateZ(-100px)",
            transformStyle: "preserve-3d",
          }}
        >
          <div className="blueprint-layer-bottom px-8 py-12 rounded-2xl relative overflow-hidden">
            <div className="absolute inset-0 rounded-2xl border-2 border-cyan-400/60 glow-border-cyan" />
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 via-transparent to-cyan-500/10 rounded-2xl" />

            {/* Layer Title */}
            <div className="relative z-10 mb-8">
              <h3 className="text-3xl font-bold text-white mb-1">MARKET VECTORS</h3>
              <p className="text-cyan-400 text-sm">PMF Quantification & Unit Economic Sustainability</p>
            </div>

            {/* Elements Flow */}
            <div className="relative z-10 flex items-center justify-between gap-4">
              {marketElements.map((element, idx) => (
                <div key={element.id} className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedElement(element)}
                    className="relative group flex flex-col items-center gap-2 p-4 rounded-xl glass-card border-2 border-cyan-400/40 hover:border-cyan-400 hover:scale-105 transition-all duration-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.4)]"
                  >
                    <StatusBadge status={element.status} />
                    <div className="w-14 h-14 rounded-full bg-cyan-400/10 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-400/20 transition-colors">
                      {element.icon}
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-semibold text-white">{element.label}</div>
                      {element.sublabel && <div className="text-xs text-white/60">{element.sublabel}</div>}
                    </div>
                  </button>

                  {idx < marketElements.length - 1 && <div className="arrow-connector" />}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Framework Badge - Top */}
        <div className="absolute -top-16 left-1/2 -translate-x-1/2 z-20">
          <div className="glass-card px-6 py-3 rounded-full border-2 border-cyan-400/60 shadow-[0_0_40px_rgba(6,182,212,0.4)]">
            <div className="text-center">
              <div className="text-sm font-bold text-cyan-400">CELERIO FRAMEWORK: SCALE WITHOUT WEIGHT</div>
              <div className="text-xs text-white/70">(Fractional Expertise, Digital Twin Ops, Agile GTM)</div>
            </div>
          </div>
        </div>

        {/* Diagnostic Loop Badge - Center */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30 pointer-events-none">
          <div className="glass-card px-4 py-2 rounded-lg border border-cyan-400/40 backdrop-blur-xl">
            <div className="text-xs text-cyan-400 font-semibold">DIAGNOSTIC & OPERATIONAL INTERVENTION LOOP</div>
          </div>
        </div>
      </div>

      {/* Modal Popup */}
      {selectedElement && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedElement(null)}
        >
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xl" />

          <Card
            className="relative w-full max-w-2xl glass-card border-2 border-cyan-400/60 shadow-[0_0_60px_rgba(6,182,212,0.4)] animate-in zoom-in duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedElement(null)}
              className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>

            <div className="p-8">
              {/* Header */}
              <div className="flex items-start gap-4 mb-6">
                <div
                  className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
                    selectedElement.findings.status === "critical"
                      ? "bg-red-500/20 text-red-400"
                      : selectedElement.findings.status === "warning"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-green-500/20 text-green-400"
                  }`}
                >
                  {selectedElement.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-white mb-2">{selectedElement.findings.title}</h3>
                  <div className="flex items-center gap-2">
                    {selectedElement.findings.status === "critical" && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/40 text-red-400 text-sm font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Critical
                      </span>
                    )}
                    {selectedElement.findings.status === "warning" && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 text-sm font-medium">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Warning
                      </span>
                    )}
                    {selectedElement.findings.status === "healthy" && (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 text-sm font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Healthy
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-white/80 text-base leading-relaxed mb-6">{selectedElement.findings.description}</p>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4 mb-8">
                {selectedElement.findings.metrics.map((metric, idx) => (
                  <div key={idx} className="glass-card p-4 rounded-lg border border-cyan-400/20">
                    <div className="text-white/60 text-sm mb-1">{metric.label}</div>
                    <div className="text-white text-2xl font-bold">{metric.value}</div>
                  </div>
                ))}
              </div>

              {/* Solution Section */}
              <div className="border-t border-cyan-400/20 pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-5 h-5 text-cyan-400" />
                  <h4 className="text-lg font-bold text-white">Recommended Solution</h4>
                </div>

                <div className="glass-card p-5 rounded-xl border border-cyan-400/30 mb-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="text-cyan-400 font-semibold text-base mb-1">
                        {selectedElement.findings.solution.agentName}
                      </div>
                      <div className="text-white/80 text-sm">{selectedElement.findings.solution.action}</div>
                    </div>
                    <div className="text-xs text-white/50 whitespace-nowrap ml-4">
                      Deploy: {selectedElement.findings.solution.deployTime}
                    </div>
                  </div>

                  <div className="glass-card bg-cyan-400/5 px-4 py-3 rounded-lg border border-cyan-400/20">
                    <div className="text-xs text-white/60 mb-1">Estimated Impact</div>
                    <div className="text-cyan-400 font-semibold">
                      {selectedElement.findings.solution.estimatedImpact}
                    </div>
                  </div>
                </div>

                {/* Deploy Button */}
                {selectedElement.findings.status !== "healthy" && (
                  <Button
                    onClick={() => handleDeploy(selectedElement.findings.solution)}
                    disabled={isDeploying}
                    className="w-full bg-cyan-400 hover:bg-cyan-500 text-slate-950 font-bold py-6 text-base rounded-lg shadow-[0_0_30px_rgba(6,182,212,0.4)] hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] transition-all"
                  >
                    {isDeploying ? (
                      <span className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-slate-950/20 border-t-slate-950 rounded-full animate-spin" />
                        Deploying...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        Deploy {selectedElement.findings.solution.agentName}
                      </span>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
