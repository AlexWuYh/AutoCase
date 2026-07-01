import request from '@/utils/request'

export interface ApiKey {
  id: number
  name: string
  prefix: string
  is_active: boolean
  created_at: string
  last_used_at: string | null
}

export interface ApiKeyCreated extends ApiKey {
  key: string
}

export const apiKeysApi = {
  list() {
    return request.get<ApiKey[]>('/api-keys')
  },
  create(name: string) {
    return request.post<ApiKeyCreated>('/api-keys', { name })
  },
  revoke(id: number) {
    return request.delete<{ message: string }>(`/api-keys/${id}`)
  },
}
