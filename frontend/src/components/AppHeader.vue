<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string) || '首页')

const apiOk = computed(() => true)

// Map route path to a short breadcrumb description
const routeDesc = computed(() => {
  const map: Record<string, string> = {
    '/':        '平台概览',
    '/import':  '数据导入',
    '/task':    '参数配置',
    '/result':  '结果展示',
    '/history': '历史任务',
  }
  return map[route.path] || ''
})
</script>

<template>
  <header class="header">
    <div class="header__left">
      <!-- Breadcrumb -->
      <div class="header__breadcrumb">
        <span class="header__brand">BenchFlow</span>
        <svg class="header__chevron" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="header__page">{{ routeDesc || title }}</span>
      </div>
    </div>

    <div class="header__right">
      <div v-if="apiOk" class="header__status">
        <span class="header__status-dot" />
        <span class="header__status-text">演示前端 · 联调后端 API</span>
      </div>
    </div>
  </header>
</template>

<style scoped lang="scss">
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.75rem;
  height: 56px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--app-border);
  box-shadow: 0 1px 0 rgba(15,23,42,.04), var(--app-shadow);
  position: sticky;
  top: 0;
  z-index: 101;
}

.header__left {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}

.header__breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.header__brand {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--app-primary);
  letter-spacing: 0.01em;
}

.header__chevron {
  color: var(--app-muted-light);
  flex-shrink: 0;
}

.header__page {
  color: var(--app-text-2);
  font-weight: 500;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header__right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header__status {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  background: rgba(16,185,129,.08);
  border: 1px solid rgba(16,185,129,.2);
}

.header__status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  flex-shrink: 0;
  animation: blink 2.5s ease-in-out infinite;
}

.header__status-text {
  font-size: 0.78rem;
  color: #059669;
  font-weight: 500;
  white-space: nowrap;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
</style>
