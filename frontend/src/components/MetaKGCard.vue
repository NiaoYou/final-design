<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchMetakgSubgraph } from '@/api/benchmark'
import { fetchDatasetMetakgSubgraph } from '@/api/dataset'
import type { MetaKGNode, MetaKGEdge } from '@/api/benchmark'
import { Search, Loading } from '@element-plus/icons-vue'

// ---- Props ----
const props = withDefaults(defineProps<{ dataset?: string }>(), { dataset: 'benchmark' })
const isBenchmark = computed(() => props.dataset === 'benchmark')

// ─── 节点类型配色 ───────────────────────────────────────────
const TYPE_COLOR: Record<string, string> = {
  Compound: '#3b82f6',
  Pathway:  '#f97316',
  Reaction: '#8b5cf6',
  Enzyme:   '#10b981',
  Drug:     '#ef4444',
  Module:   '#f59e0b',
  Network:  '#6366f1',
  Gene:     '#06b6d4',
  Protein:  '#ec4899',
  Disease:  '#78716c',
  Other:    '#94a3b8',
}

const TYPE_LABEL: Record<string, string> = {
  Compound: '代谢物',
  Pathway:  '通路',
  Reaction: '生化反应',
  Enzyme:   '酶',
  Drug:     '药物',
  Module:   '模块',
  Network:  '网络',
  Gene:     '基因',
  Protein:  '蛋白质',
  Disease:  '疾病',
  Other:    '其他',
}

const RELATION_LABEL: Record<string, string> = {
  has_pathway:        '参与通路',
  has_reaction:       '参与反应',
  has_enzyme:         '被酶催化',
  has_module:         '属于模块',
  has_network:        '属于网络',
  related_to_protein: '关联蛋白',
  related_to_gene:    '关联基因',
  has_disease:        '关联疾病',
  'is a':             '是',
  'is_a':             '是',
  'same as':          '等同于',
  'same_as':          '等同于',
}

// ─── 组件状态 ────────────────────────────────────────────────
// chartRef 不受 v-if 控制，始终存在于 DOM，彻底避免挂载时序问题
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const loading  = ref(false)
const errorMsg = ref('')

const allNodes = ref<MetaKGNode[]>([])
const allEdges = ref<MetaKGEdge[]>([])
const metaInfo = ref<Record<string, any>>({})

// 过滤选项
const enabledTypes = ref<string[]>(Object.keys(TYPE_COLOR))
const enabledRels  = ref<string[]>(['has_pathway', 'has_reaction', 'has_enzyme', 'has_module'])
const seedOnly     = ref(false)
const searchKeyword = ref('')
const maxNodes     = ref(300)

// ─── 派生数据 ────────────────────────────────────────────────
const availableRelations = computed(() => {
  if (!metaInfo.value?.relation_counts) return []
  return Object.keys(metaInfo.value.relation_counts)
})

const filteredData = computed(() => {
  const typeSet = new Set(enabledTypes.value)
  const relSet  = new Set(enabledRels.value)

  let nodes = allNodes.value.filter(n => typeSet.has(n.type))

  if (seedOnly.value) {
    nodes = nodes.filter(n => n.is_seed)
  }

  const kw = searchKeyword.value.trim().toLowerCase()
  let highlightIds = new Set<string>()
  if (kw) {
    for (const n of nodes) {
      const nameMatch = n.metabolite_name?.toLowerCase().includes(kw)
      const idMatch   = n.label.toLowerCase().includes(kw)
      if (nameMatch || idMatch) highlightIds.add(n.id)
    }
  }

  const nodeIds = new Set(nodes.map(n => n.id))
  let edges = allEdges.value.filter(
    e => relSet.has(e.relation) && nodeIds.has(e.head) && nodeIds.has(e.tail)
  )

  if (nodes.length > maxNodes.value) {
    const edgeCount = new Map<string, number>()
    for (const e of edges) {
      edgeCount.set(e.head, (edgeCount.get(e.head) ?? 0) + 1)
      edgeCount.set(e.tail, (edgeCount.get(e.tail) ?? 0) + 1)
    }

    const searchHits   = nodes.filter(n => highlightIds.has(n.id))
    const nonCompound  = nodes.filter(n => !highlightIds.has(n.id) && n.type !== 'Compound')
    const seedWithEdge = nodes.filter(n => !highlightIds.has(n.id) && n.type === 'Compound' && n.is_seed && (edgeCount.get(n.id) ?? 0) > 0)
    const rest         = nodes.filter(n => !highlightIds.has(n.id) && n.type === 'Compound' && !n.is_seed)
    const seedNoEdge   = nodes.filter(n => !highlightIds.has(n.id) && n.type === 'Compound' && n.is_seed && (edgeCount.get(n.id) ?? 0) === 0)

    nonCompound.sort((a, b) => (edgeCount.get(b.id) ?? 0) - (edgeCount.get(a.id) ?? 0))
    seedWithEdge.sort((a, b) => (edgeCount.get(b.id) ?? 0) - (edgeCount.get(a.id) ?? 0))

    nodes = [...searchHits, ...nonCompound, ...seedWithEdge, ...rest, ...seedNoEdge]
      .slice(0, maxNodes.value)

    const finalIds = new Set(nodes.map(n => n.id))
    edges = edges.filter(e => finalIds.has(e.head) && finalIds.has(e.tail))
  }

  return { nodes, edges, highlightIds }
})

