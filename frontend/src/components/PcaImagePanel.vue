<script setup lang="ts">
defineProps<{
  src: string
  alt?: string
}>()
</script>

<template>
  <div class="pca">
    <div class="pca__cap">
      <div class="pca__cap-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="5" cy="10" r="2.5" fill="#3b82f6" opacity="0.7"/>
          <circle cx="11" cy="5" r="2.5" fill="#06b6d4" opacity="0.7"/>
          <circle cx="8" cy="13" r="2" fill="#8b5cf6" opacity="0.6"/>
          <circle cx="3" cy="4" r="1.5" fill="#10b981" opacity="0.6"/>
          <circle cx="13" cy="11" r="2" fill="#f59e0b" opacity="0.6"/>
        </svg>
      </div>
      <div>
        <div class="pca__title">PCA 校正前后对比（PC1–PC2）</div>
        <div class="pca__sub">着色：batch_id 与 group_label（详见图例）</div>
      </div>
    </div>
    <div class="pca__frame">
      <img class="pca__img" :src="src" :alt="alt || 'PCA before vs after'" loading="lazy" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.pca {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: #fff;
  overflow: hidden;
  box-shadow: var(--app-shadow);
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: var(--app-shadow-md);
  }
}

.pca__cap {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.9rem 1.1rem;
  border-bottom: 1px solid var(--app-border);
  background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
}

.pca__cap-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(37,99,235,.07);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pca__title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--app-text);
}

.pca__sub {
  font-size: 0.78rem;
  color: var(--app-muted);
  margin-top: 0.2rem;
}

.pca__frame {
  padding: 1rem;
  text-align: center;
  background: #fafbff;
}

.pca__img {
  max-width: 100%;
  height: auto;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
}
</style>
