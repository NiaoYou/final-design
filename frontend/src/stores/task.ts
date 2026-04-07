import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as taskApi from '@/api/task'
import type { TaskCreateBody } from '@/types/task'

export type PipelineStepState = 'wait' | 'process' | 'success' | 'error'

export type UiRunPhase = 'idle' | 'pending' | 'running' | 'success' | 'failed'

export const useTaskStore = defineStore('task', () => {
  const taskId = ref<number | null>(null)
  const runPhase = ref<UiRunPhase>('idle')
  const runMessage = ref<string | null>(null)

  const preprocess = ref({
    normalization: 'standardize',
    log_transform: true,
    max_missing_rate: 0.5,
  })

  const imputation = ref({
    method: 'mean' as 'mean' | 'median' | 'knn',
    knn_k: 5,
  })

  /** UI：none | baseline_location_scale | combat；与 benchmark merged 的 baseline 文案区分 */
  const batchUi = ref({
    method: 'none' as 'none' | 'baseline_location_scale' | 'combat',
  })

  const stepPreprocess = ref<PipelineStepState>('wait')
  const stepImpute = ref<PipelineStepState>('wait')
  const stepBatch = ref<PipelineStepState>('wait')
  // 下方三步在 benchmark merged 管线中完成，此处作为"已就绪"展示用
  const stepImputationEval = ref<PipelineStepState>('success')
  const stepDiffAnalysis = ref<PipelineStepState>('success')
  const stepAnnotation = ref<PipelineStepState>('success')

  const steps = computed(() => [
    { key: 'pre',     label: '预处理',     state: stepPreprocess.value },
    { key: 'imp',     label: '缺失值填充', state: stepImpute.value },
    { key: 'bat',     label: '批次校正',   state: stepBatch.value },
    { key: 'imp_eval',label: '填充评估',   state: stepImputationEval.value },
    { key: 'diff',    label: '差异分析',   state: stepDiffAnalysis.value },
    { key: 'anno',    label: '特征注释',   state: stepAnnotation.value },
  ])

  function resetSteps() {
    stepPreprocess.value = 'wait'
    stepImpute.value = 'wait'
    stepBatch.value = 'wait'
    // 填充评估/差异分析/注释已在 merged 管线完成，重置时保持 success
    stepImputationEval.value = 'success'
    stepDiffAnalysis.value = 'success'
    stepAnnotation.value = 'success'
  }

  function buildTaskBody(): TaskCreateBody | null {
    if (taskId.value == null) return null

    return {
      task_id: taskId.value,
      preprocess_config: {
        normalization: preprocess.value.normalization,
        log_transform: preprocess.value.log_transform,
        max_missing_rate: preprocess.value.max_missing_rate,
      },
      imputation_config: {
        method: imputation.value.method,
        ...(imputation.value.method === 'knn' ? { knn_k: imputation.value.knn_k } : {}),
      },
      batch_config: {
        method: batchUi.value.method === 'combat' ? 'combat' : 'none',
      },
      evaluation_config: {},
    }
  }

  /**
   * 运行通用任务链：后端 batch 当前仅实现 method=combat；none 时跳过 batch 步骤。
   * baseline_location_scale 为 merged 管线能力，此处不伪造 HTTP 实现。
   */
  async function runPipeline() {
    const body = buildTaskBody()
    if (!body) {
      runPhase.value = 'failed'
      runMessage.value = '请先填写有效的 task_id（通常来自数据导入上传返回值）。'
      return
    }

    if (batchUi.value.method === 'baseline_location_scale') {
      runPhase.value = 'failed'
      runMessage.value =
        'baseline 批次校正（per_feature_batch_location_scale_baseline）已在 benchmark merged 流程中实现，请打开「结果展示」查看真实产出；此处通用任务链不重复调用该实现。'
      return
    }

    runPhase.value = 'running'
    runMessage.value = null
    resetSteps()
    try {
      await taskApi.saveTaskConfigs(body)

      stepPreprocess.value = 'process'
      await taskApi.runPreprocess(body.task_id)
      stepPreprocess.value = 'success'

      stepImpute.value = 'process'
      await taskApi.runImpute(body.task_id)
      stepImpute.value = 'success'

      if (batchUi.value.method === 'combat') {
        stepBatch.value = 'process'
        await taskApi.runBatchCorrect(body.task_id)
        stepBatch.value = 'success'
      } else {
        stepBatch.value = 'success'
      }

      runPhase.value = 'success'
      runMessage.value = '流程已执行完毕（批次步骤按配置跳过或已运行简化 combat）。'
    } catch (e) {
      runPhase.value = 'failed'
      const msg = e instanceof Error ? e.message : String(e)
      runMessage.value = msg
      if (stepPreprocess.value === 'process') stepPreprocess.value = 'error'
      else if (stepImpute.value === 'process') stepImpute.value = 'error'
      else if (stepBatch.value === 'process') stepBatch.value = 'error'
    }
  }

  return {
    taskId,
    runPhase,
    runMessage,
    preprocess,
    imputation,
    batchUi,
    steps,
    resetSteps,
    buildTaskBody,
    runPipeline,
  }
})
