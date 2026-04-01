<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  ratios: number[] | undefined
}>()

const host = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!host.value) return
  if (!chart) chart = echarts.init(host.value)
  const r = props.ratios?.length ? props.ratios.slice(0, 12) : []
  chart.setOption({
    grid: { left: 52, right: 16, top: 28, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b',
      borderColor: 'transparent',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
        const p = Array.isArray(params) ? params[0] : params
        return `${p.name}<br/><strong>${((p.value as number) * 100).toFixed(2)}%</strong>`
      },
    },
    xAxis: {
      type: 'category',
      data: r.map((_, i) => `PC${i + 1}`),
      axisLabel: { fontSize: 11, color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '解释方差比',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: {
        formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
        fontSize: 11,
        color: '#64748b',
      },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [
      {
        type: 'bar',
        data: r.map((v) => Number(v)),
        itemStyle: {
          borderRadius: [5, 5, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#06b6d4' },
          ]),
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2563eb' },
              { offset: 1, color: '#0891b2' },
            ]),
          },
        },
        barMaxWidth: 36,
      },
    ],
  })
}

onMounted(() => {
  render()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
  chart = null
})

function resize() {
  chart?.resize()
}

watch(
  () => props.ratios,
  async () => {
    await nextTick()
    render()
  },
  { deep: true },
)
</script>

<template>
  <div class="ev">
    <div class="ev__header">
      <div class="ev__icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="1" y="10" width="3" height="5" rx="1" fill="#3b82f6"/>
          <rect x="5.5" y="6" width="3" height="9" rx="1" fill="#06b6d4"/>
          <rect x="10" y="2" width="3" height="13" rx="1" fill="#8b5cf6"/>
          <rect x="14.5" y="7" width="0" height="0"/>
        </svg>
      </div>
      <span class="ev__title">校正后 PCA 解释方差比（前 12 主成分）</span>
    </div>
    <div v-if="ratios?.length" ref="host" class="ev__chart" />
    <el-empty v-else description="暂无 pca_after_correction.json 中的 explained_variance_ratio" />
  </div>
</template>

<style scoped lang="scss">
.ev {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  padding: 1rem 1rem 0.75rem;
  box-shadow: var(--app-shadow);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: var(--app-shadow-md);
  }
}

.ev__header {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.75rem;
}

.ev__icon {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: rgba(37,99,235,.07);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ev__title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--app-text);
}

.ev__chart {
  width: 100%;
  height: 280px;
}
</style>
