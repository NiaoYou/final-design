export type MergedSummaryPayload = {
  available: boolean
  merged_sample_count?: number
  merged_feature_count?: number
  merge_strategy?: string
  missing_ratio_after_merge?: number
  batch_count?: number
  batch_id_unique_values?: unknown[]
  raw_merge_report?: Record<string, unknown>
}

export type BatchCorrectionReport = {
  baseline_batch_correction?: {
    method_id?: string
    implementation_note?: string
    what_it_is?: string
    assumptions?: string[]
    limitations?: string[]
    [key: string]: unknown
  }
  strict_combat?: {
    /** "implemented" | "not_implemented" */
    status?: string
    note?: string
    library?: string
    reference?: string
    [key: string]: unknown
  }
  [key: string]: unknown
}

/** 与 backend batch_correction_metrics.json 对齐，允许额外字段 */
export type BatchCorrectionMetrics = {
  batch_centroid_separation_pc12_before?: number | null
  batch_centroid_separation_pc12_after?: number | null
  delta_batch_centroid_separation?: number | null
  silhouette_batch_id_pc12_before?: number | null
  silhouette_batch_id_pc12_after?: number | null
  delta_silhouette_batch_id?: number | null
  silhouette_group_label_pc12_before?: number | null
  silhouette_group_label_pc12_after?: number | null
  delta_silhouette_group_label?: number | null
  heuristic_mixing_improved_by_centroid?: boolean | null
  heuristic_group_overdistorted?: boolean | null
  heuristic_mixing_notes?: string[]
  [key: string]: unknown
}

export type MergedFilesResponse = {
  files: Array<{
    name: string
    size_bytes: number
    download_path: string
    purpose: string
  }>
  download_base: string
}

export type PcaAfterPayload = {
  explained_variance_ratio?: number[]
  components?: unknown
  [key: string]: unknown
}

export type EvaluationSummary = {
  available: boolean
  schema_version?: string
  methods_order: string[]
  methods_display_order: string[]
  methods_display_names: Record<string, string>
  before_method_for_plot?: string
  after_method_for_plot?: string
  before_method_for_plot_display?: string
  after_method_for_plot_display?: string
  note?: string
}

export type EvaluationTableResponse = {
  rows: Array<Record<string, string | null | undefined>>
}

export type EvaluationPcaPayload = {
  method?: string
  n_components?: number
  explained_variance_ratio?: number[]
  coords?: number[][]
  sample_index?: string[]
  [key: string]: unknown
}

export type EvaluationFilesResponse = {
  files: Array<{
    name: string
    size_bytes: number
    download_path: string
    purpose: string
  }>
  download_base: string
}

// ==============================
// imputation 评估类型
// ==============================
export type ImputationMethodStats = {
  method: string
  rmse_mean: number
  rmse_std: number
  mae_mean: number
  mae_std: number
  nrmse_mean: number
  nrmse_std: number
}

export type ImputationEvalSummary = {
  available: boolean
  schema_version?: string
  best_method?: string
  ranking_by_rmse?: string[]
  methods?: Record<string, ImputationMethodStats>
  config?: {
    mask_ratio?: number
    n_repeats?: number
    knn_k?: number
    n_samples?: number
    n_features?: number
  }
  notes?: string[]
}

export type ImputationEvalFeatureRmse = {
  methods?: string[]
  n_features?: number
  feature_rmse_by_method?: Record<string, (number | null)[]>
}

// ==============================
// 差异代谢物分析类型
// ==============================
export type DiffFeature = {
  feature: string
  mean_group1: number | null
  mean_group2: number | null
  log2fc: number | null
  tstat: number | null
  pvalue: number | null
  qvalue: number | null
  neg_log10_pvalue: number | null
  neg_log10_qvalue: number | null
  label: 'up' | 'down' | 'ns'
  // 代谢物注释字段（由 annotation_service 注入）
  metabolite_name?: string | null
  formula?: string | null
  ion_mz?: number | null
  hmdb_ids?: string[]
  kegg_ids?: string[]
  hmdb_url?: string | null
  kegg_url?: string | null
}

// 特征注释类型
export type AnnotatedFeature = {
  feature_col: string
  ion_idx: number
  ion_mz: number
  metabolite_name: string | null
  formula: string | null
  ion_mode: string | null
  hmdb_ids: string[]
  kegg_ids: string[]
  hmdb_url: string | null
  kegg_url: string | null
}

export type AnnotationSummary = {
  available: boolean
  schema_version?: string
  n_features: number
  n_annotated: number
  n_with_kegg: number
  n_with_hmdb: number
  coverage_pct: number
}

export type AnnotationFeaturesResponse = {
  total: number
  offset: number
  limit: number
  features: AnnotatedFeature[]
}

export type DiffAnalysisSummary = {
  n_total: number
  n_sig_up: number
  n_sig_down: number
  n_sig: number
  n_ns: number
}

export type DiffAnalysisResult = {
  group1: string
  group2: string
  n_group1: number
  n_group2: number
  n_features: number
  fc_threshold: number
  pvalue_threshold: number
  use_fdr: boolean
  elapsed_seconds: number
  features: DiffFeature[]
  summary: DiffAnalysisSummary
}

export type DiffGroupsResponse = {
  groups: string[]
  count: number
}
