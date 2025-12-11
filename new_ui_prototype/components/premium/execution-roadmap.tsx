"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Lock, Sparkles, CheckCircle2 } from "lucide-react"

interface RoadmapTask {
  id: number
  title: string
  description: string
  duration: string
  status: "locked" | "unlocked"
}

const roadmapTasks: RoadmapTask[] = [
  {
    id: 1,
    title: "Deploy RevOps Digital Twin",
    description: "Implement automated data pipeline from HubSpot to normalize funnel metrics",
    duration: "2 weeks",
    status: "unlocked",
  },
  {
    id: 2,
    title: "Rewrite Sales Narrative",
    description: 'Realign positioning from "Workflow Tool" to "Revenue Operations Platform"',
    duration: "1 week",
    status: "unlocked",
  },
  {
    id: 3,
    title: "Launch ICP Segmentation Matrix",
    description: "Deploy AI-powered segmentation to identify high-fit accounts",
    duration: "3 weeks",
    status: "locked",
  },
  {
    id: 4,
    title: "Optimize Unit Economics Model",
    description: "Restructure pricing to escape gross margin trap",
    duration: "2 weeks",
    status: "locked",
  },
  {
    id: 5,
    title: "Implement Expansion Playbook",
    description: "Launch land-and-expand motion with automated upsell triggers",
    duration: "4 weeks",
    status: "locked",
  },
]

interface ExecutionRoadmapProps {
  onUnlock?: () => void
}

export function ExecutionRoadmap({ onUnlock }: ExecutionRoadmapProps) {
  const [showPaywall, setShowPaywall] = useState(true)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Sparkles className="w-8 h-8 text-cyan-400" />
        <div>
          <h2 className="text-3xl font-bold text-white">Generated 90-Day Execution Roadmap</h2>
          <p className="text-cyan-400 text-lg">Agentic task sequence to resolve detected stall vectors</p>
        </div>
      </div>

      {/* Roadmap Tasks */}
      <div className="space-y-4 relative">
        {roadmapTasks.map((task, idx) => (
          <Card
            key={task.id}
            className={`p-6 border-2 transition-all duration-300 ${
              task.status === "locked" && showPaywall
                ? "opacity-50 blur-sm pointer-events-none"
                : "bg-[#0A1628] border-cyan-400/30 hover:border-cyan-400/60"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4 flex-1">
                {/* Task Number Badge */}
                <Badge
                  className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold border-2"
                  style={{
                    backgroundColor: "rgba(6, 182, 212, 0.15)",
                    borderColor: "rgb(6, 182, 212)",
                    color: "rgb(6, 182, 212)",
                  }}
                >
                  {task.id}
                </Badge>

                {/* Task Content */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-bold text-white">{task.title}</h3>
                    {task.status === "unlocked" && <CheckCircle2 className="w-5 h-5 text-green-400" />}
                  </div>
                  <p className="text-white/70 leading-relaxed">{task.description}</p>
                  <Badge
                    className="text-xs"
                    style={{
                      backgroundColor: "rgba(6, 182, 212, 0.1)",
                      color: "rgb(6, 182, 212)",
                    }}
                  >
                    {task.duration}
                  </Badge>
                </div>
              </div>
            </div>
          </Card>
        ))}

        {/* Paywall Overlay */}
        {showPaywall && (
          <div className="absolute inset-0 flex items-center justify-center pt-32">
            <Card
              className="glass-card border-2 border-cyan-400/50 p-8 max-w-lg backdrop-blur-xl"
              style={{
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
              }}
            >
              <div className="text-center space-y-6">
                {/* Lock Icon */}
                <div className="flex justify-center">
                  <div
                    className="w-16 h-16 rounded-full flex items-center justify-center"
                    style={{
                      backgroundColor: "rgba(6, 182, 212, 0.2)",
                      border: "2px solid rgb(6, 182, 212)",
                    }}
                  >
                    <Lock className="w-8 h-8 text-cyan-400" />
                  </div>
                </div>

                {/* Content */}
                <div className="space-y-3">
                  <h3 className="text-2xl font-bold text-white">Unlock Full Strategic Access</h3>
                  <p className="text-white/70 leading-relaxed">
                    Deploy the Fractional Revenue Architect to access your complete 90-day remediation plan with
                    detailed execution steps and monitoring
                  </p>
                </div>

                {/* Pricing */}
                <div className="py-4">
                  <p className="text-5xl font-bold text-white mb-2">$4,000/mo</p>
                  <p className="text-cyan-400">Continuous diagnostic & intervention</p>
                </div>

                {/* CTA Button */}
                <Button
                  size="lg"
                  className="w-full text-lg py-6"
                  style={{
                    backgroundColor: "rgb(6, 182, 212)",
                    color: "#0A1628",
                  }}
                  onClick={() => {
                    setShowPaywall(false)
                    onUnlock?.()
                  }}
                >
                  Unlock Plan
                </Button>

                {/* Trust Indicators */}
                <div className="flex items-center justify-center gap-6 pt-4 text-sm text-white/60">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span>23.4x ROI</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span>48hr delivery</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
