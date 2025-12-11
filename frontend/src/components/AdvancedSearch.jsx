import { useState, useEffect, useRef } from 'react'
import { Search, Filter, TrendingDown, Sparkles } from 'lucide-react'
import { advancedSearch, freeTextSearch } from '../services/api'
import SearchResults from './SearchResults'
import PortfolioScrapingMonitor from './PortfolioScrapingMonitor'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

function AdvancedSearch({ onCompanySelect, onSearchComplete, initialResults = null, initialQuery = null }) {
  const [searchParams, setSearchParams] = useState({
    stages: [],
    focus_areas: [],
    funding_min: null,
    funding_max: null,
    employees_min: null,
    employees_max: null,
    months_post_raise_min: null,
    months_post_raise_max: null,
    fund_tiers: [],
    rank_by_stall: true
  })
  
  const [freeTextQuery, setFreeTextQuery] = useState(initialQuery || '')
  const [results, setResults] = useState(initialResults || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showResults, setShowResults] = useState(initialResults !== null && initialResults.length > 0)
  const [parsedQuery, setParsedQuery] = useState(initialQuery)
  const [scrapingSessionId, setScrapingSessionId] = useState(null)
  const [showMonitor, setShowMonitor] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const pollingIntervalRef = useRef(null)
  const lastCompanyCountRef = useRef(0)
  const currentQueryRef = useRef(null)
  const currentSessionIdRef = useRef(null)

  // WebSocket connection for real-time company updates
  const wsRef = useRef(null)
  
  // Function to connect to WebSocket for real-time updates
  const connectWebSocket = (sessionId) => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    const ws = new WebSocket(`ws://localhost:8000/api/ws/portfolio-scraping/${sessionId}`)
    wsRef.current = ws
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('[AdvancedSearch] WebSocket event:', data.type)
      
      // Handle companies_added event - add new companies to results
      if (data.type === 'companies_added' && data.companies) {
        const newCompanies = Array.isArray(data.companies) ? data.companies : []
        console.log(`[AdvancedSearch] Received ${newCompanies.length} new companies via WebSocket`)
        
        // Add new companies to existing results
        setResults(prev => {
          const existingDomains = new Set(prev.map(c => c.domain?.toLowerCase()))
          const uniqueNew = newCompanies.filter(c => {
            const domain = c.domain?.toLowerCase()
            return domain && !existingDomains.has(domain)
          })
          
          if (uniqueNew.length > 0) {
            console.log(`[AdvancedSearch] Adding ${uniqueNew.length} unique companies to results`)
            const updated = [...prev, ...uniqueNew]
            setShowResults(true)
            
            // Update search complete callback
            if (onSearchComplete) {
              onSearchComplete(updated, currentQueryRef.current)
            }
            
            return updated
          }
          return prev
        })
      }
      
      // Handle scraping complete
      if (data.type === 'scraping_complete') {
        console.log('[AdvancedSearch] Scraping completed')
        stopPolling()
      }
    }
    
    ws.onerror = (error) => {
      console.error('[AdvancedSearch] WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('[AdvancedSearch] WebSocket closed')
    }
  }
  
  // Function to poll for new companies (fallback if WebSocket fails)
  const startPollingForCompanies = async (query, sessionId) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }
    
    currentQueryRef.current = query
    currentSessionIdRef.current = sessionId
    lastCompanyCountRef.current = results.length
    setIsPolling(true)
    
    // Connect to WebSocket for real-time updates
    if (sessionId) {
      connectWebSocket(sessionId)
    }
    
    console.log('[AdvancedSearch] Starting polling for companies...', { query, sessionId, currentCount: lastCompanyCountRef.current })
    
    // Poll every 5 seconds for new companies (fallback)
    pollingIntervalRef.current = setInterval(async () => {
      try {
        console.log('[AdvancedSearch] Polling for new companies...', { query, sessionId })
        const searchResult = await freeTextSearch(query, sessionId)
        const newCompanies = searchResult.companies || searchResult || []
        
        console.log('[AdvancedSearch] Poll result:', { 
          newCount: newCompanies.length, 
          previousCount: lastCompanyCountRef.current,
          hasMore: newCompanies.length > lastCompanyCountRef.current 
        })
        
        // Always update if we have companies (even if count is same, companies might be new)
        if (newCompanies.length > 0) {
          if (newCompanies.length !== lastCompanyCountRef.current) {
            console.log(`[AdvancedSearch] Company count changed: ${lastCompanyCountRef.current} → ${newCompanies.length}`)
          }
          setResults(newCompanies)
          lastCompanyCountRef.current = newCompanies.length
          setShowResults(true) // Ensure results are shown
          
          // Update search complete callback
          if (onSearchComplete) {
            onSearchComplete(newCompanies, query)
          }
        }
      } catch (error) {
        console.error('[AdvancedSearch] Error polling for companies:', error)
      }
    }, 5000) // Poll every 5 seconds
  }

  // Stop polling and close WebSocket when component unmounts
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  // Stop polling when monitor closes or scraping completes
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsPolling(false)
  }

  const handleSearch = async () => {
    setLoading(true)
    setError('')
    setShowResults(false)
    setShowMonitor(false) // Reset monitor visibility
    setScrapingSessionId(null) // Reset session ID
    setParsedQuery(null) // Clear "Searching for" text when starting new search
    stopPolling() // Ensure polling is stopped before new search
    
    console.log('[AdvancedSearch] Starting search...')
    console.log('[AdvancedSearch] freeTextQuery:', freeTextQuery)
    console.log('[AdvancedSearch] freeTextQuery.trim():', freeTextQuery.trim())
    console.log('[AdvancedSearch] searchParams:', searchParams)
    
    try {
      let companies
      
      // If free text query is provided, use it; otherwise use structured params
      if (freeTextQuery.trim()) {
        console.log('[AdvancedSearch] Using FREE-TEXT search endpoint')
        
        // Check if this is a portfolio query
        const isPortfolioQuery = freeTextQuery.toLowerCase().includes('portfolio') || 
                                freeTextQuery.toLowerCase().includes('retrieve') ||
                                (freeTextQuery.toLowerCase().includes('yc') && freeTextQuery.toLowerCase().includes('antler'))
        
        // Generate session ID for portfolio queries
        const currentSessionId = isPortfolioQuery ? `scrape-${Date.now()}` : null
        
        // Use free text search endpoint
        const searchResult = await freeTextSearch(freeTextQuery.trim(), currentSessionId)
        
        // Show monitor for portfolio queries
        if (isPortfolioQuery && (searchResult.sessionId || currentSessionId)) {
          const sessionIdToUse = searchResult.sessionId || currentSessionId
          setScrapingSessionId(sessionIdToUse)
          setShowMonitor(true)
          console.log('[AdvancedSearch] Portfolio query detected - showing monitor with session:', sessionIdToUse)
          companies = searchResult.companies || searchResult || []
          
          // For portfolio queries, don't set showResults=true if no companies yet
          // This will show the "Scraping in Progress" message instead
          if (companies.length > 0) {
            setResults(companies)
            setShowResults(true)
          } else {
            // Keep showResults=false to show "Scraping in Progress" message
            setResults([])
            setShowResults(false)
          }
          
          // Start polling for new companies
          console.log('[AdvancedSearch] Starting to poll for new companies...')
          startPollingForCompanies(freeTextQuery.trim(), sessionIdToUse)
        } else {
          companies = searchResult.companies || searchResult || []
          setResults(companies)
          setShowResults(true)
        }
        
        console.log('[AdvancedSearch] Free-text search returned', companies?.length, 'companies')
        // Store the parsed query for display
        setParsedQuery(freeTextQuery.trim())
      } else {
        console.log('[AdvancedSearch] Using STRUCTURED search endpoint')
        // Use structured search
        companies = await advancedSearch(searchParams)
        console.log('[AdvancedSearch] Structured search returned', companies?.length, 'companies')
        setResults(companies)
        setShowResults(true)
        setParsedQuery(null)
      }
      
      if (onSearchComplete) {
        onSearchComplete(companies, freeTextQuery.trim() || null)
      }
    } catch (err) {
      setError('Failed to search companies. Please ensure portfolios are scraped first and Ollama is running (for free text search).')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const updateParam = (key, value) => {
    setSearchParams(prev => ({ ...prev, [key]: value }))
  }

  const toggleStage = (stage) => {
    const stages = searchParams.stages || []
    if (stages.includes(stage)) {
      updateParam('stages', stages.filter(s => s !== stage))
    } else {
      updateParam('stages', [...stages, stage])
    }
  }

  const toggleFocusArea = (area) => {
    const areas = searchParams.focus_areas || []
    if (areas.includes(area)) {
      updateParam('focus_areas', areas.filter(a => a !== area))
    } else {
      updateParam('focus_areas', [...areas, area])
    }
  }

  const toggleFundTier = (tier) => {
    const tiers = searchParams.fund_tiers || []
    if (tiers.includes(tier)) {
      updateParam('fund_tiers', tiers.filter(t => t !== tier))
    } else {
      updateParam('fund_tiers', [...tiers, tier])
    }
  }

  const handleNewSearch = () => {
    setShowResults(false)
    setResults([])
    setFreeTextQuery('')
    setParsedQuery(null)
    if (onSearchComplete) {
      onSearchComplete(null, null)
    }
  }

  const handleUpdateFilters = (newFilters) => {
    setSearchParams(newFilters)
    // Re-apply search with new filters
    handleSearch()
  }

  // Show full-page results if we have results
  if (showResults && results.length > 0) {
    return (
      <SearchResults
        results={results}
        searchParams={searchParams}
        parsedQuery={parsedQuery}
        onCompanySelect={onCompanySelect}
        onUpdateFilters={handleUpdateFilters}
        onNewSearch={handleNewSearch}
      />
    )
  }

  // If we have initial results but they're empty, show empty state
  if (showResults && results.length === 0) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: '#0A1628' }}>
        <div className="fixed inset-0 grid-pattern opacity-20" />
        <div className="relative z-10 container mx-auto px-6 py-12">
          <Card className="glass-card border-cyan-400/30 p-12 text-center bg-white/5">
            <Sparkles className="w-16 h-16 text-white/30 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-white mb-2">
              {showMonitor ? 'Scraping in Progress' : 'No Results Found'}
            </h2>
            <p className="text-white/60 mb-6">
              {showMonitor 
                ? 'Portfolio scraping has started. Companies will appear as they are discovered. Check the monitor window for real-time progress.'
                : 'Try adjusting your search criteria or scraping more portfolios.'}
            </p>
            {showMonitor && (
              <div className="mb-6 p-4 bg-cyan-400/10 rounded-lg border border-cyan-400/30 max-w-md mx-auto">
                <p className="text-sm text-cyan-400">
                  💡 Tip: The monitor window shows live progress. Companies are being added to the database as scraping progresses.
                </p>
              </div>
            )}
            <Button
              onClick={handleNewSearch}
              className="text-[#0A1628] font-semibold"
              style={{ backgroundColor: 'rgb(6, 182, 212)' }}
            >
              New Search
            </Button>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      <Card className="glass-card border-cyan-400/30 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Search className="w-6 h-6 text-cyan-400" />
          <h2 className="text-2xl font-bold text-white">
            Advanced Company Search
          </h2>
        </div>

        {/* Free Text Search */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-white/80">
              Natural Language Search (Powered by Ollama)
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setFreeTextQuery('retrieve the YC and Antler portfolios')}
              className="text-xs h-7 px-2 border-cyan-400/30 text-cyan-400 hover:bg-cyan-400/10"
            >
              Test Portfolio Query
            </Button>
          </div>
          <textarea
            value={freeTextQuery}
            onChange={(e) => setFreeTextQuery(e.target.value)}
            placeholder="Example: Seed/Series A AI/B2B companies 12–18 months post-raise, typically with $3–15m in total funding from a Tier1/2 fund and 10–80 employees..."
            className="w-full px-4 py-3 glass-card border border-cyan-400/30 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-cyan-400/50 text-white placeholder-white/40 bg-white/5"
            rows={3}
          />
          <p className="mt-2 text-xs text-white/60">
            Enter a natural language query describing the companies you're looking for. The system will automatically extract criteria like stage, funding, employees, etc. Requires Ollama running locally.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Stages */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Investment Stage
            </label>
            <div className="flex flex-wrap gap-2">
              {['Pre-Seed', 'Seed', 'Series A', 'Series B', 'Growth'].map(stage => (
                <button
                  key={stage}
                  onClick={() => toggleStage(stage)}
                  className={cn(
                    "px-3 py-1 rounded-full text-sm transition-all",
                    searchParams.stages?.includes(stage)
                      ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                      : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50'
                  )}
                >
                  {stage}
                </button>
              ))}
            </div>
          </div>

          {/* Focus Areas */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Focus Areas
            </label>
            <div className="flex flex-wrap gap-2">
              {['AI/ML', 'B2B SaaS', 'Fintech', 'Enterprise', 'DevTools'].map(area => (
                <button
                  key={area}
                  onClick={() => toggleFocusArea(area)}
                  className={cn(
                    "px-3 py-1 rounded-full text-sm transition-all",
                    searchParams.focus_areas?.includes(area)
                      ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                      : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50'
                  )}
                >
                  {area}
                </button>
              ))}
            </div>
          </div>

          {/* Funding Range */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Funding Amount (M USD)
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={searchParams.funding_min || ''}
                onChange={(e) => updateParam('funding_min', parseFloat(e.target.value) || null)}
                placeholder="Min"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
              <input
                type="number"
                value={searchParams.funding_max || ''}
                onChange={(e) => updateParam('funding_max', parseFloat(e.target.value) || null)}
                placeholder="Max"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
            </div>
          </div>

          {/* Employee Count */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Employee Count
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={searchParams.employees_min || ''}
                onChange={(e) => updateParam('employees_min', parseInt(e.target.value) || null)}
                placeholder="Min"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
              <input
                type="number"
                value={searchParams.employees_max || ''}
                onChange={(e) => updateParam('employees_max', parseInt(e.target.value) || null)}
                placeholder="Max"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
            </div>
          </div>

          {/* Months Post-Raise */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Months Post-Raise
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={searchParams.months_post_raise_min || ''}
                onChange={(e) => updateParam('months_post_raise_min', parseInt(e.target.value) || null)}
                placeholder="Min"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
              <input
                type="number"
                value={searchParams.months_post_raise_max || ''}
                onChange={(e) => updateParam('months_post_raise_max', parseInt(e.target.value) || null)}
                placeholder="Max"
                className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
              />
            </div>
          </div>

          {/* Fund Tier */}
          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Fund Tier
            </label>
            <div className="flex flex-wrap gap-2">
              {['Tier 1', 'Tier 2'].map(tier => (
                <button
                  key={tier}
                  onClick={() => toggleFundTier(tier)}
                  className={cn(
                    "px-3 py-1 rounded-full text-sm transition-all",
                    searchParams.fund_tiers?.includes(tier)
                      ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                      : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50'
                  )}
                >
                  {tier}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Rank by Stall */}
        <div className="mt-6 flex items-center gap-3">
          <input
            type="checkbox"
            id="rankByStall"
            checked={searchParams.rank_by_stall}
            onChange={(e) => updateParam('rank_by_stall', e.target.checked)}
            className="w-4 h-4 text-cyan-400 bg-white/5 border-cyan-400/30 rounded focus:ring-cyan-400/50"
          />
          <label htmlFor="rankByStall" className="text-sm font-medium text-white/80 flex items-center gap-2">
            <TrendingDown className="w-4 h-4" />
            Rank by growth stall indicators (highest risk first)
          </label>
        </div>

        {/* Search Button */}
        <Button
          onClick={handleSearch}
          disabled={loading}
          className="mt-6 w-full text-lg px-6 py-3 text-[#0A1628] font-semibold"
          style={{ backgroundColor: 'rgb(6, 182, 212)' }}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#0A1628]"></div>
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Search Companies
            </>
          )}
        </Button>

        {error && (
          <div className="mt-4 p-4 glass-card border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {parsedQuery && (
          <div className="mt-4 p-4 glass-card border border-cyan-400/30 rounded-lg">
            <p className="text-sm text-white/60 mb-1">Searching for:</p>
            <p className="text-white font-medium">{parsedQuery}</p>
          </div>
        )}
      </Card>
      
      {/* Portfolio Scraping Monitor */}
      {showMonitor && scrapingSessionId && (
        <PortfolioScrapingMonitor 
          sessionId={scrapingSessionId}
          onClose={() => {
            setShowMonitor(false)
            setScrapingSessionId(null)
            setParsedQuery(null) // Clear "Searching for" text
            stopPolling()
          }}
          onComplete={() => {
            // When scraping completes, stop polling and do a final refresh
            console.log('[AdvancedSearch] Scraping completed - doing final refresh')
            stopPolling()
            // Do one final search to get all companies
            if (currentQueryRef.current) {
              handleSearch()
            }
          }}
        />
      )}
    </div>
  )
}

export default AdvancedSearch
