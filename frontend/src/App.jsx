import { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import CompanyCard from './components/CompanyCard'
import RadarChart from './components/RadarChart'
import StatsPanel from './components/StatsPanel'
import CompanyDetail from './components/CompanyDetail'
import { getCompanies, getStats, scanCompany } from './services/api'

function App() {
  const [companies, setCompanies] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedCompany, setSelectedCompany] = useState(null)
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
    try {
      const result = await scanCompany(url)
      await loadData()
      setSelectedCompany(result)
    } catch (error) {
      console.error('Error scanning company:', error)
      alert('Error scanning company. Please check the URL and try again.')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/30 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground tracking-tight">
                Celerio Scout
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                OSINT-Powered Startup Stall Detection
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search companies..."
                  className="pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <div className="celerio-card p-5">
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
            ) : (
              <>
                <div className="mb-6 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-foreground">
                    Companies <span className="text-muted-foreground font-normal">({companies.length})</span>
                  </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

                {companies.length === 0 && (
                  <div className="text-center py-16 text-muted-foreground">
                    <p className="text-sm">No companies found matching your filters.</p>
                  </div>
                )}
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

