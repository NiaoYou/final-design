import { http } from '@/utils/http'
import type {
  BatchCorrectionMetrics,
  BatchCorrectionReport,
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
