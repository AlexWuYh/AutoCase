<template>
  <div class="profile">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card>
          <template #header><span>个人信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">
              {{ auth.user?.username }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ auth.user?.email }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag :type="auth.isAdmin ? 'danger' : 'info'">
                {{ auth.isAdmin ? '管理员' : '普通用户' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最后登录">
              {{ auth.user?.last_login_at ? formatDate(auth.user.last_login_at) : '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header><span>修改密码</span></template>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            @submit.prevent
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="form.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="form.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input v-model="form.confirm" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSubmit">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const formRef = ref<FormInstance>()
const saving = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})

const rules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '长度 6-128', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, cb) => {
        if (value !== form.new_password) cb(new Error('两次输入的密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await authApi.changePassword(form.old_password, form.new_password)
    ElMessage.success('密码已修改')
    form.old_password = ''
    form.new_password = ''
    form.confirm = ''
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '修改失败')
  } finally {
    saving.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
</script>
