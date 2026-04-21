/**
 * dataset.ts
 * 多数据集通用 API，对应后端 /api/dataset/{dataset}/* 路由
 */
import { http } from '@/utils/http'
import type {
  BatchCorrectionMetrics,
  BatchCorrectionReport,
  EvaluationPcaPayload,
  EvaluationSummary,
  EvaluationTableResponse,
  MergedSummaryPayload,
  PcaAfterPayload,
} from '@/types/benchmark'

export interface DatasetInfo {
  id: string
  label: string
  description: string
  available: boolean
  pipeline_ready: boolean
}

export interface DatasetListResponse {
  datasets: DatasetInfo[]
}

// ──────────────────────────────────────────────────────────────────────────────
// 数据集列表
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetList(): Promise<DatasetListResponse> {
  const { data } = await http.get<DatasetListResponse>('/api/dataset/list')
  return data
}

// ──────────────────────────────────────────────────────────────────────────────
// 数据集核心数据
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetSummary(dataset: string): Promise<MergedSummaryPayload> {
  const { data } = await http.get<MergedSummaryPayload>(`/api/dataset/${dataset}/summary`)
  return data
}

export async function fetchDatasetBatchCorrectionReport(dataset: string): Promise<BatchCorrectionReport | null> {
  try {
    const { data } = await http.get<BatchCorrectionReport>(`/api/dataset/${dataset}/batch-correction/report`)
    return data
  } catch {
    return null
  }
}

export async function fetchDatasetBatchCorrectionMetrics(dataset: string): Promise<BatchCorrectionMetrics | null> {
  try {
    const { data } = await http.get<BatchCorrectionMetrics>(`/api/dataset/${dataset}/batch-correction/metrics`)
    return data
  } catch {
    return null
  }
}

export async function fetchDatasetPcaAfterJson(dataset: string): Promise<PcaAfterPayload | null> {
  try {
    const { data } = await http.get<PcaAfterPayload>(`/api/dataset/${dataset}/batch-correction/pca-after`)
    return data
  } catch {
    return null
  }
}

export function datasetPcaBeforeAfterImageUrl(dataset: string, cacheBust?: string): string {
  const u = `/api/dataset/${dataset}/assets/pca_before_vs_after.png`
  return cacheBust ? `${u}?t=${cacheBust}` : u
}

// ──────────────────────────────────────────────────────────────────────────────
// Evaluation（方法对比）
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetEvaluationSummary(dataset: string): Promise<EvaluationSummary | null> {
  try {
    const { data } = await http.get<EvaluationSummary>(`/api/dataset/${dataset}/evaluation/summary`)
    return data
  } catch {
    return null
  }
}

export async function fetchDatasetEvaluationTable(dataset: string): Promise<EvaluationTableResponse | null> {
  try {
    const { data } = await http.get<EvaluationTableResponse>(`/api/dataset/${dataset}/evaluation/table`)
    return data
  } catch {
    return null
  }
}

export function datasetEvaluationPcaImageUrl(dataset: string, cacheBust?: string): string {
  const u = `/api/dataset/${dataset}/evaluation/pca-image`
  return cacheBust ? `${u}?t=${cacheBust}` : u
}

export async function fetchDatasetEvaluationMethodPca(
  dataset: string,
  method: string,
): Promise<EvaluationPcaPayload | null> {
  try {
    const { data } = await http.get<EvaluationPcaPayload>(
      `/api/dataset/${dataset}/evaluation/pca/${encodeURIComponent(method)}`
    )
    return data
  } catch {
    return null
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 差异分析
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetDiffGroups(dataset: string): Promise<{ groups: string[]; count: number }> {
  const { data } = await http.get<{ groups: string[]; count: number }>(
    `/api/dataset/${dataset}/diff-analysis/groups`
  )
  return data
}

export async function fetchDatasetDiffAnalysis(
  dataset: string,
  group1: string,
  group2: string,
  fcThreshold = 1.0,
  pvalueThreshold = 0.05,
  useFdr = true,
) {
  const params = new URLSearchParams({
    group1,
    group2,
    fc_threshold: String(fcThreshold),
    pvalue_threshold: String(pvalueThreshold),
    use_fdr: String(useFdr),
  })
  const { data } = await http.get(`/api/dataset/${dataset}/diff-analysis/run?${params}`)
  return data
}

// ──────────────────────────────────────────────────────────────────────────────
// 特征注释
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetAnnotationSummary(dataset: string) {
  try {
    const { data } = await http.get(`/api/dataset/${dataset}/annotation/summary`)
    return data as import('@/types/benchmark').AnnotationSummary & { annotation_source?: string }
  } catch {
    return null
  }
}

export async function fetchDatasetAnnotationFeatures(
  dataset: string,
  offset = 0,
  limit = 100,
  search?: string,
) {
  try {
    const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
    if (search) params.set('search', search)
    const { data } = await http.get(`/api/dataset/${dataset}/annotation/features?${params}`)
    return data as import('@/types/benchmark').AnnotationFeaturesResponse
  } catch {
    return null
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 通路富集分析
// ──────────────────────────────────────────────────────────────────────────────

export async function fetchDatasetPathwayEnrichment(
  dataset: string,
  group1: string,
  group2: string,
  fcThreshold = 1.0,
  pvalueThreshold = 0.05,
  useFdr = true,
  topN = 20,
) {
  const params = new URLSearchParams({
    group1,
    group2,
    fc_threshold: String(fcThreshold),
    pvalue_threshold: String(pvalueThreshold),
    use_fdr: String(useFdr),
    top_n: String(topN),
  })
  const { data } = await http.get(`/api/dataset/${dataset}/pathway-enrichment?${params}`)
  return data
}

// ──────────────────────────────────────────────────────────────────────────────
// MetaKG 子图
// ──────────────────────────────────────────────────────────────────────────────

export interface DatasetMetaKGParams {
  node_types?: string
  relation_types?: string
  seed_only?: boolean
}

export async function fetchDatasetMetakgSubgraph(
  dataset: string,
  params?: DatasetMetaKGParams,
) {
  const qp = new URLSearchParams()
  if (params?.node_types) qp.set('node_types', params.node_types)
  if (params?.relation_types) qp.set('relation_types', params.relation_types)
  if (params?.seed_only != null) qp.set('seed_only', String(params.seed_only))
  const qs = qp.toString()
  const { data } = await http.get(`/api/dataset/${dataset}/metakg-subgraph${qs ? '?' + qs : ''}`)
  return data
}

// ──────────────────────────────────────────────────────────────────────────────
// 文件下载
// ──────────────────────────────────────────────────────────────────────────────

export function datasetDownloadUrl(dataset: string, filename: string): string {
  return `/api/dataset/${dataset}/download/${encodeURIComponent(filename)}`
}
