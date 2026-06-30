<template>
  <div class="configs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>LLM 配置管理</span>
          <el-button type="primary" :icon="Plus" @click="onCreate">新建配置</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows" stripe empty-text="暂无 LLM 配置，启动时会自动从 config/llm.yaml 导入默认配置">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="模型" width="160" />
        <el-table-column prop="base_url" label="BASE URL" min-width="180" show-overflow-tooltip />
        <el-table-column label="默认" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="danger" size="small">默认</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" @click="onTest(row)" :loading="testing[row.id]">测试</el-button>
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
      :title="editing ? '编辑 LLM 配置' : '新建 LLM 配置'"
      width="560px"
      @close="onClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" @submit.prevent>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="模型" prop="model">
          <el-input v-model="form.model" placeholder="如 gpt-4o-mini, Qwen2.5-7B" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="BASE URL" prop="base_url">
              <el-input v-model="form.base_url" placeholder="如 http://127.0.0.1:8000/v1" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="API 模式" prop="api_mode">
              <el-select v-model="form.api_mode" style="width: 100%">
                <el-option label="Chat Completions" value="chat_completions" />
                <el-option label="Responses" value="responses" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="Temperature">
              <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Max Tokens">
              <el-input-number v-model="form.max_tokens" :min="1" :max="16384" :step="100" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Top P">
              <el-input-number v-model="form.top_p" :min="0" :max="1" :step="0.1" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="API Key 环境变量">
          <el-input v-model="form.api_key_env" placeholder="如 OPENAI_API_KEY，留空则不验证" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="重试次数">
              <el-input-number v-model="form.retry_count" :min="0" :max="10" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="启用">
              <el-switch v-model="form.enabled" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="空 Key 允许">
              <el-switch v-model="form.allow_empty_key" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="额外参数" prop="extra_body_text">
          <el-input
            v-model="form.extra_body_text"
            type="textarea"
            :rows="3"
            placeholder='可选 JSON。推理模型(如 Qwen3)关闭思维链: {"chat_template_kwargs": {"enable_thinking": false}}'
            class="mono-input"
          />
          <div style="margin-top: 4px">
            <el-button link type="primary" size="small" @click="fillNoThink">
              填入「禁用思维链」模板
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="">
          <el-checkbox v-model="form.is_default">设为默认配置</el-checkbox>
          <el-checkbox v-model="form.debug_log" style="margin-left: 16px">调试日志</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogOpen = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="testOpen" title="连接测试结果" width="400px">
      <div v-if="testResult">
        <p><el-tag :type="testResult.success ? 'success' : 'danger'">
          {{ testResult.success ? '成功' : '失败' }}
        </el-tag></p>
        <p>耗时: {{ testResult.elapsed_ms.toFixed(0) }}ms</p>
        <p style="white-space: pre-wrap; word-break: break-all">{{ testResult.message }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { llmConfigsApi, type LLMConfig, type TestResult } from '@/api/llmConfigs'

const loading = ref(false)
const rows = ref<LLMConfig[]>([])
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
  model: 'gpt-4o-mini',
  provider: 'openai',
  enabled: true,
  api_key_env: '' as string | null,
  allow_empty_key: false,
  base_url: '' as string | null,
  api_mode: 'chat_completions' as string,
  temperature: 0.2,
  max_tokens: 2000,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
  retry_count: 2,
  debug_log: false,
  extra_body_text: '',
  is_default: false,
})
const form = reactive(defaultForm())

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  extra_body_text: [
    {
      validator: (_r: unknown, v: string, cb: (e?: Error) => void) => {
        if (!v || !v.trim()) return cb()
        try { JSON.parse(v); cb() } catch { cb(new Error('额外参数必须是合法 JSON')) }
      },
      trigger: 'blur',
    },
  ],
}

function fillNoThink() {
  form.extra_body_text = JSON.stringify({ chat_template_kwargs: { enable_thinking: false } }, null, 2)
}

const testOpen = ref(false)
const testResult = ref<TestResult | null>(null)
const testing = reactive<Record<number, boolean>>({})

async function reload() {
  loading.value = true
  try {
    const { data } = await llmConfigsApi.list({ page: page.value, page_size: pageSize.value })
    rows.value = data.items
    total.value = data.total
  } catch { ElMessage.error('加载失败') } finally { loading.value = false }
}

function onCreate() {
  editing.value = false
  editingId.value = 0
  Object.assign(form, defaultForm())
  dialogOpen.value = true
}

function onEdit(row: LLMConfig) {
  editing.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    model: row.model,
    provider: row.provider,
    enabled: row.enabled,
    api_key_env: row.api_key_env || '',
    allow_empty_key: row.allow_empty_key,
    base_url: row.base_url || '',
    api_mode: row.api_mode,
    temperature: row.temperature,
    max_tokens: row.max_tokens,
    top_p: row.top_p,
    frequency_penalty: row.frequency_penalty,
    presence_penalty: row.presence_penalty,
    retry_count: row.retry_count,
    debug_log: row.debug_log,
    extra_body_text: row.extra_body ? JSON.stringify(row.extra_body, null, 2) : '',
    is_default: row.is_default,
  })
  dialogOpen.value = true
}

function onClose() { formRef.value?.resetFields() }

async function onSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const { extra_body_text, ...rest } = form
    const payload = {
      ...rest,
      api_key_env: form.api_key_env || null,
      base_url: form.base_url || null,
      extra_body: extra_body_text.trim() ? JSON.parse(extra_body_text) : null,
    }
    if (editing.value) {
      await llmConfigsApi.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await llmConfigsApi.create(payload)
      ElMessage.success('已创建')
    }
    dialogOpen.value = false
    reload()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally { saving.value = false }
}

async function onTest(row: LLMConfig) {
  testing[row.id] = true
  try {
    const { data } = await llmConfigsApi.test(row.id, 'test')
    testResult.value = data
    testOpen.value = true
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '测试失败')
  } finally { testing[row.id] = false }
}

async function onDelete(row: LLMConfig) {
  try {
    await ElMessageBox.confirm(`删除配置 "${row.name}"？`, '确认', { type: 'warning' })
    await llmConfigsApi.delete(row.id)
    ElMessage.success('已删除')
    reload()
  } catch { /* cancelled */ }
}

onMounted(reload)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.mono-input :deep(textarea) { font-family: 'Courier New', monospace; font-size: 13px; }
</style>
