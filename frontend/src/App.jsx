import { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, AlertTriangle, CheckCircle, XCircle, Sparkles, Building2, ArrowRight, Download, Network } from 'lucide-react'
import CompanyCard from './components/CompanyCard'
import RadarChart from './components/RadarChart'
import StatsPanel from './components/StatsPanel'
import CompanyDetail from './components/CompanyDetail'
import PortfolioSelector from './components/PortfolioSelector'
import AdvancedSearch from './components/AdvancedSearch'
import InvestorGraph from './components/InvestorGraph'
import { getCompanies, getStats, scanCompany, exportCompanies } from './services/api'
import { Button } from './components/ui/button'
import { Card } from './components/ui/card'

function App() {
  const [companies, setCompanies] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState(null)
  const [scanInput, setScanInput] = useState('')
  const [scanError, setScanError] = useState('')
  const [showPortfolioSelector, setShowPortfolioSelector] = useState(false)
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [showInvestorGraph, setShowInvestorGraph] = useState(false)
  const [searchResults, setSearchResults] = useState(null)
  const [searchQuery, setSearchQuery] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [filters, setFilters] = useState({
    ycBatch: '',
    source: '',
    vector: '',
    search: '',
    excludeMock: false  // Changed to false to show all companies including portfolio companies
  })

  useEffect(() => {
    loadData()
  }, [filters])
  
  // Refresh company list periodically to show new companies as they're added
  useEffect(() => {
    if (!loading) {
      const interval = setInterval(() => {
        loadData()
      }, 10000) // Refresh every 10 seconds to show new companies
      
      return () => clearInterval(interval)
    }
  }, [loading])

  const loadData = async () => {
    setLoading(true)
    try {
      const [companiesData, statsData] = await Promise.all([
        getCompanies(filters),
        getStats()
      ])
      setCompanies(companiesData)
      setStats(statsData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScan = async (url) => {
    const trimmedUrl = url.trim()
    if (!trimmedUrl) {
      setScanError('Please enter a company URL or domain')
      return
    }
    
    setScanning(true)
    setScanError('')
    try {
      const result = await scanCompany(trimmedUrl)
      setScanInput('')
      await loadData()
      setSelectedCompany(result)
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Error scanning company. Please check the URL and try again.'
      setScanError(errorMessage)
    } finally {
      setScanning(false)
    }
  }

  const handleScanSubmit = (e) => {
    e.preventDefault()
    if (scanInput.trim()) {
      handleScan(scanInput)
    } else {
      setScanError('Please enter a company URL or domain')
    }
  }

  const handlePortfolioScrapeComplete = async (results) => {
    await loadData()
  }

  const handleSearchComplete = (results, query) => {
    setSearchResults(results)
    setSearchQuery(query)
    setShowAdvancedSearch(false)
  }

  const handleNewSearch = () => {
    setSearchResults(null)
    setSearchQuery(null)
    setShowAdvancedSearch(true)
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const data = await exportCompanies()
      // Convert to CSV
      if (data && data.length > 0) {
        const headers = Object.keys(data[0])
        const csvRows = [
          headers.join(','),
          ...data.map(row => 
            headers.map(header => {
              const value = row[header]
              if (value === null || value === undefined) return ''
              if (typeof value === 'object') return JSON.stringify(value)
              return String(value).replace(/"/g, '""')
            }).map(v => `"${v}"`).join(','))
        ]
        const csvContent = csvRows.join('\n')
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', `companies_export_${new Date().toISOString().split('T')[0]}.csv`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export companies. Please try again.')
    } finally {
      setExporting(false)
    }
  }

  // If search results are available, show full-page results view
  if (searchResults && searchResults.length > 0) {
    return (
      <AdvancedSearch
        onCompanySelect={setSelectedCompany}
        onSearchComplete={handleSearchComplete}
        initialResults={searchResults}
        initialQuery={searchQuery}
      />
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0A1628' }}>
      {/* Grid Background */}
      <div className="fixed inset-0 grid-pattern opacity-20" />

      {/* Gradient Orb Effects */}
      <div
        className="fixed top-20 left-20 w-96 h-96 rounded-full blur-3xl opacity-15 animate-pulse-glow"
        style={{ background: 'radial-gradient(circle, rgb(6, 182, 212) 0%, transparent 70%)' }}
      />
      <div
        className="fixed bottom-20 right-20 w-96 h-96 rounded-full blur-3xl opacity-15 animate-pulse-glow"
        style={{ background: 'radial-gradient(circle, rgb(6, 182, 212) 0%, transparent 70%)' }}
      />

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-cyan-400/20 backdrop-blur-sm sticky top-0 z-50" style={{ backgroundColor: 'oklch(0.18 0.02 240 / 0.4)' }}>
          <div className="container mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div>
                  <h1 className="text-2xl font-semibold tracking-tight text-white">
                    <span className="text-white">Celer</span>
                    <span className="text-cyan-400">io</span>
                    <span className="text-white"> Intervene</span>
                  </h1>
                  <p className="text-sm text-white/60 mt-1">
                    Agentic Revenue Architecture
                  </p>
                </div>
              </div>
              <nav className="hidden md:flex items-center gap-6">
                <button 
                  onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
                  className="text-sm text-white/80 hover:text-cyan-400 transition-colors"
                >
                  Advanced Search
                </button>
                <button 
                  onClick={() => setShowPortfolioSelector(!showPortfolioSelector)}
                  className="text-sm text-white/80 hover:text-cyan-400 transition-colors"
                >
                  Portfolios
                </button>
                <button 
                  onClick={() => setShowInvestorGraph(!showInvestorGraph)}
                  className="text-sm text-white/80 hover:text-cyan-400 transition-colors flex items-center gap-2"
                >
                  <Network className="w-4 h-4" />
                  Graph View
                </button>
                <button 
                  onClick={handleExport}
                  disabled={exporting}
                  className="text-sm text-white/80 hover:text-cyan-400 transition-colors flex items-center gap-2 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  {exporting ? 'Exporting...' : 'Export'}
                </button>
                <Button
                  size="sm"
                  className="text-sm px-4 py-2 text-[#0A1628] font-semibold"
                  style={{ backgroundColor: 'rgb(6, 182, 212)' }}
                >
                  Start Conversation
                </Button>
              </nav>
            </div>
          </div>
        </header>

        {/* Advanced Search Modal */}
        {showAdvancedSearch && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 overflow-y-auto p-4">
            <div className="max-w-7xl mx-auto py-8">
              <Card className="glass-card border-cyan-400/30 p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-semibold text-white">Advanced Search</h2>
                  <button
                    onClick={() => setShowAdvancedSearch(false)}
                    className="text-white/60 hover:text-white transition-colors"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>
                <AdvancedSearch onCompanySelect={setSelectedCompany} />
              </Card>
            </div>
          </div>
        )}

        {/* Portfolio Selector Modal */}
        {showPortfolioSelector && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="glass-card border-cyan-400/30 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 glass-card border-b border-cyan-400/30 p-6 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">Portfolio Scraper</h2>
                <button
                  onClick={() => setShowPortfolioSelector(false)}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6">
                <PortfolioSelector onScrapeComplete={handlePortfolioScrapeComplete} />
              </div>
            </Card>
          </div>
        )}

        {/* Investor Graph Modal */}
        {showInvestorGraph && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="glass-card border-cyan-400/30 max-w-[95vw] w-full max-h-[95vh] overflow-hidden flex flex-col">
              <div className="sticky top-0 glass-card border-b border-cyan-400/30 p-6 flex items-center justify-between bg-white/5 backdrop-blur-sm">
                <h2 className="text-xl font-semibold text-white">Investor-Company Relationship Graph</h2>
                <button
                  onClick={() => setShowInvestorGraph(false)}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <InvestorGraph />
              </div>
            </Card>
          </div>
        )}

        {/* Hero Scan Section */}
        <section className="border-b border-cyan-400/20">
          <div className="container mx-auto px-6 py-16">
            <div className="max-w-3xl mx-auto text-center space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-sm mb-4">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="text-cyan-400">Enterprise Revenue Architecture</span>
              </div>

              <h2 className="text-5xl font-bold text-white leading-tight text-balance">
                Analyze Startup <span className="text-glow-cyan text-cyan-400">Health</span>
              </h2>
              <p className="text-xl text-white/70 max-w-2xl mx-auto leading-relaxed text-pretty">
                Enter a company domain to analyze their 3M Revenue Architecture vectors
              </p>
              <form onSubmit={handleScanSubmit} className="flex gap-3 max-w-2xl mx-auto mt-8">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/40 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Enter company domain (e.g., langdb.ai)"
                    className="w-full pl-12 pr-4 py-3.5 glass-card border border-cyan-400/30 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400/50 transition-all text-base bg-white/5"
                    value={scanInput}
                    onChange={(e) => {
                      setScanInput(e.target.value)
                      setScanError('')
                    }}
                    disabled={scanning}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={scanning || !scanInput.trim()}
                  size="lg"
                  className="text-lg px-8 py-3.5 text-[#0A1628] font-semibold"
                  style={{ backgroundColor: 'rgb(6, 182, 212)' }}
                >
                  {scanning ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-[#0A1628]/30 border-t-[#0A1628]"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Analyze
                    </>
                  )}
                </Button>
              </form>
              {scanError && (
                <p className="text-red-400 text-sm mt-3">{scanError}</p>
              )}
            </div>
          </div>
        </section>

        <div className="container mx-auto px-6 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar */}
            <aside className="lg:col-span-1">
              <Card className="glass-card border-cyan-400/30 p-5">
                <div className="flex items-center gap-2 mb-5">
                  <Filter className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-base font-semibold text-white">Filters</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-white/60 mb-2 uppercase tracking-wide">
                      YC Batch
                    </label>
                    <select
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
                      value={filters.ycBatch}
                      onChange={(e) => setFilters({ ...filters, ycBatch: e.target.value })}
                    >
                      <option value="">All Batches</option>
                      <option value="W22">W22</option>
                      <option value="S22">S22</option>
                      <option value="W23">W23</option>
                      <option value="S23">S23</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/60 mb-2 uppercase tracking-wide">
                      Source
                    </label>
                    <select
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
                      value={filters.source}
                      onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                    >
                      <option value="">All Sources</option>
                      <option value="yc">Y Combinator</option>
                      <option value="antler">Antler</option>
                      <option value="github">GitHub</option>
                      <option value="mock">Mock Data</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-white/60 mb-2 uppercase tracking-wide">
                      Vector Weakness
                    </label>
                    <select
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
                      value={filters.vector}
                      onChange={(e) => setFilters({ ...filters, vector: e.target.value })}
                    >
                      <option value="">All Vectors</option>
                      <option value="messaging">Messaging Issues</option>
                      <option value="motion">Motion Issues</option>
                      <option value="market">Market Issues</option>
                    </select>
                  </div>
                </div>
              </Card>

              {/* Stats Panel */}
              {stats && <StatsPanel stats={stats} />}
            </aside>

            {/* Main Content */}
            <main className="lg:col-span-3">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-400/20 border-t-cyan-400"></div>
                </div>
              ) : companies.length === 0 ? (
                <div className="text-center py-20">
                  <div className="max-w-md mx-auto">
                    <Sparkles className="w-16 h-16 text-white/30 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">
                      No companies analyzed yet
                    </h3>
                    <p className="text-white/60 mb-6">
                      Enter a company domain above to begin analyzing their 3M Revenue Architecture vectors.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white">
                      Analyzed Companies <span className="text-white/60 font-normal">({companies.length})</span>
                    </h2>
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/40 w-4 h-4" />
                      <input
                        type="text"
                        placeholder="Search companies..."
                        className="w-full pl-10 pr-4 py-2 glass-card border border-cyan-400/30 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
                        value={filters.search}
                        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {companies
                      .filter(company => 
                        !filters.search || 
                        company.name.toLowerCase().includes(filters.search.toLowerCase()) ||
                        company.domain.toLowerCase().includes(filters.search.toLowerCase())
                      )
                      .map((company) => (
                        <CompanyCard
                          key={company.id}
                          company={company}
                          onClick={() => setSelectedCompany(company)}
                        />
                      ))}
                  </div>
                </>
              )}
            </main>
          </div>
        </div>

        {/* Company Detail Drawer */}
        {selectedCompany && (
          <CompanyDetail
            company={selectedCompany}
            onClose={() => setSelectedCompany(null)}
            onScan={handleScan}
          />
        )}
      </div>
    </div>
  )
}

export default App
