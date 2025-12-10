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



