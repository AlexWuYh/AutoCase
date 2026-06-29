<template>
  <div class="dashboard">
    <h4 style="margin-bottom:16px">AutoCase 平台</h4>
    <el-row :gutter="16">
      <el-col v-for="stat in stats" :key="stat.label" :span="6">
        <el-card shadow="hover" @click="stat.link ? router.push(stat.link) : undefined" :class="{ clickable: !!stat.link }">
          <template #header><span>{{ stat.label }}</span></template>
          <div class="metric" :style="{ color: stat.color }">{{ loading ? '--' : stat.value }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card v-if="recentJobs.length > 0" style="margin-top:16px">
      <template #header><span>最近任务</span></template>
      <el-table :data="recentJobs" size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="group_name" label="需求集" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="进度" width="120">
          <template #default="{ row }">{{ row.finished }}/{{ row.total }}</template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { requirementsApi } from '@/api/requirements'
import { jobsApi, type GenerationJob } from '@/api/jobs'
import { usersApi } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import StatusTag from '@/components/common/StatusTag.vue'

const auth = useAuthStore()
const router = useRouter()

const loading = ref(true)
const recentJobs = ref<GenerationJob[]>([])

const stats = reactive([
  { label: '需求集', value: '--', color: '#409EFF', link: '/requirement-groups' },
  { label: '生成任务', value: '--', color: '#E6A23C', link: '/jobs' },
  { label: auth.isAdmin ? '用户数' : '', value: '--', color: '#67C23A', link: '/users' as string | undefined },
  { label: 'LLM 配置', value: '--', color: '#F56C6C', link: '/llm-configs' },
].filter(s => s.label))

async function fetch() {
  loading.value = true
  try {
    const [groups, jobs] = await Promise.all([
      requirementsApi.listGroups({ page_size: 1 }),
      jobsApi.list({ page_size: 5 }),
    ])
    stats[0].value = String(groups.data.total)
    const jobTotal = jobs.data.total
    stats[1].value = String(jobTotal)
    recentJobs.value = jobs.data.items

    if (auth.isAdmin) {
      const users = await usersApi.list({ page_size: 1 })
      stats[2].value = String(users.data.total)
    }
  } catch { /* ignore */ } finally { loading.value = false }
}

function fmt(iso: string) { return new Date(iso).toLocaleString('zh-CN', { hour12: false }) }

onMounted(fetch)
</script>

<style scoped>
.clickable { cursor: pointer; }
.clickable:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.metric { font-size: 32px; font-weight: 600; }
</style>
