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
    grid: { left: 48, right: 24, top: 24, bottom: 32 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: r.map((_, i) => `PC${i + 1}`),
    },
    yAxis: {
      type: 'value',
      name: '解释方差比',
      axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(1)}%` },
    },
    series: [
      {
        type: 'bar',
        data: r.map((v) => Number(v)),
        itemStyle: { color: '#2563eb', borderRadius: [4, 4, 0, 0] },
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
    // 等待 DOM 更新（v-if 切换后 host 才挂载），再执行渲染
    await nextTick()
    render()
  },
  { deep: true },
)
</script>

<template>
  <div class="ev">
    <div class="ev__title">校正后 PCA 解释方差比（前 12 主成分）</div>
    <div v-if="ratios?.length" ref="host" class="ev__chart" />
    <el-empty v-else description="暂无 pca_after_correction.json 中的 explained_variance_ratio" />
  </div>
</template>

<style scoped lang="scss">
.ev {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  padding: 1rem;
  box-shadow: var(--app-shadow);
}

.ev__title {
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.ev__chart {
  width: 100%;
  height: 280px;
}
</style>
