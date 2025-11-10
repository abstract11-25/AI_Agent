import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { ElMessage } from 'element-plus'

interface User {
  id: number
  username: string
  email: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  // 设置token和用户信息
  function setAuth(accessToken: string, userData: User) {
    token.value = accessToken
    user.value = userData
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // 清除认证信息
  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 从localStorage恢复用户信息
  function restoreAuth() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Failed to parse user data:', e)
        clearAuth()
      }
    }
  }

  // 登录
  async function login(username: string, password: string) {
    try {
      // 使用FormData格式（OAuth2PasswordRequestForm要求）
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await axios.post('http://127.0.0.1:8000/api/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const { access_token, user: userData } = response.data
      setAuth(access_token, userData)
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || '登录失败，请检查用户名和密码'
      ElMessage.error(message)
      return false
    }
  }

  // 注册
  async function register(username: string, email: string, password: string) {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/auth/register', {
        username,
        email,
        password
      })

      ElMessage.success('注册成功，请登录')
      return { success: true, message: '注册成功' }
    } catch (error: any) {
      // 获取详细的错误信息
      let errorMessage = '注册失败'
      let errorDetail = ''
      
      if (error.response) {
        // 服务器返回的错误
        const detail = error.response.data?.detail || ''
        errorDetail = detail
        
        // 根据不同的错误类型提供更友好的提示
        if (detail.includes('用户名已存在')) {
          errorMessage = '注册失败：用户名已被使用'
          errorDetail = '该用户名已被其他用户注册，请尝试其他用户名'
        } else if (detail.includes('邮箱已被注册')) {
          errorMessage = '注册失败：邮箱已被注册'
          errorDetail = '该邮箱已被注册，请使用其他邮箱或直接登录'
        } else if (detail.includes('邮箱') || detail.includes('email')) {
          errorMessage = '注册失败：邮箱格式不正确'
          errorDetail = '请输入有效的邮箱地址，格式如：user@example.com'
        } else if (detail) {
          errorMessage = `注册失败：${detail}`
          errorDetail = detail
        }
      } else if (error.request) {
        // 请求已发出但没有收到响应
        errorMessage = '注册失败：无法连接到服务器'
        errorDetail = '请检查网络连接，或确认后端服务是否已启动（http://127.0.0.1:8000）'
      } else {
        // 其他错误
        errorMessage = '注册失败：发生未知错误'
        errorDetail = error.message || '请稍后重试'
      }
      
      ElMessage.error(errorMessage)
      return { success: false, message: errorMessage, detail: errorDetail }
    }
  }

  // 获取当前用户信息
  async function fetchUserInfo() {
    if (!token.value) return false

    try {
      const response = await axios.get('http://127.0.0.1:8000/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
      return true
    } catch (error: any) {
      // token可能已过期
      if (error.response?.status === 401) {
        clearAuth()
        ElMessage.warning('登录已过期，请重新登录')
      }
      return false
    }
  }

  // 退出登录
  function logout() {
    clearAuth()
    ElMessage.success('已退出登录')
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    logout,
    fetchUserInfo,
    restoreAuth,
    clearAuth
  }
})

