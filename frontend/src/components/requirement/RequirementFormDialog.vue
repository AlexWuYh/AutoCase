<template>
  <el-dialog
    v-model="visible"
    :title="editing ? '编辑功能点' : '新建功能点'"
    width="560px"
    @close="onClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent
    >
      <el-form-item label="所属模块" prop="module">
        <el-input v-model="form.module" placeholder="如: 系统设置 / 业务设置 / 机构场地" autofocus />
      </el-form-item>
      <el-form-item label="功能名称" prop="feature">
        <el-input v-model="form.feature" placeholder="如: 机构场地管理-新增场地" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="功能点详细描述，可包含校验规则、权限等" />
      </el-form-item>
      <el-form-item label="关键词" prop="keywords">
        <el-select
          v-model="form.keywords"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入后回车添加"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button :loading="saving" @click="onSave(false)">保存</el-button>
      <el-button v-if="!editing" type="primary" :loading="saving" @click="onSave(true)">保存并生成</el-button>
      <el-button v-else type="primary" :loading="saving" @click="onSave(false)">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { requirementsApi, type Requirement } from '@/api/requirements'

interface Props {
  modelValue: boolean
  requirement: Requirement | null
  groupId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved', payload?: { thenGenerate: boolean }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const editing = computed(() => !!props.requirement)
const formRef = ref<FormInstance>()
const saving = ref(false)

const form = reactive({
  module: '',
  feature: '',
  description: '',
  keywords: [] as string[],
})

const rules: FormRules = {
  module: [{ required: true, message: '请输入所属模块', trigger: 'blur' }],
  feature: [{ required: true, message: '请输入功能名称', trigger: 'blur' }],
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      if (props.requirement) {
        form.module = props.requirement.module
        form.feature = props.requirement.feature
        form.description = props.requirement.description
        form.keywords = [...(props.requirement.keywords || [])]
      } else {
        form.module = ''
        form.feature = ''
        form.description = ''
        form.keywords = []
      }
    }
  },
)

function onClose() {
  formRef.value?.resetFields()
}

async function onSave(thenGenerate = false) {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value && props.requirement) {
      await requirementsApi.update(props.requirement.id, {
        module: form.module,
        feature: form.feature,
        description: form.description,
        keywords: form.keywords,
      })
      ElMessage.success('已更新')
    } else {
      // 新建：通过 batchCreate 以 append 模式真实写入一条需求
      await requirementsApi.batchCreate(
        props.groupId,
        [{
          module: form.module,
          feature: form.feature,
          description: form.description,
          keywords: form.keywords,
        }],
        'append',
      )
      ElMessage.success('已新增')
    }
    emit('saved', { thenGenerate })
    visible.value = false
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    ElMessage.error(msg || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>
