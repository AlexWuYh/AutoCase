<template>
  <div class="ac-page jobs">
    <el-card>
      <template #header>
        <div class="ac-toolbar">
          <span>自动用例生成</span>
          <el-button type="primary" :icon="MagicStick" @click="createOpen = true">新建生成</el-button>
        </div>
      </template>

      <div class="ac-filters">
        <el-select v-model="statusFilter" placeholder="状态过滤" clearable style="width: 140px" @change="reload">
          <el-option label="待处理" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="canceled" />
        </el-select>
        <el-button :icon="Refresh" @click="reload">刷新</el-button>
        <el-tag v-if="polling" type="warning" effect="plain" size="small" style="align-self:center">
          有任务进行中，自动刷新…
        </el-tag>
      </div>

      <el-table v-loading="loading" :data="rows" empty-text="暂无生成任务，点击右上角「新建生成」开始">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="group_name" label="需求集" min-width="150" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="row.percent"
              :stroke-width="12"
              :status="row.status === 'failed' ? 'exception' : (row.status === 'success' ? 'success' : undefined)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="提交人" width="110" />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'success'" size="small" type="success" :loading="exporting[row.id]" @click="onExport(row, 'xlsx')">导出</el-button>
            <el-button v-if="['pending','running'].includes(row.status)" size="small" type="danger" @click="onCancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[10,20,50]" :total="total"
        layout="total, sizes, prev, pager, next" style="margin-top:16px; justify-content:flex-end" @current-change="reload" @size-change="reload" />
    </el-card>

    <JobCreateDialog v-model="createOpen" @created="onCreated" />

    <el-drawer v-model="drawerOpen" title="任务详情" size="68%" @close="stopDetailPoll">
      <template v-if="detail">
        <el-descriptions :column="3" border style="margin-bottom:16px">
          <el-descriptions-item label="状态"><StatusTag :status="detail.status" /></el-descriptions-item>
          <el-descriptions-item label="进度">{{ detail.finished }} / {{ detail.total }}</el-descriptions-item>
          <el-descriptions-item label="需求集">{{ detail.group_name }}</el-descriptions-item>
          <el-descriptions-item label="LLM 配置">{{ detail.llm_config_name || '默认' }}</el-descriptions-item>
          <el-descriptions-item label="Prompt">{{ detail.prompt_name || '默认' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmt(detail.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-alert v-if="detail.error" type="error" :title="detail.error" :closable="false" style="margin-bottom:12px" />
        <el-progress
          :percentage="detail.percent"
          :status="detail.status==='failed'?'exception':(detail.status==='success'?'success':undefined)"
          style="margin-bottom:16px"
        />

        <el-table v-loading="casesLoading" :data="caseRows" max-height="46vh" empty-text="暂无用例（任务运行中或未生成）">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="case-detail">
                <p><b>前置条件：</b>{{ row.preconditions || '无' }}</p>
                <p><b>步骤：</b></p>
                <ol><li v-for="(s, i) in row.steps" :key="i">{{ s }}</li></ol>
                <p><b>预期：</b></p>
                <ol><li v-for="(e, i) in row.expected" :key="i">{{ e }}</li></ol>
                <p><b>关键词：</b>{{ row.keywords || '无' }}</p>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="case_id" label="用例ID" width="120" />
          <el-table-column prop="module" label="模块" min-width="120" show-overflow-tooltip />
          <el-table-column prop="name" label="用例名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="priority" label="优先级" width="80" />
          <el-table-column prop="stage" label="阶段" width="120" />
        </el-table>
        <el-pagination v-model:current-page="casePage" v-model:page-size="casePageSize" :total="caseTotal"
          layout="total, prev, pager, next" style="margin-top:12px; justify-content:flex-end" @current-change="loadCases" @size-change="loadCases" />

        <div style="margin-top:16px; display:flex; gap:8px; justify-content:flex-end">
          <el-button v-if="detail.status==='success'" type="success" :loading="exporting[detail.id]" @click="onExportDetail('xlsx')">导出 Excel</el-button>
          <el-button v-if="detail.status==='success'" :loading="exporting[detail.id]" @click="onExportDetail('csv')">导出 CSV</el-button>
          <el-button v-if="['pending','running'].includes(detail.status)" type="danger" @click="onCancelDetail">取消任务</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Refresh } from '@element-plus/icons-vue'
import { jobsApi, type GenerationJob, type TestCase } from '@/api/jobs'
import StatusTag from '@/components/common/StatusTag.vue'
import JobCreateDialog from '@/components/job/JobCreateDialog.vue'

const loading = ref(false)
const rows = ref<GenerationJob[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

const createOpen = ref(false)
const exporting = reactive<Record<number, boolean>>({})

const drawerOpen = ref(false)
const detail = ref<GenerationJob | null>(null)
const caseRows = ref<TestCase[]>([])
const casesLoading = ref(false)
const caseTotal = ref(0)
const casePage = ref(1)
const casePageSize = ref(50)

const jobId = computed(() => detail.value?.id)

// ─── list polling while any job is active ────────────────────────────────
let listTimer: number | undefined
const polling = computed(() => rows.value.some((j) => j.status === 'pending' || j.status === 'running'))

function scheduleListPoll() {
  if (listTimer) return
  listTimer = window.setInterval(async () => {
    if (!polling.value) { stopListPoll(); return }
    await reload(true)
  }, 3000)
}
function stopListPoll() {
  if (listTimer) { clearInterval(listTimer); listTimer = undefined }
}

async function reload(silent = false) {
  if (!silent) loading.value = true
  try {
    const { data } = await jobsApi.list({ page: page.value, page_size: pageSize.value, status: statusFilter.value || undefined })
    rows.value = data.items
    total.value = data.total
    if (polling.value) scheduleListPoll()
    else stopListPoll()
  } catch { if (!silent) ElMessage.error('加载失败') } finally { loading.value = false }
}

// ─── detail polling ──────────────────────────────────────────────────────
let detailTimer: number | undefined
function scheduleDetailPoll() {
  stopDetailPoll()
  detailTimer = window.setInterval(async () => {
    if (!detail.value) return
    const { data } = await jobsApi.get(detail.value.id)
    detail.value = data
    if (['success', 'failed', 'canceled'].includes(data.status)) {
      stopDetailPoll()
      loadCases()
    }
  }, 3000)
}
function stopDetailPoll() {
  if (detailTimer) { clearInterval(detailTimer); detailTimer = undefined }
}

async function loadCases() {
  if (!jobId.value) return
  casesLoading.value = true
  try {
    const { data } = await jobsApi.listCases(jobId.value, { page: casePage.value, page_size: casePageSize.value })
    caseRows.value = data.items
    caseTotal.value = data.total
  } catch { ElMessage.error('加载用例失败') } finally { casesLoading.value = false }
}

async function onDetail(row: GenerationJob) {
  detail.value = row
  drawerOpen.value = true
  casePage.value = 1
  loadCases()
  if (['pending', 'running'].includes(row.status)) scheduleDetailPoll()
}

function onCreated() {
  reload()
  ElMessage.success('任务已进入队列，进度将自动刷新')
}

// ─── export via blob (JWT in header — fixes prior 401) ────────────────────
async function onExport(row: GenerationJob, fmt: 'xlsx' | 'csv') {
  exporting[row.id] = true
  try {
    const resp = await jobsApi.exportBlob(row.id, fmt)
    const blob = new Blob([resp.data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `job_${row.id}_testcases.${fmt}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    ElMessage.success('已开始下载')
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '导出失败')
  } finally { exporting[row.id] = false }
}

function onExportDetail(fmt: 'xlsx' | 'csv') { if (detail.value) onExport(detail.value, fmt) }

async function onCancel(row: GenerationJob) {
  try {
    await ElMessageBox.confirm('确定取消该任务？', '确认', { type: 'warning' })
    await jobsApi.cancel(row.id)
    ElMessage.success('已取消')
    reload()
  } catch { /* cancelled */ }
}

async function onCancelDetail() { if (detail.value) { await onCancel(detail.value); drawerOpen.value = false } }

function fmt(iso: string) { return new Date(iso).toLocaleString('zh-CN', { hour12: false }) }

onMounted(reload)
onUnmounted(() => { stopListPoll(); stopDetailPoll() })
</script>

<style scoped>
.case-detail { padding: 8px 24px; line-height: 1.8; }
.case-detail p { margin: 4px 0; }
.case-detail ol { margin: 4px 0 8px; padding-left: 22px; }
</style>
