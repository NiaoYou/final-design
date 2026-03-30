<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import SidebarMenu from '@/components/SidebarMenu.vue'
</script>

<template>
  <div class="layout">
    <aside class="layout__side">
      <SidebarMenu />
    </aside>
    <div class="layout__main">
      <AppHeader />
      <main class="layout__content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  min-height: 100vh;
  display: flex;
  background: var(--app-bg);
}

.layout__side {
  width: 240px;
  flex-shrink: 0;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}

.layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.layout__content {
  flex: 1;
  padding: 1.5rem 1.75rem 2.5rem;
}
</style>
