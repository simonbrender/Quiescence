import { X, ExternalLink, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'
import RadarChart from './RadarChart'
import RevenueBowtie from './RevenueBowtie'
import { useState } from 'react'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

function CompanyDetail({ company, onClose, onScan }) {
  const [scanUrl, setScanUrl] = useState('')
  const [scanning, setScanning] = useState(false)

  const handleScanSubmit = async (e) => {
    e.preventDefault()
    if (!scanUrl.trim()) return
    
    setScanning(true)
    try {
      await onScan(scanUrl)
      setScanUrl('')
    } finally {
      setScanning(false)
    }
  }

  const getRecommendation = () => {
    const { messaging_score, motion_score, market_score } = company
    const recommendations = []
    
    if (messaging_score < 50) {
      recommendations.push({
        vector: 'Messaging',
        issue: 'Low narrative consistency or high jargon density',
        action: 'Recommend: Strategic Narrative Audit & Messaging Workshop'
      })
    }
    
    if (motion_score < 50) {
      recommendations.push({
        vector: 'Motion',
        issue: 'GTM velocity signals indicate stagnation',
        action: 'Recommend: Revenue Architecture Review & Sales Velocity Analysis'
      })
    }
    
    if (market_score < 50) {
      recommendations.push({
        vector: 'Market',
        issue: 'Weak PMF signals or low market engagement',
        action: 'Recommend: PMF Survey & ICP Segmentation Analysis'
      })
    }
    
    return recommendations.length > 0 ? recommendations : [{
      vector: 'Overall',
      issue: 'Company shows healthy signals across all vectors',
      action: 'Continue monitoring for early warning signs'
    }]
  }

  const signals = company.signals || {}

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="glass-card border-cyan-400/30 max-w-4xl w-full max-h-[90vh] overflow-y-auto bg-white/5">
        {/* Header */}
        <div className="sticky top-0 glass-card border-b border-cyan-400/30 p-4 flex items-center justify-between bg-white/5 backdrop-blur-sm">
          <div>
            <h2 className="text-2xl font-bold text-white">{company.name}</h2>
            <p className="text-white/60">{company.domain}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Radar Chart */}
          <Card className="glass-card border-cyan-400/30 p-6 bg-white/5">
            <h3 className="text-lg font-semibold text-white mb-4">Celerio Radar</h3>
            <div className="flex justify-center">
              <RadarChart
                messaging={company.messaging_score}
                motion={company.motion_score}
                market={company.market_score}
                size={300}
              />
            </div>
          </Card>

          {/* Revenue Architecture Bowtie */}
          <RevenueBowtie company={company} />

          {/* Scores Grid */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="glass-card border-cyan-400/30 p-4 bg-white/5">
              <div className="text-sm text-white/60 mb-2">Messaging Score</div>
              <div className={cn(
                "text-3xl font-bold",
                company.messaging_score >= 60 ? 'text-green-400' :
                company.messaging_score >= 40 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {company.messaging_score.toFixed(1)}
              </div>
              <div className="text-xs text-white/40 mt-2">
                Jargon: {(signals.messaging?.jargon_density * 100 || 0).toFixed(1)}%
              </div>
            </Card>
            
            <Card className="glass-card border-cyan-400/30 p-4 bg-white/5">
              <div className="text-sm text-white/60 mb-2">Motion Score</div>
              <div className={cn(
                "text-3xl font-bold",
                company.motion_score >= 60 ? 'text-green-400' :
                company.motion_score >= 40 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {company.motion_score.toFixed(1)}
              </div>
              <div className="text-xs text-white/40 mt-2">
                Hiring: {signals.motion?.hiring_status || 'unknown'}
              </div>
            </Card>
            
            <Card className="glass-card border-cyan-400/30 p-4 bg-white/5">
              <div className="text-sm text-white/60 mb-2">Market Score</div>
              <div className={cn(
                "text-3xl font-bold",
                company.market_score >= 60 ? 'text-green-400' :
                company.market_score >= 40 ? 'text-yellow-400' : 'text-red-400'
              )}>
                {company.market_score.toFixed(1)}
              </div>
              <div className="text-xs text-white/40 mt-2">
                Stars: {signals.market?.github_stars || 0}
              </div>
            </Card>
          </div>

          {/* Signals Detail */}
          <Card className="glass-card border-cyan-400/30 p-6 bg-white/5">
            <h3 className="text-lg font-semibold text-white mb-4">Signal Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-cyan-400 mb-2">Messaging Signals</h4>
                <ul className="space-y-1 text-sm text-white/80">
                  <li>H1 Volatility: {signals.messaging?.h1_volatility || 0}</li>
                  <li>Positioning Consistency: {(signals.messaging?.positioning_consistency || 0).toFixed(1)}%</li>
                  <li>Jargon Density: {(signals.messaging?.jargon_density * 100 || 0).toFixed(1)}%</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-medium text-cyan-400 mb-2">Motion Signals</h4>
                <ul className="space-y-1 text-sm text-white/80">
                  <li>Traffic Score: {(signals.motion?.traffic_score || 0).toFixed(1)}</li>
                  <li>Hiring Status: {signals.motion?.hiring_status || 'unknown'}</li>
                  <li>Sales/Eng Ratio: {(signals.motion?.sales_to_eng_ratio || 0).toFixed(1)}</li>
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-medium text-cyan-400 mb-2">Market Signals</h4>
                <ul className="space-y-1 text-sm text-white/80">
                  <li>Reddit Mentions: {signals.market?.reddit_mentions || 0}</li>
                  <li>Sentiment Score: {(signals.market?.sentiment_score || 0).toFixed(1)}</li>
                  <li>Last Commit: {signals.market?.last_commit_days || 0} days ago</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Recommendations */}
          <Card className="glass-card border-cyan-400/30 p-6 bg-white/5">
            <h3 className="text-lg font-semibold text-white mb-4">Remediation Recommendations</h3>
            <div className="space-y-3">
              {getRecommendation().map((rec, idx) => (
                <Card key={idx} className="glass-card border-cyan-400/20 p-4 bg-white/5">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-medium text-white mb-1">{rec.vector} Vector</div>
                      <div className="text-sm text-white/60 mb-2">{rec.issue}</div>
                      <div className="text-sm text-cyan-400">{rec.action}</div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </Card>

          {/* Scan New Company */}
          <Card className="glass-card border-cyan-400/30 p-6 bg-white/5">
            <h3 className="text-lg font-semibold text-white mb-4">Scan New Company</h3>
            <form onSubmit={handleScanSubmit} className="flex gap-2">
              <input
                type="text"
                placeholder="Enter company URL (e.g., example.com)"
                className="flex-1 px-4 py-2 glass-card border border-cyan-400/30 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
                value={scanUrl}
                onChange={(e) => setScanUrl(e.target.value)}
              />
              <Button
                type="submit"
                disabled={scanning}
                className="text-[#0A1628] font-semibold"
                style={{ backgroundColor: 'rgb(6, 182, 212)' }}
              >
                {scanning ? 'Scanning...' : 'Scan'}
              </Button>
            </form>
          </Card>
        </div>
      </Card>
    </div>
  )
}

export default CompanyDetail
