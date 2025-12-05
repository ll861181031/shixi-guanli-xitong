import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'positions',
        name: 'Positions',
        component: () => import('@/views/Positions.vue'),
        meta: { title: '岗位管理', permission: 'positions' }
      },
      {
        path: 'applications',
        name: 'Applications',
        component: () => import('@/views/Applications.vue'),
        meta: { title: '申请管理', permission: 'applications' }
      },
      {
        path: 'checkins',
        name: 'Checkins',
        component: () => import('@/views/Checkins.vue'),
        meta: { title: '签到管理', permission: 'checkins' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/Reports.vue'),
        meta: { title: '周报管理', permission: 'reports' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '数据统计', permission: 'statistics' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'forum/posts',
        name: 'ForumPosts',
        component: () => import('@/views/ForumPosts.vue'),
        meta: { title: '论坛帖子', permission: 'forum' }
      },
      {
        path: 'forum/comments',
        name: 'ForumComments',
        component: () => import('@/views/ForumComments.vue'),
        meta: { title: '论坛评论', permission: 'forum' }
      },
      {
        path: 'forum/categories',
        name: 'ForumCategories',
        component: () => import('@/views/ForumCategories.vue'),
        meta: { title: '论坛分类', permission: 'forum' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresAdmin && authStore.user?.role !== 'admin') {
    next('/dashboard')
  } else if (
    to.meta.permission &&
    authStore.user?.role === 'teacher' &&
    !(authStore.user?.permissions || []).includes(to.meta.permission)
  ) {
    next('/dashboard')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

