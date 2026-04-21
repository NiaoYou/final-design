<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchDiffGroups, fetchDiffAnalysis } from '@/api/benchmark'
import { fetchDatasetDiffGroups, fetchDatasetDiffAnalysis } from '@/api/dataset'
import type { DiffAnalysisResult, DiffFeature } from '@/types/benchmark'

// ---- Props ----
const props = withDefaults(defineProps<{
  dataset?: string
}>(), {
  dataset: 'benchmark',
})

// ---- 状态 ----
const groups = ref<string[]>([])
const groupsLoading = ref(false)

const selectedGroup1 = ref('')
const selectedGroup2 = ref('')
const fcThreshold = ref(1.0)
const pvalueThreshold = ref(0.05)
const useFdr = ref(true)

const result = ref<DiffAnalysisResult | null>(null)
const running = ref(false)
const errorMsg = ref('')

// ---- 图表 ref ----
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

// ---- 颜色映射 ----
const COLOR = { up: '#ef4444', down: '#3b82f6', ns: '#cbd5e1' }
const LABEL_ZH = { up: '上调', down: '下调', ns: '无显著' }

// ---- 是否为 benchmark 数据集 ----
const isBenchmark = computed(() => props.dataset === 'benchmark')

// ---- 加载可用组 ----
async function loadGroups() {
  groupsLoading.value = true
  result.value = null
  selectedGroup1.value = ''
  selectedGroup2.value = ''
  try {
    const r = isBenchmark.value
      ? await fetchDiffGroups()
      : await fetchDatasetDiffGroups(props.dataset)
    groups.value = r.groups ?? []
    if (groups.value.length >= 2) {
      selectedGroup1.value = groups.value[0]
      selectedGroup2.value = groups.value[1]
    }
  } catch {
    groups.value = []
  } finally {
    groupsLoading.value = false
  }
}

onMounted(loadGroups)

// 数据集切换时重新加载组列表
watch(() => props.dataset, loadGroups)

onUnmounted(() => {
  chart?.dispose()
  chart = null
})

// ---- 散点数据（计算属性） ----
const scatterSeries = computed(() => {
  if (!result.value) return []
  const byLabel: Record<string, DiffFeature[]> = { up: [], down: [], ns: [] }
  for (const f of result.value.features) {
    ;(byLabel[f.label] ?? byLabel.ns).push(f)
  }
  return (['up', 'down', 'ns'] as const).map((label) => ({
    name: LABEL_ZH[label],
    type: 'scatter' as const,
    symbolSize: label === 'ns' ? 4 : 6,
    itemStyle: {
      color: COLOR[label],
      opacity: label === 'ns' ? 0.35 : 0.82,
      borderColor: label === 'ns' ? 'transparent' : COLOR[label],
      borderWidth: 1,
    },
    data: byLabel[label].map((f) => ({
      value: [f.log2fc ?? 0, useFdr.value ? (f.neg_log10_qvalue ?? 0) : (f.neg_log10_pvalue ?? 0)],
      name: f.feature,
      extra: f,
    })),
    emphasis: { scale: 1.5 },
    large: true,
    largeThreshold: 800,
  }))
})

