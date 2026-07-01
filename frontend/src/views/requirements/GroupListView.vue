<template>
  <div class="group-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>需求集管理</span>
          <el-button type="primary" :icon="Plus" @click="onCreateGroup">新建需求集</el-button>
        </div>
      </template>

      <div class="filters">
        <el-input
          v-model="search"
          placeholder="搜索名称或描述"
          clearable
          :prefix-icon="Search"
          style="width: 280px"
          @keyup.enter="reload"
        />
        <el-button @click="reload">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="rows" stripe row-key="id" highlight-current-row style="cursor: pointer" @row-click="onRowClick">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="onEnter(row)">{{ row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="owner_username" label="创建者" width="120" />
        <el-table-column prop="requirement_count" label="功能点数" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="onGenerate(row)">生成</el-button>
            <el-button size="small" @click.stop="onEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="reload"
        @size-change="reload"
      />
    </el-card>

    <el-dialog
      v-model="dialogOpen"
      :title="editingGroup ? '编辑需求集' : '新建需求集'"
      width="420px"
      @close="onClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" autofocus />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <JobCreateDialog v-model="genOpen" :preset-group-id="genGroupId" @created="onGenerated" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { requirementsApi, type RequirementGroup } from '@/api/requirements'
import JobCreateDialog from '@/components/job/JobCreateDialog.vue'

const router = useRouter()
const loading = ref(false)
const rows = ref<RequirementGroup[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')

const dialogOpen = ref(false)
const editingGroup = ref<RequirementGroup | null>(null)
const formRef = ref<FormInstance>()
const saving = ref(false)
const form = reactive({ name: '', description: '' })

// Quick-generate dialog
const genOpen = ref(false)
const genGroupId = ref<number | null>(null)

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

function onGenerate(row: RequirementGroup) {
  if (row.requirement_count === 0) {
    ElMessage.warning('该需求集暂无功能点，请先添加需求')
    return
  }
  genGroupId.value = row.id
  genOpen.value = true
}

async function onGenerated() {
  try {
    await ElMessageBox.confirm('生成任务已创建，是否前往「自动用例生成」查看进度？', '任务已创建', {
      confirmButtonText: '查看任务',
      cancelButtonText: '留在本页',
      type: 'success',
    })
    router.push('/jobs')
  } catch {
    /* stay */
  }
}

async function reload() {
  loading.value = true
  try {
    const { data } = await requirementsApi.listGroups({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function onEnter(row: RequirementGroup) {
  router.push(`/requirement-groups/${row.id}`)
}

function onRowClick(row: RequirementGroup) {
  router.push(`/requirement-groups/${row.id}`)
}

function onCreateGroup() {
  editingGroup.value = null
  form.name = ''
  form.description = ''
  dialogOpen.value = true
}

function onEdit(row: RequirementGroup) {
  editingGroup.value = row
  form.name = row.name
  form.description = row.description || ''
  dialogOpen.value = true
}

function onClose() {
  formRef.value?.resetFields()
}

async function onSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingGroup.value) {
      await requirementsApi.updateGroup(editingGroup.value.id, { name: form.name, description: form.description })
      ElMessage.success('已更新')
    } else {
      await requirementsApi.createGroup({ name: form.name, description: form.description })
      ElMessage.success('已创建')
    }
    dialogOpen.value = false
    reload()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally {
    saving.value = false
  }
}

async function onDelete(row: RequirementGroup) {
  try {
    await ElMessageBox.confirm(`删除 "${row.name}" 将同时删除其中所有功能点，不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
    })
    await requirementsApi.deleteGroup(row.id)
    ElMessage.success('已删除')
    reload()
  } catch {
    // cancelled
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(reload)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
</style>
