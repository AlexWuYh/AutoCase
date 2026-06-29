<template>
  <div class="prompts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Prompt 模板管理</span>
          <el-button type="primary" :icon="Plus" @click="onCreate">新建模板</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows" stripe empty-text="暂无 Prompt，启动时会自动从 config/system_prompt.txt 导入默认模板">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="内容预览" min-width="200">
          <template #default="{ row }">{{ truncate(row.content, 80) }}</template>
        </el-table-column>
        <el-table-column label="默认" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="danger" size="small">默认</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onView(row)">查看/编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
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
      :title="editing ? '编辑 Prompt 模板' : '新建 Prompt 模板'"
      width="680px"
      @close="onClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="16"
            class="mono-input"
          />
        </el-form-item>
        <el-form-item label="">
          <el-checkbox v-model="form.is_default">设为默认模板</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { promptsApi, type SystemPrompt } from '@/api/prompts'

const loading = ref(false)
const rows = ref<SystemPrompt[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const dialogOpen = ref(false)
const editing = ref(false)
const editingId = ref(0)
const formRef = ref<FormInstance>()
const saving = ref(false)

const defaultForm = () => ({
  name: '',
  description: null as string | null,
  content: '',
  is_default: false,
})
const form = reactive(defaultForm())

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }],
}

async function reload() {
  loading.value = true
  try {
    const { data } = await promptsApi.list({ page: page.value, page_size: pageSize.value })
    rows.value = data.items
    total.value = data.total
  } catch { ElMessage.error('加载失败') } finally { loading.value = false }
}

function onCreate() {
  editing.value = false; editingId.value = 0
  Object.assign(form, defaultForm())
  dialogOpen.value = true
}

function onView(row: SystemPrompt) {
  editing.value = true; editingId.value = row.id
  form.name = row.name
  form.description = row.description
  form.content = row.content
  form.is_default = row.is_default
  dialogOpen.value = true
}

function onClose() { formRef.value?.resetFields() }

async function onSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) {
      await promptsApi.update(editingId.value, { name: form.name, description: form.description, content: form.content, is_default: form.is_default })
      ElMessage.success('已更新')
    } else {
      await promptsApi.create({ name: form.name, description: form.description, content: form.content, is_default: form.is_default })
      ElMessage.success('已创建')
    }
    dialogOpen.value = false
    reload()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally { saving.value = false }
}

async function onDelete(row: SystemPrompt) {
  try {
    await ElMessageBox.confirm(`删除 "${row.name}"？`, '确认', { type: 'warning' })
    await promptsApi.delete(row.id)
    ElMessage.success('已删除')
    reload()
  } catch { /* cancelled */ }
}

function truncate(text: string, n: number) {
  return text.length > n ? text.slice(0, n) + '...' : text
}

onMounted(reload)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.mono-input :deep(textarea) { font-family: 'Courier New', monospace; font-size: 13px; }
</style>