// ---- 渲染图表 ----
function renderChart() {
  if (!chartRef.value || !result.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
  }

  const yLabel = useFdr.value ? '-log10(q-value)' : '-log10(p-value)'
  const sigLine = -Math.log10(pvalueThreshold.value)

  const markLines: any[] = [
    {
      xAxis: fcThreshold.value,
      lineStyle: { color: '#ef4444', type: 'dashed', opacity: 0.5 },
      label: { show: false },
    },
    {
      xAxis: -fcThreshold.value,
      lineStyle: { color: '#3b82f6', type: 'dashed', opacity: 0.5 },
      label: { show: false },
    },
    {
      yAxis: sigLine,
      lineStyle: { color: '#64748b', type: 'dashed', opacity: 0.4 },
      label: {
        formatter: () => `p=${pvalueThreshold.value}`,
        position: 'end',
        fontSize: 10,
        color: '#64748b',
      },
    },
  ]

  chart.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        enterable: true,
        formatter: (p: any) => {
          const f: DiffFeature = p.data?.extra
          if (!f) return ''
          const nameHtml = f.metabolite_name
            ? `<b>${f.metabolite_name}</b> <span style="color:#94a3b8;font-size:11px">(ion ${f.feature})</span>`
            : `<b>${f.feature}</b>`
          const mzHtml = f.ion_mz != null
            ? `<br/><span style="color:#64748b;font-size:11px">m/z ${f.ion_mz.toFixed(4)}${f.formula ? '  ' + f.formula : ''}</span>`
            : ''
          const statsHtml = `<br/>log2FC: <b>${f.log2fc?.toFixed(3) ?? '—'}</b>&emsp;` +
            `p: ${f.pvalue?.toExponential(2) ?? '—'}&emsp;q: ${f.qvalue?.toExponential(2) ?? '—'}`
          const labelHtml = `<br/><span style="color:${COLOR[f.label]};font-weight:600">${LABEL_ZH[f.label]}</span>`
          const linksHtml = [
            f.hmdb_url ? `<a href="${f.hmdb_url}" target="_blank" style="color:#3b82f6;font-size:11px">HMDB</a>` : '',
            f.kegg_url ? `<a href="${f.kegg_url}" target="_blank" style="color:#10b981;font-size:11px">KEGG</a>` : '',
          ].filter(Boolean).join('&ensp;')
          return nameHtml + mzHtml + statsHtml + labelHtml + (linksHtml ? `<br/>${linksHtml}` : '')
        },
      },
      legend: {
        data: ['上调', '下调', '无显著'],
        top: 8,
        right: 16,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: { fontSize: 12 },
      },
      grid: { left: 54, right: 24, top: 48, bottom: 42 },
      xAxis: {
        type: 'value',
        name: 'log2 Fold Change',
        nameLocation: 'middle',
        nameGap: 28,
        nameTextStyle: { fontSize: 12, color: '#475569' },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { show: false },
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
      },
      yAxis: {
        type: 'value',
        name: yLabel,
        nameLocation: 'middle',
        nameGap: 42,
        nameTextStyle: { fontSize: 11, color: '#475569' },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
        axisLabel: { formatter: (v: number) => v.toFixed(1) },
      },
      series: scatterSeries.value.map((s, i) => ({
        ...s,
        markLine:
          i === 0
            ? { silent: true, symbol: 'none', data: markLines, animation: false }
            : undefined,
      })),
    },
    true,
  )
}

watch(result, () => nextTick(renderChart), { deep: false })

// ---- 运行差异分析 ----
async function runAnalysis() {
  if (!selectedGroup1.value || !selectedGroup2.value) {
    errorMsg.value = '请选择两个不同的组别。'
    return
  }
  if (selectedGroup1.value === selectedGroup2.value) {
    errorMsg.value = '对照组与实验组不能相同。'
    return
  }
  errorMsg.value = ''
  running.value = true
  result.value = null
  try {
    result.value = isBenchmark.value
      ? await fetchDiffAnalysis(
          selectedGroup1.value,
          selectedGroup2.value,
          fcThreshold.value,
          pvalueThreshold.value,
          useFdr.value,
        )
      : await fetchDatasetDiffAnalysis(
          props.dataset,
          selectedGroup1.value,
          selectedGroup2.value,
          fcThreshold.value,
          pvalueThreshold.value,
          useFdr.value,
        )
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '差异分析请求失败，请检查后端连接。'
  } finally {
    running.value = false
  }
}

