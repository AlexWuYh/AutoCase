import request from '@/utils/request'

export interface LoginPayload {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export const authApi = {
  login(payload: LoginPayload) {
    return request.post<TokenResponse>('/auth/login', payload)
  },
  refresh(refreshToken: string) {
    return request.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
  },
  me() {
    return request.get<UserInfo>('/auth/me')
  },
  changePassword(oldPassword: string, newPassword: string) {
    return request.post<{ message: string }>('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },
}
