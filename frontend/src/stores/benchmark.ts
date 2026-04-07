import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/benchmark'
import type {
  BatchCorrectionMetrics,
  BatchCorrectionReport,
  EvaluationFilesResponse,
  EvaluationPcaPayload,
  EvaluationSummary,
  EvaluationTableResponse,
  ImputationEvalFeatureRmse,
  ImputationEvalSummary,
  MergedFilesResponse,
  MergedSummaryPayload,
  PcaAfterPayload,
} from '@/types/benchmark'

export const useBenchmarkStore = defineStore('benchmark', () => {
  const summary = ref<MergedSummaryPayload | null>(null)
  const report = ref<BatchCorrectionReport | null>(null)
  const metrics = ref<BatchCorrectionMetrics | null>(null)
  const files = ref<MergedFilesResponse | null>(null)
  const pcaAfter = ref<PcaAfterPayload | null>(null)
  const evaluationSummary = ref<EvaluationSummary | null>(null)
  const evaluationTable = ref<EvaluationTableResponse | null>(null)
  const evaluationPcas = ref<Record<string, EvaluationPcaPayload | null>>({})
  const evaluationFiles = ref<EvaluationFilesResponse | null>(null)
  // 缺失值填充评估
  const imputationEvalSummary = ref<ImputationEvalSummary | null>(null)
  const imputationEvalFeatureRmse = ref<ImputationEvalFeatureRmse | null>(null)

  const loading = ref(false)
  const error = ref<string | null>(null)
  const loadedAt = ref(0)

  async function loadAll() {
    loading.value = true
    error.value = null
    try {
      summary.value = await api.fetchMergedSummary()
      const [rep, met, fil, pca, es, et, ef, ies, ief] = await Promise.all([
        api.fetchBatchCorrectionReport().catch(() => null),
        api.fetchBatchCorrectionMetrics().catch(() => null),
        api.fetchMergedFiles().catch(() => null),
        api.fetchPcaAfterJson().catch(() => null),
        api.fetchEvaluationSummary().catch(() => null),
        api.fetchEvaluationTable().catch(() => null),
        api.fetchEvaluationFiles().catch(() => null),
        api.fetchImputationEvalSummary().catch(() => null),
        api.fetchImputationEvalFeatureRmse().catch(() => null),
      ])
      report.value = rep
      metrics.value = met
      files.value = fil
      pcaAfter.value = pca
      evaluationSummary.value = es
      evaluationTable.value = et
      evaluationFiles.value = ef
      imputationEvalSummary.value = ies
      imputationEvalFeatureRmse.value = ief
      loadedAt.value = Date.now()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function loadEvaluationPca(method: string) {
    if (!method) return
    try {
      evaluationPcas.value[method] = await api.fetchEvaluationMethodPca(method)
    } catch {
      evaluationPcas.value[method] = null
    }
  }

  return {
    summary,
    report,
    metrics,
    files,
    pcaAfter,
    evaluationSummary,
    evaluationTable,
    evaluationPcas,
    evaluationFiles,
    imputationEvalSummary,
    imputationEvalFeatureRmse,
    loading,
    error,
    loadedAt,
    loadAll,
    loadEvaluationPca,
  }
})
