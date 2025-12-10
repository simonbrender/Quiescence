import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import RadarChart from './RadarChart'

function CompanyCard({ company, onClick }) {
  const getStallBadge = () => {
    const { stall_probability } = company
    if (stall_probability === 'high') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20">
          <XCircle className="w-3 h-3" />
          High Risk
        </span>
      )
    } else if (stall_probability === 'medium') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">
          <AlertTriangle className="w-3 h-3" />
          Medium Risk
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-500 border border-green-500/20">
          <CheckCircle className="w-3 h-3" />
          Low Risk
        </span>
      )
    }
  }

  const getKeySignals = () => {
    const signals = company.signals || {}
    const keySignals = []
    
    if (signals.motion?.hiring_status === 'frozen') {
      keySignals.push('Hiring Frozen')
    }
    if (signals.market?.reddit_mentions === 0) {
      keySignals.push('Reddit Silent')
    }
    if (signals.messaging?.jargon_density > 0.1) {
      keySignals.push('High Jargon')
    }
    if (signals.market?.last_commit_days > 90) {
      keySignals.push('Stale Codebase')
    }
    
    return keySignals.slice(0, 3)
  }

  return (
    <div
      onClick={onClick}
      className="celerio-card p-5 cursor-pointer"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-foreground truncate">{company.name}</h3>
          <p className="text-sm text-muted-foreground mt-0.5 truncate">{company.domain}</p>
        </div>
        <div className="ml-2 flex-shrink-0">
          {getStallBadge()}
        </div>
      </div>

      <div className="mb-4">
        <RadarChart
          messaging={company.messaging_score}
          motion={company.motion_score}
          market={company.market_score}
          size={120}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Messaging</div>
          <div className={`text-base font-semibold ${
            company.messaging_score >= 60 ? 'text-green-500' :
            company.messaging_score >= 40 ? 'text-yellow-500' : 'text-red-500'
          }`}>
            {company.messaging_score.toFixed(0)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Motion</div>
          <div className={`text-base font-semibold ${
            company.motion_score >= 60 ? 'text-green-500' :
            company.motion_score >= 40 ? 'text-yellow-500' : 'text-red-500'
          }`}>
            {company.motion_score.toFixed(0)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Market</div>
          <div className={`text-base font-semibold ${
            company.market_score >= 60 ? 'text-green-500' :
            company.market_score >= 40 ? 'text-yellow-500' : 'text-red-500'
          }`}>
            {company.market_score.toFixed(0)}
          </div>
        </div>
      </div>

      {getKeySignals().length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {getKeySignals().map((signal, idx) => (
            <span
              key={idx}
              className="px-2 py-1 rounded text-xs bg-background text-muted-foreground border border-border"
            >
              {signal}
            </span>
          ))}
        </div>
      )}

      {company.yc_batch && (
        <div className="mt-3 text-xs text-muted-foreground">
          YC {company.yc_batch}
        </div>
      )}
    </div>
  )
}

export default CompanyCard

