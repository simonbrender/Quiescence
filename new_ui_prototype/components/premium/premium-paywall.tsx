"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Lock, Check, ArrowRight } from "lucide-react"

interface PremiumPaywallProps {
  onUnlock: () => void
}

export function PremiumPaywall({ onUnlock }: PremiumPaywallProps) {
  return (
    <div className="max-w-5xl mx-auto">
      <Card
        className="glass-card border-2 p-12 text-center space-y-8"
        style={{ borderColor: "var(--color-celerio-cyan)" }}
      >
        <div
          className="w-20 h-20 rounded-full glass-card mx-auto flex items-center justify-center border-2"
          style={{ borderColor: "var(--color-celerio-cyan)" }}
        >
          <Lock className="w-10 h-10" style={{ color: "var(--color-celerio-cyan-bright)" }} />
        </div>

        <div className="space-y-4">
          <h2 className="text-4xl font-bold text-white text-balance">
            Unlock Your Complete <span style={{ color: "var(--color-celerio-cyan-bright)" }}>90-Day Blueprint</span>
          </h2>
          <p className="text-xl text-white/70 max-w-2xl mx-auto text-pretty">
            Get the full diagnostic report, prescriptive action plan, and embedded execution monitoring
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 text-left max-w-3xl mx-auto">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Included in Premium Access:</h3>
            <ul className="space-y-3">
              {[
                "Complete 3-Vector Diagnostic Report",
                "90-Day Prescriptive Action Plan",
                "Live Revenue Dashboard",
                "Weekly AI-Powered Progress Audits",
                "Direct Slack Access to Architects",
                "Quarterly Strategy Recalibration",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <Check
                    className="w-5 h-5 mt-0.5 flex-shrink-0"
                    style={{ color: "var(--color-celerio-cyan-bright)" }}
                  />
                  <span className="text-white/90">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-6">
            <div className="glass-card p-6 rounded-lg border-2" style={{ borderColor: "var(--color-celerio-cyan)" }}>
              <div className="text-white/60 text-sm mb-2">One-Time Investment</div>
              <div className="text-5xl font-bold text-white mb-4">$89,000</div>
              <div className="text-white/60 text-sm mb-4">Average client ROI: 23.4x within 12 months</div>
              <div className="text-xs text-white/50">Typical consulting firm equivalent: $500K - $2M</div>
            </div>

            <Button size="lg" className="w-full text-lg py-6 bg-white text-black hover:bg-white/90" onClick={onUnlock}>
              Unlock Full Blueprint
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>

            <p className="text-xs text-white/50 text-center">
              ROI Guarantee: 10x return or we work for free until you hit it
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
