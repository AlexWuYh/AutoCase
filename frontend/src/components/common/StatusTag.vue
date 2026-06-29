<template>
  <el-tag :type="type" size="small">{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const type = computed(() => {
  const m: Record<string, string> = {
    pending: 'info', running: 'warning', success: 'success', failed: 'danger', canceled: 'info',
  }
  return m[props.status] || 'info'
})

const label = computed(() => {
  const m: Record<string, string> = {
    pending: '待处理', running: '运行中', success: '已完成', failed: '失败', canceled: '已取消',
  }
  return m[props.status] || props.status
})
</script>
