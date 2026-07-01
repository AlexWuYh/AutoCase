<template>
  <div class="group-detail">
    <el-page-header @back="router.push('/requirement-groups')">
      <template #content>
        <span>{{ group?.name || '加载中...' }}</span>
        <el-tag v-if="group" size="small" style="margin-left: 8px">
          {{ group.requirement_count }} 条功能点
        </el-tag>
      </template>
      <template #extra>
        <el-button :icon="Download" @click="onExportYaml">导出 YAML</el-button>
        <el-button :icon="UploadFilled" @click="importOpen = true">导入 YAML</el-button>
        <el-button :icon="Plus" @click="onBatchAdd">批量添加</el-button>
        <el-button :icon="Plus" @click="onCreate">新增功能点</el-button>
        <el-button :icon="MagicStick" type="primary" @click="genOpen = true">自动生成用例</el-button>
      </template>
    </el-page-header>

    <el-card v-if="group" style="margin-top: 16px">
      <template #header>
        <span>{{ group.description || '无描述' }}</span>
        <span class="owner-label">创建者: {{ group.owner_username }}</span>
      </template>

      <div class="filters">
        <el-input
          v-model="search"
          placeholder="搜索模块/功能/描述"
          clearable
          :prefix-icon="Search"
          style="width: 320px"
          @keyup.enter="reload"
        />
        <el-button @click="reload">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="rows" stripe empty-text="暂无功能点">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="req-detail">
              <p><b>所属模块：</b>{{ row.module }}</p>
              <p><b>功能名称：</b>{{ row.feature }}</p>
              <p><b>描述：</b>{{ row.description || '无' }}</p>
              <p>
                <b>关键词：</b>
                <el-tag v-for="kw in row.keywords" :key="kw" size="small" style="margin-right: 4px">{{ kw }}</el-tag>
                <span v-if="!row.keywords?.length" style="color: #909399">无</span>
              </p>
            </div>
          </template>
        </el-table-column>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="module" label="所属模块" min-width="140" show-overflow-tooltip />
        <el-table-column prop="feature" label="功能名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="keywords" label="关键词" width="160">
          <template #default="{ row }">
            <el-tag
              v-for="kw in row.keywords"
              :key="kw"
              size="small"
              style="margin-right: 4px"
            >{{ kw }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Edit" @click="onEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="onDelete(row)" />
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="reload"
        @size-change="reload"
      />
    </el-card>

    <RequirementFormDialog v-model="formOpen" :requirement="editingReq" :group-id="groupId" @saved="onAfterSave" />

    <RequirementImportDialog
      v-if="groupId"
      v-model="importOpen"
      :group-id="groupId"
      @imported="reload"
    />

    <el-dialog v-model="batchOpen" title="批量添加功能点" width="700px" @close="onBatchClose">
      <el-form ref="batchFormRef" :model="batchForm" label-width="80px">
        <el-form-item
          v-for="(item, idx) in batchForm.items"
          :key="idx"
          :label="`#${idx + 1}`"
          :prop="`items.${idx}.module`"
          :rules="[{ required: true, message: '请输入模块', trigger: 'blur' }]"
        >
          <div class="batch-row">
            <el-input v-model="item.module" placeholder="所属模块" style="width: 160px" />
            <el-input v-model="item.feature" placeholder="功能名称" style="width: 160px" />
            <el-input v-model="item.description" placeholder="描述" style="flex: 1" />
            <el-input v-model="item.keywords" placeholder="关键词(逗号分隔)" style="width: 150px" />
            <el-button type="danger" :icon="Close" circle size="small" @click="onRemoveItem(idx)" />
          </div>
        </el-form-item>
      </el-form>
      <div style="margin-bottom: 12px">
        <el-button :icon="Plus" @click="onAddItems(1)">添加一行</el-button>
        <el-button :icon="Plus" @click="onAddItems(5)">添加五行</el-button>
      </div>
      <div class="batch-footer">
        <el-radio-group v-model="batchMode">
          <el-radio value="append">追加（保留已有）</el-radio>
          <el-radio value="replace">替换（清除已有后导入）</el-radio>
        </el-radio-group>
        <div>
          <el-button @click="batchOpen = false">取消</el-button>
          <el-button :loading="savingBatch" @click="onSaveBatch(false)">保存</el-button>
          <el-button type="primary" :loading="savingBatch" @click="onSaveBatch(true)">保存并生成</el-button>
        </div>
      </div>
    </el-dialog>

    <JobCreateDialog v-model="genOpen" :preset-group-id="groupId" @created="onGenerated" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Plus, Search, Edit, Delete, Download, UploadFilled, Close, MagicStick,
} from '@element-plus/icons-vue'
import { requirementsApi, type Requirement, type RequirementGroup } from '@/api/requirements'
import RequirementFormDialog from '@/components/requirement/RequirementFormDialog.vue'
import RequirementImportDialog from '@/components/requirement/RequirementImportDialog.vue'
import JobCreateDialog from '@/components/job/JobCreateDialog.vue'

