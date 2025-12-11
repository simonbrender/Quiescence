import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { addVC } from '../services/api'

function AddVCForm({ onAdd, onCancel }) {
  const [formData, setFormData] = useState({
    firm_name: '',
    url: '',
    portfolio_url: '',
    type: 'VC',
    stage: '',
    focus_areas: []
  })
  const [focusInput, setFocusInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const focusOptions = [
    'AI/ML', 'B2B SaaS', 'Fintech', 'Healthcare', 'Consumer', 
    'Enterprise', 'DevTools', 'Security', 'Climate', 'General'
  ]

  const handleAddFocus = () => {
    if (focusInput.trim() && !formData.focus_areas.includes(focusInput.trim())) {
      setFormData({
        ...formData,
        focus_areas: [...formData.focus_areas, focusInput.trim()]
      })
      setFocusInput('')
    }
  }

  const handleRemoveFocus = (focus) => {
    setFormData({
      ...formData,
      focus_areas: formData.focus_areas.filter(f => f !== focus)
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await addVC(formData)
      if (onAdd) {
        onAdd(result)
      }
    } catch (err) {
      setError(err.message || 'Failed to add VC')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Firm Name *
        </label>
        <input
          type="text"
          required
          value={formData.firm_name}
          onChange={(e) => setFormData({ ...formData, firm_name: e.target.value })}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          placeholder="e.g., Example Ventures"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Website URL *
        </label>
        <input
          type="url"
          required
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          placeholder="https://example.com"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Portfolio URL (optional)
        </label>
        <input
          type="url"
          value={formData.portfolio_url}
          onChange={(e) => setFormData({ ...formData, portfolio_url: e.target.value })}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          placeholder="https://example.com/portfolio"
        />
        <p className="text-xs text-muted-foreground mt-1">
          If different from website URL
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Type
          </label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="VC">VC</option>
            <option value="Accelerator">Accelerator</option>
            <option value="Studio">Studio</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Stage
          </label>
          <select
            value={formData.stage}
            onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            <option value="">Select stage</option>
            <option value="Pre-Seed">Pre-Seed</option>
            <option value="Seed">Seed</option>
            <option value="Series A">Series A</option>
            <option value="Series B">Series B</option>
            <option value="Growth">Growth</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Focus Areas
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={focusInput}
            onChange={(e) => setFocusInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddFocus())}
            className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="Add focus area"
          />
          <button
            type="button"
            onClick={handleAddFocus}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.focus_areas.map((focus) => (
            <span
              key={focus}
              className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded text-sm"
            >
              {focus}
              <button
                type="button"
                onClick={() => handleRemoveFocus(focus)}
                className="hover:text-primary/70"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {focusOptions.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => {
                if (!formData.focus_areas.includes(option)) {
                  setFormData({
                    ...formData,
                    focus_areas: [...formData.focus_areas, option]
                  })
                }
              }}
              className="px-2 py-1 text-xs bg-card border border-border rounded hover:border-primary/50 transition-colors"
            >
              + {option}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-500">
          {error}
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'Adding...' : 'Add VC'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-card border border-border rounded-lg hover:border-primary/50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default AddVCForm


