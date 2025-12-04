import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
const token = ref(localStorage.getItem('token') || '')
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

if (token.value) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
}

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(tokenValue, userValue) {
    token.value = tokenValue
    user.value = userValue
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('user', JSON.stringify(userValue))
    api.defaults.headers.common['Authorization'] = `Bearer ${tokenValue}`
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete api.defaults.headers.common['Authorization']
  }

  async function login(username, password) {
    try {
      const response = await api.post('/auth/login', { username, password })
      if (response.data.success) {
        setAuth(response.data.data.token, response.data.data.user)
        return { success: true }
      }
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || '登录失败'
      }
    }
  }

  async function logout() {
    clearAuth()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    setAuth,
    clearAuth
  }
})