const route = useRoute()
const router = useRouter()

const groupId = computed(() => Number(route.params.id))
const group = ref<RequirementGroup | null>(null)
const loading = ref(false)
const rows = ref<Requirement[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const search = ref('')

// Edit / create single
const formOpen = ref(false)
const editingReq = ref<Requirement | null>(null)

// Auto-generation dialog
const genOpen = ref(false)

// Import
const importOpen = ref(false)

// Batch add
const batchOpen = ref(false)
const batchMode = ref<'append' | 'replace'>('append')
const savingBatch = ref(false)
const batchFormRef = ref<FormInstance>()
type BatchItem = { module: string; feature: string; description: string; keywords: string }
const batchForm = reactive({
  items: [{ module: '', feature: '', description: '', keywords: '' }] as BatchItem[],
})

async function fetchGroup() {
  try {
    const { data } = await requirementsApi.getGroup(groupId.value)
    group.value = data
  } catch {
    ElMessage.error('需求集不存在或无权访问')
    router.push('/requirement-groups')
  }
}

async function reload() {
  if (!groupId.value) return
  loading.value = true
  try {
    const { data } = await requirementsApi.listRequirements(groupId.value, {
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

function onCreate() {
  editingReq.value = null
  formOpen.value = true
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

async function onAfterSave(payload?: { thenGenerate: boolean }) {
  await fetchGroup()  // refresh requirement_count in header
  reload()
  if (payload?.thenGenerate) genOpen.value = true
}

function onEdit(row: Requirement) {
  editingReq.value = row
  formOpen.value = true
}

async function onDelete(row: Requirement) {
  try {
    await ElMessageBox.confirm(`删除功能点 "${row.feature}"？`, '确认', { type: 'warning' })
    await requirementsApi.deleteRequirement(row.id)
    ElMessage.success('已删除')
    reload()
  } catch {
    // cancelled
  }
}

async function onExportYaml() {
  try {
    const resp = await requirementsApi.exportYaml(groupId.value)
    const blob = new Blob([resp.data], { type: 'application/x-yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${group.value?.name || 'export'}.yaml`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出')
  } catch {
    ElMessage.error('导出失败')
  }
}

// ─── Batch add ──────────────────────────────────────────────────────────

function onBatchAdd() {
  batchForm.items = [{ module: '', feature: '', description: '', keywords: '' }]
  batchMode.value = 'append'
  batchOpen.value = true
}

function onAddItems(n = 1) {
  for (let i = 0; i < n; i++) {
    batchForm.items.push({ module: '', feature: '', description: '', keywords: '' })
  }
}

function onRemoveItem(idx: number) {
  if (batchForm.items.length <= 1) return
  batchForm.items.splice(idx, 1)
}

function onBatchClose() {
  batchFormRef.value?.resetFields()
}

function splitKeywords(text: string): string[] {
  return text.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
}

async function onSaveBatch(thenGenerate = false) {
  savingBatch.value = true
  try {
    const items = batchForm.items.filter((it) => it.module.trim())
    if (items.length === 0) {
      ElMessage.warning('请至少填写一个功能点的模块名称')
      savingBatch.value = false
      return
    }
    await requirementsApi.batchCreate(
      groupId.value,
      items.map((it) => ({
        module: it.module,
        feature: it.feature || it.module,
        description: it.description,
        keywords: splitKeywords(it.keywords),
      })),
      batchMode.value,
    )
    ElMessage.success(`已添加 ${items.length} 条功能点`)
    batchOpen.value = false
    await fetchGroup()
    reload()
    if (thenGenerate) genOpen.value = true
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally {
    savingBatch.value = false
  }
}

onMounted(async () => {
  await fetchGroup()
  reload()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.owner-label { float: right; color: #909399; font-size: 12px; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.batch-row { display: flex; gap: 6px; align-items: center; }
.batch-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.req-detail { padding: 8px 24px; line-height: 1.9; }
.req-detail p { margin: 0; }
</style>
