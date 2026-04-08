import { http } from '@/utils/http'
import type {
  AnnotationFeaturesResponse,
  AnnotationSummary,
  BatchCorrectionMetrics,
  BatchCorrectionReport,
  DiffAnalysisResult,
  DiffGroupsResponse,
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
    const { data } = await http.get<PcaAfterPayload>('/api/benchmark/merged/batch-correction/pca-after')
    return data
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

// ==============================
// imputation 评估（Mask-then-Impute）只读 API
// ==============================

export async function fetchImputationEvalSummary() {
  try {
    const { data } = await http.get('/api/benchmark/merged/imputation-eval/summary')
    return data as import('@/types/benchmark').ImputationEvalSummary
  } catch {
    return null
  }
}

// ==============================
// 差异代谢物分析 API
// ==============================

export async function fetchDiffGroups(): Promise<DiffGroupsResponse> {
  const { data } = await http.get<DiffGroupsResponse>('/api/benchmark/merged/diff-analysis/groups')
  return data
}

export async function fetchDiffAnalysis(
  group1: string,
  group2: string,
  fcThreshold = 1.0,
  pvalueThreshold = 0.05,
  useFdr = true,
): Promise<DiffAnalysisResult> {
  const params = new URLSearchParams({
    group1,
    group2,
    fc_threshold: String(fcThreshold),
    pvalue_threshold: String(pvalueThreshold),
    use_fdr: String(useFdr),
  })
  const { data } = await http.get<DiffAnalysisResult>(
    `/api/benchmark/merged/diff-analysis/run?${params}`
  )
  return data
}

// ==============================
// 特征注释 API
// ==============================

export async function fetchAnnotationSummary(): Promise<AnnotationSummary | null> {
  try {
    const { data } = await http.get<AnnotationSummary>('/api/benchmark/merged/annotation/summary')
    return data
  } catch {
    return null
  }
}

export async function fetchAnnotationFeatures(
  offset = 0,
  limit = 100,
  search?: string,
): Promise<AnnotationFeaturesResponse | null> {
  try {
    const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
    if (search) params.set('search', search)
    const { data } = await http.get<AnnotationFeaturesResponse>(
      `/api/benchmark/merged/annotation/features?${params}`
    )
    return data
  } catch {
    return null
  }
}

export async function fetchImputationEvalFeatureRmse() {
  try {
    const { data } = await http.get('/api/benchmark/merged/imputation-eval/feature-rmse')
    return data as import('@/types/benchmark').ImputationEvalFeatureRmse
  } catch {
    return null
  }
}

// ==============================
// 通路富集分析 API
// ==============================

export interface PathwayItem {
  pathway_id: string
  pathway_name: string
  hits: number
  pathway_size: number
  background_size: number
  sig_size: number
  rich_factor: number
  gene_ratio: string
  bg_ratio: string
  pvalue: number
  qvalue: number
  hit_cpd_ids: string[]
}

export interface NetworkNode {
  id: string
  name: string
  category: number       // 0=代谢物, 1=通路
  symbolSize: number
  value: number
  label: { show: boolean; fontSize?: number }
  _meta: Record<string, any>
}

export interface NetworkEdge {
  source: string
  target: string
  lineStyle: { opacity: number; width: number }
}

export interface PathwayEnrichmentResult {
  available: boolean
  reason?: string
  group1?: string
  group2?: string
  fc_threshold?: number
  pvalue_threshold?: number
  use_fdr?: boolean
  n_sig_features?: number
  n_sig_features_total?: number
  n_bg_features?: number
  n_pathways_tested?: number
  n_sig_pathways?: number
  pathways: PathwayItem[]
  network: {
    nodes: NetworkNode[]
    edges: NetworkEdge[]
    categories: { name: string }[]
  }
}

export async function fetchPathwayEnrichment(
  group1: string,
  group2: string,
  fcThreshold = 1.0,
  pvalueThreshold = 0.05,
  useFdr = true,
  topN = 20,
): Promise<PathwayEnrichmentResult> {
  const params = new URLSearchParams({
    group1,
    group2,
    fc_threshold: String(fcThreshold),
    pvalue_threshold: String(pvalueThreshold),
    use_fdr: String(useFdr),
    top_n: String(topN),
  })
  const { data } = await http.get<PathwayEnrichmentResult>(
    `/api/benchmark/merged/pathway-enrichment?${params}`,
  )
  return data
}
