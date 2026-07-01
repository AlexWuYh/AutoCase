<template>
  <el-container class="layout">
    <el-aside width="228px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">AC</div>
        <div class="brand-name">AutoCase</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="side-menu"
        @select="onMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/requirement-groups">
          <el-icon><Document /></el-icon>
          <span>需求集</span>
        </el-menu-item>
        <el-menu-item index="/jobs">
          <el-icon><MagicStick /></el-icon>
          <span>自动用例生成</span>
        </el-menu-item>
        <el-menu-item index="/api-keys">
          <el-icon><Key /></el-icon>
          <span>API 密钥</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/llm-configs">
          <el-icon><Setting /></el-icon>
          <span>LLM 配置</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/prompts">
          <el-icon><EditPen /></el-icon>
          <span>Prompt 模板</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-trigger">
            <span class="avatar">{{ (auth.user?.username || 'U')[0].toUpperCase() }}</span>
            <span class="uname">{{ auth.user?.username || '加载中...' }}</span>
            <el-tag v-if="isAdmin" size="small" type="success" effect="light" round>管理员</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/requirement-groups')) return '/requirement-groups'
  if (route.path.startsWith('/jobs')) return '/jobs'
  return route.path
})

const pageTitle = computed(() => (route.meta.title as string) || 'AutoCase')

const isAdmin = computed(() => {
  if (auth.user?.role === 'admin') return true
  const raw = localStorage.getItem('access_token')
  if (!raw) return false
  try {
    return JSON.parse(atob(raw.split('.')[1])).role === 'admin'
  } catch {
    return false
  }
})

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}

function onMenuSelect(index: string) {
  router.push(index)
}

onMounted(() => {
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchMe().catch(() => auth.logout())
  }
})
</script>

<style scoped>
.layout { height: 100vh; }

.sidebar {
  background: #ffffff;
  border-right: 1px solid var(--ac-border, #eaecef);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--ac-border, #eaecef);
}
.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.35);
}
.brand-name { font-size: 18px; font-weight: 700; color: #1f2933; }

.side-menu {
  border-right: none;
  padding: 10px 12px;
  flex: 1;
}
.side-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  border-radius: 8px;
  margin-bottom: 4px;
  color: #4b5563;
  font-weight: 500;
}
.side-menu :deep(.el-menu-item:hover) {
  background: var(--el-color-primary-light-9, #f2fbf8);
  color: var(--el-color-primary, #10b981);
}
.side-menu :deep(.el-menu-item.is-active) {
  background: var(--el-color-primary-light-9, #e9f8f3);
  color: var(--el-color-primary-dark-2, #0d9668);
  font-weight: 600;
}

.header {
  background: #ffffff;
  border-bottom: 1px solid var(--ac-border, #eaecef);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
}
.header-title { font-size: 17px; font-weight: 600; color: #1f2933; }
.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #303133;
}
.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.uname { font-weight: 500; }
.main { background: var(--ac-bg, #f6f8fa); padding: 24px; overflow-y: auto; }
</style>
