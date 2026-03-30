<script setup lang="ts">
import { mergedDownloadUrl } from '@/api/benchmark'
import { formatBytes } from '@/utils/format'

const props = defineProps<{
  name: string
  purpose: string
  sizeBytes: number
  href?: string
}>()
</script>

<template>
  <div class="dl">
    <div class="dl__main">
      <div class="dl__name">{{ name }}</div>
      <div class="dl__purpose">{{ purpose }}</div>
      <div class="dl__meta">{{ formatBytes(sizeBytes) }}</div>
    </div>
    <el-button
      type="primary"
      tag="a"
      :href="props.href ?? mergedDownloadUrl(name)"
      rel="noopener"
      download
    >
      下载
    </el-button>
  </div>
</template>

<style scoped lang="scss">
.dl {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 0;
  border-bottom: 1px solid var(--app-border);

  &:last-child {
    border-bottom: none;
  }
}

.dl__name {
  font-weight: 600;
  font-size: 0.9rem;
}

.dl__purpose {
  font-size: 0.82rem;
  color: var(--app-muted);
  margin-top: 0.2rem;
  line-height: 1.45;
}

.dl__meta {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}
</style>
