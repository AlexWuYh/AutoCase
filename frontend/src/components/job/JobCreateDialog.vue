<template>
  <el-dialog
    v-model="visible"
    title="新建自动用例生成"
    width="520px"
    top="8vh"
    @open="onOpen"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="需求集" prop="group_id">
        <el-select
          v-model="form.group_id"
          filterable
          placeholder="选择要生成用例的需求集"
          style="width: 100%"
          :disabled="lockGroup"
          @change="onGroupChange"
        >
          <el-option
            v-for="g in groups"
            :key="g.id"
            :label="`${g.name}（${g.requirement_count} 个功能点）`"
            :value="g.id"
          />
        </el-select>
        <div v-if="selectedGroup" class="hint">
          将为该需求集的 <b>{{ selectedGroup.requirement_count }}</b> 个功能点批量生成测试用例
        </div>
      </el-form-item>

      <el-form-item v-if="isAdmin" label="LLM 配置">
        <el-select v-model="form.llm_config_id" clearable placeholder="默认使用系统默认配置" style="width: 100%">
          <el-option
            v-for="c in llmConfigs"
            :key="c.id"
            :label="c.name + (c.is_default ? '（默认）' : '')"
            :value="c.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="isAdmin" label="Prompt 模板">
        <el-select v-model="form.prompt_id" clearable placeholder="默认使用系统默认模板" style="width: 100%">
          <el-option
            v-for="p in prompts"
            :key="p.id"
            :label="p.name + (p.is_default ? '（默认）' : '')"
            :value="p.id"
          />
        </el-select>
      </el-form-item>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="生成任务将在后台异步执行，可在任务列表查看进度与结果。"
      />
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">开始生成</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { jobsApi } from '@/api/jobs'
import { requirementsApi, type RequirementGroup } from '@/api/requirements'
import { llmConfigsApi, type LLMConfig } from '@/api/llmConfigs'
import { promptsApi, type SystemPrompt } from '@/api/prompts'
import { useAuthStore } from '@/stores/auth'

interface Props {
  modelValue: boolean
  /** 预选需求集（详情页入口传入），传了则锁定不可改 */
  presetGroupId?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'created', jobId: number): void
}>()

const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})
const lockGroup = computed(() => !!props.presetGroupId)

const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = ref<{ group_id: number | null; llm_config_id: number | null; prompt_id: number | null }>({
  group_id: null,
  llm_config_id: null,
  prompt_id: null,
})

const groups = ref<RequirementGroup[]>([])
const llmConfigs = ref<LLMConfig[]>([])
const prompts = ref<SystemPrompt[]>([])

const rules: FormRules = {
  group_id: [{ required: true, message: '请选择需求集', trigger: 'change' }],
}

const selectedGroup = computed(() => groups.value.find((g) => g.id === form.value.group_id) || null)

async function onOpen() {
  form.value = { group_id: props.presetGroupId ?? null, llm_config_id: null, prompt_id: null }
  // Load groups
  const { data } = await requirementsApi.listGroups({ page_size: 200 })
  groups.value = data.items
  // Admin extras
  if (isAdmin.value) {
    try {
      const [cfgs, pmts] = await Promise.all([
        llmConfigsApi.list({ page_size: 100 }),
        promptsApi.list({ page_size: 100 }),
      ])
      llmConfigs.value = cfgs.data.items
      prompts.value = pmts.data.items
      form.value.llm_config_id = cfgs.data.items.find((c) => c.is_default)?.id ?? null
      form.value.prompt_id = pmts.data.items.find((p) => p.is_default)?.id ?? null
    } catch {
      /* non-fatal: backend falls back to defaults */
    }
  }
}

function onGroupChange() {
  formRef.value?.validateField('group_id').catch(() => {})
}

async function onSubmit() {
  if (!formRef.value) return
  const ok = await formRef.value.validate().catch(() => false)
  if (!ok) return
  if (selectedGroup.value && selectedGroup.value.requirement_count === 0) {
    ElMessage.warning('该需求集还没有功能点，请先添加需求')
    return
  }
  submitting.value = true
  try {
    const { data } = await jobsApi.create({
      group_id: form.value.group_id as number,
      llm_config_id: form.value.llm_config_id ?? undefined,
      prompt_id: form.value.prompt_id ?? undefined,
    })
    ElMessage.success('生成任务已创建')
    emit('created', data.id)
    visible.value = false
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '创建任务失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--ac-text-secondary, #6b7684);
}
</style>