// ---- 窗口 resize ----
function onResize() { chart?.resize() }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <div class="volcano">
    <!-- 参数面板 -->
    <div class="volcano__params">
      <div class="volcano__param-row">
        <div class="volcano__param-item">
          <label>对照组 (group1)</label>
          <el-select
            v-model="selectedGroup1"
            placeholder="选择对照组"
            filterable
            :loading="groupsLoading"
            size="small"
            style="width: 180px"
          >
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
        </div>

        <div class="volcano__vs">vs</div>

        <div class="volcano__param-item">
          <label>实验组 (group2)</label>
          <el-select
            v-model="selectedGroup2"
            placeholder="选择实验组"
            filterable
            :loading="groupsLoading"
            size="small"
            style="width: 180px"
          >
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
        </div>

        <div class="volcano__param-item">
          <label>|log2FC| 阈值</label>
          <el-input-number
            v-model="fcThreshold"
            :min="0"
            :max="10"
            :step="0.5"
            :precision="1"
            size="small"
            style="width: 110px"
          />
        </div>

        <div class="volcano__param-item">
          <label>p / q 阈值</label>
          <el-input-number
            v-model="pvalueThreshold"
            :min="0.001"
            :max="0.5"
            :step="0.01"
            :precision="3"
            size="small"
            style="width: 110px"
          />
        </div>

        <div class="volcano__param-item">
          <label>多重校正</label>
          <el-switch
            v-model="useFdr"
            active-text="FDR"
            inactive-text="raw p"
            size="small"
          />
        </div>

        <el-button
          type="primary"
          size="small"
          :loading="running"
          :disabled="!selectedGroup1 || !selectedGroup2"
          @click="runAnalysis"
        >
          运行分析
        </el-button>
      </div>

      <div v-if="errorMsg" class="volcano__error">{{ errorMsg }}</div>
    </div>

    <!-- 结果区 -->
    <el-skeleton v-if="running" :rows="6" animated />

    <template v-else-if="result">
      <!-- 摘要 badge 行 -->
      <div class="volcano__summary">
        <span class="volcano__badge volcano__badge--meta">
          {{ result.group1 }} (n={{ result.n_group1 }}) vs {{ result.group2 }} (n={{ result.n_group2 }})
        </span>
        <span class="volcano__badge volcano__badge--up">
          ↑ 上调 {{ result.summary.n_sig_up }}
        </span>
        <span class="volcano__badge volcano__badge--down">
          ↓ 下调 {{ result.summary.n_sig_down }}
        </span>
        <span class="volcano__badge volcano__badge--ns">
          无显著 {{ result.summary.n_ns }}
        </span>
        <span class="volcano__badge volcano__badge--time">
          {{ result.elapsed_seconds }}s
        </span>
      </div>

      <!-- 火山图 -->
      <div ref="chartRef" class="volcano__chart" />

      <!-- 显著特征表（top 20） -->
      <div class="volcano__table-section">
        <div class="volcano__subhead">显著差异代谢物（按 q-value 升序，前 20 条）</div>
        <el-table
          :data="
            result.features
              .filter((f) => f.label !== 'ns')
              .sort((a, b) => (a.qvalue ?? 1) - (b.qvalue ?? 1))
              .slice(0, 20)
          "
          size="small"
          stripe
          border
          max-height="340"
        >
          <!-- 代谢物名 -->
          <el-table-column label="代谢物" min-width="140">
            <template #default="{ row }">
              <span v-if="row.metabolite_name" class="volcano__met-name">
                {{ row.metabolite_name }}
              </span>
              <span v-else class="volcano__met-fallback">{{ row.feature }}</span>
            </template>
          </el-table-column>
          <!-- 分子式（仅 benchmark 有注释时才有值） -->
          <el-table-column label="分子式" min-width="90">
            <template #default="{ row }">
              <span class="volcano__formula">{{ row.formula ?? '—' }}</span>
            </template>
          </el-table-column>
          <!-- log2FC -->
          <el-table-column label="log2FC" min-width="88">
            <template #default="{ row }">
              <span :style="{ color: row.label === 'up' ? '#ef4444' : '#3b82f6', fontWeight: 600 }">
                {{ row.log2fc?.toFixed(3) ?? '—' }}
              </span>
            </template>
          </el-table-column>
          <!-- q-value -->
          <el-table-column label="q-value" min-width="100">
            <template #default="{ row }">{{ row.qvalue?.toExponential(2) ?? '—' }}</template>
          </el-table-column>
          <!-- 方向 -->
          <el-table-column label="方向" min-width="68">
            <template #default="{ row }">
              <el-tag
                :type="row.label === 'up' ? 'danger' : 'primary'"
                size="small"
                effect="light"
              >
                {{ row.label === 'up' ? '↑ 上调' : '↓ 下调' }}
              </el-tag>
            </template>
          </el-table-column>
          <!-- 数据库链接（仅 benchmark 有注释时才有） -->
          <el-table-column label="数据库" min-width="100">
            <template #default="{ row }">
              <a
                v-if="row.hmdb_url"
                :href="row.hmdb_url"
                target="_blank"
                class="volcano__db-link volcano__db-link--hmdb"
              >HMDB</a>
              <a
                v-if="row.kegg_url"
                :href="row.kegg_url"
                target="_blank"
                class="volcano__db-link volcano__db-link--kegg"
              >KEGG</a>
              <span v-if="!row.hmdb_url && !row.kegg_url" class="volcano__muted">—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <!-- 初始提示 -->
    <el-empty
      v-else-if="!running"
      description="选择对照组与实验组后点击【运行分析】，生成火山图"
      :image-size="80"
    />
  </div>
