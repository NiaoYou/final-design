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
    <div class="dl__icon">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <rect x="2" y="1" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <path d="M5 6h8M5 9h8M5 12h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      </svg>
    </div>
    <div class="dl__main">
      <div class="dl__name">{{ name }}</div>
      <div class="dl__purpose">{{ purpose }}</div>
    </div>
    <div class="dl__size">{{ formatBytes(sizeBytes) }}</div>
    <a
      class="dl__btn"
      :href="props.href ?? mergedDownloadUrl(name)"
      rel="noopener"
      download
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 1v8M3.5 6l3.5 3.5L10.5 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M1.5 12h11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      下载
    </a>
  </div>
</template>

<style scoped lang="scss">
.dl {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.85rem 0.75rem;
  border-radius: 10px;
  border: 1px solid var(--app-border-light);
  background: var(--app-bg);
  margin-bottom: 0.6rem;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;

  &:last-child { margin-bottom: 0; }

  &:hover {
    border-color: rgba(37,99,235,.25);
    background: #fff;
    box-shadow: var(--app-shadow);
  }
}

.dl__icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--app-primary-soft);
  color: var(--app-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dl__main {
  flex: 1;
  min-width: 0;
}

.dl__name {
  font-weight: 600;
  font-size: 0.88rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--app-text);
}

.dl__purpose {
  font-size: 0.78rem;
  color: var(--app-muted);
  margin-top: 0.15rem;
  line-height: 1.4;
}

.dl__size {
  font-size: 0.75rem;
  color: var(--app-muted-light);
  font-family: ui-monospace, monospace;
  flex-shrink: 0;
}

.dl__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.38rem 0.85rem;
  border-radius: 8px;
  background: var(--app-primary);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  flex-shrink: 0;
  transition: background 0.15s, transform 0.12s;

  &:hover {
    background: var(--app-primary-dark);
    transform: translateY(-1px);
  }
}
</style>
