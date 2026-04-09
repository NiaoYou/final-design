<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  before: unknown
  after: unknown
  delta?: unknown
  /**
   * 当 delta 为正时是否表示"好"。
   * - 默认 false：delta < 0 = 好（如 batch_centroid_separation / silhouette_batch_id，越低越好）
   * - true：delta > 0 = 好（如 silhouette_group_label，越高越好，说明生物信号保留越好）
   */
  positiveIsGood?: boolean
  /** 可选的指标解释提示文字，悬浮时显示 */
  hint?: string
}>()

const deltaNum = computed(() => {
  if (typeof props.delta === 'number') return props.delta
  return null
})

const deltaStr = computed(() => {
  if (deltaNum.value == null) return '—'
  return (deltaNum.value >= 0 ? '+' : '') + deltaNum.value.toFixed(4)
})

const deltaGood = computed(() => {
  if (deltaNum.value == null) return null
  return props.positiveIsGood ? deltaNum.value > 0 : deltaNum.value < 0
})

function fmt(v: unknown) {
  if (v == null) return '—'
  if (typeof v === 'number') return v.toFixed(4)
  return String(v)
}
</script>

<template>
  <div class="metric">
    <div class="metric__title">
      {{ title }}
      <span v-if="hint" class="metric__hint" :title="hint">(?)</span>
    </div>

    <div class="metric__compare">
      <!-- Before -->
      <div class="metric__col">
        <div class="metric__col-label">校正前</div>
        <div class="metric__col-value metric__col-value--before">{{ fmt(before) }}</div>
      </div>

      <!-- Arrow -->
      <div class="metric__arrow">
        <svg width="28" height="16" viewBox="0 0 28 16" fill="none">
          <path d="M1 8h22M19 3l6 5-6 5" stroke="currentColor" stroke-width="1.8"
            stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>

      <!-- After -->
      <div class="metric__col">
        <div class="metric__col-label">校正后</div>
        <div class="metric__col-value metric__col-value--after">{{ fmt(after) }}</div>
      </div>
    </div>

    <!-- Delta badge -->
    <div
      class="metric__delta"
      :class="{
        'metric__delta--good': deltaGood === true,
        'metric__delta--bad':  deltaGood === false,
        'metric__delta--neutral': deltaGood === null,
      }"
    >
      <span class="metric__delta-label">Δ</span>
      <span class="metric__delta-value">{{ deltaStr }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.metric {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  padding: 1.1rem 1.2rem;
  box-shadow: var(--app-shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--app-shadow-md);
  }
}

.metric__title {
  font-size: 0.78rem;
  font-weight: 700;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  color: var(--app-muted);
  margin-bottom: 0.9rem;
  word-break: break-all;
  line-height: 1.4;
  display: flex;
  align-items: flex-start;
  gap: 4px;
  flex-wrap: wrap;
}

.metric__hint {
  font-size: 0.68rem;
  color: var(--app-muted-light);
  cursor: help;
  opacity: 0.7;
  font-family: sans-serif;
  flex-shrink: 0;
  margin-top: 1px;

  &:hover { opacity: 1; }
}

.metric__compare {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.metric__col {
  flex: 1;
  text-align: center;
}

.metric__col-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--app-muted-light);
  margin-bottom: 0.25rem;
}

.metric__col-value {
  font-size: 1.15rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;

  &--before {
    color: #94a3b8;
    text-decoration: line-through;
    text-decoration-color: rgba(148,163,184,.5);
  }

  &--after {
    color: var(--app-text);
  }
}

.metric__arrow {
  color: var(--app-muted-light);
  flex-shrink: 0;
}

.metric__delta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;

  &--good {
    background: rgba(16,185,129,.1);
    color: #059669;
    border: 1px solid rgba(16,185,129,.2);
  }

  &--bad {
    background: rgba(239,68,68,.08);
    color: #dc2626;
    border: 1px solid rgba(239,68,68,.15);
  }

  &--neutral {
    background: var(--app-bg);
    color: var(--app-muted);
    border: 1px solid var(--app-border);
  }
}

.metric__delta-label {
  font-size: 0.75rem;
  opacity: 0.7;
}

.metric__delta-value {
  font-size: 0.92rem;
}
</style>
