import request from '@/utils/request'

export interface SystemPrompt {
  id: number
  name: string
  content: string
  description: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export const promptsApi = {
  list(params: { page?: number; page_size?: number } = {}) {
    return request.get<{ items: SystemPrompt[]; total: number; page: number; page_size: number }>('/system-prompts', { params })
  },
  create(payload: { name: string; content: string; description?: string | null; is_default?: boolean }) {
    return request.post<SystemPrompt>('/system-prompts', payload)
  },
  update(id: number, payload: Partial<{ name: string; content: string; description: string | null; is_default: boolean }>) {
    return request.put<SystemPrompt>(`/system-prompts/${id}`, payload)
  },
  delete(id: number) {
    return request.delete(`/system-prompts/${id}`)
  },
}
