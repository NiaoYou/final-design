<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Loading } from '@element-plus/icons-vue'
import { fetchDiffGroups, fetchPathwayEnrichment } from '@/api/benchmark'
import type { PathwayEnrichmentResult, PathwayItem } from '@/api/benchmark'

// ---- 组别选择 ----
const groups = ref<string[]>([])
const groupsLoading = ref(false)
const selectedGroup1 = ref('')
const selectedGroup2 = ref('')
const fcThreshold = ref(1.0)
const pvalThreshold = ref(0.05)
const useFdr = ref(true)

// ---- 运行状态 ----
const running = ref(false)
const errorMsg = ref('')
const statusMsg = ref('')   // 进度文案（首次调用 KEGG API 需提示用户等待）
const result = ref<PathwayEnrichmentResult | null>(null)

// ---- 图表模式 ----
type ChartMode = 'bubble' | 'network'
const chartMode = ref<ChartMode>('bubble')

// ---- ECharts refs ----
const bubbleRef = ref<HTMLDivElement | null>(null)
const networkRef = ref<HTMLDivElement | null>(null)
let bubbleChart: echarts.ECharts | null = null
let networkChart: echarts.ECharts | null = null

// ---- 加载组别 ----
onMounted(async () => {
  groupsLoading.value = true
  try {
    const r = await fetchDiffGroups()
    groups.value = r.groups ?? []
    if (groups.value.length >= 2) {
      selectedGroup1.value = groups.value[0]
      selectedGroup2.value = groups.value[1]
    }
  } catch {
    // 无数据时保持空
  } finally {
    groupsLoading.value = false
  }
})

onUnmounted(() => {
  bubbleChart?.dispose()
  networkChart?.dispose()
})

// ---- 运行分析 ----
async function runEnrichment() {
  if (!selectedGroup1.value || !selectedGroup2.value) {
    errorMsg.value = '请先选择对照组与实验组。'
    return
  }
  if (selectedGroup1.value === selectedGroup2.value) {
    errorMsg.value = '对照组与实验组不能相同。'
    return
  }
  errorMsg.value = ''
  result.value = null
  running.value = true
  statusMsg.value = '正在运行差异分析并获取 KEGG 通路数据（首次运行需下载 KEGG 数据，约 15~30 秒）…'

  try {
    const r = await fetchPathwayEnrichment(
      selectedGroup1.value,
      selectedGroup2.value,
      fcThreshold.value,
      pvalThreshold.value,
      useFdr.value,
    )
    result.value = r
    statusMsg.value = ''
    // 切回气泡图并渲染
    chartMode.value = 'bubble'
    await nextTick()
    renderBubble()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '通路富集分析请求失败，请检查后端连接。'
    statusMsg.value = ''
  } finally {
    running.value = false
  }
}

// ---- 气泡图（lollipop/dot plot 风格） ----
// Y轴=通路名, X轴=RichFactor, 点大小=hits, 颜色=-log10(qvalue)
function renderBubble() {
  const pathways = result.value?.pathways
  if (!Array.isArray(pathways) || pathways.length === 0 || !bubbleRef.value) return

  if (!bubbleChart) {
    bubbleChart = echarts.init(bubbleRef.value, undefined, { renderer: 'canvas' })
  }

  // 取前 15 条（从小 pvalue 排），倒序让最显著在顶部
  const top = pathways.slice(0, 15).reverse()
  const maxNegLog = Math.max(...top.map(p => -Math.log10(Math.max(p.qvalue, 1e-10))))
  const maxHits = Math.max(...top.map(p => p.hits))

  // 颜色渐变：浅黄→深红（仿 clusterProfiler 风格）
  const colorScale = (negLog: number) => {
    const t = Math.min(1, negLog / Math.max(maxNegLog, 1))
    // 插值：#fde68a → #b91c1c
    const r = Math.round(253 + (185 - 253) * t)
    const g = Math.round(230 + (28 - 230) * t)
    const b = Math.round(138 + (28 - 138) * t)
    return `rgb(${r},${g},${b})`
  }

  bubbleChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const d = p.data as any
        if (!d) return ''
        return `<b>${d.name}</b><br/>
          RichFactor: <b>${d.rich_factor}</b> (${d.gene_ratio})<br/>
          Hits: <b>${d.hits}</b> / 通路大小: ${d.pathway_size}<br/>
          p-value: ${d.pvalue?.toExponential(2)}<br/>
          q-value (FDR): <b>${d.qvalue?.toExponential(2)}</b>`
      },
    },
    grid: { left: 24, right: 80, top: 16, bottom: 40, containLabel: true },
    xAxis: {
      type: 'value',
      name: 'RichFactor',
      nameLocation: 'middle',
      nameGap: 26,
      nameTextStyle: { fontSize: 11, color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { fontSize: 11, formatter: (v: number) => v.toFixed(2) },
    },
    yAxis: {
      type: 'category',
      data: top.map(p => p.pathway_name),
      axisLabel: {
        fontSize: 10,
        width: 220,
        overflow: 'truncate',
        formatter: (v: string) => v.length > 38 ? v.slice(0, 36) + '…' : v,
      },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    visualMap: {
      min: 0,
      max: Math.ceil(maxNegLog),
      dimension: 2,
      orient: 'vertical',
      right: 4,
      top: 'center',
      text: ['-log10(q)', '0'],
      textStyle: { fontSize: 10, color: '#64748b' },
      inRange: { color: ['#fde68a', '#ef4444', '#7f1d1d'] },
      calculable: true,
    },
    series: [{
      type: 'scatter',
      data: top.map(p => ({
        value: [p.rich_factor, p.pathway_name, -Math.log10(Math.max(p.qvalue, 1e-10))],
        name: p.pathway_name,
        symbolSize: Math.max(8, Math.round(8 + (p.hits / maxHits) * 28)),
        itemStyle: { color: colorScale(-Math.log10(Math.max(p.qvalue, 1e-10))), borderColor: '#fff', borderWidth: 1 },
        // extra for tooltip
        rich_factor: p.rich_factor,
        gene_ratio: p.gene_ratio,
        hits: p.hits,
        pathway_size: p.pathway_size,
        pvalue: p.pvalue,
        qvalue: p.qvalue,
      })),
      emphasis: { scale: 1.3 },
    }],
  }, true)
}

