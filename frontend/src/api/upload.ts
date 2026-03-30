import { http } from '@/utils/http'
import type { AxiosProgressEvent } from 'axios'

export type UploadResponse = {
  task_id: number
  dataset_id: number
  original_filename: string
  sample_count: number
  feature_count: number
  preview: Record<string, unknown>[]
}

/**
 * 当前后端 /api/upload 为「长表 long」CSV/xlsx 及列名配置。
 * 多 sheet 原始 Excel 完整自检接口：TODO 待接后端（页面保留结构与状态区）。
 */
export type PreviewResponse = {
  dataset_id: number
  preview: Record<string, unknown>[]
}

export async function fetchDatasetPreview(taskId: number): Promise<PreviewResponse> {
  const { data } = await http.get<PreviewResponse>(`/api/datasets/${taskId}/preview`)
  return data
}

export async function uploadLongTable(
  file: File,
  fields: {
    task_name?: string
    feature_column: string
    sample_column: string
    value_column: string
    batch_column: string
    group_column: string
    data_format?: string
  },
  onProgress?: (pct: number) => void,
): Promise<UploadResponse> {
  const fd = new FormData()
  fd.append('file', file)
  if (fields.task_name) fd.append('task_name', fields.task_name)
  fd.append('data_format', fields.data_format ?? 'long')
  fd.append('feature_column', fields.feature_column)
  fd.append('sample_column', fields.sample_column)
  fd.append('value_column', fields.value_column)
  fd.append('batch_column', fields.batch_column)
  fd.append('group_column', fields.group_column)

  const { data } = await http.post<UploadResponse>('/api/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e: AxiosProgressEvent) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return data
}
