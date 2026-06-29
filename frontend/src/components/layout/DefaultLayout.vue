<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">AutoCase</div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="rgba(255,255,255,0.85)"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/requirement-groups">
          <el-icon><Document /></el-icon>
          <span>需求集</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/llm-configs">
          <el-icon><Setting /></el-icon>
          <span>LLM 配置</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/prompts">
          <el-icon><EditPen /></el-icon>
          <span>Prompt 模板</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <!-- Additional menu items will be added in later phases -->
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-trigger">
            <el-icon><UserFilled /></el-icon>
            {{ auth.user?.username || '用户' }}
            <el-tag
              v-if="auth.isAdmin"
              size="small"
              type="danger"
              effect="dark"
              style="margin-left: 4px"
            >管理员</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
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

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => (route.meta.title as string) || 'AutoCase')

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}

onMounted(() => {
  // Refetch profile in case token is valid but user info is missing
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchMe().catch(() => auth.logout())
  }
})
</script>

<style scoped>
.layout { height: 100vh; }
.sidebar { background: #001529; }
.logo {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-title { font-size: 16px; font-weight: 600; }
.user-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
}
.main { background: #f5f7fa; padding: 24px; }
:deep(.el-menu) { border-right: none; }
</style>