// ---- 力导向网络图 ----
function renderNetwork() {
  const net = result.value?.network
  if (!net?.nodes || net.nodes.length === 0 || !networkRef.value) return

  if (!networkChart) {
    networkChart = echarts.init(networkRef.value, undefined, { renderer: 'canvas' })
  }

  // 通路节点颜色：深度按 -log10(qvalue)
  const pathwayNodes = net.nodes.filter(n => n.category === 1)
  const rawMax = pathwayNodes.length > 0
    ? Math.max(...pathwayNodes.map(n => n._meta?.intensity ?? 0))
    : 0
  const maxIntensity = rawMax > 0 ? rawMax : 1   // 防止除以零

  const coloredNodes = net.nodes.map(n => {
    if (n.category === 1) {
      const t = Math.min(1, (n._meta?.intensity ?? 0) / maxIntensity)
      const r = Math.round(251 + (185 - 251) * t)
      const g = Math.round(146 + (28 - 146) * t)
      const b = Math.round(60 + (28 - 60) * t)
      return { ...n, itemStyle: { color: `rgb(${r},${g},${b})`, borderColor: '#fff', borderWidth: 2 } }
    }
    return { ...n, itemStyle: { color: '#3b82f6', borderColor: '#fff', borderWidth: 1, opacity: 0.85 } }
  })

  networkChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const d = p.data
        if (!d?._meta) return d?.name ?? ''
        if (d.category === 1) {
          const m = d._meta
          return `<b>${d.name}</b><br/>
            命中代谢物: <b>${m.hits}</b> / 通路大小: ${m.pathway_size}<br/>
            RichFactor: ${m.rich_factor}<br/>
            q-value: <b>${m.qvalue?.toExponential(2)}</b>`
        }
        const m = d._meta
        return `<b>${m.metabolite_name || d.name}</b>${m.formula ? '<br/>' + m.formula : ''}<br/>${d.id}`
      },
    },
    legend: {
      data: net.categories.map(c => c.name),
      top: 8,
      right: 16,
      textStyle: { fontSize: 11 },
      icon: 'circle',
    },
    series: [{
      type: 'graph',
      layout: 'force',
      animation: true,
      animationDuration: 1200,
      data: coloredNodes,
      links: net.edges,
      categories: net.categories,
      roam: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 9,
        color: '#334155',
        formatter: (p: any) => p.data.category === 1
          ? (p.data.name.length > 24 ? p.data.name.slice(0, 22) + '…' : p.data.name)
          : '',
      },
      force: {
        repulsion: 120,
        gravity: 0.08,
        edgeLength: [60, 160],
        layoutAnimation: true,
      },
      edgeSymbol: ['none', 'none'],
      lineStyle: { color: '#cbd5e1', opacity: 0.5, width: 1 },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { opacity: 0.9, width: 2 },
      },
    }],
  }, true)
}

// ---- 监听图表模式切换 ----
watch(chartMode, async (mode) => {
  await nextTick()
  if (mode === 'bubble') renderBubble()
  else renderNetwork()
})

