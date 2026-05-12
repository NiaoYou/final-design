<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchDiffAnalysis } from '@/api/benchmark'
import type { DiffFeature } from '@/types/benchmark'

// 预设参数：P1_AA_0001 vs P1_AA_1024
const GROUP1 = 'P1_AA_0001'
const GROUP2 = 'P1_AA_1024'
const FC_THR = 1.0
const P_THR  = 0.05

const COLOR = { up: '#ef4444', down: '#3b82f6', ns: '#cbd5e1' }

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const loading  = ref(true)
const errorMsg = ref('')
const statText = ref('')
type TableRow = { name: string; log2fc: number; pval: number; qval: number; label: string }
const tableRows = ref<TableRow[]>([])

async function loadAndRender() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await fetchDiffAnalysis(GROUP1, GROUP2, FC_THR, P_THR, true)
    const features: DiffFeature[] = res.features ?? []

    const up   = features.filter(f => f.label === 'up')
    const down = features.filter(f => f.label === 'down')
    const ns   = features.filter(f => f.label === 'ns')
    statText.value = `上调 ${up.length}  下调 ${down.length}  无显著 ${ns.length}  共 ${features.length} 个特征`

    // 表格：显著特征按 |log2fc| 降序，取前 12 行
    tableRows.value = features
      .filter(f => f.label !== 'ns')
      .sort((a, b) => Math.abs(b.log2fc) - Math.abs(a.log2fc))
      .slice(0, 12)
      .map(f => ({
        name:   f.metabolite_name || f.feature,
        log2fc: f.log2fc,
        pval:   f.pvalue,
        qval:   f.qvalue,
        label:  f.label,
      }))

    loading.value = false
    await nextTick()
    if (!chartRef.value) return
    if (!chart) chart = echarts.init(chartRef.value, undefined, { renderer: 'svg' })
    chart.resize()

    // 散点数据
    const makeSeries = (data: DiffFeature[], color: string, name: string) => ({
      name,
      type: 'scatter',
      symbolSize: 6,
      itemStyle: { color, opacity: 0.82 },
      data: data.map(f => [f.log2fc, -Math.log10(Math.max(f.qvalue, 1e-300))]),
    })

    const xMax = Math.max(...features.map(f => Math.abs(f.log2fc))) * 1.08

    chart.setOption({
      backgroundColor: '#ffffff',
      grid: { left: 60, right: 30, top: 30, bottom: 50 },
      xAxis: {
        type: 'value',
        min: -xMax, max: xMax,
        name: `log₂FC（${GROUP2} / ${GROUP1}）`,
        nameLocation: 'middle',
        nameGap: 32,
        nameTextStyle: { fontSize: 12, color: '#475569' },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      yAxis: {
        type: 'value',
        name: '−log₁₀(q)',
        nameLocation: 'middle',
        nameGap: 40,
        nameTextStyle: { fontSize: 12, color: '#475569' },
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      legend: {
        top: 8, right: 12,
        data: ['上调', '下调', '无显著'],
        textStyle: { fontSize: 12, color: '#475569' },
      },
      tooltip: {
        trigger: 'item',
        formatter: (p: any) => {
          const [fc, nlp] = p.data as number[]
          return `log2FC: ${fc.toFixed(3)}<br/>−log10(q): ${nlp.toFixed(3)}`
        },
      },
      // 阈值线
      markLine: { silent: true },
      series: [
        {
          ...makeSeries(up, COLOR.up, '上调'),
          markLine: {
            silent: true,
            lineStyle: { color: '#94a3b8', type: 'dashed', width: 1 },
            data: [
              { xAxis: FC_THR },
              { xAxis: -FC_THR },
              { yAxis: -Math.log10(P_THR) },
            ],
            label: { show: false },
          },
        },
        makeSeries(down, COLOR.down, '下调'),
        makeSeries(ns, COLOR.ns, '无显著'),
      ],
    }, { notMerge: true })
  } catch (e: any) {
    loading.value = false
    errorMsg.value = e?.response?.data?.detail ?? e?.message ?? '加载失败'
  }
}

onMounted(() => void loadAndRender())
onUnmounted(() => { chart?.dispose(); chart = null })
</script>

<template>
  <div class="shot-page">
    <div class="shot-header">
      <div class="shot-title">差异代谢物火山图</div>
      <div class="shot-desc">
        对照组 <strong>{{ GROUP1 }}</strong> vs 实验组 <strong>{{ GROUP2 }}</strong>
        &nbsp;·&nbsp; |log₂FC| ≥ {{ FC_THR }} &amp; q &lt; {{ P_THR }}（BH-FDR 校正）
      </div>
    </div>

    <div v-if="statText" class="shot-stat">
      <span v-for="seg in statText.split('  ').filter(Boolean)" :key="seg" class="stat-chip">
        {{ seg }}
      </span>
    </div>

    <div v-if="loading"  class="shot-center">正在运行差异分析…</div>
    <div v-if="errorMsg" class="shot-error">{{ errorMsg }}</div>

    <div class="shot-body" v-if="!loading && !errorMsg">
      <!-- 火山图 -->
      <div ref="chartRef" class="shot-chart" />

      <!-- 差异代谢物表格 -->
      <div class="shot-table-wrap">
        <div class="table-title">显著差异代谢物（按 |log₂FC| 排序，前 12 条）</div>
        <table class="diff-table">
          <thead>
            <tr>
              <th>代谢物</th>
              <th>log₂FC</th>
              <th>q 值</th>
              <th>调控方向</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in tableRows" :key="r.name">
              <td class="name-cell">{{ r.name }}</td>
              <td :class="r.label === 'up' ? 'up' : 'down'">{{ r.log2fc.toFixed(3) }}</td>
              <td>{{ r.qval.toExponential(2) }}</td>
              <td>
                <span class="badge" :class="r.label">{{ r.label === 'up' ? '上调' : '下调' }}</span>
              </td>
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
  flex: 1; height: 580px;
  background: #fff; border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 6px rgba(0,0,0,.06);
}

.shot-table-wrap { width: 320px; flex-shrink: 0; }
.table-title { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 8px; }
.diff-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.diff-table th {
  background: #f1f5f9; color: #475569;
  padding: 6px 8px; text-align: left;
  font-weight: 600; border-bottom: 1px solid #e2e8f0;
}
.diff-table td { padding: 5px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.name-cell { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.up   { color: #dc2626; font-weight: 600; }
.down { color: #2563eb; font-weight: 600; }
.badge {
  display: inline-block; padding: 1px 7px; border-radius: 8px;
  font-size: 11px; font-weight: 600;
}
.badge.up   { background: #fee2e2; color: #dc2626; }
.badge.down { background: #dbeafe; color: #2563eb; }

.shot-center { text-align: center; padding: 60px; color: #94a3b8; font-size: 14px; }
.shot-error  { text-align: center; padding: 40px; color: #ef4444; font-size: 14px; }
</style>
