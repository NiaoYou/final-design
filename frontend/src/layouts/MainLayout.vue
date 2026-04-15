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
  min-height: 100vh;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: hidden;
  z-index: 99;
  box-shadow: 2px 0 16px rgba(11,17,32,.18);
}

.layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.layout__content {
  flex: 1;
  padding: 1.75rem 2rem 3rem;
  overflow-y: auto;

  @media (max-width: 768px) {
    padding: 1.25rem 1.5rem 2rem;
  }

  @media (max-width: 480px) {
    padding: 1rem 1rem 1.5rem;
  }
}
</style>
