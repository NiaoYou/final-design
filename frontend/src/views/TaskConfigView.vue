<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/task'
import PipelineStepBar from '@/components/PipelineStepBar.vue'

const taskStore = useTaskStore()
const { taskId, preprocess, imputation, batchUi, steps, runPhase, runMessage } = storeToRefs(taskStore)

const phaseTag = computed(() => {
  if (runPhase.value === 'idle') return { type: 'info' as const, text: '待运行' }
  if (runPhase.value === 'pending') return { type: 'warning' as const, text: '等待中' }
  if (runPhase.value === 'running') return { type: 'warning' as const, text: '运行中' }
  if (runPhase.value === 'success') return { type: 'success' as const, text: '成功' }
  return { type: 'danger' as const, text: '失败' }
})

function run() {
  void taskStore.runPipeline().then(() => {
    if (runPhase.value === 'success') ElMessage.success('任务流执行完成')
    else if (runPhase.value === 'failed') ElMessage.error(runMessage.value || '执行失败')
  })
}
</script>

<template>
  <div class="page-container">
    <p class="page-title">参数配置 / 任务运行</p>
    <p class="page-sub">
      与通用 HTTP 任务链（上传 → 预处理 → 填充 → 批次）对应。<strong>benchmark merged 的 baseline 批次校正</strong>在独立管线中实现，详见「结果展示」；此处批次选项中的
      baseline 会提示使用 merged 页面。
    </p>

    <div class="card-panel">
      <h3 class="h3">任务与状态</h3>
      <el-form label-width="140px" class="form-narrow">
        <el-form-item label="task_id">
          <el-input-number
            :min="1"
            :controls="false"
            placeholder="从数据导入页获得"
            :model-value="taskId ?? undefined"
            @update:model-value="(v) => (taskStore.taskId = v ?? null)"
          />
        </el-form-item>
        <el-form-item label="运行状态">
          <el-tag :type="phaseTag.type">{{ phaseTag.text }}</el-tag>
          <span v-if="runMessage" class="run-msg">{{ runMessage }}</span>
        </el-form-item>
      </el-form>
      <PipelineStepBar :steps="steps" />
    </div>

    <div class="card-panel">
      <h3 class="h3">预处理</h3>
      <el-form label-width="160px" class="form-max">
        <el-form-item label="标准化方式">
          <el-select v-model="preprocess.normalization" style="width: 220px">
            <el-option label="standardize（Z-score，后端当前实现）" value="standardize" />
          </el-select>
        </el-form-item>
        <el-form-item label="log transform">
          <el-switch v-model="preprocess.log_transform" />
        </el-form-item>
        <el-form-item label="最大缺失率阈值">
          <el-slider v-model="preprocess.max_missing_rate" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
      </el-form>
    </div>

    <div class="card-panel">
      <h3 class="h3">缺失值填充</h3>
      <el-form label-width="160px">
        <el-form-item label="方法">
          <el-radio-group v-model="imputation.method">
            <el-radio-button label="mean" />
            <el-radio-button label="median" />
            <el-radio-button label="knn" />
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="imputation.method === 'knn'" label="KNN k">
          <el-input-number v-model="imputation.knn_k" :min="1" :max="20" />
        </el-form-item>
      </el-form>
    </div>

    <div class="card-panel">
      <h3 class="h3">批次校正</h3>
      <el-alert
        class="mb"
        type="warning"
        :closable="false"
        show-icon
        title="说明"
        description="当前实现的是 baseline 批次校正（在 benchmark merged 流程中）。通用任务链后端仅提供简化 combat MVP；strict ComBat 未实现。"
      />
      <el-form label-width="200px">
        <el-form-item label="方法">
          <el-radio-group v-model="batchUi.method">
            <el-radio label="none">none（跳过批次 HTTP 步骤）</el-radio>
            <el-radio label="baseline_location_scale">baseline_location_scale（merged 管线，此处不直接调 HTTP）</el-radio>
            <el-radio label="combat">简化 combat（通用任务链当前可跑的后端实现）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="strict ComBat">
          <el-select model-value="" disabled placeholder="未实现" style="width: 240px">
            <el-option label="strict ComBat（empirical Bayes）— 未实现" value="" disabled />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div class="card-panel actions">
      <el-button type="primary" size="large" :loading="runPhase === 'running'" @click="run">保存配置并运行流水线</el-button>
      <p class="hint">
        配置通过 <code>POST /api/tasks</code> 写入；依次调用 preprocess → impute → batch-correct（按选项跳过）。
        完整「一键任务」接口如另有设计，请在代码标注处对接。
      </p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.h3 {
  margin: 0 0 1rem;
  font-size: 1.05rem;
}

.form-narrow {
  max-width: 480px;
}

.form-max {
  max-width: 640px;
}

.mb {
  margin-bottom: 0.75rem;
}

.run-msg {
  margin-left: 0.75rem;
  color: var(--app-muted);
  font-size: 0.88rem;
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
}

.hint {
  margin: 0;
  font-size: 0.85rem;
  color: var(--app-muted);
  max-width: 720px;
  line-height: 1.55;
}
</style>
