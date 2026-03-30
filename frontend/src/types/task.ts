export type ApiTaskStatus = 'pending' | 'preprocess_done' | 'impute_done' | 'batch_done' | 'eval_done' | 'error' | string

export type ApiTask = {
  id: number
  task_name: string
  status: ApiTaskStatus
  created_at: string
  updated_at: string
  error_message?: string | null
}

export type TaskCreateBody = {
  task_id: number
  task_name?: string
  preprocess_config: Record<string, unknown>
  imputation_config: Record<string, unknown>
  batch_config: Record<string, unknown>
  evaluation_config: Record<string, unknown>
}
