<template>
  <el-container class="layout-container">
    <el-aside :width="collapsed ? '64px' : '200px'" class="sidebar">
      <div class="logo">
        <h2 v-if="!collapsed">实习管理系统</h2>
        <el-button link class="collapse-btn" @click="toggleCollapse">
          <el-icon v-if="collapsed"><Expand /></el-icon>
          <el-icon v-else><Fold /></el-icon>
        </el-button>
      </div>
      <el-menu
        :collapse="collapsed"
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('positions')" index="/positions">
          <el-icon><Briefcase /></el-icon>
          <span>岗位管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('applications')" index="/applications">
          <el-icon><Document /></el-icon>
          <span>申请管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('checkins')" index="/checkins">
          <el-icon><Location /></el-icon>
          <span>签到管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('reports')" index="/reports">
          <el-icon><EditPen /></el-icon>
          <span>周报管理</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('statistics')" index="/statistics">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据统计</span>
        </el-menu-item>
        <el-menu-item v-if="canAccess('users')" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-sub-menu v-if="canAccess('forum')" index="/forum">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>论坛管理</span>
          </template>
          <el-menu-item index="/forum/posts">帖子</el-menu-item>
          <el-menu-item index="/forum/comments">评论</el-menu-item>
          <el-menu-item index="/forum/categories">分类</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h3>{{ currentTitle }}</h3>
          <el-tag size="small" type="warning" effect="plain" class="env-tag">{{ envLabel }}</el-tag>
        </div>
        <div class="header-right">
          <el-badge :value="noticeCount" class="notice-badge">
            <el-button link @click="goNotice">
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ user?.real_name || user?.username }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { DataBoard, Briefcase, Document, Location, EditPen, DataAnalysis, User, ArrowDown, Bell, Fold, Expand } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const permissionSet = computed(() => new Set(user.value?.permissions || []))
const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '仪表盘')
const collapsed = ref(false)
const envLabel = import.meta.env.MODE === 'production' ? '生产环境' : '测试/开发'
const noticeCount = computed(() => authStore.noticeCount || 0)

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function canAccess(key) {
  if (user.value?.role === 'admin') return true
  if (user.value?.role === 'teacher') {
    return permissionSet.value.has(key)
  }
  return false
}

function toggleCollapse() {
  collapsed.value = !collapsed.value
}

function goNotice() {
  router.push('/messages')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow-y: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  border-bottom: 1px solid #434a55;
  padding: 0 12px;
}

.logo h2 {
  font-size: 18px;
  font-weight: 500;
}

.collapse-btn {
  color: #bfcbd9;
}

.sidebar-menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #606266;
}

.notice-badge {
  margin-right: 4px;
}

.env-tag {
  margin-left: 6px;
}
.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>

