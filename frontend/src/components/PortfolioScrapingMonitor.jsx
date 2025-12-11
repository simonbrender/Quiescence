import { useState, useEffect, useRef } from 'react'
import { X, Maximize2, Minimize2, Camera, Loader2, TrendingUp, Activity } from 'lucide-react'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

function PortfolioScrapingMonitor({ sessionId, onClose, onComplete }) {
  const [events, setEvents] = useState([])
  const [isMinimized, setIsMinimized] = useState(false)
  const [latestScreenshot, setLatestScreenshot] = useState(null)
  const [status, setStatus] = useState('starting')
  const [stats, setStats] = useState({
    yc: { companies: 0, scrolls: 0 },
    antler: { companies: 0, clicks: 0 },
    total: 0
  })
  const [chartData, setChartData] = useState([]) // For progress chart
  const [rateData, setRateData] = useState([]) // For rate chart
  const wsRef = useRef(null)
  const eventsEndRef = useRef(null)

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/api/ws/portfolio-scraping/${sessionId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setEvents(prev => [...prev, data])
      
      // Update status
      if (data.type === 'start' || data.type === 'start_both') {
        setStatus('running')
      } else if (data.type === 'complete' || data.type === 'complete_both') {
        setStatus('completed')
        if (onComplete) {
          onComplete()
        }
      } else if (data.type === 'error') {
        setStatus('error')
      }
      
      // Update screenshot
      if (data.type === 'screenshot' && data.screenshot) {
        setLatestScreenshot(`data:image/png;base64,${data.screenshot}`)
      }
      
      // Update stats
      if (data.type === 'progress') {
        const timestamp = Date.now()
        const totalCompanies = data.total_companies || 0
        
        if (data.portfolio === 'YC' || data.source === 'yc') {
          setStats(prev => ({
            ...prev,
            yc: {
              companies: data.yc_companies || data.companies_found || prev.yc.companies,
              scrolls: data.scroll_attempt || prev.yc.scrolls
            },
            total: totalCompanies || prev.total
          }))
        } else if (data.portfolio === 'Antler' || data.source === 'antler') {
          setStats(prev => ({
            ...prev,
            antler: {
              companies: data.antler_companies || data.companies_found || prev.antler.companies,
              clicks: data.load_more_attempt || prev.antler.clicks
            },
            total: totalCompanies || prev.total
          }))
        } else {
          setStats(prev => ({
            ...prev,
            total: totalCompanies || prev.total
          }))
        }
        
        // Update chart data
        setChartData(prev => {
          const newData = [...prev, { time: timestamp, companies: totalCompanies }]
          return newData.slice(-50) // Keep last 50 data points
        })
        
        // Calculate rate (companies per minute)
        if (chartData.length > 0) {
          const timeDiff = (timestamp - chartData[0].time) / 60000 // minutes
          const companiesDiff = totalCompanies - (chartData[0].companies || 0)
          const rate = timeDiff > 0 ? companiesDiff / timeDiff : 0
          setRateData(prev => {
            const newRate = [...prev, { time: timestamp, rate }]
            return newRate.slice(-50)
          })
        }
      }
      
      // Update total from any event with total_companies
      if (data.total_companies !== undefined) {
        setStats(prev => ({ ...prev, total: data.total_companies }))
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setStatus('error')
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [sessionId])

  useEffect(() => {
    // Auto-scroll to bottom
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'text-cyan-400'
      case 'completed': return 'text-green-400'
      case 'error': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'starting': return 'Starting...'
      case 'running': return 'Scraping in progress...'
      case 'completed': return 'Scraping completed!'
      case 'error': return 'Error occurred'
      default: return 'Unknown'
    }
  }

  return (
    <Card className={cn(
      "fixed bottom-4 right-4 z-[9999]",
      "bg-gray-900/90 backdrop-blur-lg shadow-2xl border-cyan-400/40",
      "border-2 rounded-lg",
      isMinimized ? "w-80 h-16" : "w-[700px] h-[600px]",
      "transition-all duration-300 flex flex-col",
      "overflow-hidden"
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-cyan-400/20">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-white">Portfolio Scraping Monitor</span>
          {status === 'running' && <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMinimized(!isMinimized)}
            className="h-6 w-6 p-0 text-white/60 hover:text-white"
          >
            {isMinimized ? <Maximize2 className="w-3 h-3" /> : <Minimize2 className="w-3 h-3" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-6 w-6 p-0 text-white/60 hover:text-white"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Status Bar */}
          <div className="p-3 border-b border-cyan-400/20">
            <div className="flex items-center justify-between mb-2">
              <span className={cn("text-xs font-medium", getStatusColor())}>
                {getStatusText()}
              </span>
              <span className="text-xs text-white/60">Session: {sessionId.slice(0, 8)}</span>
            </div>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-2 mt-2">
              <div className="bg-white/5 rounded p-2 border border-cyan-400/20">
                <div className="text-xs text-white/60 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  Total Companies
                </div>
                <div className="text-2xl font-bold text-cyan-400">{stats.total}</div>
                <div className="text-xs text-white/40 mt-1">
                  {rateData.length > 0 && rateData[rateData.length - 1]?.rate > 0 && (
                    <span className="text-green-400">
                      {Math.round(rateData[rateData.length - 1].rate)}/min
                    </span>
                  )}
                </div>
              </div>
              <div className="bg-white/5 rounded p-2 border border-cyan-400/20">
                <div className="text-xs text-white/60">YC Companies</div>
                <div className="text-xl font-bold text-cyan-400">{stats.yc.companies}</div>
                <div className="text-xs text-white/40">Scrolls: {stats.yc.scrolls}</div>
              </div>
              <div className="bg-white/5 rounded p-2 border border-purple-400/20">
                <div className="text-xs text-white/60">Antler Companies</div>
                <div className="text-xl font-bold text-purple-400">{stats.antler.companies}</div>
                <div className="text-xs text-white/40">Clicks: {stats.antler.clicks}</div>
              </div>
            </div>
            
            {/* Progress Chart */}
            {chartData.length > 1 && (
              <div className="mt-3 p-2 bg-black/30 rounded border border-cyan-400/10">
                <div className="text-xs text-white/60 mb-1 flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  Progress Chart
                </div>
                <div className="h-16 relative">
                  <svg className="w-full h-full" viewBox={`0 0 ${chartData.length * 10} 60`} preserveAspectRatio="none">
                    <polyline
                      points={chartData.map((d, i) => `${i * 10},${60 - (d.companies / Math.max(stats.total, 1)) * 60}`).join(' ')}
                      fill="none"
                      stroke="rgb(34, 211, 238)"
                      strokeWidth="2"
                      className="drop-shadow-lg"
                    />
                  </svg>
                  <div className="absolute bottom-0 left-0 right-0 text-xs text-white/40 text-center">
                    {stats.total} companies
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Screenshot Preview - Picture in Picture */}
          {latestScreenshot && (
            <div className="p-3 border-b border-cyan-400/20 relative">
              <div className="text-xs text-white/60 mb-1 flex items-center gap-1">
                <Camera className="w-3 h-3" />
                Browser Activity (Live)
              </div>
              <div className="relative rounded-lg overflow-hidden border-2 border-cyan-400/30 shadow-lg">
                <img 
                  src={latestScreenshot} 
                  alt="Scraping progress" 
                  className="w-full max-h-48 object-contain bg-black/40"
                />
                <div className="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-white">
                  Live
                </div>
              </div>
            </div>
          )}

                {/* Event Log */}
                <div className="flex-1 overflow-y-auto p-3 space-y-1">
                  {events.map((event, idx) => {
                    const eventType = event.type || 'unknown'
                    const getTypeColor = (type) => {
                      if (type.includes('error')) return 'text-red-400'
                      if (type.includes('complete') || type.includes('success')) return 'text-green-400'
                      if (type.includes('start') || type.includes('initiated')) return 'text-blue-400'
                      if (type.includes('ollama')) return 'text-yellow-400'
                      if (type.includes('db_')) return 'text-purple-400'
                      if (type.includes('scraping')) return 'text-cyan-400'
                      return 'text-cyan-400'
                    }
                    return (
                      <div key={idx} className="text-xs text-white/80 font-mono border-l-2 border-cyan-400/20 pl-2 py-1">
                        <span className="text-white/40">[{new Date(event.timestamp || Date.now()).toLocaleTimeString()}]</span>
                        <span className={`${getTypeColor(eventType)} ml-2 font-semibold`}>{eventType}</span>
                        {event.portfolio && (
                          <span className="text-purple-400 ml-2">{event.portfolio}</span>
                        )}
                        {event.message && (
                          <span className="text-white/60 ml-2">{event.message}</span>
                        )}
                        {event.companies_found !== undefined && (
                          <span className="text-green-400 ml-2">{event.companies_found} companies</span>
                        )}
                        {event.count !== undefined && (
                          <span className="text-green-400 ml-2">{event.count} results</span>
                        )}
                        {event.model && (
                          <span className="text-yellow-400 ml-2">Model: {event.model}</span>
                        )}
                      </div>
                    )
                  })}
                  {events.length === 0 && (
                    <div className="text-xs text-white/40 text-center py-4">
                      Waiting for events...
                    </div>
                  )}
                  <div ref={eventsEndRef} />
                </div>
        </>
      )}
    </Card>
  )
}

export default PortfolioScrapingMonitor

