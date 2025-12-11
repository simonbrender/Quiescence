import { useState, useEffect, useCallback } from 'react'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  MarkerType,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow'
import 'reactflow/dist/style.css'
import axios from 'axios'
import { Card } from './ui/card'
import { Loader2, RefreshCw } from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

const nodeStyles = {
  investor: {
    background: 'rgba(6, 182, 212, 0.2)',
    border: '2px solid rgb(6, 182, 212)',
    color: '#fff',
    borderRadius: '8px',
    padding: '10px',
    minWidth: '150px',
  },
  company: {
    background: 'rgba(255, 255, 255, 0.1)',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    color: '#fff',
    borderRadius: '8px',
    padding: '10px',
    minWidth: '150px',
  },
}

function InvestorGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchGraphData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Fetch investors
      let investors = []
      try {
        const investorsRes = await axios.get(`${API_BASE_URL}/investors`)
        investors = investorsRes.data || []
      } catch (err) {
        console.warn('Failed to fetch investors:', err)
        // Continue with empty investors
      }

      // Fetch companies with their investors
      let companies = []
      try {
        const companiesRes = await axios.get(`${API_BASE_URL}/companies?limit=1000`)
        companies = companiesRes.data || []
      } catch (err) {
        console.warn('Failed to fetch companies:', err)
        // Continue with empty companies
      }

      // Fetch investment relationships
      let investments = []
      try {
        const investmentsRes = await axios.get(`${API_BASE_URL}/investors/relationships`)
        investments = investmentsRes.data || []
      } catch (err) {
        console.warn('Failed to fetch relationships:', err)
        // Continue with empty relationships - we can still show nodes
      }

      // Create nodes
      const investorNodes = investors.slice(0, 50).map((investor, index) => ({
        id: `investor-${investor.id}`,
        type: 'default',
        position: {
          x: Math.cos((index / 50) * 2 * Math.PI) * 300 + 400,
          y: Math.sin((index / 50) * 2 * Math.PI) * 300 + 400,
        },
        data: {
          label: investor.firm_name || investor.name || `Investor ${investor.id}`,
          type: 'investor',
        },
        style: nodeStyles.investor,
      }))

      const companyNodes = companies.slice(0, 100).map((company, index) => ({
        id: `company-${company.id}`,
        type: 'default',
        position: {
          x: Math.cos((index / 100) * 2 * Math.PI) * 200 + 400,
          y: Math.sin((index / 100) * 2 * Math.PI) * 200 + 400,
        },
        data: {
          label: company.name || company.domain || `Company ${company.id}`,
          type: 'company',
        },
        style: nodeStyles.company,
      }))

      // Create edges from investment relationships
      const relationshipEdges = investments.slice(0, 200).map((investment, index) => ({
        id: `edge-${investment.id || index}`,
        source: `investor-${investment.investor_id}`,
        target: `company-${investment.company_id}`,
        type: 'smoothstep',
        animated: true,
        style: { stroke: 'rgba(6, 182, 212, 0.6)', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'rgba(6, 182, 212, 0.6)',
        },
        label: investment.investment_type || '',
      }))

      // Only set nodes/edges if we have data
      if (investorNodes.length > 0 || companyNodes.length > 0) {
        setNodes([...investorNodes, ...companyNodes])
        setEdges(relationshipEdges)
      } else {
        // Show message if no data
        setError('No investor or company data available. Please scrape some portfolios first.')
      }
    } catch (err) {
      console.error('Error fetching graph data:', err)
      if (err.response?.status === 404) {
        setError('API endpoints not found. Please ensure the backend server is running and has been restarted with the latest code.')
      } else {
        setError(err.message || 'Failed to load graph data')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGraphData()
  }, [fetchGraphData])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-4" />
          <p className="text-white/60">Loading graph data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="glass-card border-red-500/30 p-6 bg-red-500/10">
          <p className="text-red-400">Error: {error}</p>
          <button
            onClick={fetchGraphData}
            className="mt-4 px-4 py-2 bg-cyan-400 text-[#0A1628] rounded-lg hover:bg-cyan-300 transition-colors"
          >
            Retry
          </button>
        </Card>
      </div>
    )
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={fetchGraphData}
          className="px-4 py-2 bg-cyan-400/20 border border-cyan-400/30 text-white rounded-lg hover:bg-cyan-400/30 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        style={{ background: 'transparent' }}
      >
        <Controls className="bg-white/10 border-cyan-400/30" />
        <MiniMap
          className="bg-white/10 border-cyan-400/30"
          nodeColor={(node) => {
            if (node.data?.type === 'investor') return 'rgb(6, 182, 212)'
            return 'rgba(255, 255, 255, 0.5)'
          }}
        />
        <Background color="rgba(6, 182, 212, 0.1)" gap={16} />
      </ReactFlow>
    </div>
  )
}

export default InvestorGraph

