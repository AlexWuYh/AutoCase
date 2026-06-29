import request from '@/utils/request'

export interface RequirementGroup {
  id: number
  name: string
  description: string | null
  owner_id: number
  owner_username: string | null
  requirement_count: number
  created_at: string
  updated_at: string
}

export interface Requirement {
  id: number
  group_id: number
  module: string
  feature: string
  description: string
  keywords: string[]
  sort_order: number
  created_at: string
  updated_at: string
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const requirementsApi = {
  // Groups
  listGroups(params: {
    page?: number
    page_size?: number
    search?: string
    scope?: string
  } = {}) {
    return request.get<PageResponse<RequirementGroup>>('/requirement-groups', { params })
  },
  createGroup(payload: { name: string; description?: string | null }) {
    return request.post<RequirementGroup>('/requirement-groups', payload)
  },
  getGroup(id: number) {
    return request.get<RequirementGroup>(`/requirement-groups/${id}`)
  },
  updateGroup(id: number, payload: { name?: string; description?: string | null }) {
    return request.put<RequirementGroup>(`/requirement-groups/${id}`, payload)
  },
  deleteGroup(id: number) {
    return request.delete<{ message: string }>(`/requirement-groups/${id}`)
  },

  // Requirements within a group
  listRequirements(
    groupId: number,
    params: { page?: number; page_size?: number; search?: string } = {},
  ) {
    return request.get<PageResponse<Requirement>>(
      `/requirement-groups/${groupId}/requirements`,
      { params },
    )
  },
  batchCreate(groupId: number, items: Omit<Requirement, 'id' | 'group_id' | 'sort_order' | 'created_at' | 'updated_at'>[], mode: 'append' | 'replace' = 'append') {
    return request.post<Requirement[]>(
      `/requirement-groups/${groupId}/requirements`,
      { items, mode },
    )
  },
  update(id: number, payload: Partial<Pick<Requirement, 'module' | 'feature' | 'description' | 'keywords'>>) {
    return request.put<Requirement>(`/requirement-groups/requirements/${id}`, payload)
  },
  deleteRequirement(id: number) {
    return request.delete<{ message: string }>(`/requirement-groups/requirements/${id}`)
  },

  // YAML import/export
  importYaml(groupId: number, text: string, mode: 'append' | 'replace' = 'append') {
    const formData = new FormData()
    formData.append('text', text)
    return request.post(`/requirement-groups/${groupId}/import-yaml?mode=${mode}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  importYamlFile(groupId: number, file: File, mode: 'append' | 'replace' = 'append') {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/requirement-groups/${groupId}/import-yaml?mode=${mode}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportYaml(groupId: number) {
    return request.get(`/requirement-groups/${groupId}/export-yaml`, {
      responseType: 'text',
    })
  },
}