// ─── 加载数据 ────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  errorMsg.value = ''
  allNodes.value = []
  allEdges.value = []
  metaInfo.value = {}
  try {
    const sg = isBenchmark.value
      ? await fetchMetakgSubgraph()
      : await fetchDatasetMetakgSubgraph(props.dataset)
    allNodes.value  = sg.nodes
    allEdges.value  = sg.edges
    metaInfo.value  = sg.meta
    const rels = Object.keys(sg.meta?.relation_counts ?? {})
    enabledRels.value = rels.slice(0, 4)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? e?.message ?? '加载失败'
  } finally {
    loading.value = false
    // 等 DOM 更新后渲染（chartRef 始终在 DOM 里，无需担心 null）
    await nextTick()
    renderGraph()
  }
}

// 数据集切换时重新加载
watch(() => props.dataset, () => void loadData())

// ─── 渲染图表 ────────────────────────────────────────────────
function renderGraph() {
  if (!chartRef.value) return
  if (loading.value) return          // 加载中不渲染
  if (!allNodes.value.length) return // 无数据不渲染

  const el = chartRef.value

  if (!chart) {
    chart = echarts.init(el, undefined, { renderer: 'canvas' })
  }
  chart.resize()

  const { nodes, edges, highlightIds } = filteredData.value
  const kw = searchKeyword.value.trim()

  const eNodes = nodes.map(n => {
    const color  = TYPE_COLOR[n.type] ?? TYPE_COLOR.Other
    const isSeed = n.is_seed
    const isHit  = highlightIds.has(n.id)
    const name   = n.metabolite_name || n.label
    return {
      id:         n.id,
      name,
      node_id:    n.id,
      node_label: n.label,
      node_type:  n.type,
      is_seed:    isSeed,
      formula:    n.formula,
      ion_mz:     n.ion_mz,
      symbolSize: isSeed ? (isHit ? 20 : 12) : 8,
      itemStyle: {
        color:       isHit ? '#fbbf24' : color,
        borderColor: isSeed ? '#1e40af' : 'transparent',
        borderWidth: isSeed ? 2 : 0,
        opacity:     kw && !isHit ? 0.3 : 1,
        shadowBlur:  isHit ? 12 : 0,
        shadowColor: '#fbbf24',
      },
      label: {
        show:      isSeed && nodes.length < 150,
        formatter: name.length > 12 ? name.slice(0, 12) + '…' : name,
        fontSize:  9,
        color:     '#334155',
      },
    }
  })

  const eEdges = edges.map(e => ({
    source:   e.head,
    target:   e.tail,
    relation: e.relation,
    lineStyle: {
      color:     '#94a3b8',
      width:     1,
      opacity:   kw ? 0.15 : 0.5,
      curveness: 0.1,
    },
  }))

  const option: echarts.EChartsOption = {
    backgroundColor: '#f8fafc',
    tooltip: {
      trigger: 'item',
      formatter(params: any) {
        if (params.dataType === 'node') {
          const d = params.data as typeof eNodes[0]
          const typeLabel = TYPE_LABEL[d.node_type] ?? d.node_type
          let html = `<div style="font-size:13px;font-weight:600;margin-bottom:4px">${d.name}</div>`
          html += `<div style="color:#64748b">类型：${typeLabel}</div>`
          html += `<div style="color:#64748b">ID：${d.node_id}</div>`
          if (d.formula) html += `<div style="color:#64748b">分子式：${d.formula}</div>`
          if (d.ion_mz)  html += `<div style="color:#64748b">m/z：${Number(d.ion_mz).toFixed(4)}</div>`
          if (d.is_seed) html += `<div style="color:#3b82f6;margin-top:4px">✦ 本项目代谢物</div>`
          return html
        }
        if (params.dataType === 'edge') {
          const rel = (params.data as any).relation
          return `<div style="font-size:12px;color:#334155">${RELATION_LABEL[rel] ?? rel}</div>`
        }
        return ''
      },
    },
    series: [
      {
        type:      'graph',
        layout:    'force',
        animation: true,
        animationDuration: 1500,
        data:      eNodes,
        edges:     eEdges,
        roam:      true,
        draggable: true,
        center:    ['50%', '50%'],
        zoom:      1,
        force: {
          initLayout:      'circular',
          repulsion:       nodes.length > 200 ? 60 : 120,
          edgeLength:      [20, 80],
          gravity:         0.05,
          friction:        0.6,
          layoutAnimation: true,
        },
        emphasis: {
          focus:     'adjacency',
          scale:     true,
          lineStyle: { width: 2, opacity: 0.9 },
        },
        edgeSymbol:     ['none', 'arrow'],
        edgeSymbolSize: 5,
        lineStyle:      { curveness: 0.1 },
      },
    ],
  }

  chart.setOption(option, { notMerge: true, lazyUpdate: false })
}

