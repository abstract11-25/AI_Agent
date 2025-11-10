import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import EvaluationView from '../views/EvaluationView.vue'
import LoginView from '../views/LoginView.vue'
import { useUserStore } from '../stores/user'

// 定义路由类型
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'evaluation',
    component: EvaluationView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫：检查登录状态
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (userStore.isLoggedIn) {
      next()
    } else {
      // 未登录，跳转到登录页
      next({ name: 'login', query: { redirect: to.fullPath } })
    }
  } else {
    // 登录页面，如果已登录则跳转到首页
    if (to.name === 'login' && userStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  }
})

export default router