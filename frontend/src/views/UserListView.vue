<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" :icon="Plus" @click="onCreate">新建用户</el-button>
        </div>
      </template>

      <div class="filters">
        <el-input
          v-model="search"
          placeholder="搜索用户名或邮箱"
          clearable
          :prefix-icon="Search"
          style="width: 280px"
          @keyup.enter="reload"
        />
        <el-button @click="reload">查询</el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        style="width: 100%"
        empty-text="暂无用户"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'warning'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login_at ? formatDate(row.last_login_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" @click="onResetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.id === currentUserId"
              @click="onDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="reload"
        @size-change="reload"
      />
    </el-card>

    <UserFormDialog v-model="dialogOpen" :user="editingUser" @saved="reload" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { usersApi } from '@/api/users'
import type { UserInfo } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import UserFormDialog from '@/components/user/UserFormDialog.vue'

const auth = useAuthStore()
const loading = ref(false)
const rows = ref<UserInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')

const dialogOpen = ref(false)
const editingUser = ref<UserInfo | null>(null)

const currentUserId = computed(() => auth.user?.id)

async function reload() {
  loading.value = true
  try {
    const { data } = await usersApi.list({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function onCreate() {
  editingUser.value = null
  dialogOpen.value = true
}

function onEdit(row: UserInfo) {
  editingUser.value = row
  dialogOpen.value = true
}

async function onResetPassword(row: UserInfo) {
  try {
    const { value: newPwd } = await ElMessageBox.prompt(
      `为用户 "${row.username}" 设置新密码 (至少 6 位)`,
      '重置密码',
      {
        inputType: 'password',
        inputValidator: (v) => (v && v.length >= 6 ? true : '密码长度至少 6 位'),
        confirmButtonText: '确认',
        cancelButtonText: '取消',
      },
    )
    if (newPwd) {
      await usersApi.resetPassword(row.id, newPwd)
      ElMessage.success('密码已重置')
    }
  } catch (e: unknown) {
    if ((e as { type?: string })?.type === 'cancel') return
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '重置失败')
  }
}

async function onDelete(row: UserInfo) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
    await usersApi.remove(row.id)
    ElMessage.success('已删除')
    reload()
  } catch (e: unknown) {
    if ((e as { type?: string })?.type === 'cancel') return
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '删除失败')
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(reload)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
</style>
