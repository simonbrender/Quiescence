"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowRight, Check, Sparkles } from "lucide-react"
import { NativeBlueprint } from "@/components/premium/native-blueprint"
import { DiagnosticCards } from "@/components/premium/diagnostic-cards"
import { ExecutionRoadmap } from "@/components/premium/execution-roadmap"

export default function PremiumPage() {
  const [isUnlocked, setIsUnlocked] = useState(false)

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0A1628" }}>
      {/* Grid Background */}
      <div className="fixed inset-0 grid-pattern opacity-20" />

      {/* Gradient Orb Effects */}
      <div
        className="fixed top-20 left-20 w-96 h-96 rounded-full blur-3xl opacity-15 animate-pulse-glow"
        style={{ background: "radial-gradient(circle, rgb(6, 182, 212) 0%, transparent 70%)" }}
      />
      <div
        className="fixed bottom-20 right-20 w-96 h-96 rounded-full blur-3xl opacity-15 animate-pulse-glow"
        style={{ background: "radial-gradient(circle, rgb(6, 182, 212) 0%, transparent 70%)" }}
      />

      <div className="relative z-10">
        {/* Hero Section */}
        <section className="container mx-auto px-4 pt-24 pb-16">
          <div className="max-w-6xl mx-auto text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-sm mb-4">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span className="text-cyan-400">Enterprise Revenue Architecture</span>
            </div>

            <h1 className="text-7xl font-bold text-white leading-tight text-balance">
              Celerio <span className="text-glow-cyan text-cyan-400">Intervene</span>
            </h1>

            <p className="text-2xl text-white/70 max-w-3xl mx-auto leading-relaxed text-pretty">
              Agentic Revenue Architecture that diagnoses and fixes $3M+ ARR stalls with surgical precision
            </p>

            <div className="flex items-center justify-center gap-4 pt-6">
              <Button
                size="lg"
                className="text-lg px-8 py-6 text-[#0A1628] font-semibold"
                style={{ backgroundColor: "rgb(6, 182, 212)" }}
              >
                Request Diagnostic
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8 py-6 glass-card text-white border-2 hover:bg-white/10 bg-transparent border-cyan-400/50"
              >
                View Methodology
              </Button>
            </div>
          </div>
        </section>

        {/* Trust Indicators */}
        <section className="container mx-auto px-4 py-12">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { value: "$847M", label: "Revenue Diagnosed" },
                { value: "127", label: "B2B Companies" },
                { value: "23.4x", label: "Avg. ROI Multiple" },
              ].map((stat) => (
                <Card key={stat.label} className="glass-card p-8 text-center border-0">
                  <div className="text-5xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-white/60 text-lg">{stat.label}</div>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Interactive Blueprint */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-5xl font-bold text-white mb-4 text-balance">
                The Revenue <span className="text-cyan-400">Architecture Blueprint</span>
              </h2>
              <p className="text-xl text-white/70 max-w-3xl mx-auto text-pretty">
                Click any element to explore diagnostic insights across Messaging, Motion, and Market vectors
              </p>
            </div>

            <NativeBlueprint />
          </div>
        </section>

        {/* Diagnostic Cards */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-5xl font-bold text-white mb-4">
                Real-Time <span className="text-cyan-400">Vector Diagnostics</span>
              </h2>
              <p className="text-xl text-white/70">Live scoring across all three architectural dimensions</p>
            </div>

            <DiagnosticCards />
          </div>
        </section>

        {/* Execution Roadmap */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-6xl mx-auto">
            <ExecutionRoadmap onUnlock={() => setIsUnlocked(true)} />
          </div>
        </section>

        {/* Value Proposition Grid */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-4xl font-bold text-white text-center mb-12">
              Why Celerio Outperforms <span className="text-cyan-400">Traditional Consulting</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  title: "Traditional Consulting",
                  subtitle: "Bain, McKinsey, BCG",
                  items: [
                    "12-16 week engagements",
                    "Junior analyst heavy",
                    "PowerPoint deliverables",
                    "No execution accountability",
                    "$500K - $2M+ fees",
                  ],
                  highlight: false,
                },
                {
                  title: "Celerio Intervene",
                  subtitle: "Agentic Revenue Architecture",
                  items: [
                    "48-hour diagnostic delivery",
                    "AI + senior operator hybrid",
                    "Live dashboard + 90-day playbook",
                    "Embedded execution monitoring",
                    "ROI-based pricing",
                  ],
                  highlight: true,
                },
              ].map((column) => (
                <Card
                  key={column.title}
                  className={`p-8 border-2 ${column.highlight ? "glass-card border-cyan-400" : "bg-black/40 border-white/10"}`}
                >
                  <div className="mb-6">
                    <h3 className="text-2xl font-bold text-white mb-1">{column.title}</h3>
                    <p className="text-white/60">{column.subtitle}</p>
                  </div>

                  <ul className="space-y-4">
                    {column.items.map((item) => (
                      <li key={item} className="flex items-start gap-3">
                        <Check
                          className={`w-5 h-5 mt-0.5 flex-shrink-0 ${column.highlight ? "text-cyan-400" : "text-white/40"}`}
                        />
                        <span className={column.highlight ? "text-white" : "text-white/60"}>{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="container mx-auto px-4 py-24">
          <div className="max-w-4xl mx-auto text-center space-y-6">
            <h2 className="text-5xl font-bold text-white text-balance">
              Ready to architect your <span className="text-cyan-400">next growth phase?</span>
            </h2>
            <p className="text-xl text-white/70 text-pretty">
              Join 127 B2B companies that chose precision over PowerPoint
            </p>
            <Button
              size="lg"
              className="text-lg px-12 py-6 text-[#0A1628] font-semibold"
              style={{ backgroundColor: "rgb(6, 182, 212)" }}
            >
              Schedule Diagnostic Call
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
