import { TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { Card } from './ui/card'
import { cn } from '@/lib/utils'

function StatsPanel({ stats }) {
  return (
    <Card className="glass-card border-cyan-400/30 p-4 mt-4 bg-white/5">
      <h2 className="text-lg font-semibold text-white mb-4">Market Health</h2>
      
      <div className="space-y-4">
        <div>
          <div className="text-sm text-white/60 mb-1">Total Companies</div>
          <div className="text-2xl font-bold text-white">{stats.total_companies}</div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 glass-card border border-cyan-400/20 rounded bg-white/5">
            <div className="text-xs text-white/60 mb-1">Messaging</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_messaging_score.toFixed(0)}
            </div>
          </div>
          <div className="text-center p-2 glass-card border border-cyan-400/20 rounded bg-white/5">
            <div className="text-xs text-white/60 mb-1">Motion</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_motion_score.toFixed(0)}
            </div>
          </div>
          <div className="text-center p-2 glass-card border border-cyan-400/20 rounded bg-white/5">
            <div className="text-xs text-white/60 mb-1">Market</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_market_score.toFixed(0)}
            </div>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-cyan-400/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-white/80">High Risk</span>
            </div>
            <span className="text-sm font-semibold text-red-400">{stats.high_risk_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-white/80">Medium Risk</span>
            </div>
            <span className="text-sm font-semibold text-yellow-400">{stats.medium_risk_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm text-white/80">Low Risk</span>
            </div>
            <span className="text-sm font-semibold text-green-400">{stats.low_risk_count}</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default StatsPanel
