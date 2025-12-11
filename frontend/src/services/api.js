import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const getCompanies = async (filters = {}) => {
  const params = new URLSearchParams()
  if (filters.ycBatch) params.append('yc_batch', filters.ycBatch)
  if (filters.source) params.append('source', filters.source)
  if (filters.vector) params.append('vector', filters.vector)
  if (filters.excludeMock) params.append('exclude_mock', 'true')
  
  const response = await api.get(`/companies?${params.toString()}`)
  return response.data
}

export const getStats = async () => {
  const response = await api.get('/stats')
  return response.data
}

export const scanCompany = async (url) => {
  try {
    const response = await api.post('/scan', { url })
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    if (error.response) {
      // Server responded with error status
      throw new Error(error.response.data?.detail || error.response.statusText || 'Server error')
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server. Is the backend running?')
    } else {
      // Error setting up request
      throw error
    }
  }
}

export const getPortfolios = async () => {
  const response = await api.get('/portfolios')
  return response.data
}

export const scrapePortfolios = async (portfolioNames) => {
  try {
    const response = await api.post('/portfolios/scrape', { portfolio_names: portfolioNames })
    return response.data
  } catch (error) {
    console.error('Portfolio scraping error:', error)
    if (error.response) {
      throw new Error(error.response.data?.detail || error.response.statusText || 'Scraping error')
    } else if (error.request) {
      throw new Error('No response from server. Is the backend running?')
    } else {
      throw error
    }
  }
}

export const discoverVCs = async () => {
  const response = await api.post('/portfolios/discover')
  return response.data
}

export const addVC = async (vcData) => {
  const response = await api.post('/portfolios/add', vcData)
  return response.data
}

export const getStages = async () => {
  const response = await api.get('/portfolios/stages')
  return response.data
}

export const getFocusAreas = async () => {
  const response = await api.get('/portfolios/focus-areas')
  return response.data
}

export const advancedSearch = async (params) => {
  const response = await api.post('/companies/search', params)
  return response.data
}

export const freeTextSearch = async (query, sessionId = null) => {
  try {
    // Generate session ID if not provided and this is a portfolio query
    const isPortfolioQuery = query.toLowerCase().includes('portfolio') || 
                            query.toLowerCase().includes('retrieve') ||
                            (query.toLowerCase().includes('yc') && query.toLowerCase().includes('antler'))
    
    const finalSessionId = sessionId || (isPortfolioQuery ? `scrape-${Date.now()}` : null)
    
    const payload = { query }
    if (finalSessionId) {
      payload.session_id = finalSessionId
    }
    
    const response = await api.post('/companies/search/free-text', payload)
    
    // Check for session ID in response headers
    const responseSessionId = response.headers['x-session-id'] || finalSessionId
    
    // Return data with session info for portfolio queries
    if (isPortfolioQuery && responseSessionId) {
      return {
        companies: response.data,
        sessionId: responseSessionId,
        isPortfolioQuery: true
      }
    }
    
    return response.data
  } catch (error) {
    console.error('Free text search error:', error)
    if (error.response) {
      throw new Error(error.response.data?.detail || error.response.statusText || 'Search error')
    } else if (error.request) {
      throw new Error('No response from server. Is the backend running?')
    } else {
      throw error
    }
  }
}

export const getPortfoliosFiltered = async (filters = {}) => {
  const params = new URLSearchParams()
  if (filters.stage) params.append('stage', filters.stage)
  if (filters.focus_area) params.append('focus_area', filters.focus_area)
  if (filters.vc_type) params.append('vc_type', filters.vc_type)
  
  const response = await api.get(`/portfolios?${params.toString()}`)
  return response.data
}