// ---- 窗口 resize ----
function onResize() {
  bubbleChart?.resize()
  networkChart?.resize()
}
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

// ---- 汇总数据 ----
const sigPathways = computed(() =>
  (result.value?.pathways ?? []).filter(p => p.qvalue < 0.05).length
)
</script>

<template>
  <div class="pe">
    <!-- 参数面板 -->
    <div class="pe__params">
      <div class="pe__param-row">
        <div class="pe__param-item">
          <label>对照组 (group1)</label>
          <el-select
            v-model="selectedGroup1"
            placeholder="选择对照组"
            filterable
            :loading="groupsLoading"
            size="small"
            style="width: 176px"
          >
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
        </div>

        <span class="pe__vs">vs</span>

        <div class="pe__param-item">
          <label>实验组 (group2)</label>
          <el-select
            v-model="selectedGroup2"
            placeholder="选择实验组"
            filterable
            :loading="groupsLoading"
            size="small"
            style="width: 176px"
          >
            <el-option v-for="g in groups" :key="g" :label="g" :value="g" />
          </el-select>
        </div>

        <div class="pe__param-item">
          <label>|log2FC| 阈值</label>
          <el-input-number v-model="fcThreshold" :min="0" :max="10" :step="0.5" :precision="1" size="small" style="width: 108px" />
        </div>

        <div class="pe__param-item">
          <label>p/q 阈值</label>
          <el-input-number v-model="pvalThreshold" :min="0.001" :max="0.5" :step="0.01" :precision="3" size="small" style="width: 108px" />
        </div>

        <div class="pe__param-item">
          <label>多重校正</label>
          <el-switch v-model="useFdr" active-text="FDR" inactive-text="raw p" size="small" />
        </div>

        <el-button
          type="primary"
          size="small"
          :loading="running"
          :disabled="!selectedGroup1 || !selectedGroup2"
          @click="runEnrichment"
        >
          运行富集分析
        </el-button>
      </div>

      <div v-if="errorMsg" class="pe__error">{{ errorMsg }}</div>
      <div v-if="statusMsg && running" class="pe__status">
        <el-icon class="is-loading" style="margin-right:6px"><Loading /></el-icon>
        {{ statusMsg }}
      </div>
    </div>

    <!-- 结果区 -->
    <el-skeleton v-if="running" :rows="8" animated />

    <template v-else-if="result?.available">
      <!-- 汇总 badges -->
      <div class="pe__summary">
        <span class="pe__badge pe__badge--meta">
          {{ result.group1 }} vs {{ result.group2 }}
        </span>
        <span class="pe__badge pe__badge--feat">
          显著特征 {{ result.n_sig_features_total }} 个
          <span class="pe__badge-sub">（含 KEGG ID {{ result.n_sig_features }} 个）</span>
        </span>
        <span class="pe__badge pe__badge--path">
          检验通路 {{ result.n_pathways_tested }} 条
        </span>
        <span class="pe__badge pe__badge--ok">
          FDR&lt;0.05 显著通路 {{ sigPathways }} 条
        </span>
        <span class="pe__badge pe__badge--bg">
          背景 {{ result.n_bg_features }} 个代谢物
        </span>
      </div>

      <!-- 图表模式切换 -->
      <div class="pe__tabs">
        <button
          class="pe__tab"
          :class="{ 'pe__tab--active': chartMode === 'bubble' }"
          @click="chartMode = 'bubble'"
        >
          气泡图（通路概览）
        </button>
        <button
          class="pe__tab"
          :class="{ 'pe__tab--active': chartMode === 'network' }"
          @click="chartMode = 'network'"
        >
          网络图（代谢物-通路关联）
        </button>
      </div>

      <!-- 气泡图 -->
      <div v-show="chartMode === 'bubble'" ref="bubbleRef" class="pe__chart" />

      <!-- 网络图 -->
      <div v-show="chartMode === 'network'" ref="networkRef" class="pe__chart pe__chart--network">
        <div class="pe__network-hint">可拖拽节点 / 滚轮缩放；蓝色=显著差异代谢物，橙色=KEGG 通路</div>
      </div>

      <!-- 明细表 -->
      <div class="pe__section">
        <div class="pe__subhead">富集通路明细（按 p-value 升序，前 {{ result.pathways.length }} 条）</div>
        <el-table :data="result.pathways" size="small" stripe border max-height="340">
          <el-table-column label="#" type="index" width="44" align="center" />
          <el-table-column label="通路名称" min-width="220">
            <template #default="{ row }: { row: PathwayItem }">
              <a
                :href="`https://www.kegg.jp/pathway/${row.pathway_id}`"
                target="_blank"
                class="pe__path-link"
              >
                {{ row.pathway_name }}
              </a>
              <span class="pe__path-id">{{ row.pathway_id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="Hits/通路大小" width="120" align="center">
            <template #default="{ row }: { row: PathwayItem }">
              <span class="pe__hits">{{ row.hits }}</span>
              <span class="pe__slash">/</span>
              <span>{{ row.pathway_size }}</span>
            </template>
          </el-table-column>
          <el-table-column label="RichFactor ↑" width="108" align="center">
            <template #default="{ row }: { row: PathwayItem }">
              <span :class="{ 'pe__best-val': row.qvalue < 0.05 }">
                {{ row.rich_factor.toFixed(3) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="p-value ↓" width="108" align="center">
            <template #default="{ row }: { row: PathwayItem }">
              {{ row.pvalue.toExponential(2) }}
            </template>
          </el-table-column>
          <el-table-column label="q-value (FDR) ↓" width="124" align="center">
            <template #default="{ row }: { row: PathwayItem }">
              <span :class="{ 'pe__sig': row.qvalue < 0.05 }">
                {{ row.qvalue.toExponential(2) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <!-- 无富集结果 -->
    <div v-else-if="result && !result.available" class="pe__unavail">
      <el-empty :description="result.reason || '无富集通路'" :image-size="64" />
    </div>

    <!-- 初始提示 -->
    <el-empty
      v-else-if="!running"
      description="选择两个组别后点击【运行富集分析】，自动调用 KEGG REST API 做通路富集"
      :image-size="80"
    />
  </div>
</template>

<style scoped lang="scss">
.pe__params {
  background: rgba(139, 92, 246, 0.03);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.pe__param-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.6rem 1rem;
}

.pe__param-item {
  display: flex;
  flex-direction: column;
  gap: 3px;

  label {
    font-size: 0.75rem;
    color: var(--app-muted);
    font-weight: 500;
  }
}

.pe__vs {
  font-size: 0.9rem;
  color: var(--app-muted);
  align-self: flex-end;
  padding-bottom: 4px;
}

.pe__error {
  margin-top: 0.5rem;
  color: #dc2626;
  font-size: 0.82rem;
}

.pe__status {
  margin-top: 0.5rem;
  color: #8b5cf6;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
}

.pe__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.6rem;
  margin-bottom: 0.85rem;
}

.pe__badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;

  &--meta { background: #f1f5f9; color: #475569; }
  &--feat { background: #ede9fe; color: #6d28d9; }
  &--path { background: #fef3c7; color: #92400e; }
  &--ok   { background: #dcfce7; color: #15803d; }
  &--bg   { background: #f0f9ff; color: #0369a1; }
}

.pe__badge-sub {
  font-weight: 400;
  font-size: 0.73rem;
  opacity: 0.8;
}

/* 图表模式切换 */
.pe__tabs {
  display: flex;
  gap: 0;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 8px;
  overflow: hidden;
  width: fit-content;
}

.pe__tab {
  padding: 5px 18px;
  font-size: 0.82rem;
  cursor: pointer;
  background: transparent;
  border: none;
  color: var(--app-muted);
  transition: all 0.2s;

  &:hover { background: rgba(139, 92, 246, 0.06); }
  &--active {
    background: #8b5cf6;
    color: #fff;
    font-weight: 600;
  }
}

.pe__chart {
  width: 100%;
  height: 420px;
  margin-bottom: 1.25rem;
  position: relative;
}

.pe__chart--network {
  height: 500px;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #fafbff;
}

.pe__network-hint {
  position: absolute;
  bottom: 10px;
  left: 12px;
  font-size: 0.75rem;
  color: var(--app-muted);
  pointer-events: none;
  z-index: 10;
}

.pe__section {
  margin-bottom: 1rem;
}

.pe__subhead {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--app-muted);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pe__path-link {
  font-weight: 500;
  color: #7c3aed;
  text-decoration: none;
  display: block;
  font-size: 0.85rem;
  &:hover { text-decoration: underline; }
}

.pe__path-id {
  font-size: 0.72rem;
  color: var(--app-muted);
  display: block;
  font-family: 'Courier New', monospace;
}

.pe__hits {
  font-weight: 700;
  color: #7c3aed;
}

.pe__slash {
  margin: 0 2px;
  color: var(--app-muted);
}

.pe__best-val {
  font-weight: 700;
  color: #059669;
}

.pe__sig {
  font-weight: 700;
  color: #dc2626;
}

.pe__unavail {
  padding: 2rem 0;
  text-align: center;
}
</style>
