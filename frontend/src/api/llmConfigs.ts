import request from '@/utils/request'

export interface LLMConfig {
  id: number
  name: string
  provider: string
  enabled: boolean
  api_key_env: string | null
  allow_empty_key: boolean
  base_url: string | null
  api_mode: string
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  frequency_penalty: number
  presence_penalty: number
  retry_count: number
  debug_log: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface LLMConfigCreate {
  name: string
  provider?: string
  enabled?: boolean
  api_key_env?: string | null
  allow_empty_key?: boolean
  base_url?: string | null
  api_mode?: string
  model?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  retry_count?: number
  debug_log?: boolean
  is_default?: boolean
}

export type LLMConfigUpdate = Partial<LLMConfigCreate>

export interface TestResult {
  success: boolean
  elapsed_ms: number
  message: string
}

export const llmConfigsApi = {
  list(params: { page?: number; page_size?: number } = {}) {
    return request.get<{ items: LLMConfig[]; total: number; page: number; page_size: number }>('/llm-configs', { params })
  },
  create(payload: LLMConfigCreate) {
    return request.post<LLMConfig>('/llm-configs', payload)
  },
  update(id: number, payload: LLMConfigUpdate) {
    return request.put<LLMConfig>(`/llm-configs/${id}`, payload)
  },
  delete(id: number) {
    return request.delete(`/llm-configs/${id}`)
  },
  test(id: number, message?: string) {
    return request.post<TestResult>(`/llm-configs/${id}/test`, { message: message || 'Say OK' })
  },
}
