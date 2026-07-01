<template>
  <div class="ac-page api-keys">
    <el-card>
      <template #header>
        <div class="ac-toolbar">
          <span>API 密钥</span>
          <el-button type="primary" :icon="Plus" @click="onCreate">新建密钥</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
        <template #title>
          API 密钥用于第三方工具（飞书 / 微信机器人、脚本等）免登录调用生成接口。
          调用时在请求头携带 <code>X-API-Key: 你的密钥</code>。密钥仅在创建时完整显示一次，请妥善保存。
        </template>
      </el-alert>

      <el-table v-loading="loading" :data="rows" empty-text="暂无 API 密钥">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="密钥" width="200">
          <template #default="{ row }">
            <code>{{ row.prefix }}••••••••</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="最后使用" width="180">
          <template #default="{ row }">{{ row.last_used_at ? fmt(row.last_used_at) : '从未' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="onRevoke(row)">吊销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建密钥 -->
    <el-dialog v-model="createOpen" title="新建 API 密钥" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称（用途备注）" prop="name">
          <el-input v-model="form.name" placeholder="如：飞书机器人 / 自动化脚本" autofocus />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="onSubmit">创建</el-button>
      </template>
    </el-dialog>

    <!-- 显示一次性明文密钥 -->
    <el-dialog v-model="showKeyOpen" title="密钥创建成功" width="520px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon title="请立即复制并保存，此密钥仅显示这一次，关闭后无法再次查看。" style="margin-bottom: 12px" />
      <div class="key-box">
        <code class="key-text">{{ newKey }}</code>
        <el-button :icon="CopyDocument" @click="copyKey">复制</el-button>
      </div>
      <el-divider content-position="left">调用示例</el-divider>
      <pre class="curl">curl -X POST {{ apiBase }}/open/generate \
  -H "X-API-Key: {{ newKey }}" \
  -H "Content-Type: application/json" \
  -d '{"cases":[{"module":"登录","feature":"登录成功","description":"正常登录"}]}'</pre>
      <template #footer>
        <el-button type="primary" @click="showKeyOpen = false">我已保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, CopyDocument } from '@element-plus/icons-vue'
import { apiKeysApi, type ApiKey } from '@/api/apiKeys'

const apiBase = (import.meta.env.VITE_API_BASE || '/api/v1')

const loading = ref(false)
const rows = ref<ApiKey[]>([])

const createOpen = ref(false)
const creating = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ name: '' })
const rules: FormRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

const showKeyOpen = ref(false)
const newKey = ref('')

async function reload() {
  loading.value = true
  try {
    const { data } = await apiKeysApi.list()
    rows.value = data
  } catch { ElMessage.error('加载失败') } finally { loading.value = false }
}

function onCreate() {
  form.name = ''
  createOpen.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  creating.value = true
  try {
    const { data } = await apiKeysApi.create(form.name)
    newKey.value = data.key
    createOpen.value = false
    showKeyOpen.value = true
    reload()
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '创建失败')
  } finally { creating.value = false }
}

async function copyKey() {
  try {
    await navigator.clipboard.writeText(newKey.value)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择复制')
  }
}

async function onRevoke(row: ApiKey) {
  try {
    await ElMessageBox.confirm(`确定吊销密钥 "${row.name}"？使用该密钥的调用将立即失效。`, '吊销确认', {
      type: 'warning', confirmButtonText: '吊销',
    })
    await apiKeysApi.revoke(row.id)
    ElMessage.success('已吊销')
    reload()
  } catch { /* cancelled */ }
}

function fmt(iso: string) { return new Date(iso).toLocaleString('zh-CN', { hour12: false }) }

onMounted(reload)
</script>

<style scoped>
.key-box { display: flex; gap: 10px; align-items: center; }
.key-text {
  flex: 1;
  background: #f6f8fa;
  border: 1px solid var(--ac-border, #eaecef);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  word-break: break-all;
}
.curl {
  background: #1f2933;
  color: #e6edf3;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
code { background: #f2fbf8; color: #0d9668; padding: 1px 6px; border-radius: 4px; }
</style>
