import { http } from '@/utils/http'
import type { ApiTask, TaskCreateBody } from '@/types/task'

export async function listTasks(): Promise<ApiTask[]> {
  const { data } = await http.get<ApiTask[]>('/api/tasks')
  return data
}

export async function getTask(id: number): Promise<ApiTask> {
  const { data } = await http.get<ApiTask>(`/api/tasks/${id}`)
  return data
}

export async function saveTaskConfigs(body: TaskCreateBody): Promise<ApiTask> {
  const { data } = await http.post<ApiTask>('/api/tasks', body)
  return data
}

export async function runPreprocess(taskId: number): Promise<Record<string, unknown>> {
  const { data } = await http.post<Record<string, unknown>>(`/api/tasks/${taskId}/preprocess`)
  return data
}

export async function runImpute(taskId: number): Promise<Record<string, unknown>> {
  const { data } = await http.post<Record<string, unknown>>(`/api/tasks/${taskId}/impute`)
  return data
}

export async function runBatchCorrect(taskId: number): Promise<Record<string, unknown>> {
  const { data } = await http.post<Record<string, unknown>>(`/api/tasks/${taskId}/batch-correct`)
  return data
}

export async function runEvaluation(taskId: number): Promise<Record<string, unknown>> {
  const { data } = await http.get<Record<string, unknown>>(`/api/tasks/${taskId}/evaluation`)
  return data
}
