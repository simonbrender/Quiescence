import { useState, useEffect, useRef } from 'react'
import { Loader2, CheckCircle2, XCircle, AlertCircle, Clock, TrendingUp } from 'lucide-react'

export default function DiscoveryProgress({ onComplete, onClose }) {
  const [status, setStatus] = useState('Starting discovery...')
  const [currentLayer, setCurrentLayer] = useState('')
  const [progress, setProgress] = useState(0)
  const [stats, setStats] = useState({
    discovered: 0,
    added: 0,
    skipped: 0,
    errors: 0,
    vcs: 0,
    accelerators: 0,
    studios: 0
  })
  const [logs, setLogs] = useState([])
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState(null)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    // Connect to Server-Sent Events endpoint
    const eventSource = new EventSource('http://localhost:8000/portfolios/discover/stream')
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'status') {
          setStatus(data.message)
          if (data.layer) {
            setCurrentLayer(data.layer)
          }
        } else if (data.type === 'progress') {
          setProgress(data.progress || 0)
        } else if (data.type === 'stats') {
          setStats(prev => ({
            ...prev,
            ...data.stats
          }))
        } else if (data.type === 'log') {
          setLogs(prev => [...prev, {
            level: data.level || 'info',
            message: data.message,
            timestamp: new Date().toLocaleTimeString()
          }])
        } else if (data.type === 'complete') {
          setIsComplete(true)
          setProgress(100)
          setStatus('Discovery complete!')
          eventSource.close()
          if (onComplete) {
            setTimeout(() => {
              onComplete(data.result)
            }, 2000)
          }
        } else if (data.type === 'error') {
          setError(data.message)
          eventSource.close()
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err)
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      setError('Connection error. Discovery may still be running.')
      // Don't close on error - might be temporary
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [onComplete])

  const handleClose = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    if (onClose) {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-lg border border-cyan-400/30 w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {!isComplete && !error && (
              <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
            )}
            {isComplete && (
              <CheckCircle2 className="w-6 h-6 text-green-400" />
            )}
            {error && (
              <XCircle className="w-6 h-6 text-red-400" />
            )}
            <h2 className="text-xl font-bold text-white">VC Discovery Progress</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">{status}</span>
            <span className="text-sm text-gray-400">{progress}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-cyan-500 to-cyan-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          {currentLayer && (
            <p className="text-xs text-gray-500 mt-2">Current: {currentLayer}</p>
          )}
        </div>

        {/* Stats Grid */}
        <div className="p-6 border-b border-gray-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Discovered</div>
              <div className="text-2xl font-bold text-white">{stats.discovered}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Added</div>
              <div className="text-2xl font-bold text-green-400">{stats.added}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Skipped</div>
              <div className="text-2xl font-bold text-yellow-400">{stats.skipped}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Errors</div>
              <div className="text-2xl font-bold text-red-400">{stats.errors}</div>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">VCs</div>
              <div className="text-xl font-bold text-cyan-400">{stats.vcs}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Accelerators</div>
              <div className="text-xl font-bold text-blue-400">{stats.accelerators}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Studios</div>
              <div className="text-xl font-bold text-purple-400">{stats.studios}</div>
            </div>
          </div>
        </div>

        {/* Logs */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Activity Log</h3>
          <div className="space-y-2">
            {logs.length === 0 && (
              <p className="text-sm text-gray-500">Waiting for updates...</p>
            )}
            {logs.slice(-50).map((log, idx) => (
              <div
                key={idx}
                className={`text-xs font-mono p-2 rounded ${
                  log.level === 'error' ? 'bg-red-500/10 text-red-400' :
                  log.level === 'warn' ? 'bg-yellow-500/10 text-yellow-400' :
                  log.level === 'success' ? 'bg-green-500/10 text-green-400' :
                  'bg-gray-800/50 text-gray-300'
                }`}
              >
                <span className="text-gray-500">[{log.timestamp}]</span>{' '}
                {log.message}
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-6 border-t border-red-500/30 bg-red-500/10">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span className="font-semibold">Error:</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Actions */}
        {isComplete && (
          <div className="p-6 border-t border-gray-700 flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

