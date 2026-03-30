<script setup lang="ts">
defineProps<{
  src: string
  alt?: string
}>()
</script>

<template>
  <div class="pca">
    <div class="pca__cap">
      PCA 校正前后对比（PC1–PC2）
      <span class="pca__sub">着色：batch_id 与 group_label（详见图例）</span>
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
}

.pca__cap {
  padding: 0.85rem 1.1rem;
  font-weight: 600;
  border-bottom: 1px solid var(--app-border);
  background: linear-gradient(180deg, #f8fafc, #fff);
}

.pca__sub {
  display: block;
  font-weight: 400;
  font-size: 0.8rem;
  color: var(--app-muted);
  margin-top: 0.25rem;
}

.pca__frame {
  padding: 1rem;
  text-align: center;
  background: #fafafa;
}

.pca__img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
}
</style>
