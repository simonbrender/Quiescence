import { TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

function StatsPanel({ stats }) {
  return (
    <div className="bg-slate-800/50 border border-blue-800/30 rounded-lg p-4 mt-4 backdrop-blur-sm">
      <h2 className="text-lg font-semibold text-white mb-4">Market Health</h2>
      
      <div className="space-y-4">
        <div>
          <div className="text-sm text-slate-400 mb-1">Total Companies</div>
          <div className="text-2xl font-bold text-white">{stats.total_companies}</div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-slate-900/50 rounded">
            <div className="text-xs text-slate-400 mb-1">Messaging</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_messaging_score.toFixed(0)}
            </div>
          </div>
          <div className="text-center p-2 bg-slate-900/50 rounded">
            <div className="text-xs text-slate-400 mb-1">Motion</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_motion_score.toFixed(0)}
            </div>
          </div>
          <div className="text-center p-2 bg-slate-900/50 rounded">
            <div className="text-xs text-slate-400 mb-1">Market</div>
            <div className="text-sm font-semibold text-cyan-400">
              {stats.avg_market_score.toFixed(0)}
            </div>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-slate-300">High Risk</span>
            </div>
            <span className="text-sm font-semibold text-red-400">{stats.high_risk_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-slate-300">Medium Risk</span>
            </div>
            <span className="text-sm font-semibold text-yellow-400">{stats.medium_risk_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm text-slate-300">Low Risk</span>
            </div>
            <span className="text-sm font-semibold text-green-400">{stats.low_risk_count}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StatsPanel

