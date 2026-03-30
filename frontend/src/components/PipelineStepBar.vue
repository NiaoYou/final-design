<script setup lang="ts">
import { CircleCheck, CircleClose, Loading, Minus } from '@element-plus/icons-vue'
import type { PipelineStepState } from '@/stores/task'

defineProps<{
  steps: { key: string; label: string; state: PipelineStepState }[]
}>()

function cmp(s: PipelineStepState) {
  if (s === 'success') return CircleCheck
  if (s === 'error') return CircleClose
  if (s === 'process') return Loading
  return Minus
}

function cls(s: PipelineStepState) {
  return {
    'pipe__dot--ok': s === 'success',
    'pipe__dot--err': s === 'error',
    'pipe__dot--run': s === 'process',
    'pipe__dot--wait': s === 'wait',
  }
}
</script>

<template>
  <div class="pipe">
    <div v-for="st in steps" :key="st.key" class="pipe__step">
      <el-icon class="pipe__dot" :class="cls(st.state)" :size="22">
        <component :is="cmp(st.state)" />
      </el-icon>
      <span class="pipe__label">{{ st.label }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.pipe {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-radius: var(--app-radius);
  border: 1px solid var(--app-border);
}

.pipe__step {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.pipe__label {
  font-size: 0.88rem;
  color: var(--app-text);
}

.pipe__dot {
  &--ok {
    color: #16a34a;
  }
  &--err {
    color: #dc2626;
  }
  &--run {
    color: var(--app-primary);
    animation: spin 1s linear infinite;
  }
  &--wait {
    color: #cbd5e1;
  }
}

@keyframes spin {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
