<script setup lang="ts">
import type { BatchCorrectionReport } from '@/types/benchmark'

defineProps<{
  report: BatchCorrectionReport | null
  loading?: boolean
}>()
</script>

<template>
  <div class="method card-panel card-panel--flat">
    <h3 class="method__h">方法说明</h3>
    <el-skeleton v-if="loading" :rows="6" animated />
    <template v-else-if="report">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="method__banner"
        title="当前实现的是 baseline 批次校正"
        description="本页展示的批次校正结果为 baseline（per-feature batch location-scale，见报告内 method_id）。strict ComBat（经验 Bayes 等）尚未在本项目中实现，请勿与 baseline 混称。"
      />
      <div class="method__grid">
        <div>
          <div class="method__sub">Baseline 方法</div>
          <p class="method__mono">{{ report.baseline_batch_correction?.method_id ?? '—' }}</p>
          <p class="method__note">{{ report.baseline_batch_correction?.implementation_note }}</p>
        </div>
        <div>
          <div class="method__sub">strict ComBat 状态</div>
          <el-tag type="warning" effect="plain">{{ report.strict_combat?.status ?? '未实现' }}</el-tag>
          <p class="method__note">{{ report.strict_combat?.note }}</p>
        </div>
      </div>
      <div v-if="report.baseline_batch_correction?.assumptions?.length" class="method__list">
        <div class="method__sub">方法假设</div>
        <ul>
          <li v-for="(a, i) in report.baseline_batch_correction?.assumptions" :key="i">{{ a }}</li>
        </ul>
      </div>
      <div v-if="report.baseline_batch_correction?.limitations?.length" class="method__list">
        <div class="method__sub">方法局限</div>
        <ul>
          <li v-for="(a, i) in report.baseline_batch_correction?.limitations" :key="i">{{ a }}</li>
        </ul>
      </div>
    </template>
    <el-empty v-else description="暂无 batch_correction_method_report.json（请先运行 merged baseline 流程）" />
  </div>
</template>

<style scoped lang="scss">
.method__h {
  margin: 0 0 1rem;
  font-size: 1.05rem;
}

.method__banner {
  margin-bottom: 1rem;
}

.method__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.method__sub {
  font-size: 0.8rem;
  color: var(--app-muted);
  margin-bottom: 0.35rem;
}

.method__mono {
  font-family: ui-monospace, monospace;
  font-size: 0.9rem;
  margin: 0 0 0.5rem;
}

.method__note {
  font-size: 0.88rem;
  color: var(--app-muted);
  margin: 0;
  line-height: 1.5;
}

.method__list {
  margin-top: 1rem;

  ul {
    margin: 0.25rem 0 0;
    padding-left: 1.25rem;
    font-size: 0.88rem;
    color: var(--app-text);
  }
}
</style>
