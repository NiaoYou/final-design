<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

type MethodStats = {
  method: string
  rmse_mean: number
  rmse_std: number
  mae_mean: number
  mae_std: number
  nrmse_mean: number
  nrmse_std: number
}

type EvalSummary = {
  available: boolean
  best_method?: string
  ranking_by_rmse?: string[]
  methods?: Record<string, MethodStats>
  config?: {
    mask_ratio?: number
    n_repeats?: number
    knn_k?: number
    ae_epochs?: number
    ae_hidden?: number[]
    n_samples?: number
    n_features?: number
  }
  notes?: string[]
}

type FeatureRmse = {
  methods?: string[]
  n_features?: number
  feature_rmse_by_method?: Record<string, (number | null)[]>
}

const props = defineProps<{
  summary: EvalSummary | null
  featureRmse: FeatureRmse | null
  loading?: boolean
}>()

// ---- 指标表格数据 ----
const tableRows = computed(() => {
  const m = props.summary?.methods
  if (!m) return []
  const ranking = props.summary?.ranking_by_rmse ?? Object.keys(m)
  return ranking.map((key) => ({
    method: key,
    rmse: m[key]?.rmse_mean?.toFixed(4) ?? '—',
    rmse_std: m[key]?.rmse_std?.toFixed(4) ?? '—',
    mae: m[key]?.mae_mean?.toFixed(4) ?? '—',
    nrmse: m[key]?.nrmse_mean?.toFixed(4) ?? '—',
    is_best: key === props.summary?.best_method,
  }))
})

// ---- 箱线图 ----
const boxChartRef = ref<HTMLDivElement | null>(null)
let boxChart: echarts.ECharts | null = null

const METHOD_COLORS: Record<string, string> = {
  mean:        '#3b82f6',
  median:      '#06b6d4',
  knn:         '#10b981',
  autoencoder: '#8b5cf6',
}

/** 需要显示"深度学习"标签的方法 */
const DL_METHODS = new Set(['autoencoder'])

function buildBoxData(values: (number | null)[]): [number, number, number, number, number] | null {
  const nums = values.filter((v): v is number => v !== null && !isNaN(v))
  if (nums.length < 4) return null
  nums.sort((a, b) => a - b)
  const n = nums.length
  const q1 = nums[Math.floor(n * 0.25)]
  const median = nums[Math.floor(n * 0.5)]
  const q3 = nums[Math.floor(n * 0.75)]
  const iqr = q3 - q1
  const lo = Math.max(nums[0], q1 - 1.5 * iqr)
  const hi = Math.min(nums[n - 1], q3 + 1.5 * iqr)
  return [lo, q1, median, q3, hi]
}

