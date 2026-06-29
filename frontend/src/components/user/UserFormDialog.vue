<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑用户' : '新建用户'"
    width="480px"
    @close="onClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" :disabled="isEdit" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item v-if="!isEdit" label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-form-item label="角色" prop="role">
        <el-radio-group v-model="form.role">
          <el-radio value="user">普通用户</el-radio>
          <el-radio value="admin">管理员</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch
          v-model="form.is_active"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { usersApi } from '@/api/users'
import type { UserInfo } from '@/api/auth'

interface Props {
  modelValue: boolean
  user: UserInfo | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.user)
const formRef = ref<FormInstance>()
const saving = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user' as 'admin' | 'user',
  is_active: true,
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '长度 3-64', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '长度 6-128', trigger: 'blur' },
  ],
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      if (props.user) {
        form.username = props.user.username
        form.email = props.user.email
        form.role = props.user.role
        form.is_active = props.user.is_active
        form.password = ''
      } else {
        form.username = ''
        form.email = ''
        form.password = ''
        form.role = 'user'
        form.is_active = true
      }
    }
  },
)

function onClose() {
  formRef.value?.resetFields()
}

async function onSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value && props.user) {
      await usersApi.update(props.user.id, {
        email: form.email,
        role: form.role,
        is_active: form.is_active,
      })
      ElMessage.success('已更新')
    } else {
      await usersApi.create({
        username: form.username,
        email: form.email,
        password: form.password,
        role: form.role,
        is_active: form.is_active,
      })
      ElMessage.success('已创建')
    }
    emit('saved')
    visible.value = false
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
