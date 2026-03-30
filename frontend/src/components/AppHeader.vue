<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = computed(() => useRoute())
const title = computed(() => (route.value.meta.title as string) || '代谢组学数据处理平台')

const apiOk = computed(() => {
  // 轻量状态：结果 store 可在子页刷新；此处仅展示静态提示
  return true
})
</script>

<template>
  <header class="header">
    <div class="header__left">
      <span class="header__brand">代谢组学数据处理平台</span>
      <span class="header__sep">/</span>
      <span class="header__page">{{ title }}</span>
    </div>
    <div class="header__right">
      <el-tag v-if="apiOk" type="success" effect="plain" size="small">演示前端 · 联调后端 API</el-tag>
    </div>
  </header>
</template>

<style scoped lang="scss">
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.75rem;
  background: #fff;
  border-bottom: 1px solid var(--app-border);
  box-shadow: var(--app-shadow);
}

.header__left {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}

.header__brand {
  font-weight: 700;
  color: var(--app-primary);
  font-size: 0.95rem;
  white-space: nowrap;
}

.header__sep {
  color: var(--app-muted);
}

.header__page {
  color: var(--app-text);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header__right {
  flex-shrink: 0;
}
</style>
