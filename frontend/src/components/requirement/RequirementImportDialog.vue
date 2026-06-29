<template>
  <el-dialog v-model="visible" title="导入 YAML" width="600px" @close="onClose">
    <el-tabs v-model="tab">
      <el-tab-pane label="粘贴文本" name="text">
        <el-input
          v-model="yamlText"
          type="textarea"
          :rows="12"
          placeholder="粘贴 YAML 内容，格式与 CLI 输入文件一致..."
          class="mono-input"
        />
      </el-tab-pane>
      <el-tab-pane label="上传文件" name="file">
        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".yaml,.yml"
          :on-change="onFileChange"
        >
          <el-icon :size="40"><Document /></el-icon>
          <div class="upload-text">拖拽 YAML 文件到此处或 <em>点击选择</em></div>
          <template #tip>
            <div class="upload-tip">仅支持 .yaml / .yml 文件</div>
          </template>
        </el-upload>
      </el-tab-pane>
    </el-tabs>

    <div class="import-footer">
      <el-radio-group v-model="mode">
        <el-radio value="append">追加（保留已有）</el-radio>
        <el-radio value="replace">替换（清除已有后导入）</el-radio>
      </el-radio-group>
      <div style="display: flex; gap: 8px">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="onImport">开始导入</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { requirementsApi } from '@/api/requirements'

interface Props {
  modelValue: boolean
  groupId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'imported'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const tab = ref('text')
const yamlText = ref('')
const selectedFile = ref<File | null>(null)
const mode = ref<'append' | 'replace'>('append')
const importing = ref(false)

function onFileChange(file: UploadFile) {
  selectedFile.value = file.raw || null
}

function onClose() {
  yamlText.value = ''
  selectedFile.value = null
  tab.value = 'text'
}

async function onImport() {
  importing.value = true
  try {
    let resp
    if (tab.value === 'file' && selectedFile.value) {
      resp = await requirementsApi.importYamlFile(props.groupId, selectedFile.value, mode.value)
    } else if (tab.value === 'text' && yamlText.value.trim()) {
      resp = await requirementsApi.importYaml(props.groupId, yamlText.value, mode.value)
    } else {
      ElMessage.warning('请提供 YAML 内容')
      importing.value = false
      return
    }
    ElMessage.success(`成功导入 ${resp.data.imported} 条功能点`)
    emit('imported')
    visible.value = false
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '导入失败')
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.mono-input :deep(textarea) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
.import-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}
.upload-text { color: #909399; font-size: 13px; }
.upload-tip { color: #c0c4cc; font-size: 12px; }
</style>
