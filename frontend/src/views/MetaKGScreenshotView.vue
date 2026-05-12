<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchMetakgSubgraph } from '@/api/benchmark'
import type { MetaKGNode, MetaKGEdge } from '@/api/benchmark'

// ─── 配色 ────────────────────────────────────────────────────
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
}

// ─── 状态 ─────────────────────────────────────────────────────
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const loading   = ref(true)
const errorMsg  = ref('')
const statText  = ref('')
const metaSeeds = ref(0)

// ─── 加载 + 渲染 ─────────────────────────────────────────────
async function loadAndRender() {
  loading.value = true
  errorMsg.value = ''
  try {
    // 只取 4 类节点、4 类关系，减小数据量
    const sg = await fetchMetakgSubgraph({
      nodeTypes:     'Compound,Pathway,Enzyme,Reaction',
      relationTypes: 'has_pathway,has_reaction,has_enzyme,has_module',
    })

    const allNodes: MetaKGNode[] = sg.nodes
    const allEdges: MetaKGEdge[] = sg.edges
    metaSeeds.value = sg.meta?.n_seed_compounds ?? 0

    // ── 优先级裁剪到 300 个节点 ──────────────────────────────
    const MAX = 300
    let nodes = allNodes
    let edges = allEdges

    if (nodes.length > MAX) {
      // 计算每个节点的度数
      const deg = new Map<string, number>()
      for (const e of edges) {
        deg.set(e.head, (deg.get(e.head) ?? 0) + 1)
        deg.set(e.tail, (deg.get(e.tail) ?? 0) + 1)
      }
      // 边的连通结构是 Compound <-> Pathway/Enzyme/Reaction
      // 优先保留 seed Compound（本项目代谢物），再加高度数的 Pathway/Enzyme/Reaction
      // 最后用普通 Compound 补足，保证图中有大量连边可见
      const byDeg = (a: MetaKGNode, b: MetaKGNode) =>
        (deg.get(b.id) ?? 0) - (deg.get(a.id) ?? 0)

      const seedNodes    = nodes.filter(n => n.is_seed).sort(byDeg)
      const pathwayNodes = nodes.filter(n => n.type === 'Pathway').sort(byDeg)
      const enzymeNodes  = nodes.filter(n => n.type === 'Enzyme').sort(byDeg)
      const reactionNodes= nodes.filter(n => n.type === 'Reaction').sort(byDeg)
      const otherCompound= nodes.filter(n => n.type === 'Compound' && !n.is_seed).sort(byDeg)

      // 配额：seed全保留（≤977），其余按比例填满 500
      const nSeed    = Math.min(seedNodes.length, 80)
      const nPathway = Math.min(pathwayNodes.length, 90)
      const nEnzyme  = Math.min(enzymeNodes.length, 70)
      const nReaction= Math.min(reactionNodes.length, 40)
      const nOther   = Math.max(0, MAX - nSeed - nPathway - nEnzyme - nReaction)

      nodes = [
        ...seedNodes.slice(0, nSeed),
        ...pathwayNodes.slice(0, nPathway),
        ...enzymeNodes.slice(0, nEnzyme),
        ...reactionNodes.slice(0, nReaction),
        ...otherCompound.slice(0, nOther),
      ].slice(0, MAX)

      const keepIds = new Set(nodes.map(n => n.id))
      edges = edges.filter(e => keepIds.has(e.head) && keepIds.has(e.tail))
    }

    // 统计
    const typeCnt: Record<string, number> = {}
    for (const n of nodes) typeCnt[n.type] = (typeCnt[n.type] ?? 0) + 1
    statText.value = `节点 ${nodes.length}  边 ${edges.length}  `
      + Object.entries(typeCnt)
          .map(([t, c]) => `${TYPE_LABEL[t] ?? t} ${c}`)
          .join('  ')

    // ── 渲染 ECharts ─────────────────────────────────────────
    loading.value = false
    await nextTick()
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value, undefined, { renderer: 'svg' })
    chart.resize()

    // 只给度数最高的 Top-30 通路节点显示标签，其余靠 tooltip
    const deg2 = new Map<string, number>()
    for (const e of edges) {
      deg2.set(e.head, (deg2.get(e.head) ?? 0) + 1)
      deg2.set(e.tail, (deg2.get(e.tail) ?? 0) + 1)
    }
    const topPathwayIds = new Set(
      nodes
        .filter(n => n.type === 'Pathway')
        .sort((a, b) => (deg2.get(b.id) ?? 0) - (deg2.get(a.id) ?? 0))
        .slice(0, 30)
        .map(n => n.id)
    )

    const eNodes = nodes.map(n => {
      const color = TYPE_COLOR[n.type] ?? '#94a3b8'
      const name  = n.metabolite_name || n.label
      const showLabel = topPathwayIds.has(n.id)   // 仅 Top-30 通路显示标签
      return {
        id:        n.id,
        name,
        node_type: n.type,
        is_seed:   n.is_seed,
        symbolSize: n.type === 'Pathway' ? 18 : n.type === 'Enzyme' ? 12 : n.is_seed ? 14 : 7,
        itemStyle: {
          color,
          borderColor: n.is_seed ? '#1d4ed8' : n.type === 'Pathway' ? '#c2410c' : 'transparent',
          borderWidth: n.is_seed ? 3 : n.type === 'Pathway' ? 3 : 0,
        },
        label: {
          show:      showLabel,
          formatter: name.length > 16 ? name.slice(0, 15) + '…' : name,
          fontSize:  10,
          color:     '#1e293b',
          fontWeight: 500,
        },
      }
    })

    const eEdges = edges.map(e => ({
      source:    e.head,
      target:    e.tail,
      relation:  e.relation,
      lineStyle: { color: '#cbd5e1', width: 1, opacity: 0.6, curveness: 0.08 },
    }))

    chart.setOption({
      backgroundColor: '#ffffff',
      series: [{
        type:      'graph',
        layout:    'force',
        animation: true,
        animationDuration: 3000,
        data:      eNodes,
        edges:     eEdges,
        roam:      false,
        draggable: false,
        center:    ['50%', '50%'],
        zoom:      1.1,
        force: {
          initLayout: 'circular',
          repulsion:  nodes.length > 300 ? 55 : 90,
          edgeLength: [25, 90],
          gravity:    0.06,
          friction:   0.65,
          layoutAnimation: true,
        },
        // ECharts 内置自动去重叠：隐藏被遮挡的标签，保留间距最大的那些
        labelLayout: {
          hideOverlap: true,
        },
        emphasis: {
          focus:     'adjacency',
          scale:     true,
          lineStyle: { width: 2.5, opacity: 1 },
        },
        edgeSymbol:     ['none', 'arrow'],
        edgeSymbolSize: 5,
      }],
    }, { notMerge: true })

  } catch (e: any) {
    loading.value = false
    errorMsg.value = e?.response?.data?.detail ?? e?.message ?? '加载失败'
  }
}

