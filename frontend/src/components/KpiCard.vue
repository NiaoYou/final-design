<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  hint?: string
}>()
</script>

<template>
  <div class="kpi">
    <div class="kpi__label">{{ label }}</div>
    <div class="kpi__value">{{ value }}</div>
    <div v-if="hint" class="kpi__hint">{{ hint }}</div>
  </div>
</template>

<style scoped lang="scss">
.kpi {
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 1rem 1.25rem;
  box-shadow: var(--app-shadow);
  min-height: 96px;
}

.kpi__label {
  font-size: 0.8rem;
  color: var(--app-muted);
  margin-bottom: 0.35rem;
}

.kpi__value {
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--app-text);
}

.kpi__hint {
  margin-top: 0.35rem;
  font-size: 0.75rem;
  color: var(--app-muted);
}
</style>
