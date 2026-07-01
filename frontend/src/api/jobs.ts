import request from '@/utils/request'

export interface TestCase {
  id: number
  job_id: number
  case_id: string
  module: string
  case_type: string
  name: string
  priority: string
  preconditions: string
  steps: string[]
  expected: string[]
  keywords: string
  stage: string
  created_at: string
}

export interface GenerationJob {
  id: number
  group_id: number | null
  user_id: number | null
  status: 'pending' | 'running' | 'success' | 'failed' | 'canceled'
  total: number
  finished: number
  percent: number
  error: string | null
  group_name: string | null
  user_name: string | null
  llm_config_name: string | null
  prompt_name: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface Page<T> { items: T[]; total: number; page: number; page_size: number }

export const jobsApi = {
  list(params: { page?: number; page_size?: number; status?: string; group_id?: number } = {}) {
    return request.get<Page<GenerationJob>>('/jobs', { params })
  },
  create(payload: { group_id: number; llm_config_id?: number; prompt_id?: number }) {
    return request.post<GenerationJob>('/jobs', payload)
  },
  get(id: number) {
    return request.get<GenerationJob>(`/jobs/${id}`)
  },
  cancel(id: number) {
    return request.delete<{ message: string }>(`/jobs/${id}`)
  },
  listCases(jobId: number, params: { page?: number; page_size?: number } = {}) {
    return request.get<Page<TestCase>>(`/jobs/${jobId}/cases`, { params })
  },
  // Download via axios (blob) so the JWT is sent in the Authorization header.
  // The previous window.open(?token=) approach failed with 401 because the
  // backend only reads the token from the header, not a query param.
  exportBlob(jobId: number, format: 'xlsx' | 'csv' = 'xlsx') {
    return request.get(`/jobs/${jobId}/export`, {
      params: { format },
      responseType: 'blob',
    })
  },
}
