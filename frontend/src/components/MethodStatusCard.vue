<script setup lang="ts">
import { InfoFilled } from '@element-plus/icons-vue'
import type { BatchCorrectionReport } from '@/types/benchmark'

defineProps<{
  report: BatchCorrectionReport | null
  loading?: boolean
}>()
</script>

<template>
  <div class="method card-panel card-panel--flat">
    <h3 class="section-heading">方法说明</h3>
    <el-skeleton v-if="loading" :rows="6" animated />
    <template v-else-if="report">

      <!-- ComBat 实现状态横幅 -->
      <el-alert
        v-if="report.strict_combat?.status === 'implemented'"
        type="success"
        :closable="false"
        show-icon
        class="method__banner"
        title="ComBat-like 校正已实现（neuroCombat）"
        :description="report.strict_combat?.note ?? 'ComBat（Johnson et al., 2007）经验 Bayes 实现（neuroCombat 库），可与 baseline 对比评估。'"
      />
      <el-alert
        v-else
        type="warning"
        :closable="false"
        show-icon
        class="method__banner"
        title="当前主链路展示 baseline 批次校正"
        description="主页结果展示为 baseline（per-feature location-scale 对齐）。ComBat-like 校正（neuroCombat）已实现，可在方法对比区块查看对比结果。"
      />

      <div class="method__grid">
        <!-- Baseline 信息 -->
        <div class="method__block">
          <div class="method__sub">主链路方法（Baseline）</div>
          <p class="method__mono">{{ report.baseline_batch_correction?.method_id ?? '—' }}</p>
          <p class="method__note">{{ report.baseline_batch_correction?.what_it_is }}</p>
        </div>

        <!-- ComBat 信息 -->
        <div class="method__block">
          <div class="method__sub">ComBat-like 校正（对比方法）</div>
          <el-tag
            :type="report.strict_combat?.status === 'implemented' ? 'success' : 'warning'"
            effect="light"
            class="method__tag"
          >
            {{ report.strict_combat?.status === 'implemented' ? '已实现（neuroCombat）' : '未实现' }}
          </el-tag>
          <p class="method__note method__note--small">
            <template v-if="report.strict_combat?.status === 'implemented'">
              库：{{ report.strict_combat?.library ?? 'neuroCombat' }}<br />
              参考：{{ report.strict_combat?.reference ?? 'Johnson et al., 2007' }}
            </template>
            <template v-else>
              {{ report.strict_combat?.note }}
            </template>
          </p>
        </div>
      </div>

      <!-- 方法对比说明 -->
      <div class="method__compare-note">
        <el-icon style="color: var(--app-primary); margin-right: 0.4rem"><InfoFilled /></el-icon>
        <span>
          主链路 KPI 与 PCA 图展示 <strong>baseline</strong>（逐特征位置尺度对齐）校正结果；
          <strong>combat-like（neuroCombat）vs baseline</strong> 的指标对比见下方「方法对比实验（evaluation）」区块。
        </span>
      </div>

      <!-- Baseline 假设 & 局限 -->
      <div v-if="report.baseline_batch_correction?.assumptions?.length" class="method__list">
        <div class="method__sub">Baseline 方法假设</div>
        <ul>
          <li v-for="(a, i) in report.baseline_batch_correction?.assumptions" :key="i">{{ a }}</li>
        </ul>
      </div>
      <div v-if="report.baseline_batch_correction?.limitations?.length" class="method__list">
        <div class="method__sub">Baseline 方法局限</div>
        <ul>
          <li v-for="(a, i) in report.baseline_batch_correction?.limitations" :key="i">{{ a }}</li>
        </ul>
      </div>

    </template>
    <el-empty v-else description="暂无 batch_correction_method_report.json（请先运行 merged pipeline）" />
  </div>
</template>

<style scoped lang="scss">
.method__banner {
  margin-bottom: 1.25rem;
}

.method__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.method__block {
  padding: 0.9rem 1rem;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #f8faff;
}

.method__sub {
  font-size: 0.78rem;
  color: var(--app-muted);
  margin-bottom: 0.4rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.method__mono {
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
  color: var(--app-text);
  word-break: break-all;
}

.method__tag {
  margin-bottom: 0.5rem;
}

.method__note {
  font-size: 0.85rem;
  color: var(--app-muted);
  margin: 0;
  line-height: 1.55;

  &--small {
    font-size: 0.8rem;
  }
}

.method__compare-note {
  display: flex;
  align-items: flex-start;
  gap: 0.25rem;
  font-size: 0.86rem;
  color: var(--app-text-2);
  background: rgba(37, 99, 235, 0.06);
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  margin-bottom: 1.25rem;
  line-height: 1.55;
}

.method__list {
  margin-top: 0.9rem;

  ul {
    margin: 0.25rem 0 0;
    padding-left: 1.25rem;
    font-size: 0.85rem;
    color: var(--app-text);
    line-height: 1.6;
  }
}
</style>
