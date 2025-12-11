import { useState, useEffect } from 'react'
import { Search, Filter, TrendingDown, X, SlidersHorizontal, Sparkles, ArrowLeft, Download } from 'lucide-react'
import CompanyCard from './CompanyCard'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

function SearchResults({ 
  results, 
  searchParams, 
  parsedQuery,
  onCompanySelect, 
  onUpdateFilters,
  onNewSearch 
}) {
  const [showFilters, setShowFilters] = useState(false)
  const [localFilters, setLocalFilters] = useState({
    stages: searchParams?.stages || [],
    focus_areas: searchParams?.focus_areas || [],
    funding_min: searchParams?.funding_min || null,
    funding_max: searchParams?.funding_max || null,
    employees_min: searchParams?.employees_min || null,
    employees_max: searchParams?.employees_max || null,
    months_post_raise_min: searchParams?.months_post_raise_min || null,
    months_post_raise_max: searchParams?.months_post_raise_max || null,
    fund_tiers: searchParams?.fund_tiers || [],
    rank_by_stall: searchParams?.rank_by_stall !== false,
  })

  const [filteredResults, setFilteredResults] = useState(results)
  const [sortBy, setSortBy] = useState('stall') // 'stall', 'name', 'score'
  const [searchText, setSearchText] = useState('')

  const toggleStage = (stage) => {
    const stages = localFilters.stages || []
    if (stages.includes(stage)) {
      setLocalFilters({ ...localFilters, stages: stages.filter(s => s !== stage) })
    } else {
      setLocalFilters({ ...localFilters, stages: [...stages, stage] })
    }
  }

  const toggleFocusArea = (area) => {
    const areas = localFilters.focus_areas || []
    if (areas.includes(area)) {
      setLocalFilters({ ...localFilters, focus_areas: areas.filter(a => a !== area) })
    } else {
      setLocalFilters({ ...localFilters, focus_areas: [...areas, area] })
    }
  }

  const toggleFundTier = (tier) => {
    const tiers = localFilters.fund_tiers || []
    if (tiers.includes(tier)) {
      setLocalFilters({ ...localFilters, fund_tiers: tiers.filter(t => t !== tier) })
    } else {
      setLocalFilters({ ...localFilters, fund_tiers: [...tiers, tier] })
    }
  }

  const applyFilters = () => {
    let filtered = [...results]

    // Text search
    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase()
      filtered = filtered.filter(c => 
        c.name.toLowerCase().includes(searchLower) ||
        c.domain.toLowerCase().includes(searchLower) ||
        (c.focus_areas && c.focus_areas.some(fa => fa.toLowerCase().includes(searchLower)))
      )
    }

    // Filter by stages
    if (localFilters.stages && localFilters.stages.length > 0) {
      filtered = filtered.filter(c => 
        localFilters.stages.includes(c.last_raise_stage) || 
        (c.yc_batch && localFilters.stages.includes('Seed'))
      )
    }

    // Filter by focus areas
    if (localFilters.focus_areas && localFilters.focus_areas.length > 0) {
      filtered = filtered.filter(c => {
        const focusAreas = c.focus_areas || []
        return localFilters.focus_areas.some(fa => 
          focusAreas.some(cfa => cfa.toLowerCase().includes(fa.toLowerCase()))
        )
      })
    }

    // Filter by funding
    if (localFilters.funding_min !== null) {
      filtered = filtered.filter(c => 
        !c.funding_amount || c.funding_amount >= localFilters.funding_min
      )
    }
    if (localFilters.funding_max !== null) {
      filtered = filtered.filter(c => 
        !c.funding_amount || c.funding_amount <= localFilters.funding_max
      )
    }

    // Filter by employees
    if (localFilters.employees_min !== null) {
      filtered = filtered.filter(c => 
        !c.employee_count || c.employee_count >= localFilters.employees_min
      )
    }
    if (localFilters.employees_max !== null) {
      filtered = filtered.filter(c => 
        !c.employee_count || c.employee_count <= localFilters.employees_max
      )
    }

    // Filter by fund tiers
    if (localFilters.fund_tiers && localFilters.fund_tiers.length > 0) {
      filtered = filtered.filter(c => 
        localFilters.fund_tiers.includes(c.fund_tier)
      )
    }

    // Sort
    if (sortBy === 'stall') {
      filtered.sort((a, b) => {
        const aScore = (a.messaging_score + a.motion_score + a.market_score) / 3
        const bScore = (b.messaging_score + b.motion_score + b.market_score) / 3
        return aScore - bScore
      })
    } else if (sortBy === 'name') {
      filtered.sort((a, b) => a.name.localeCompare(b.name))
    } else if (sortBy === 'score') {
      filtered.sort((a, b) => {
        const aScore = (a.messaging_score + a.motion_score + a.market_score) / 3
        const bScore = (b.messaging_score + b.motion_score + b.market_score) / 3
        return bScore - aScore
      })
    }

    setFilteredResults(filtered)
  }

  useEffect(() => {
    applyFilters()
  }, [localFilters, sortBy, searchText, results])

  const exportResults = () => {
    const csv = [
      ['Name', 'Domain', 'Messaging Score', 'Motion Score', 'Market Score', 'Stall Risk', 'Funding (M)', 'Employees', 'Stage', 'Focus Areas'].join(','),
      ...filteredResults.map(c => [
        c.name,
        c.domain,
        c.messaging_score.toFixed(1),
        c.motion_score.toFixed(1),
        c.market_score.toFixed(1),
        c.stall_probability,
        c.funding_amount || '',
        c.employee_count || '',
        c.last_raise_stage || '',
        (c.focus_areas || []).join(';')
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `celerio-search-results-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0A1628' }}>
      {/* Grid Background */}
      <div className="fixed inset-0 grid-pattern opacity-20" />

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-cyan-400/20 backdrop-blur-sm sticky top-0 z-50" style={{ backgroundColor: 'oklch(0.18 0.02 240 / 0.4)' }}>
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  onClick={onNewSearch}
                  className="text-white/80 hover:text-white hover:bg-white/10"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  New Search
                </Button>
                <div>
                  <h1 className="text-xl font-semibold text-white">Search Results</h1>
                  {parsedQuery && (
                    <p className="text-sm text-white/60 mt-1 line-clamp-1">{parsedQuery}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  onClick={exportResults}
                  className="glass-card border-cyan-400/30 text-white hover:bg-white/10"
                  size="sm"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
              </div>
            </div>
          </div>
        </header>

        <div className="container mx-auto px-6 py-8">
          {/* Search and Filters Bar */}
          <Card className="glass-card border-cyan-400/30 p-4 mb-6 bg-white/5">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="text"
                  placeholder="Search within results..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 glass-card border border-cyan-400/30 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
                />
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-4 py-2 glass-card border border-cyan-400/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5"
                >
                  <option value="stall">Sort by Stall Risk</option>
                  <option value="score">Sort by Score</option>
                  <option value="name">Sort by Name</option>
                </select>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(
                    "glass-card border-cyan-400/30 text-white hover:bg-white/10",
                    showFilters && "bg-cyan-400/20 border-cyan-400/50"
                  )}
                >
                  <SlidersHorizontal className="w-4 h-4 mr-2" />
                  Filters
                </Button>
              </div>
            </div>
          </Card>

          {/* Results Summary */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">
                {filteredResults.length} {filteredResults.length === 1 ? 'Company' : 'Companies'} Found
              </h2>
              <p className="text-white/60 text-sm">
                {results.length !== filteredResults.length && (
                  <>Showing {filteredResults.length} of {results.length} results</>
                )}
                {results.length === filteredResults.length && results.length > 0 && (
                  <>All results displayed</>
                )}
              </p>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <Card className="glass-card border-cyan-400/30 p-6 mb-6 bg-white/5">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-xl font-semibold text-white">Refine Results</h3>
                </div>
                <button
                  onClick={() => setShowFilters(false)}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
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
                          localFilters.stages?.includes(stage)
                            ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                            : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50 bg-white/5'
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
                          localFilters.focus_areas?.includes(area)
                            ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                            : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50 bg-white/5'
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
                      value={localFilters.funding_min || ''}
                      onChange={(e) => setLocalFilters({ ...localFilters, funding_min: parseFloat(e.target.value) || null })}
                      placeholder="Min"
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
                    />
                    <input
                      type="number"
                      value={localFilters.funding_max || ''}
                      onChange={(e) => setLocalFilters({ ...localFilters, funding_max: parseFloat(e.target.value) || null })}
                      placeholder="Max"
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
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
                      value={localFilters.employees_min || ''}
                      onChange={(e) => setLocalFilters({ ...localFilters, employees_min: parseInt(e.target.value) || null })}
                      placeholder="Min"
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
                    />
                    <input
                      type="number"
                      value={localFilters.employees_max || ''}
                      onChange={(e) => setLocalFilters({ ...localFilters, employees_max: parseInt(e.target.value) || null })}
                      placeholder="Max"
                      className="w-full px-3 py-2 glass-card border border-cyan-400/30 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-white/5 text-sm"
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
                          localFilters.fund_tiers?.includes(tier)
                            ? 'bg-cyan-400 text-[#0A1628] font-semibold'
                            : 'glass-card border border-cyan-400/30 text-white/80 hover:border-cyan-400/50 bg-white/5'
                        )}
                      >
                        {tier}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setLocalFilters({
                      stages: [],
                      focus_areas: [],
                      funding_min: null,
                      funding_max: null,
                      employees_min: null,
                      employees_max: null,
                      months_post_raise_min: null,
                      months_post_raise_max: null,
                      fund_tiers: [],
                      rank_by_stall: true,
                    })
                    setSearchText('')
                  }}
                  className="glass-card border-cyan-400/30 text-white hover:bg-white/10"
                >
                  Clear All
                </Button>
                <Button
                  onClick={() => {
                    if (onUpdateFilters) {
                      onUpdateFilters(localFilters)
                    }
                  }}
                  className="text-[#0A1628] font-semibold"
                  style={{ backgroundColor: 'rgb(6, 182, 212)' }}
                >
                  Apply Filters
                </Button>
              </div>
            </Card>
          )}

          {/* Results Grid */}
          {filteredResults.length === 0 ? (
            <Card className="glass-card border-cyan-400/30 p-12 text-center bg-white/5">
              <Sparkles className="w-16 h-16 text-white/30 mx-auto mb-4" />
              <p className="text-white/60 text-lg mb-2">No companies match your filters.</p>
              <p className="text-white/40 text-sm">Try adjusting your search criteria or clearing filters.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredResults.map(company => (
                <CompanyCard
                  key={company.id}
                  company={company}
                  onClick={() => onCompanySelect(company)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SearchResults
