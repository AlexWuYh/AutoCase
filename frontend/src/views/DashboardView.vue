<template>
  <div class="ac-page dashboard">
    <div class="page-head">
      <h2>概览</h2>
      <p>LLM 自动生成测试用例平台</p>
    </div>

    <el-row :gutter="16">
      <el-col v-for="stat in stats" :key="stat.label" :xs="12" :sm="12" :md="6">
        <div class="stat-card" :class="{ clickable: !!stat.link }" @click="stat.link && router.push(stat.link)">
          <div class="stat-icon" :style="{ background: stat.bg }">
            <el-icon :size="22"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ loading ? '—' : stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card style="margin-top:18px">
      <template #header>
        <div class="ac-toolbar">
          <span>最近生成任务</span>
          <el-button link type="primary" @click="router.push('/jobs')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentJobs" empty-text="暂无任务">
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column prop="group_name" label="需求集" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="110">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">{{ row.finished }} / {{ row.total }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { Document, MagicStick, User, Setting } from '@element-plus/icons-vue'
import { requirementsApi } from '@/api/requirements'
import { jobsApi, type GenerationJob } from '@/api/jobs'
import { usersApi } from '@/api/users'
import { llmConfigsApi } from '@/api/llmConfigs'
import { useAuthStore } from '@/stores/auth'
import StatusTag from '@/components/common/StatusTag.vue'

const auth = useAuthStore()
const router = useRouter()

const loading = ref(true)
const recentJobs = ref<GenerationJob[]>([])

interface Stat { label: string; value: string; icon: unknown; bg: string; link?: string }
const stats = reactive<Stat[]>([
  { label: '需求集', value: '—', icon: markRaw(Document), bg: 'linear-gradient(135deg,#10b981,#059669)', link: '/requirement-groups' },
  { label: '生成任务', value: '—', icon: markRaw(MagicStick), bg: 'linear-gradient(135deg,#3b82f6,#2563eb)', link: '/jobs' },
  ...(auth.isAdmin
    ? [
        { label: '用户数', value: '—', icon: markRaw(User), bg: 'linear-gradient(135deg,#f59e0b,#d97706)', link: '/users' } as Stat,
        { label: 'LLM 配置', value: '—', icon: markRaw(Setting), bg: 'linear-gradient(135deg,#8b5cf6,#7c3aed)', link: '/llm-configs' } as Stat,
      ]
    : []),
])

async function fetchData() {
  loading.value = true
  try {
    const [groups, jobs] = await Promise.all([
      requirementsApi.listGroups({ page_size: 1 }),
      jobsApi.list({ page_size: 5 }),
    ])
    stats[0].value = String(groups.data.total)
    stats[1].value = String(jobs.data.total)
    recentJobs.value = jobs.data.items
    if (auth.isAdmin) {
      const [users, cfgs] = await Promise.all([
        usersApi.list({ page_size: 1 }),
        llmConfigsApi.list({ page_size: 1 }),
      ])
      stats[2].value = String(users.data.total)
      stats[3].value = String(cfgs.data.total)
    }
  } catch { /* ignore */ } finally { loading.value = false }
}

function fmt(iso: string) { return new Date(iso).toLocaleString('zh-CN', { hour12: false }) }

onMounted(fetchData)
</script>

<style scoped>
.page-head { margin-bottom: 18px; }
.page-head h2 { margin: 0 0 4px; font-size: 22px; color: #1f2933; }
.page-head p { margin: 0; color: #6b7684; font-size: 13px; }

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border: 1px solid var(--ac-border, #eaecef);
  border-radius: 12px;
  padding: 18px 20px;
  box-shadow: var(--ac-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.stat-card.clickable { cursor: pointer; }
.stat-card.clickable:hover { transform: translateY(-2px); box-shadow: var(--ac-shadow-hover); }
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value { font-size: 26px; font-weight: 700; color: #1f2933; line-height: 1.2; }
.stat-label { font-size: 13px; color: #6b7684; margin-top: 2px; }
</style>
