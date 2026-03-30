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
    <div class="side__logo">
      <span class="side__dot" />
      BenchFlow
    </div>
    <nav class="side__nav">
      <button
        v-for="it in items"
        :key="it.path"
        type="button"
        class="side__link"
        :class="{ 'side__link--active': active === it.path }"
        @click="go(it.path)"
      >
        <el-icon class="side__ico"><component :is="it.icon" /></el-icon>
        {{ it.label }}
      </button>
    </nav>
    <div class="side__foot">毕业答辩演示 · Vue3</div>
  </div>
</template>

<style scoped lang="scss">
.side {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.25rem 0.75rem;
}

.side__logo {
  font-weight: 700;
  font-size: 1rem;
  padding: 0 0.75rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  margin-bottom: 1rem;
}

.side__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25);
}

.side__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.side__link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  background: transparent;
  color: #cbd5e1;
  font-size: 0.9rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, color 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #fff;
  }

  &--active {
    background: rgba(37, 99, 235, 0.35);
    color: #fff;
    font-weight: 600;
  }
}

.side__ico {
  font-size: 1.1rem;
}

.side__foot {
  font-size: 0.7rem;
  color: #64748b;
  padding: 1rem 0.75rem 0;
  line-height: 1.4;
}
</style>
