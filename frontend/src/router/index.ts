import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/DefaultLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '概览' },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/UserListView.vue'),
        meta: { title: '用户管理', requiresAdmin: true },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: '个人中心' },
      },
      {
        path: 'requirement-groups',
        name: 'requirement-groups',
        component: () => import('@/views/requirements/GroupListView.vue'),
        meta: { title: '需求集管理' },
      },
      {
        path: 'requirement-groups/:id',
        name: 'requirement-group-detail',
        component: () => import('@/views/requirements/GroupDetailView.vue'),
        meta: { title: '需求集详情' },
      },
      {
        path: 'llm-configs',
        name: 'llm-configs',
        component: () => import('@/views/configs/LLMConfigListView.vue'),
        meta: { title: 'LLM 配置', requiresAdmin: true },
      },
      {
        path: 'prompts',
        name: 'prompts',
        component: () => import('@/views/configs/PromptListView.vue'),
        meta: { title: 'Prompt 模板', requiresAdmin: true },
      },
      // Feature routes will be added in later phases.
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth + role guard
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }
})

export default router
