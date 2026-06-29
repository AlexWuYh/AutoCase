<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>需求集</span></template>
          <div class="metric">--</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>生成任务</span></template>
          <div class="metric">--</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>测试用例</span></template>
          <div class="metric">--</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>LLM 配置</span></template>
          <div class="metric">--</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header><span>欢迎使用 AutoCase 平台</span></template>
      <p>这是一个 LLM 自动生成测试用例的工具平台。当前为阶段 1 基础设施搭建完成版本。</p>
      <p style="color: #909399">
        阶段 1 已完成：后端 FastAPI 骨架、前端 Vue 3 骨架、Docker Compose 部署。
      </p>
      <p style="color: #909399">
        阶段 2-6 将陆续交付：认证、需求管理、LLM 配置、生成任务、导出。
      </p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// Dashboard view - placeholder for Phase 1.
</script>

<style scoped>
.metric { font-size: 32px; font-weight: 600; color: #409eff; }
</style>
