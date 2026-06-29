<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="login-header">
          <h2>AutoCase 平台</h2>
          <p>LLM 自动生成测试用例工具</p>
        </div>
      </template>

      <el-alert
        v-if="phase1Notice"
        type="info"
        :closable="false"
        title="阶段 1 占位"
        description="认证功能将在阶段 2 完成。当前为前端骨架预览。"
        style="margin-bottom: 16px"
      />

      <el-form :model="form" label-width="80px" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-tips">
        默认管理员账号将在阶段 2 启动时自动创建
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const phase1Notice = ref(true)

const form = reactive({ username: '', password: '' })

async function onSubmit() {
  // Phase 1: just navigate to dashboard to show the layout works.
  loading.value = true
  setTimeout(() => {
    loading.value = false
    router.push('/dashboard')
  }, 400)
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card { width: 420px; }
.login-header { text-align: center; }
.login-header h2 { margin: 0 0 8px; color: #303133; }
.login-header p { margin: 0; color: #909399; font-size: 13px; }
.login-tips { text-align: center; color: #909399; font-size: 12px; margin-top: 12px; }
</style>
