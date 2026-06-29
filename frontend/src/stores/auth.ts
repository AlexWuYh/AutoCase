import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type UserInfo } from '@/api/auth'

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem(ACCESS_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))

  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
    accessToken.value = access
    refreshToken.value = refresh
  }

  function setUser(u: UserInfo) {
    user.value = u
  }

  async function login(username: string, password: string) {
    const { data } = await authApi.login({ username, password })
    setTokens(data.access_token, data.refresh_token)
    await fetchMe()
  }

  async function fetchMe() {
    if (!accessToken.value) return
    const { data } = await authApi.me()
    setUser(data)
  }

  function logout() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    accessToken.value = null
    refreshToken.value = null
    user.value = null
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isAdmin,
    setTokens,
    setUser,
    login,
    fetchMe,
    logout,
  }
})
