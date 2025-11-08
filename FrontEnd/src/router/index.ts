import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import EvaluationView from '../views/EvaluationView.vue'

// 定义路由类型
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'evaluation',
    component: EvaluationView
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router