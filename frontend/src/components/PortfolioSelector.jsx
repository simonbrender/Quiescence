import { useState, useEffect } from 'react'
import { Building2, Loader2, CheckCircle2, XCircle, Sparkles, Plus, Search, Filter as FilterIcon } from 'lucide-react'
import { getPortfoliosFiltered, scrapePortfolios, discoverVCs, getStages, getFocusAreas } from '../services/api'
import AddVCForm from './AddVCForm'
import DiscoveryProgress from './DiscoveryProgress'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

function PortfolioSelector({ onScrapeComplete }) {
  const [portfolios, setPortfolios] = useState([])
  const [selectedPortfolios, setSelectedPortfolios] = useState([])
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [scrapeResults, setScrapeResults] = useState(null)
  const [error, setError] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [discovering, setDiscovering] = useState(false)
  const [filters, setFilters] = useState({
    stage: '',
    focus_area: '',
    vc_type: '',
    search: ''
  })
  const [stages, setStages] = useState([])
  const [focusAreas, setFocusAreas] = useState([])

  useEffect(() => {
    loadPortfolios()
    loadFilters()
  }, [filters.stage, filters.focus_area, filters.vc_type])

  const loadFilters = async () => {
    try {
      const [stagesData, focusAreasData] = await Promise.all([
        getStages(),
        getFocusAreas()
      ])
      setStages(stagesData)
      setFocusAreas(focusAreasData)
    } catch (err) {
      console.error('Error loading filters:', err)
    }
  }

  const loadPortfolios = async () => {
    setLoading(true)
    try {
      const data = await getPortfoliosFiltered({
        stage: filters.stage || undefined,
        focus_area: filters.focus_area || undefined,
        vc_type: filters.vc_type || undefined
      })
      
      let filtered = data
      if (filters.search) {
        filtered = data.filter(p => 
          p.firm_name.toLowerCase().includes(filters.search.toLowerCase()) ||
          (p.domain && p.domain.toLowerCase().includes(filters.search.toLowerCase()))
        )
      }
      
      setPortfolios(filtered)
    } catch (err) {
      if (err.response?.status === 404 || err.code === 'ECONNREFUSED' || err.message?.includes('refused')) {
        setError('Backend server is not running. Please start the backend server (python backend/main.py)')
      } else {
        setError(`Failed to load portfolios: ${err.message || 'Unknown error'}`)
      }
      console.error('Portfolio loading error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDiscover = async () => {
    setDiscovering(true)
    setError('')
    setShowDiscoveryProgress(true)
    // DiscoveryProgress component handles the SSE connection and shows progress
  }

  const handleDiscoveryComplete = async (result) => {
    setDiscovering(false)
    setShowDiscoveryProgress(false)
    await loadPortfolios()
    // Results are shown in the progress modal, no alert needed
  }

  const handleDiscoveryClose = () => {
    setShowDiscoveryProgress(false)
    setDiscovering(false)
  }

  const handleAddVC = (newVC) => {
    setShowAddForm(false)
    loadPortfolios()
  }

  const togglePortfolio = (firmName) => {
    setSelectedPortfolios(prev => 
      prev.includes(firmName)
        ? prev.filter(name => name !== firmName)
        : [...prev, firmName]
    )
  }

  const handleScrape = async () => {
    if (selectedPortfolios.length === 0) {
      setError('Please select at least one portfolio')
      return
    }

    setScraping(true)
    setError('')
    setScrapeResults(null)

    try {
      const results = await scrapePortfolios(selectedPortfolios)
      setScrapeResults(results)
      
      if (onScrapeComplete) {
        onScrapeComplete(results)
      }
    } catch (err) {
      setError(err.message || 'Failed to scrape portfolios')
      console.error(err)
    } finally {
      setScraping(false)
    }
  }

  const groupByStage = (portfolios) => {
    const grouped = {}
    portfolios.forEach(portfolio => {
      const stage = portfolio.stage || 'Unknown'
      if (!grouped[stage]) {
        grouped[stage] = []
      }
      grouped[stage].push(portfolio)
    })
    return grouped
  }

  const groupedPortfolios = groupByStage(portfolios)

  return (
    <Card className="glass-card border-cyan-400/30 p-6 bg-white/5">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-400/10 rounded-lg">
            <Building2 className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Portfolio Scraper</h2>
            <p className="text-sm text-white/60">Select VC portfolios to scrape and analyze</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleDiscover}
            disabled={discovering}
            variant="outline"
            size="sm"
            className="glass-card border-cyan-400/30 text-white hover:bg-white/10"
          >
            {discovering ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                Discovering...
              </>
            ) : (
              'Discover VCs'
            )}
          </Button>
          <Button
            onClick={() => setShowAddForm(!showAddForm)}
            size="sm"
            className="text-[#0A1628] font-semibold"
            style={{ backgroundColor: 'rgb(6, 182, 212)' }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add VC
          </Button>
        </div>
      </div>

      {/* Add VC Form */}
      {showAddForm && (
        <Card className="glass-card border-cyan-400/30 mb-6 p-4 bg-white/5">
          <AddVCForm onAdd={handleAddVC} onCancel={() => setShowAddForm(false)} />
        </Card>
      )}

      {/* Filters */}
      <div className="mb-6 space-y-3">
        <div className="flex items-center gap-2">
          <FilterIcon className="w-4 h-4 text-white/60" />
          <span className="text-sm font-medium text-white/60">Filters</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
            <input
              type="text"
              placeholder="Search VCs..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white placeholder-white/40 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
            />
          </div>
          <select
            value={filters.stage}
            onChange={(e) => setFilters({ ...filters, stage: e.target.value })}
            className="px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
          >
            <option value="">All Stages</option>
            {stages.map(stage => (
              <option key={stage} value={stage}>{stage}</option>
            ))}
          </select>
          <select
            value={filters.focus_area}
            onChange={(e) => setFilters({ ...filters, focus_area: e.target.value })}
            className="px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
          >
            <option value="">All Focus Areas</option>
            {focusAreas.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
          <select
            value={filters.vc_type}
            onChange={(e) => setFilters({ ...filters, vc_type: e.target.value })}
            className="px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
          >
            <option value="">All Types</option>
            <option value="VC">VC</option>
            <option value="Accelerator">Accelerator</option>
            <option value="Studio">Studio</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
        </div>
      ) : (
        <>
          {/* Portfolio Selection - Grouped by Stage */}
          <div className="space-y-6 mb-6 max-h-96 overflow-y-auto">
            {Object.entries(groupedPortfolios).map(([stage, stagePortfolios]) => (
              <div key={stage}>
                <h3 className="text-sm font-semibold text-white mb-3 uppercase tracking-wide flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-400 rounded-full"></span>
                  {stage} ({stagePortfolios.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {stagePortfolios.map(portfolio => (
                    <label
                      key={portfolio.firm_name}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all",
                        selectedPortfolios.includes(portfolio.firm_name)
                          ? 'border-cyan-400 bg-cyan-400/10'
                          : 'glass-card border-cyan-400/30 hover:border-cyan-400/50 bg-white/5'
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={selectedPortfolios.includes(portfolio.firm_name)}
                        onChange={() => togglePortfolio(portfolio.firm_name)}
                        className="w-4 h-4 text-cyan-400 border-cyan-400/30 rounded focus:ring-cyan-400/50 bg-white/5"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-white text-sm truncate">
                          {portfolio.firm_name}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-white/60">
                            {portfolio.type}
                          </span>
                          {portfolio.focus_areas && portfolio.focus_areas.length > 0 && (
                            <span className="text-xs text-cyan-400">
                              • {portfolio.focus_areas.slice(0, 2).join(', ')}
                            </span>
                          )}
                          {portfolio.user_added && (
                            <span className="text-xs bg-green-500/10 text-green-400 px-1 rounded border border-green-500/30">
                              Custom
                            </span>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Action Button */}
          <Button
            onClick={handleScrape}
            disabled={scraping || selectedPortfolios.length === 0}
            className="w-full text-lg px-4 py-3 text-[#0A1628] font-semibold disabled:opacity-50"
            style={{ backgroundColor: 'rgb(6, 182, 212)' }}
          >
            {scraping ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Scraping {selectedPortfolios.length} portfolio{selectedPortfolios.length > 1 ? 's' : ''}...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Scrape & Analyze Selected ({selectedPortfolios.length})
              </>
            )}
          </Button>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 glass-card border border-red-500/30 rounded-lg flex items-center gap-2 bg-red-500/10">
              <XCircle className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">{error}</span>
            </div>
          )}

          {/* Results */}
          {scrapeResults && (
            <Card className="glass-card border-green-500/30 mt-6 p-4 bg-green-500/10">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-5 h-5 text-green-400" />
                <h3 className="font-semibold text-white">Scraping Complete</h3>
              </div>
              <div className="space-y-2 text-sm text-white/80">
                <div>
                  <span className="font-medium text-white">Portfolios scraped:</span>{' '}
                  {scrapeResults.portfolios.join(', ')}
                </div>
                <div>
                  <span className="font-medium text-white">Companies found:</span>{' '}
                  {scrapeResults.scraped_count}
                </div>
                <div>
                  <span className="font-medium text-white">Companies analyzed:</span>{' '}
                  {scrapeResults.analyzed_count}
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      {showDiscoveryProgress && (
        <DiscoveryProgress
          onComplete={handleDiscoveryComplete}
          onClose={handleDiscoveryClose}
        />
      )}
    </Card>
  )
}

export default PortfolioSelector
