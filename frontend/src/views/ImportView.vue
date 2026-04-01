<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadLongTable, fetchDatasetPreview, type PreviewResponse } from '@/api/upload'
import { useTaskStore } from '@/stores/task'
import type { UploadResponse } from '@/api/upload'

/** TODO 待接后端：GET 列出 benchmark 目录或已注册数据集 */
const benchmarkDatasets = ref([
  { id: 'merged-demo', label: 'benchmark_merged（本地已合并产物）', hint: '可直接打开「结果展示」查看 API 数据' },
  { id: 'raw-xlsx-todo', label: '原始多 sheet xlsx（示例槽位）', hint: '完整 sheet 解析与可用性报告接口待接' },
])

const router = useRouter()
const taskStore = useTaskStore()

const file = ref<File | null>(null)
const uploadPct = ref(0)
const uploading = ref(false)
const lastResult = ref<UploadResponse | null>(null)
const preview = ref<PreviewResponse | null>(null)
const previewLoading = ref(false)

const form = ref({
  task_name: '',
  feature_column: 'ionIdx',
  sample_column: 'sample_id',
  value_column: 'intensity',
  batch_column: 'batch_id',
  group_column: 'group_label',
})

const sheetProbe = ref<{
  sheets: string[]
  row_estimate?: string
  preprocess_ready: boolean
  impute_ready: boolean
  batch_ready: boolean
  downstream_ready: boolean
} | null>(null)

function onFileChange(f: File | null) {
  file.value = f
  lastResult.value = null
  preview.value = null
  sheetProbe.value = null
}

async function doUpload() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  uploadPct.value = 0
  try {
    const res = await uploadLongTable(file.value, form.value, (p) => {
      uploadPct.value = p
    })
    lastResult.value = res
    if (typeof res.task_id === 'number') taskStore.taskId = res.task_id
    ElMessage.success('上传成功，已绑定 task_id（可用于参数配置页）')
    sheetProbe.value = {
      sheets: ['(当前 /api/upload 不返回 sheet 列表，待接多 sheet 接口)'],
      row_estimate: `样本数 ${res.sample_count ?? '—'} · 特征数 ${res.feature_count ?? '—'}`,
      preprocess_ready: true,
      impute_ready: true,
      batch_ready: true,
      downstream_ready: true,
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : String(e))
  } finally {
    uploading.value = false
  }
}

async function loadPreview() {
  const tid = lastResult.value?.task_id
  if (tid == null) return
  previewLoading.value = true
  try {
    preview.value = await fetchDatasetPreview(tid)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : String(e))
  } finally {
    previewLoading.value = false
  }
}

function goTask() {
  void router.push('/task')
}

function goResult() {
  void router.push('/result')
}
</script>

<template>
  <div class="page-container">
    <p class="page-title">数据导入</p>
    <p class="page-sub">
      当前后端 <code>POST /api/upload</code> 面向 <strong>长表（long）格式</strong> 及列名映射。多 sheet 原始 Excel 的完整解析、sheet 级检查与可用性 JSON
      <strong>待接后端</strong>；下方已预留展示区域。
    </p>

    <div class="card-panel">
      <h3 class="h3">上传数据文件</h3>
      <el-form label-width="120px" class="form">
        <el-form-item label="任务名称">
          <el-input v-model="form.task_name" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="特征列">
          <el-input v-model="form.feature_column" />
        </el-form-item>
        <el-form-item label="样本列">
          <el-input v-model="form.sample_column" />
        </el-form-item>
        <el-form-item label="数值列">
          <el-input v-model="form.value_column" />
        </el-form-item>
        <el-form-item label="批次列">
          <el-input v-model="form.batch_column" />
        </el-form-item>
        <el-form-item label="分组列">
          <el-input v-model="form.group_column" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="(f) => onFileChange(f.raw!)"
            :on-remove="() => onFileChange(null)"
            accept=".csv,.xlsx,.xls"
          >
            <el-button type="primary">选取文件</el-button>
          </el-upload>
          <el-progress v-if="uploading" :percentage="uploadPct" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="uploading" @click="doUpload">上传并创建任务</el-button>
          <el-button v-if="lastResult?.task_id != null" :loading="previewLoading" @click="loadPreview">拉取预览</el-button>
          <el-button @click="goTask">前往参数配置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="lastResult" class="card-panel">
      <h3 class="h3">上传结果</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="task_id">{{ lastResult.task_id }}</el-descriptions-item>
        <el-descriptions-item label="dataset_id">{{ lastResult.dataset_id }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ lastResult.original_filename }}</el-descriptions-item>
        <el-descriptions-item label="规模"
          >样本 {{ lastResult.sample_count }} · 特征 {{ lastResult.feature_count }}</el-descriptions-item
        >
      </el-descriptions>
    </div>

    <div v-if="preview" class="card-panel">
      <h3 class="h3">数据预览（前 20 行）</h3>
      <el-table :data="preview.preview" height="280" stripe border size="small">
        <el-table-column
          v-for="col in preview.preview.length ? Object.keys(preview.preview[0]) : []"
          :key="col"
          :prop="col"
          :label="col"
          min-width="120"
          show-overflow-tooltip
        />
      </el-table>
    </div>

    <div class="card-panel">
      <h3 class="h3">Benchmark / 已有数据集（占位）</h3>
      <el-alert
        type="info"
        :closable="false"
        class="mb"
        title="TODO 待接后端：列出可导入 benchmark 或服务器端路径"
      />
      <el-table :data="benchmarkDatasets" size="small" border>
        <el-table-column prop="label" label="数据集" />
        <el-table-column prop="hint" label="说明" />
        <el-table-column label="操作" width="160">
          <template #default>
            <el-button link type="primary" @click="goResult">打开 merged 结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card-panel">
      <h3 class="h3">Sheet 与可用性检查（预留）</h3>
      <template v-if="sheetProbe">
        <p class="muted">检测到的 sheets（占位 / 待接真实接口）：</p>
        <el-tag v-for="s in sheetProbe.sheets" :key="s" class="tag">{{ s }}</el-tag>
        <el-descriptions class="mt" :column="1" border>
          <el-descriptions-item label="样本/特征概览">{{ sheetProbe.row_estimate }}</el-descriptions-item>
          <el-descriptions-item label="可运行预处理">{{ sheetProbe.preprocess_ready ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="可运行填充">{{ sheetProbe.impute_ready ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="可运行批次校正">{{ sheetProbe.batch_ready ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="可运行下游分析">{{ sheetProbe.downstream_ready ? '是' : '否' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <el-empty v-else description="上传文件后将显示占位状态；真实多 sheet 报告待接后端" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.h3 {
  margin: 0 0 1rem;
  font-size: 1.05rem;
}

.form {
  max-width: 640px;
}

.mb {
  margin-bottom: 0.75rem;
}

.muted {
  color: var(--app-muted);
  font-size: 0.9rem;
}

.tag {
  margin: 0 0.35rem 0.35rem 0;
}

.mt {
  margin-top: 0.75rem;
}
</style>