function renderBoxChart() {
  const fr = props.featureRmse
  if (!fr?.feature_rmse_by_method || !boxChartRef.value) return
  if (!boxChart) {
    boxChart = echarts.init(boxChartRef.value, undefined, { renderer: 'svg' })
  }

  const methods = fr.methods ?? Object.keys(fr.feature_rmse_by_method)

  // 构建每个方法的箱线图数据（[min, Q1, median, Q3, max] 顺序，ECharts boxplot 要求）
  const boxData = methods.map((m) => {
    const vals = fr.feature_rmse_by_method?.[m] ?? []
    return buildBoxData(vals)
  })

  // 用单 series + category x 轴，保证每个箱子与 x 轴标签严格对齐
  // ECharts boxplot 单 series 时 data[i] 对应 xAxis.data[i]
  // 注意：data 中不能传 null，跳过无数据的方法（用 '-' 占位让 ECharts 忽略）
  const seriesData = boxData.map((d, i) => {
    if (!d) return { value: '-' }  // ECharts boxplot 用字符串 '-' 跳过无效项
    return {
      value: d,
      itemStyle: {
        color: (METHOD_COLORS[methods[i]] ?? '#94a3b8') + '44', // 半透明填充
        borderColor: METHOD_COLORS[methods[i]] ?? '#94a3b8',
        borderWidth: 2,
        opacity: 1,
      },
    }
  })

  boxChart.setOption({
    tooltip: {
      trigger: 'item',
      axisPointer: { type: 'shadow' },
      formatter: (p: any) => {
        const d = Array.isArray(p.data?.value) ? p.data.value : p.data
        if (!d || d.length < 5) return p.name ?? ''
        const fmt = (v: number | undefined) => (v != null && isFinite(v) ? v.toFixed(4) : '—')
        const methodName = methods[p.dataIndex] ?? p.name ?? ''
        return `<b>${methodName}</b><br/>
          min: ${fmt(d[0])}<br/>
          Q1: ${fmt(d[1])}<br/>
          Median: ${fmt(d[2])}<br/>
          Q3: ${fmt(d[3])}<br/>
          max: ${fmt(d[4])}`
      },
    },
    grid: { left: 56, right: 20, top: 28, bottom: 48 },
    xAxis: {
      type: 'category',
      data: methods,
      axisLabel: {
        fontSize: 12,
        fontWeight: 600,
        color: '#334155',
        // 防止长标签被截断
        interval: 0,
      },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value',
      name: 'RMSE（特征级）',
      nameTextStyle: { fontSize: 11, color: '#64748b' },
      axisLabel: { formatter: (v: number) => v.toFixed(2) },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [
      {
        name: '特征级 RMSE',
        type: 'boxplot',
        // data 中每一项对应 xAxis.data 中同索引的类目，null 跳过
        data: seriesData,
        // 单 series 时每项 itemStyle 写在数据里，这里设置默认兜底
        itemStyle: {
          color: '#3b82f644',
          borderColor: '#3b82f6',
          borderWidth: 2,
        },
      },
    ],
  }, true) // notMerge=true，防止旧 series 残留
}

onMounted(async () => {
  await nextTick()
  renderBoxChart()
})

watch(
  () => props.featureRmse,
  async () => {
    await nextTick()   // 等待 v-if="featureRmse?.feature_rmse_by_method" 的 DOM 插入
    renderBoxChart()
  },
  { deep: true },
)
</script>

<template>
  <div class="ieval">
    <!-- 加载中 -->
    <el-skeleton v-if="loading" :rows="5" animated />

    <!-- 无数据 -->
    <template v-else-if="!summary?.available">
      <el-empty description="暂无填充评估结果（请先运行 merged pipeline 生成评估产物）" />
    </template>

    <template v-else>
      <!-- 配置信息条 -->
      <div class="ieval__config">
        <span class="ieval__config-item">
          遮蔽比例 <strong>{{ ((summary.config?.mask_ratio ?? 0) * 100).toFixed(0) }}%</strong>
        </span>
        <span class="ieval__config-item">
          重复次数 <strong>{{ summary.config?.n_repeats }}</strong>
        </span>
        <span class="ieval__config-item">
          KNN k=<strong>{{ summary.config?.knn_k }}</strong>
        </span>
        <span v-if="summary.config?.ae_epochs" class="ieval__config-item">
          AE epochs=<strong>{{ summary.config.ae_epochs }}</strong>
        </span>
        <span v-if="summary.config?.ae_hidden?.length" class="ieval__config-item">
          AE hidden=<strong>{{ summary.config.ae_hidden.join('→') }}</strong>
        </span>
        <span class="ieval__config-item">
          样本 <strong>{{ summary.config?.n_samples }}</strong>
          × 特征 <strong>{{ summary.config?.n_features }}</strong>
        </span>
        <el-tag
          v-if="summary.best_method"
          type="success"
          effect="light"
          class="ieval__best-tag"
        >
          最优方法: {{ summary.best_method }} (RMSE 最低)
        </el-tag>
      </div>

      <!-- 指标对比表 -->
      <div class="ieval__section">
        <div class="ieval__subhead">方法指标对比（均值 ± 标准差，{{ summary.config?.n_repeats }} 次重复）</div>
        <el-table :data="tableRows" size="small" stripe border>
          <el-table-column label="填充方法" prop="method" width="110">
            <template #default="{ row }">
              <span class="ieval__method-cell">
                <span
                  class="ieval__dot"
                  :style="{ background: METHOD_COLORS[row.method] ?? '#94a3b8' }"
                />
                {{ row.method }}
                <el-tag
                  v-if="DL_METHODS.has(row.method)"
                  type="warning"
                  size="small"
                  effect="light"
                  style="margin-left:4px"
                >深度学习</el-tag>
                <el-tag v-if="row.is_best" type="success" size="small" effect="light" style="margin-left:4px">最优</el-tag>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="RMSE ↓" min-width="130">
            <template #default="{ row }">
              <span :class="{ 'ieval__best-val': row.is_best }">
                {{ row.rmse }} <span class="ieval__std">± {{ row.rmse_std }}</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="MAE ↓" min-width="100">
            <template #default="{ row }">
              <span :class="{ 'ieval__best-val': row.is_best }">{{ row.mae }}</span>
            </template>
          </el-table-column>
          <el-table-column label="NRMSE ↓" min-width="100">
            <template #default="{ row }">
              <span :class="{ 'ieval__best-val': row.is_best }">{{ row.nrmse }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 箱线图 -->
      <div v-if="featureRmse?.feature_rmse_by_method" class="ieval__section">
        <div class="ieval__subhead">特征级 RMSE 分布（箱线图，反映各方法在不同特征上的稳定性）</div>
        <div ref="boxChartRef" class="ieval__chart" />
      </div>

      <!-- 说明注释 -->
      <div v-if="summary.notes?.length" class="ieval__notes">
        <div class="ieval__subhead">评估说明</div>
        <ul>
          <li v-for="(n, i) in summary.notes" :key="i">{{ n }}</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.ieval__config {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem 1.2rem;
  font-size: 0.85rem;
  color: var(--app-muted);
  margin-bottom: 1rem;
  padding: 0.6rem 0.9rem;
  background: rgba(37, 99, 235, 0.04);
  border: 1px solid rgba(37, 99, 235, 0.1);
  border-radius: 8px;
}

.ieval__config-item strong {
  color: var(--app-text);
  margin-left: 2px;
}

.ieval__best-tag {
  margin-left: auto;
}

.ieval__section {
  margin-bottom: 1.25rem;

  :deep(.el-table) {
    max-height: 400px;

    @media (max-width: 768px) {
      max-height: 300px;
    }
  }
}

.ieval__subhead {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--app-muted);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ieval__method-cell {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.ieval__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ieval__best-val {
  font-weight: 700;
  color: #059669;
}

/* autoencoder 行高亮背景（淡紫） */
:deep(.el-table__row) td .ieval__method-cell {
  .ieval__dot[style*='8b5cf6'] {
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
  }
}

.ieval__std {
  font-size: 0.78rem;
  color: var(--app-muted);
}

.ieval__chart {
  width: 100%;
  height: 280px;
  margin-top: 0.5rem;
}

.ieval__notes {
  font-size: 0.83rem;
  color: var(--app-muted);
  background: #f8faff;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 0.75rem 1rem;

  ul {
    margin: 0.25rem 0 0;
    padding-left: 1.25rem;
    line-height: 1.75;
  }
}
</style>
