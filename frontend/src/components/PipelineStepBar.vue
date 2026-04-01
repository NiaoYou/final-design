<script setup lang="ts">
import type { PipelineStepState } from '@/stores/task'

defineProps<{
  steps: { key: string; label: string; state: PipelineStepState }[]
}>()

function stateClass(s: PipelineStepState) {
  return {
    'step--ok':   s === 'success',
    'step--err':  s === 'error',
    'step--run':  s === 'process',
    'step--wait': s === 'wait',
  }
}
</script>

<template>
  <div class="pipeline">
    <template v-for="(st, idx) in steps" :key="st.key">
      <div class="step" :class="stateClass(st.state)">
        <div class="step__circle">
          <!-- Success -->
          <svg v-if="st.state === 'success'" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 8l4 4 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <!-- Error -->
          <svg v-else-if="st.state === 'error'" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <!-- Running spinner -->
          <svg v-else-if="st.state === 'process'" class="spin" width="15" height="15" viewBox="0 0 15 15" fill="none">
            <circle cx="7.5" cy="7.5" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="25 13" stroke-linecap="round"/>
          </svg>
          <!-- Wait: step number -->
          <span v-else class="step__num">{{ idx + 1 }}</span>
        </div>
        <span class="step__label">{{ st.label }}</span>
      </div>

      <!-- Connector line -->
      <div v-if="idx < steps.length - 1" class="pipeline__connector"
           :class="{ 'pipeline__connector--done': st.state === 'success' }" />
    </template>
  </div>
</template>

<style scoped lang="scss">
.pipeline {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 1.1rem 1.25rem;
  background: var(--app-bg);
  border-radius: var(--app-radius);
  border: 1px solid var(--app-border);
  flex-wrap: nowrap;
  overflow-x: auto;
}

/* ---- Connector ---- */
.pipeline__connector {
  flex: 1;
  min-width: 24px;
  height: 2px;
  background: var(--app-border);
  border-radius: 1px;
  transition: background 0.3s ease;

  &--done {
    background: linear-gradient(90deg, #10b981, #06b6d4);
  }
}

/* ---- Step ---- */
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
  min-width: 56px;
}

.step__circle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s;

  .step--wait & {
    background: #fff;
    border: 2px solid var(--app-border);
    color: var(--app-muted-light);
  }

  .step--ok & {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff;
    border: 2px solid transparent;
    box-shadow: 0 4px 10px rgba(16,185,129,.3);
  }

  .step--err & {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #fff;
    border: 2px solid transparent;
    box-shadow: 0 4px 10px rgba(239,68,68,.3);
  }

  .step--run & {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    color: #fff;
    border: 2px solid transparent;
    box-shadow: 0 4px 14px rgba(37,99,235,.35);
  }
}

.step__num {
  font-variant-numeric: tabular-nums;
}

.step__label {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  color: var(--app-muted);
  transition: color 0.2s;

  .step--ok &  { color: #059669; }
  .step--err & { color: #dc2626; }
  .step--run & { color: var(--app-primary); }
}

/* ---- Spin animation ---- */
.spin {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
