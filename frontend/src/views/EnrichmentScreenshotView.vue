<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchPathwayEnrichment } from '@/api/benchmark'
import type { PathwayItem } from '@/api/benchmark'

// 预设参数
const GROUP1 = 'P1_AA_0001'
const GROUP2 = 'P1_AA_1024'
const FC_THR = 1.0
const P_THR  = 0.05

const bubbleRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const loading  = ref(true)
const errorMsg = ref('')
const pathways = ref<PathwayItem[]>([])
const statText = ref('')

async function loadAndRender() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await fetchPathwayEnrichment(GROUP1, GROUP2, FC_THR, P_THR, true, 20)
    if (!res.available) {
      errorMsg.value = res.reason ?? '无富集结果'
      loading.value = false
      return
    }
    const items = (res.pathways ?? [])
      .sort((a, b) => a.qvalue - b.qvalue)
      .slice(0, 18)
    pathways.value = items

    statText.value = [
      `显著通路 ${res.n_sig_pathways ?? items.length}`,
      `显著代谢物 ${res.n_sig_features ?? '—'}`,
      `背景代谢物 ${res.n_bg_features ?? '—'}`,
      `测试通路数 ${res.n_pathways_tested ?? '—'}`,
    ].join('  ')

    loading.value = false
    await nextTick()
    if (!bubbleRef.value) return
    if (!chart) chart = echarts.init(bubbleRef.value, undefined, { renderer: 'svg' })
    chart.resize()
    renderBubble(items)
  } catch (e: any) {
    loading.value = false
    errorMsg.value = e?.response?.data?.detail ?? e?.message ?? '加载失败'
  }
}

function renderBubble(items: PathwayItem[]) {
  if (!chart) return
  const names = items.map(p => p.pathway_name)
  const yPos  = names.map((_, i) => items.length - 1 - i)
  const qvals = items.map(p => -Math.log10(Math.max(p.qvalue, 1e-300)))
  const maxQ  = Math.max(...qvals)

  chart.setOption({
    backgroundColor: '#ffffff',
    grid: { left: 220, right: 100, top: 30, bottom: 50 },
    xAxis: {
      type: 'value',
      name: 'Rich Factor',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { fontSize: 12, color: '#475569' },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      min: -0.5, max: items.length - 0.5,
      axisLabel: {
        formatter: (v: number) => {
          const idx = items.length - 1 - Math.round(v)
          if (idx < 0 || idx >= items.length) return ''
          const n = names[idx]
          return n.length > 28 ? n.slice(0, 27) + '…' : n
        },
        fontSize: 11,
        color: '#334155',
      },
      axisTick: { show: false },
      axisLine: { show: false },
      splitLine: { show: false },
    },
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const item = items[items.length - 1 - Math.round(p.data[1])]
        if (!item) return ''
        return [
          `<b>${item.pathway_name}</b>`,
          `Rich Factor: ${item.rich_factor.toFixed(3)}`,
          `Hits: ${item.hits} / ${item.pathway_size}`,
          `q 值: ${item.qvalue.toExponential(2)}`,
        ].join('<br/>')
      },
    },
    visualMap: {
      show: true,
      min: 0, max: maxQ,
      dimension: 2,
      orient: 'vertical',
      right: 12, top: 'center',
      text: ['高', '低'],
      textStyle: { fontSize: 11, color: '#64748b' },
      inRange: { color: ['#bfdbfe', '#2563eb'] },
      seriesIndex: 0,
    },
    series: [{
      type: 'scatter',
      data: items.map((p, i) => [
        p.rich_factor,
        yPos[i],
        -Math.log10(Math.max(p.qvalue, 1e-300)),
        p.hits,
      ]),
      symbolSize: (d: number[]) => Math.max(10, Math.min(40, d[3] * 5)),
      itemStyle: { opacity: 0.9, borderColor: '#fff', borderWidth: 1 },
    }],
  }, { notMerge: true })
}

onMounted(() => void loadAndRender())
onUnmounted(() => { chart?.dispose(); chart = null })
</script>

<template>
  <div class="shot-page">
    <div class="shot-header">
      <div class="shot-title">KEGG 通路富集气泡图</div>
      <div class="shot-desc">
        对照组 <strong>{{ GROUP1 }}</strong> vs 实验组 <strong>{{ GROUP2 }}</strong>
        &nbsp;·&nbsp; BH-FDR 校正，q &lt; {{ P_THR }}；气泡大小 = 命中代谢物数；颜色深浅 = −log₁₀(q)
      </div>
    </div>

    <div v-if="statText" class="shot-stat">
      <span v-for="seg in statText.split('  ').filter(Boolean)" :key="seg" class="stat-chip">
        {{ seg }}
      </span>
    </div>

    <div v-if="loading"  class="shot-center">正在调用 KEGG API 运行富集分析，首次约需 30s…</div>
    <div v-if="errorMsg" class="shot-error">{{ errorMsg }}</div>

    <div v-if="!loading && !errorMsg" class="shot-body">
      <!-- 气泡图 -->
      <div ref="bubbleRef" class="shot-chart" />

      <!-- 通路明细表 -->
      <div class="shot-table-wrap">
        <div class="table-title">显著富集通路（按 q 值排序，前 {{ pathways.length }} 条）</div>
        <table class="enrich-table">
          <thead>
            <tr>
              <th>通路名称</th>
              <th>Hits</th>
              <th>Rich Factor</th>
              <th>q 值</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in pathways" :key="p.pathway_id">
              <td class="name-cell">{{ p.pathway_name }}</td>
              <td>{{ p.hits }}/{{ p.pathway_size }}</td>
              <td>{{ p.rich_factor.toFixed(3) }}</td>
              <td>{{ p.qvalue.toExponential(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
* { box-sizing: border-box; }
.shot-page {
  width: 100vw; min-height: 100vh;
  background: #f8fafc;
  padding: 18px 28px 24px;
  font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
}
.shot-header { margin-bottom: 10px; }
.shot-title  { font-size: 19px; font-weight: 700; color: #1e293b; margin-bottom: 3px; }
.shot-desc   { font-size: 13px; color: #64748b; }

.shot-stat { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.stat-chip {
  background: #eff6ff; color: #2563eb;
  border: 1px solid #bfdbfe; border-radius: 10px;
  padding: 2px 10px; font-size: 12px; font-weight: 500;
}

.shot-body { display: flex; gap: 20px; align-items: flex-start; }
.shot-chart {
  flex: 1; height: 620px;
  background: #fff; border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 6px rgba(0,0,0,.06);
}

.shot-table-wrap { width: 280px; flex-shrink: 0; }
.table-title { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 8px; }
.enrich-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.enrich-table th {
  background: #f1f5f9; color: #475569;
  padding: 5px 6px; text-align: left;
  font-weight: 600; border-bottom: 1px solid #e2e8f0;
}
.enrich-table td { padding: 4px 6px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.name-cell { max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.shot-center { text-align: center; padding: 60px; color: #94a3b8; font-size: 14px; }
.shot-error  { text-align: center; padding: 40px; color: #ef4444; font-size: 14px; }
</style>
