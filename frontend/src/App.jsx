import { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, AlertTriangle, CheckCircle, XCircle, Sparkles } from 'lucide-react'
import CompanyCard from './components/CompanyCard'
import RadarChart from './components/RadarChart'
import StatsPanel from './components/StatsPanel'
import CompanyDetail from './components/CompanyDetail'
import { getCompanies, getStats, scanCompany } from './services/api'

function App() {
  const [companies, setCompanies] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState(null)
  const [scanInput, setScanInput] = useState('')
  const [scanError, setScanError] = useState('')
  const [filters, setFilters] = useState({
    ycBatch: '',
    source: '',
    vector: '',
    search: ''
  })

  useEffect(() => {
    loadData()
  }, [filters])

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
    if (!url.trim()) {
      setScanError('Please enter a company URL or domain')
      return
    }
    
    setScanning(true)
    setScanError('')
    try {
      const result = await scanCompany(url)
      await loadData()
      setSelectedCompany(result)
      setScanInput('')
    } catch (error) {
      console.error('Error scanning company:', error)
      setScanError('Error scanning company. Please check the URL and try again.')
    } finally {
      setScanning(false)
    }
  }

  const handleScanSubmit = (e) => {
    e.preventDefault()
    handleScan(scanInput)
  }

  return (
    <div className="min-h-screen bg-background celerio-content">
      {/* Header */}
      <header className="border-b border-border/30 bg-background/80 backdrop-blur-sm sticky top-0 z-50 celerio-content">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              {/* Celerio Scout Logo */}
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                  <span className="text-foreground">Celer</span>
                  <span className="text-primary">io</span>
                  <span className="text-foreground"> Scout</span>
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  OSINT-Powered Startup Stall Detection
                </p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#" className="text-sm text-foreground hover:text-primary transition-colors">Expertise</a>
              <a href="#" className="text-sm text-foreground hover:text-primary transition-colors">Insights</a>
              <a href="#" className="text-sm text-foreground hover:text-primary transition-colors">Impact</a>
              <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:bg-foreground/90 transition-colors">
                Start Conversation
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Scan Section */}
      <section className="border-b border-border/30 bg-background celerio-content">
        <div className="container mx-auto px-6 py-16">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 mb-6 rounded-lg bg-primary/10 border border-primary/20">
              <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-4xl font-semibold text-foreground mb-4">
              Analyze Startup Health
            </h2>
            <p className="text-muted-foreground mb-10 text-lg">
              Enter a company domain to analyze their 3M Revenue Architecture vectors
            </p>
            <form onSubmit={handleScanSubmit} className="flex gap-3 max-w-2xl mx-auto">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5 top-1/2 left-4" />
                <input
                  type="text"
                  placeholder="Enter company domain (e.g., langdb.ai)"
                  className="w-full pl-12 pr-4 py-3.5 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all text-base"
                  value={scanInput}
                  onChange={(e) => {
                    setScanInput(e.target.value)
                    setScanError('')
                  }}
                  disabled={scanning}
                />
              </div>
              <button
                type="submit"
                disabled={scanning || !scanInput.trim()}
                className="px-8 py-3.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-primary/20"
              >
                {scanning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Analyze
                  </>
                )}
              </button>
            </form>
            {scanError && (
              <p className="text-red-500 text-sm mt-3">{scanError}</p>
            )}
          </div>
        </div>
      </section>

      <div className="container mx-auto px-6 py-12 celerio-content">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <div className="celerio-card p-5 celerio-content">
              <div className="flex items-center gap-2 mb-5">
                <Filter className="w-4 h-4 text-primary" />
                <h2 className="text-base font-semibold text-foreground">Filters</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                    YC Batch
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
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
                  <label className="block text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                    Source
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
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
                  <label className="block text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                    Vector Weakness
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
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
            </div>

            {/* Stats Panel */}
            {stats && <StatsPanel stats={stats} />}
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary/20 border-t-primary"></div>
              </div>
            ) : companies.length === 0 ? (
              <div className="text-center py-20">
                <div className="max-w-md mx-auto">
                  <Sparkles className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    No companies analyzed yet
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    Enter a company domain above to begin analyzing their 3M Revenue Architecture vectors.
                  </p>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p>Try analyzing:</p>
                    <div className="flex gap-2 justify-center flex-wrap">
                      <button
                        onClick={() => {
                          setScanInput('langdb.ai')
                          handleScan('langdb.ai')
                        }}
                        className="px-3 py-1.5 bg-card border border-border rounded text-primary hover:border-primary/50 transition-colors"
                      >
                        langdb.ai
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-6 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-foreground">
                    Analyzed Companies <span className="text-muted-foreground font-normal">({companies.length})</span>
                  </h2>
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search companies..."
                      className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all text-sm"
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
  )
}

export default App

