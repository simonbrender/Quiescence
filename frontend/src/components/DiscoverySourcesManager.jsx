import { useState, useEffect } from 'react'
import { Settings, Plus, Trash2, Edit, Play, CheckCircle2, XCircle, Loader } from 'lucide-react'
import { getDiscoverySources, addDiscoverySource, updateDiscoverySource, deleteDiscoverySource } from '../services/api'

export default function DiscoverySourcesManager() {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingSource, setEditingSource] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    source_type: 'VC',
    discovery_method: 'scrape',
    priority: 100,
    enabled: true,
    config: {}
  })

  useEffect(() => {
    loadSources()
  }, [])

  const loadSources = async () => {
    setLoading(true)
    try {
      const data = await getDiscoverySources()
      setSources(data.sources || [])
    } catch (err) {
      console.error('Failed to load discovery sources:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddSource = async () => {
    try {
      await addDiscoverySource(formData)
      setShowAddModal(false)
      resetForm()
      loadSources()
    } catch (err) {
      console.error('Failed to add source:', err)
      alert(`Failed to add source: ${err.message}`)
    }
  }

  const handleUpdateSource = async (sourceId, updates) => {
    try {
      await updateDiscoverySource(sourceId, updates)
      loadSources()
    } catch (err) {
      console.error('Failed to update source:', err)
      alert(`Failed to update source: ${err.message}`)
    }
  }

  const handleDeleteSource = async (sourceId) => {
    if (!confirm('Are you sure you want to delete this source?')) return
    
    try {
      await deleteDiscoverySource(sourceId)
      loadSources()
    } catch (err) {
      console.error('Failed to delete source:', err)
      alert(`Failed to delete source: ${err.message}`)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      source_type: 'VC',
      discovery_method: 'scrape',
      priority: 100,
      enabled: true,
      config: {}
    })
    setEditingSource(null)
  }

  const startEdit = (source) => {
    setEditingSource(source.id)
    setFormData({
      name: source.name,
      url: source.url,
      source_type: source.source_type,
      discovery_method: source.discovery_method,
      priority: source.priority,
      enabled: source.enabled,
      config: source.config || {}
    })
    setShowAddModal(true)
  }

  const groupedSources = sources.reduce((acc, source) => {
    const type = source.source_type || 'Other'
    if (!acc[type]) acc[type] = []
    acc[type].push(source)
    return acc
  }, {})

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="w-6 h-6 animate-spin text-cyan-400" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6" />
          Discovery Sources Management
        </h2>
        <button
          onClick={() => {
            resetForm()
            setShowAddModal(true)
          }}
          className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Source
        </button>
      </div>

      {/* Source Groups */}
      {Object.entries(groupedSources).map(([type, typeSources]) => (
        <div key={type} className="bg-gray-800/50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">{type}</h3>
          <div className="space-y-2">
            {typeSources.map((source) => (
              <div
                key={source.id}
                className="bg-gray-700/50 rounded-lg p-4 flex items-center justify-between hover:bg-gray-700/70 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h4 className="text-white font-medium">{source.name}</h4>
                    {source.enabled ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    {source.user_added && (
                      <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">User Added</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400 mt-1">{source.url}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>Method: {source.discovery_method}</span>
                    <span>Priority: {source.priority}</span>
                    {source.last_run && (
                      <span>Last run: {new Date(source.last_run).toLocaleDateString()}</span>
                    )}
                    {source.last_count !== null && (
                      <span>Found: {source.last_count}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleUpdateSource(source.id, { enabled: !source.enabled })}
                    className="p-2 hover:bg-gray-600 rounded transition-colors"
                    title={source.enabled ? 'Disable' : 'Enable'}
                  >
                    {source.enabled ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                  {source.user_added && (
                    <>
                      <button
                        onClick={() => startEdit(source)}
                        className="p-2 hover:bg-gray-600 rounded transition-colors"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4 text-gray-400" />
                      </button>
                      <button
                        onClick={() => handleDeleteSource(source.id)}
                        className="p-2 hover:bg-gray-600 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md space-y-4">
            <h3 className="text-xl font-bold text-white">
              {editingSource ? 'Edit Source' : 'Add Discovery Source'}
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-cyan-500 focus:outline-none"
                  placeholder="e.g., Crunchbase VC Directory"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">URL</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-cyan-500 focus:outline-none"
                  placeholder="https://example.com/vc-directory"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Type</label>
                  <select
                    value={formData.source_type}
                    onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="VC">VC</option>
                    <option value="Accelerator">Accelerator</option>
                    <option value="Studio">Studio</option>
                    <option value="Incubator">Incubator</option>
                    <option value="Custom">Custom</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Method</label>
                  <select
                    value={formData.discovery_method}
                    onChange={(e) => setFormData({ ...formData, discovery_method: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="scrape">Scrape</option>
                    <option value="api">API</option>
                    <option value="search">Search</option>
                    <option value="portfolio">Portfolio</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Priority (lower = higher priority)</label>
                <input
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 100 })}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-cyan-500 focus:outline-none"
                  min="1"
                  max="1000"
                />
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="w-4 h-4 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                />
                <label htmlFor="enabled" className="text-sm text-gray-300">Enabled</label>
              </div>
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={() => {
                  setShowAddModal(false)
                  resetForm()
                }}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={editingSource ? () => handleUpdateSource(editingSource, formData).then(() => {
                  setShowAddModal(false)
                  resetForm()
                }) : handleAddSource}
                className="flex-1 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors"
              >
                {editingSource ? 'Update' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

