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
  
  const response = await api.get(`/companies?${params.toString()}`)
  return response.data
}

export const getStats = async () => {
  const response = await api.get('/stats')
  return response.data
}

export const scanCompany = async (url) => {
  const response = await api.post('/scan', { url })
  return response.data
}

