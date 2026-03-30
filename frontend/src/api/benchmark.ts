import { http } from '@/utils/http'
import type {
  BatchCorrectionMetrics,
  BatchCorrectionReport,
  EvaluationPcaPayload,
  EvaluationFilesResponse,
  EvaluationSummary,
  EvaluationTableResponse,
  MergedFilesResponse,
  MergedSummaryPayload,
  PcaAfterPayload,
} from '@/types/benchmark'

export async function fetchMergedSummary(): Promise<MergedSummaryPayload> {
  const { data } = await http.get<MergedSummaryPayload>('/api/benchmark/merged/summary')
  return data
}

export async function fetchBatchCorrectionReport(): Promise<BatchCorrectionReport> {
  const { data } = await http.get<BatchCorrectionReport>('/api/benchmark/merged/batch-correction/report')
  return data
}

export async function fetchBatchCorrectionMetrics(): Promise<BatchCorrectionMetrics> {
  const { data } = await http.get<BatchCorrectionMetrics>('/api/benchmark/merged/batch-correction/metrics')
  return data
}

export async function fetchMergedFiles(): Promise<MergedFilesResponse> {
  const { data } = await http.get<MergedFilesResponse>('/api/benchmark/merged/files')
  return data
}

export function pcaBeforeAfterImageUrl(cacheBust?: string): string {
  const u = '/api/benchmark/merged/assets/pca_before_vs_after.png'
  return cacheBust ? `${u}?t=${cacheBust}` : u
}

export function mergedDownloadUrl(filename: string): string {
  return `/api/benchmark/merged/download/${encodeURIComponent(filename)}`
}

export async function fetchPcaAfterJson(): Promise<PcaAfterPayload | null> {
  try {
    const { data } = await http.get<string>(mergedDownloadUrl('pca_after_correction.json'), {
      responseType: 'text',
    })
    return JSON.parse(data) as PcaAfterPayload
  } catch {
    return null
  }
}

// ==============================
// evaluation（方法对比实验）只读 API
// ==============================

export async function fetchEvaluationSummary(): Promise<EvaluationSummary> {
  const { data } = await http.get<EvaluationSummary>('/api/benchmark/merged/evaluation/summary')
  return data
}

export async function fetchEvaluationTable(): Promise<EvaluationTableResponse> {
  const { data } = await http.get<EvaluationTableResponse>('/api/benchmark/merged/evaluation/table')
  return data
}

export function evaluationPcaImageUrl(cacheBust?: string): string {
  const u = '/api/benchmark/merged/evaluation/pca-image'
  return cacheBust ? `${u}?t=${cacheBust}` : u
}

export async function fetchEvaluationMethodPca(method: string): Promise<EvaluationPcaPayload> {
  const { data } = await http.get<EvaluationPcaPayload>(`/api/benchmark/merged/evaluation/pca/${encodeURIComponent(method)}`)
  return data
}

export async function fetchEvaluationFiles(): Promise<EvaluationFilesResponse> {
  const { data } = await http.get<EvaluationFilesResponse>('/api/benchmark/merged/evaluation/files')
  return data
}

export function evaluationDownloadUrl(filename: string): string {
  return `/api/benchmark/merged/evaluation/download/${encodeURIComponent(filename)}`
}