</template>

<style scoped lang="scss">
.volcano__params {
  background: rgba(37, 99, 235, 0.03);
  border: 1px solid rgba(37, 99, 235, 0.1);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.volcano__param-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.6rem 1rem;
  min-height: 56px;
}

.volcano__param-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 56px;
  justify-content: flex-end;

  label {
    font-size: 0.75rem;
    color: var(--app-muted);
    font-weight: 500;
  }
}

.volcano__vs {
  font-size: 0.9rem;
  color: var(--app-muted);
  align-self: flex-end;
  padding-bottom: 4px;
}

.volcano__error {
  margin-top: 0.5rem;
  color: #dc2626;
  font-size: 0.82rem;
}

.volcano__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.6rem;
  margin-bottom: 0.75rem;
  align-items: center;
}

.volcano__badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  height: 24px;

  &--meta {
    background: #f1f5f9;
    color: #475569;
  }

  &--up {
    background: #fee2e2;
    color: #b91c1c;
  }

  &--down {
    background: #dbeafe;
    color: #1d4ed8;
  }

  &--ns {
    background: #f1f5f9;
    color: #64748b;
  }

  &--time {
    background: #f0fdf4;
    color: #15803d;
    font-weight: 400;
  }
}

.volcano__chart {
  width: 100%;
  height: 400px;
  margin-bottom: 1.25rem;

  @media (max-width: 768px) {
    height: 300px;
  }
}

.volcano__table-section {
  margin-top: 0.25rem;
}

.volcano__subhead {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--app-muted);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.volcano__met-name {
  font-weight: 500;
  color: var(--app-text);
}

.volcano__met-fallback {
  color: var(--app-muted);
  font-size: 0.82rem;
}

.volcano__formula {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: #475569;
}

.volcano__muted {
  color: var(--app-muted);
  font-size: 0.82rem;
}

.volcano__db-link {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-decoration: none;
  margin-right: 4px;

  &--hmdb {
    background: #dbeafe;
    color: #1d4ed8;
    &:hover { background: #bfdbfe; }
  }

  &--kegg {
    background: #dcfce7;
    color: #15803d;
    &:hover { background: #bbf7d0; }
  }
}
</style>
