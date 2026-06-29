import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

const instance: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

// Request interceptor: attach JWT token
instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401, surface errors
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail || error.message

    if (status === 401) {
      // Token invalid/expired - clear and bounce to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else if (status && status >= 500) {
      ElMessage.error(`服务器错误: ${detail}`)
    }

    return Promise.reject(error)
  },
)

export default instance
