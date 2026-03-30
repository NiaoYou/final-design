import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/benchmark'
import type {
  BatchCorrectionMetrics,
  BatchCorrectionReport,
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
  const loading = ref(false)
  const error = ref<string | null>(null)
  const loadedAt = ref(0)

  async function loadAll() {
    loading.value = true
    error.value = null
    try {
      summary.value = await api.fetchMergedSummary()
      const [rep, met, fil, pca] = await Promise.all([
        api.fetchBatchCorrectionReport().catch(() => null),
        api.fetchBatchCorrectionMetrics().catch(() => null),
        api.fetchMergedFiles().catch(() => null),
        api.fetchPcaAfterJson().catch(() => null),
      ])
      report.value = rep
      metrics.value = met
      files.value = fil
      pcaAfter.value = pca
      loadedAt.value = Date.now()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  return {
    summary,
    report,
    metrics,
    files,
    pcaAfter,
    loading,
    error,
    loadedAt,
    loadAll,
  }
})