// 过滤条件变化时重新渲染（数据已加载完成时）
watch(filteredData, () => {
  if (!loading.value && allNodes.value.length > 0) renderGraph()
})

// ─── 节点数统计 ─────────────────────────────────────────────
const stats = computed(() => {
  const { nodes, edges } = filteredData.value
  const typeMap: Record<string, number> = {}
  for (const n of nodes) typeMap[n.type] = (typeMap[n.type] ?? 0) + 1
  return { total: nodes.length, edges: edges.length, byType: typeMap }
})

// ─── resize ──────────────────────────────────────────────────
const ro = typeof ResizeObserver !== 'undefined'
  ? new ResizeObserver(() => chart?.resize())
  : null

onMounted(() => {
  // chartRef 始终在 DOM 中，可以立即 observe
  if (chartRef.value && ro) ro.observe(chartRef.value)
  void loadData()
})

onBeforeUnmount(() => {
  ro?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="mkg-card">
    <!-- 标题 -->
    <div class="mkg-card__header">
      <div>
        <span class="mkg-card__title">MetaKG 知识图谱溯源</span>
        <el-tag size="small" type="info" style="margin-left:8px">实验性</el-tag>
      </div>
      <p class="mkg-card__desc">
        基于 MetaKG 数据集（整合 KEGG / SMPDB / HMDB），展示本项目
        <strong>{{ metaInfo?.n_seed_compounds ?? '…' }} 个代谢物（蓝色）</strong>与通路、反应、酶等实体的一跳关系网络。
        节点可拖拽，滚轮缩放，悬浮查看详细信息。
      </p>
    </div>

    <!-- 加载提示（覆盖在图表上方，不从 DOM 移除 chartRef） -->
    <div v-if="loading" class="mkg-card__loading">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span>正在加载子图数据…</span>
    </div>
    <el-alert v-else-if="errorMsg" type="error" :title="errorMsg" :closable="false" />

    <!-- 控制面板：数据加载完才显示 -->
    <template v-if="!loading && !errorMsg && allNodes.length > 0">
      <div class="mkg-card__controls">
        <!-- 搜索 -->
        <el-input
          v-model="searchKeyword"
          placeholder="搜索代谢物名或 ID（高亮）"
          clearable
          style="width:220px"
          :prefix-icon="Search"
        />

        <!-- 节点类型 -->
        <div class="mkg-ctrl-group">
          <span class="mkg-ctrl-label">节点类型：</span>
          <el-checkbox-group v-model="enabledTypes" size="small">
            <el-checkbox-button
              v-for="(label, t) in TYPE_LABEL"
              :key="t"
              :value="t"
              :style="{ '--btn-color': TYPE_COLOR[t] }"
            >
              <span class="type-dot" :style="{ background: TYPE_COLOR[t] }" />
              {{ label }}
            </el-checkbox-button>
          </el-checkbox-group>
        </div>

        <!-- 关系类型 -->
        <div class="mkg-ctrl-group">
          <span class="mkg-ctrl-label">关系类型：</span>
          <el-checkbox-group v-model="enabledRels" size="small">
            <el-checkbox-button
              v-for="r in availableRelations"
              :key="r"
              :value="r"
            >
              {{ RELATION_LABEL[r] ?? r }}
            </el-checkbox-button>
          </el-checkbox-group>
        </div>

        <!-- 其他选项 -->
        <div class="mkg-ctrl-row">
          <el-switch v-model="seedOnly" active-text="仅展示代谢物直连节点" />
          <div class="mkg-ctrl-label" style="margin-left:16px">最大节点数：</div>
          <el-slider
            v-model="maxNodes"
            :min="50" :max="800" :step="50"
            style="width:160px;margin-left:8px"
            :marks="{ 100: '100', 300: '300', 500: '500' }"
          />
          <span class="mkg-count-badge">{{ maxNodes }}</span>
        </div>
      </div>

      <!-- 统计条 -->
      <div class="mkg-stat-bar">
        <el-tag size="small" type="primary">节点 {{ stats.total }}</el-tag>
        <el-tag size="small" type="info">边 {{ stats.edges }}</el-tag>
        <template v-for="(cnt, t) in stats.byType" :key="t">
          <el-tag
            size="small"
            :style="{ background: (TYPE_COLOR[t] ?? '#94a3b8') + '22', color: TYPE_COLOR[t] ?? '#94a3b8', borderColor: (TYPE_COLOR[t] ?? '#94a3b8') + '55' }"
          >
            <span class="type-dot" :style="{ background: TYPE_COLOR[t] ?? '#94a3b8' }" />
            {{ TYPE_LABEL[t] ?? t }} {{ cnt }}
          </el-tag>
        </template>
        <span v-if="searchKeyword && filteredData.highlightIds.size" class="mkg-hit-tip">
          命中 {{ filteredData.highlightIds.size }} 个节点
        </span>
      </div>
    </template>

    <!-- 图表容器：始终保留在 DOM 中，用 visibility 控制显示 -->
    <div
      ref="chartRef"
      class="mkg-chart"
      :style="{ visibility: (!loading && !errorMsg && allNodes.length > 0) ? 'visible' : 'hidden' }"
    />

    <!-- 图例说明 -->
    <div v-if="!loading && !errorMsg && allNodes.length > 0" class="mkg-legend">
      <div v-for="(color, t) in TYPE_COLOR" :key="t" class="mkg-legend__item">
        <span class="type-dot lg" :style="{ background: color }" />
        <span>{{ TYPE_LABEL[t] ?? t }}</span>
      </div>
      <div class="mkg-legend__item">
        <span class="type-dot lg" style="background:#3b82f6;outline:2px solid #1e40af;outline-offset:1px" />
        <span>本项目代谢物（蓝框）</span>
      </div>
      <div class="mkg-legend__item">
        <span class="type-dot lg" style="background:#fbbf24" />
        <span>搜索命中</span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.mkg-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}

.mkg-card__header { margin-bottom: 12px; }
.mkg-card__title  { font-size: 17px; font-weight: 600; color: #1e293b; }
.mkg-card__desc   { font-size: 13px; color: #64748b; margin: 6px 0 0; line-height: 1.55; }

.mkg-card__loading {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 120px;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
}

/* 控制面板 */
.mkg-card__controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
}

.mkg-ctrl-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.mkg-ctrl-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.mkg-ctrl-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  flex-shrink: 0;
}

.mkg-count-badge {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
  min-width: 36px;
}

/* 统计条 */
.mkg-stat-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.mkg-hit-tip {
  font-size: 12px;
  color: #f59e0b;
  font-weight: 600;
  margin-left: 4px;
}

/* 图表：始终占据高度，用 visibility 控制是否可见 */
.mkg-chart {
  width: 100%;
  height: 560px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;

  @media (max-width: 768px) {
    height: 400px;
  }

  @media (max-width: 480px) {
    height: 300px;
  }
}

/* 图例 */
.mkg-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.mkg-legend__item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #64748b;
}

/* 节点颜色圆点 */
.type-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-dot.lg {
  width: 12px;
  height: 12px;
}

/* checkbox-button 颜色适配 */
:deep(.el-checkbox-button__inner) {
  padding: 2px 8px;
  font-size: 12px;
}
</style>
