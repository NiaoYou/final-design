<template>
  <div class="dataset-selector">
    <div class="selector-label">当前数据集</div>
    <div class="selector-tabs">
      <button
        v-for="ds in datasets"
        :key="ds.id"
        class="tab-btn"
        :class="{
          active: ds.id === modelValue,
          disabled: !ds.available,
        }"
        :title="ds.available ? ds.description : `${ds.label}（数据未就绪，请先运行 pipeline 脚本）`"
        @click="ds.available && emit('update:modelValue', ds.id)"
      >
        <span class="tab-label">{{ ds.label }}</span>
        <span v-if="!ds.available" class="tab-badge unavailable">未就绪</span>
        <span v-else-if="!ds.pipeline_ready" class="tab-badge partial">部分就绪</span>
      </button>
    </div>
    <div v-if="currentDs" class="dataset-desc">
      {{ currentDs.description }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DatasetInfo } from '@/api/dataset'

const props = defineProps<{
  modelValue: string
  datasets: DatasetInfo[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const currentDs = computed(() => props.datasets.find((d) => d.id === props.modelValue))
</script>

<style scoped>
.dataset-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 16px;
  background: var(--surface-card, #fff);
  border: 1px solid var(--surface-border, #e5e7eb);
  border-radius: 10px;
  margin-bottom: 20px;
}

.selector-label {
  font-size: 0.82rem;
  color: var(--text-color-secondary, #6b7280);
  font-weight: 500;
  white-space: nowrap;
  margin-right: 4px;
}

.selector-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border-radius: 20px;
  border: 1.5px solid var(--surface-border, #e5e7eb);
  background: transparent;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-color-secondary, #6b7280);
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn:hover:not(.disabled) {
  border-color: var(--primary-color, #6366f1);
  color: var(--primary-color, #6366f1);
  background: var(--primary-50, #eef2ff);
}

.tab-btn.active {
  border-color: var(--primary-color, #6366f1);
  background: var(--primary-color, #6366f1);
  color: #fff;
}

.tab-btn.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tab-badge {
  font-size: 0.68rem;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.tab-badge.unavailable {
  background: #fee2e2;
  color: #dc2626;
}

.tab-badge.partial {
  background: #fef3c7;
  color: #d97706;
}

.dataset-desc {
  font-size: 0.78rem;
  color: var(--text-color-secondary, #6b7280);
  flex: 1;
  min-width: 200px;
  font-style: italic;
}
</style>
