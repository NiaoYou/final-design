<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, Upload, Setting, DataLine, Clock } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const active = computed(() => route.path)

const items = [
  { path: '/', label: '首页', icon: House },
  { path: '/import', label: '数据导入', icon: Upload },
  { path: '/task', label: '参数配置', icon: Setting },
  { path: '/result', label: '结果展示', icon: DataLine },
  { path: '/history', label: '历史任务', icon: Clock },
]

function go(p: string) {
  void router.push(p)
}
</script>

<template>
  <div class="side">
    <!-- Logo -->
    <div class="side__logo">
      <div class="side__logo-icon">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="9" stroke="url(#g1)" stroke-width="2"/>
          <circle cx="10" cy="10" r="4" fill="url(#g2)"/>
          <defs>
            <linearGradient id="g1" x1="1" y1="1" x2="19" y2="19">
              <stop offset="0%" stop-color="#38bdf8"/>
              <stop offset="100%" stop-color="#3b82f6"/>
            </linearGradient>
            <linearGradient id="g2" x1="6" y1="6" x2="14" y2="14">
              <stop offset="0%" stop-color="#7dd3fc"/>
              <stop offset="100%" stop-color="#2563eb"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="side__logo-text">
        <span class="side__logo-name">BenchFlow</span>
        <span class="side__logo-sub">代谢组学平台</span>
      </div>
    </div>

    <!-- Nav -->
    <nav class="side__nav">
      <button
        v-for="it in items"
        :key="it.path"
        type="button"
        class="side__link"
        :class="{ 'side__link--active': active === it.path }"
        @click="go(it.path)"
      >
        <span class="side__link-bar" />
        <el-icon class="side__ico"><component :is="it.icon" /></el-icon>
        <span class="side__label">{{ it.label }}</span>
      </button>
    </nav>

    <!-- Footer -->
    <div class="side__foot">
      <div class="side__foot-dot" />
      <span>毕业答辩演示 · Vue 3</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.side {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem 0;
  background: linear-gradient(180deg, var(--side-bg) 0%, var(--side-bg-2) 100%);
  position: relative;
  overflow: hidden;

  // Subtle grid/noise texture
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      radial-gradient(circle at 20% 20%, rgba(56,189,248,.06) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(37,99,235,.08) 0%, transparent 50%);
    pointer-events: none;
  }
}

/* ---- Logo ---- */
.side__logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1.25rem 1.25rem;
  border-bottom: 1px solid rgba(148,163,184,.12);
  margin-bottom: 0.75rem;
  position: relative;
  z-index: 1;
}

.side__logo-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(56,189,248,.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(56,189,248,.2);
  box-shadow: 0 0 12px rgba(56,189,248,.15);
}

.side__logo-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.side__logo-name {
  font-weight: 700;
  font-size: 1rem;
  color: #f1f5f9;
  letter-spacing: 0.01em;
}

.side__logo-sub {
  font-size: 0.68rem;
  color: var(--side-text);
  letter-spacing: 0.02em;
}

/* ---- Nav ---- */
.side__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  padding: 0 0.75rem;
  position: relative;
  z-index: 1;
}

.side__link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  background: transparent;
  color: var(--side-text);
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease, color 0.18s ease, transform 0.12s ease;
  overflow: hidden;

  &:hover {
    background: rgba(255,255,255,.06);
    color: var(--side-text-hover);
    transform: translateX(2px);
  }

  &--active {
    background: var(--side-active);
    color: var(--side-text-active);
    font-weight: 600;
    box-shadow: inset 0 0 0 1px rgba(59,130,246,.25);

    .side__link-bar {
      opacity: 1;
      transform: scaleY(1);
    }
  }
}

.side__link-bar {
  position: absolute;
  left: 0;
  top: 20%;
  width: 3px;
  height: 60%;
  border-radius: 0 2px 2px 0;
  background: linear-gradient(180deg, #38bdf8, #3b82f6);
  opacity: 0;
  transform: scaleY(0);
  transition: opacity 0.18s, transform 0.18s;
  box-shadow: 0 0 6px rgba(59,130,246,.6);
}

.side__ico {
  font-size: 1.05rem;
  flex-shrink: 0;
}

.side__label {
  flex: 1;
}

/* ---- Footer ---- */
.side__foot {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  color: #475569;
  padding: 1rem 1.25rem 0.5rem;
  border-top: 1px solid rgba(148,163,184,.1);
  margin-top: 0.5rem;
  position: relative;
  z-index: 1;
}

.side__foot-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(16,185,129,.25);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(16,185,129,.25); }
  50%       { box-shadow: 0 0 0 4px rgba(16,185,129,.1); }
}
</style>
