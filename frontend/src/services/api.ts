/**
 * @fileoverview Centralized API service for all backend communications
 * Provides a single source of truth for API endpoints and request handling
 */

const API_BASE_URL = '/api'

// ==================== TYPE DEFINITIONS ====================

export interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface Sample {
  id: string
  question: string
  answer: string
  topic: string
  difficulty: 'foundational' | 'basic' | 'intermediate' | 'advanced' | 'expert'
  case_citation: string
  reasoning: string
  jurisdiction?: string
  batch_id?: string
  sample_type?: 'case_analysis' | 'educational' | 'client_interaction' | 'statutory_interpretation'
  provider?: string
  model?: string
  created_at?: string
  updated_at?: string
}

export interface Stats {
  total: number
  difficulty_distribution?: Array<{ difficulty: string; count: number; len?: number }>
  top_topics?: Array<{ topic: string; count: number; len?: number }>
  file_size_kb?: number
  unique_practice_areas?: number
  unique_topics?: number
}

export interface DetailedStats {
  unique_practice_areas: number
  unique_topics: number
  avg_lengths: {
    question: number
    answer: number
    reasoning: number
    case_citation: number
  }
  practice_areas: Array<{ practice_area: string; count: number; len?: number }>
  difficulty_breakdown: Array<{
    difficulty: string
    count: number
    avg_question_length: number
    avg_answer_length: number
  }>
}

export interface TokenStats {
  total_tokens: number
  avg_tokens_per_sample: number
  encoding: string
  tokens_by_field: Record<string, { total: number; avg: number }>
  tokens_by_difficulty: Record<string, { total_tokens: number; avg_tokens: number; count: number }>
  tokens_by_practice_area: Array<{ practice_area: string; total_tokens: number; avg_tokens: number }>
  estimated_costs: Record<string, { name: string; cost_usd: number }>
}

export interface BatchHistory {
  id: string
  started_at: string
  completed_at?: string | null
  model: string
  provider: string
  topic_filter?: string | null
  difficulty_filter?: string | null
  target: number
  samples_generated: number
  tokens_used: number
  status: 'running' | 'completed' | 'stopped'
  errors: Array<string | { error: string }>
}

export interface Model {
  id: string
  provider: string
  context_window?: number
}

export interface Provider {
  id: string
  name: string
  requests_per_minute: number
}

export interface Topic {
  practice_area: string
  topic: string
}

export interface SampleType {
  id: string
  name: string
  description: string
}

export interface GenerationConfig {
  target_count: number
  provider: string
  model: string
  sample_type?: string
  topic?: string
  difficulty?: string
  reasoning_instruction?: string
}

export interface HuggingFaceConfig {
  repo_name: string
  format?: 'parquet' | 'json' | 'csv'
  private?: boolean
  token?: string
}

// ==================== API REQUEST WRAPPER ====================

/**
 * Generic API request wrapper with error handling
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }))
      throw new Error(error.error || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error)
    throw error
  }
}

// ==================== API SERVICE ====================

/**
 * API Service Object - All backend API methods
 */
