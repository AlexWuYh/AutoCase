import request from '@/utils/request'
import type { UserInfo } from './auth'

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface UserCreatePayload {
  username: string
  email: string
  password: string
  role: 'admin' | 'user'
  is_active: boolean
}

export interface UserUpdatePayload {
  email?: string
  role?: 'admin' | 'user'
  is_active?: boolean
}

export const usersApi = {
  list(params: { page?: number; page_size?: number; search?: string } = {}) {
    return request.get<PageResponse<UserInfo>>('/users', { params })
  },
  get(id: number) {
    return request.get<UserInfo>(`/users/${id}`)
  },
  create(payload: UserCreatePayload) {
    return request.post<UserInfo>('/users', payload)
  },
  update(id: number, payload: UserUpdatePayload) {
    return request.put<UserInfo>(`/users/${id}`, payload)
  },
  remove(id: number) {
    return request.delete<{ message: string }>(`/users/${id}`)
  },
  resetPassword(id: number, newPassword: string) {
    return request.post<{ message: string }>(`/users/${id}/reset-password`, {
      new_password: newPassword,
    })
  },
}
