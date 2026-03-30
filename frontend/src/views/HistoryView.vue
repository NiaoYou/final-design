<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listTasks } from '@/api/task'
import type { ApiTask } from '@/types/task'
import { useTaskStore } from '@/stores/task'

/** 若后端扩展历史字段（方法名等），在此映射；当前列表来自真实 GET /api/tasks */
const router = useRouter()
const taskStore = useTaskStore()
const loading = ref(false)
const tasks = ref<ApiTask[]>([])

async function load() {
  loading.value = true
  try {
    tasks.value = await listTasks()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : String(e))
    // TODO 待接后端：分页、筛选、与 merged 离线任务统一编号
    tasks.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})

function methodLabel(_t: ApiTask) {
  return '见任务配置 / CLI'
}

function openResult(t: ApiTask) {
  taskStore.taskId = t.id
  void router.push({ path: '/result', query: { task: String(t.id) } })
}

function statusType(s: string) {
  if (s === 'error') return 'danger'
  if (s.includes('done')) return 'success'
  return 'info'
}
</script>

<template>
  <div class="page-container">
    <p class="page-title">历史任务</p>
    <p class="page-sub">
      列表数据来自 <code>GET /api/tasks</code>。与 benchmark merged 离线产物无 task 关联时，请直接打开「结果展示」。
    </p>

    <div class="card-panel">
      <div class="toolbar">
        <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
      </div>
      <el-table :data="tasks" stripe border v-loading="loading">
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="task_name" label="任务名/数据集" min-width="160" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="方法" width="140">
          <template #default="{ row }">
            {{ methodLabel(row) }}
          </template>
        </el-table-column>
        <el-table-column label="结果入口" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openResult(row)">打开仪表盘</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !tasks.length" description="暂无任务记录" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.toolbar {
  margin-bottom: 0.75rem;
}
</style>
