<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  hint?: string
  color?: string   // optional accent color override
}>()
</script>

<template>
  <div class="kpi" :style="color ? { '--kpi-color': color } : {}">
    <div class="kpi__stripe" />
    <div class="kpi__body">
      <div class="kpi__label">{{ label }}</div>
      <div class="kpi__value">{{ value }}</div>
      <div v-if="hint" class="kpi__hint">{{ hint }}</div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.kpi {
  --kpi-color: var(--app-primary);

  position: relative;
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  overflow: hidden;
  box-shadow: var(--app-shadow);
  min-height: 100px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--app-shadow-md);
  }
}

.kpi__stripe {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--kpi-color), color-mix(in srgb, var(--kpi-color) 60%, #06b6d4));
  border-radius: 0;
}

.kpi__body {
  padding: 1.1rem 1.25rem 1rem;
}

.kpi__label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--app-muted);
  margin-bottom: 0.5rem;
}

.kpi__value {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--app-text);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.kpi__hint {
  margin-top: 0.4rem;
  font-size: 0.72rem;
  color: var(--app-muted-light);
  font-family: ui-monospace, 'Cascadia Code', monospace;
}
</style>