export const api = {
  // ==================== STATS ENDPOINTS ====================

  stats: {
    get: (): Promise<Stats> => apiRequest<Stats>('/stats'),
    getDetailed: (): Promise<APIResponse<DetailedStats>> =>
      apiRequest<APIResponse<DetailedStats>>('/stats/detailed'),
    getTokens: (): Promise<APIResponse<TokenStats>> =>
      apiRequest<APIResponse<TokenStats>>('/stats/tokens'),
  },

  // ==================== DATA ENDPOINTS ====================

  data: {
    getAll: (limit?: number, offset?: number): Promise<Sample[]> => {
      const params = new URLSearchParams()
      if (limit) params.append('limit', String(limit))
      if (offset) params.append('offset', String(offset))
      return apiRequest<Sample[]>(`/data?${params}`)
    },

    getSample: (id: string): Promise<APIResponse<Sample>> =>
      apiRequest<APIResponse<Sample>>(`/sample/${id}`),

    updateSample: (id: string, data: Partial<Sample>): Promise<APIResponse> =>
      apiRequest<APIResponse>(`/sample/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    deleteSample: (id: string): Promise<APIResponse> =>
      apiRequest<APIResponse>(`/sample/${id}`, { method: 'DELETE' }),

    downloadSample: (id: string): void => {
      window.open(`${API_BASE_URL}/sample/${id}/download`, '_blank')
    },

    downloadMultiple: async (sampleIds: string[]): Promise<void> => {
      const response = await fetch(`${API_BASE_URL}/samples/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_ids: sampleIds }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Download failed')
      }

      const contentDisposition = response.headers.get('Content-Disposition')
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/)
      const filename = filenameMatch ? filenameMatch[1] : 'samples.jsonl'

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },

    search: (query: string, limit: number = 10): Promise<APIResponse<Sample[]>> => {
      const params = new URLSearchParams({ q: query, limit: String(limit) })
      return apiRequest<APIResponse<Sample[]>>(`/search?${params}`)
    },

    getRandom: (count: number = 5, difficulty?: string): Promise<APIResponse<Sample[]>> => {
      const params = new URLSearchParams({ count: String(count) })
      if (difficulty) params.append('difficulty', difficulty)
      return apiRequest<APIResponse<Sample[]>>(`/samples/random?${params}`)
    },

    filter: (filters: Record<string, string>): Promise<APIResponse<Sample[]>> => {
      const params = new URLSearchParams(filters)
      return apiRequest<APIResponse<Sample[]>>(`/samples/filter?${params}`)
    },

    add: (sample: Partial<Sample>): Promise<APIResponse> =>
      apiRequest<APIResponse>('/add', {
        method: 'POST',
        body: JSON.stringify(sample),
      }),

    importJsonl: (content: string): Promise<APIResponse<{ total_samples: number }>> =>
      apiRequest<APIResponse<{ total_samples: number }>>('/import/jsonl', {
        method: 'POST',
        body: JSON.stringify({ content }),
      }),
  },

  // ==================== GENERATION ENDPOINTS ====================

  generation: {
    start: (config: GenerationConfig): Promise<APIResponse> =>
      apiRequest<APIResponse>('/generate/batch/start', {
        method: 'POST',
        body: JSON.stringify(config),
      }),

    stop: (batchId?: string): Promise<APIResponse> =>
      apiRequest<APIResponse>('/generate/batch/stop', {
        method: 'POST',
        body: JSON.stringify(batchId ? { batch_id: batchId } : {}),
      }),

    getStatus: (): Promise<any> => apiRequest('/generate/batch/status'),

    getHistory: (): Promise<APIResponse<{ batches: BatchHistory[] }>> =>
      apiRequest<APIResponse<{ batches: BatchHistory[] }>>('/generate/batch/history'),

    getStuckBatches: (): Promise<APIResponse<{ stuck_batches: any[] }>> =>
      apiRequest<APIResponse<{ stuck_batches: any[] }>>('/batches/stuck'),

    connectSSE: (): EventSource => new EventSource(`${API_BASE_URL}/generate/batch/stream`),
  },

  // ==================== CONFIGURATION ENDPOINTS ====================

  config: {
    getModels: (): Promise<APIResponse<{ models: Model[] }>> =>
      apiRequest<APIResponse<{ models: Model[] }>>('/models'),

    getProviders: (): Promise<APIResponse<{ providers: Provider[]; default_provider: string }>> =>
      apiRequest<APIResponse<{ providers: Provider[]; default_provider: string }>>('/providers'),

    getTopics: (): Promise<{ topics: Topic[] }> =>
      apiRequest<{ topics: Topic[] }>('/topics'),

    getSampleTypes: (): Promise<APIResponse<{ sample_types: SampleType[]; default: string }>> =>
      apiRequest<APIResponse<{ sample_types: SampleType[]; default: string }>>('/sample-types'),
  },

  // ==================== HUGGINGFACE ENDPOINTS ====================

  huggingface: {
    push: (config: HuggingFaceConfig): Promise<APIResponse> =>
      apiRequest<APIResponse>('/huggingface/push', {
        method: 'POST',
        body: JSON.stringify(config),
      }),
  },
}

export default api
