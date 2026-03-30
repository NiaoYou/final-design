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
    assumptions?: string[]
    limitations?: string[]
    [key: string]: unknown
  }
  strict_combat?: {
    status?: string
    note?: string
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