const ro = typeof ResizeObserver !== 'undefined'
  ? new ResizeObserver(() => chart?.resize())
  : null

onMounted(() => {
  if (chartRef.value && ro) ro.observe(chartRef.value)
  void loadAndRender()
})
onBeforeUnmount(() => {
  ro?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="shot-page">
    <!-- 标题 -->
    <div class="shot-header">
      <div class="shot-title">MetaKG 知识图谱溯源</div>
      <div class="shot-desc">
        基于 MetaKG（整合 KEGG / SMPDB / HMDB），展示
        <strong>{{ metaSeeds }} 个代谢物</strong>
        与通路、生化反应、酶等实体的一跳关系网络
        &nbsp;·&nbsp; 显示节点上限 300
      </div>
    </div>

    <!-- 统计条 -->
    <div v-if="statText" class="shot-stat">
      <span
        v-for="seg in statText.split('  ').filter(Boolean)"
        :key="seg"
        class="stat-chip"
      >{{ seg }}</span>
    </div>

    <div v-if="loading"  class="shot-center">正在加载子图数据…</div>
    <div v-if="errorMsg" class="shot-error">{{ errorMsg }}</div>

    <!-- 图表 -->
    <div
      ref="chartRef"
      class="shot-chart"
      :style="{ visibility: !loading && !errorMsg ? 'visible' : 'hidden' }"
    />

    <!-- 图例 -->
    <div v-if="!loading && !errorMsg" class="shot-legend">
      <div v-for="(color, t) in TYPE_COLOR" :key="t" class="leg-item">
        <span class="dot" :style="{ background: color }" />
        {{ TYPE_LABEL[t as string] ?? t }}
      </div>
      <div class="leg-item">
        <span class="dot seed" />
        本项目代谢物（蓝框）
      </div>
    </div>
  </div>
</template>

<style scoped>
* { box-sizing: border-box; }
.shot-page {
  width: 100vw;
  min-height: 100vh;
  background: #f8fafc;
  padding: 18px 28px 24px;
  font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
}
.shot-header { margin-bottom: 10px; }
.shot-title  { font-size: 19px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.shot-desc   { font-size: 13px; color: #64748b; line-height: 1.5; }

.shot-stat {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.stat-chip {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 500;
}

.shot-chart {
  width: 100%;
  height: 680px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 6px rgba(0,0,0,.06);
}

.shot-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 12px;
  padding-top: 11px;
  border-top: 1px solid #e2e8f0;
}
.leg-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #64748b;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot.seed {
  background: #3b82f6;
  outline: 2.5px solid #1d4ed8;
  outline-offset: 1px;
}

.shot-center { text-align: center; padding: 60px; color: #94a3b8; font-size: 14px; }
.shot-error  { text-align: center; padding: 40px; color: #ef4444; font-size: 14px; }
</style>
