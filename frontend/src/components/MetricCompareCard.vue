<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  before: unknown
  after: unknown
  delta?: unknown
}>()

const deltaStr = computed(() => {
  if (props.delta == null) return '—'
  if (typeof props.delta === 'number') return props.delta.toFixed(4)
  return String(props.delta)
})
</script>

<template>
  <div class="metric">
    <div class="metric__title">{{ title }}</div>
    <div class="metric__row">
      <span class="metric__k">校正前</span>
      <span class="metric__v">{{ before == null ? '—' : String(before) }}</span>
    </div>
    <div class="metric__row">
      <span class="metric__k">校正后</span>
      <span class="metric__v">{{ after == null ? '—' : String(after) }}</span>
    </div>
    <div class="metric__row metric__row--delta">
      <span class="metric__k">Δ</span>
      <span class="metric__v">{{ deltaStr }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.metric {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  padding: 1rem 1.15rem;
  box-shadow: var(--app-shadow);
}

.metric__title {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
  color: var(--app-text);
}

.metric__row {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  padding: 0.2rem 0;

  &--delta {
    border-top: 1px dashed var(--app-border);
    margin-top: 0.35rem;
    padding-top: 0.5rem;
    font-weight: 600;
  }
}

.metric__k {
  color: var(--app-muted);
}

.metric__v {
  font-variant-numeric: tabular-nums;
}
</style>
