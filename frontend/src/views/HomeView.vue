<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    icon: '📊',
    title: '多 sheet Excel 导入',
    text: '解析 injections / intensities 等工作表，对齐离子索引并完成跨 batch 合并。',
    color: '#3b82f6',
  },
  {
    icon: '⚗️',
    title: '预处理与质控',
    text: '标准化、对数变换、缺失率阈值与样本过滤，形成可分析的数值矩阵。',
    color: '#06b6d4',
  },
  {
    icon: '🔬',
    title: '缺失值填充评估',
    text: 'Mask-then-Impute 框架：随机遮蔽 15% 数据，对 mean / median / KNN 三种策略计算 RMSE/MAE/NRMSE，KNN 以 RMSE=0.298 显著优于其余方法。',
    color: '#8b5cf6',
  },
  {
    icon: '🧬',
    title: 'baseline 批次校正',
    text: 'per-feature batch location-scale baseline 校正，batch centroid separation 从 5.38 降至 ≈0（降幅 100%），产出可复现矩阵与报告。',
    color: '#10b981',
  },
  {
    icon: '⚡',
    title: 'strict ComBat（pyComBat）',
    text: '经验 Bayes ComBat（Johnson et al., 2007）通过 pyComBat 实现，与 baseline 做 5 方法量化对比（Silhouette、batch centroid 分离距离），batch 效应完全消除。',
    color: '#0ea5e9',
  },
  {
    icon: '🌋',
    title: '差异代谢物分析',
    text: '任意两组样本执行 Welch t-test + BH-FDR 多重校正 + log2 Fold Change，识别显著差异代谢物并以交互式火山图展示，支持点击跳转 HMDB/KEGG 数据库。',
    color: '#f59e0b',
  },
  {
    icon: '🏷️',
    title: '特征注释',
    text: '基于 m/z 精确质量匹配将 1180 个代谢特征全覆盖注释至代谢物名称，关联 HMDB 与 KEGG 数据库 ID，支持关键词搜索，注释结果自动注入差异分析报告。',
    color: '#ec4899',
  },
  {
    icon: '📈',
    title: '结果仪表盘',
    text: 'KPI、PCA 四宫格、校正前后指标、方法对比表与文件下载，适合答辩投屏演示。',
    color: '#ef4444',
  },
]

const steps = [
  {
    num: '01',
    title: '数据导入',
    desc: '上传多 batch Excel，自动解析并跨 batch 合并',
    color: '#3b82f6',
  },
  {
    num: '02',
    title: '预处理 & 填充',
    desc: '标准化、对数变换、KNN/mean/median 填充评估',
    color: '#06b6d4',
  },
  {
    num: '03',
    title: '批次校正',
    desc: 'baseline + ComBat 双方法，5 维指标量化对比',
    color: '#8b5cf6',
  },
  {
    num: '04',
    title: '差异分析',
    desc: 't-test + BH-FDR，交互火山图，可选任意两组',
    color: '#f59e0b',
  },
  {
    num: '05',
    title: '注释 & 展示',
    desc: 'm/z 精确匹配全覆盖注释，HMDB/KEGG 链接可跳转',
    color: '#ec4899',
  },
]
</script>

<template>
  <div class="page-container home">

    <!-- Hero -->
    <section class="hero">
      <div class="hero__bg-orb hero__bg-orb--1" />
      <div class="hero__bg-orb hero__bg-orb--2" />
      <div class="hero__inner">
        <div class="hero__badge">
          <span class="hero__badge-dot" />
          代谢组学 · Web 处理平台
        </div>
        <h1 class="hero__title">
          面向代谢组学数据处理<br />
          的 <span class="hero__title-accent">Web 平台</span>
        </h1>
        <p class="hero__lead">
          支持原始多 sheet Excel 导入、跨 batch 合并、预处理、KNN 缺失值填充评估、
          <strong>baseline 批次校正</strong>与 <strong>strict ComBat（pyComBat）</strong> 批次校正，
          并集成 <strong>差异代谢物分析</strong>（t-test + BH-FDR + 交互火山图）与
          <strong>m/z 精确质量特征注释</strong>（HMDB / KEGG 全覆盖）。
        </p>
        <div class="hero__actions">
          <button class="btn btn--primary" @click="router.push('/import')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v9M4 7l4 4 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 14h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            进入数据导入
          </button>
          <button class="btn btn--ghost" @click="router.push('/result')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="2" y="9" width="3" height="5" rx="1" fill="currentColor"/>
              <rect x="6.5" y="5" width="3" height="9" rx="1" fill="currentColor"/>
              <rect x="11" y="2" width="3" height="12" rx="1" fill="currentColor"/>
            </svg>
            查看 merged 结果
          </button>
        </div>
      </div>
      <!-- Decorative chart lines -->
      <div class="hero__deco" aria-hidden="true">
        <svg width="260" height="160" viewBox="0 0 260 160" fill="none" opacity="0.18">
          <polyline points="0,140 40,100 80,120 120,60 160,80 200,30 260,50"
            stroke="#3b82f6" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <polyline points="0,155 40,130 80,145 120,100 160,115 200,70 260,90"
            stroke="#06b6d4" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="6 3"/>
        </svg>
      </div>
    </section>

    <!-- Features -->
    <section class="card-panel features-section">
      <h2 class="section-heading">技术亮点</h2>
      <div class="features">
        <div v-for="f in features" :key="f.title" class="feature" :style="{ '--feat-color': f.color }">
          <div class="feature__icon">{{ f.icon }}</div>
          <div class="feature__title">{{ f.title }}</div>
          <p class="feature__text">{{ f.text }}</p>
          <div class="feature__bar" />
        </div>
      </div>
    </section>

    <!-- Steps -->
    <section class="card-panel steps-section">
      <h2 class="section-heading">系统流程</h2>
      <div class="steps">
        <div v-for="(s, i) in steps" :key="s.num" class="step" :style="{ '--step-color': s.color }">
          <div class="step__num">{{ s.num }}</div>
          <div class="step__body">
            <div class="step__title">{{ s.title }}</div>
            <div class="step__desc">{{ s.desc }}</div>
          </div>
          <div v-if="i < steps.length - 1" class="step__arrow">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 10h10M11 6l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<style scoped lang="scss">
/* ===== Hero ===== */
.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #e8f0fe 0%, #fff 45%, #f0fdf9 100%);
  border-radius: var(--app-radius-lg);
  padding: 3rem 2.5rem 2.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(37,99,235,.12);
  box-shadow: 0 4px 24px rgba(37,99,235,.08), var(--app-shadow);
}

.hero__bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;

  &--1 {
    width: 340px;
    height: 340px;
    top: -120px;
    right: -60px;
    background: radial-gradient(circle, rgba(37,99,235,.12) 0%, transparent 70%);
  }

  &--2 {
    width: 260px;
    height: 260px;
    bottom: -80px;
    left: 20%;
    background: radial-gradient(circle, rgba(6,182,212,.1) 0%, transparent 70%);
  }
}

.hero__inner {
  position: relative;
  z-index: 1;
  max-width: 680px;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.9rem;
  border-radius: 20px;
  background: rgba(37,99,235,.08);
  border: 1px solid rgba(37,99,235,.2);
  color: var(--app-primary);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  margin-bottom: 1.25rem;
}

.hero__badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--app-primary);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(1.3); }
}

.hero__title {
  font-size: 2.2rem;
  font-weight: 800;
  margin: 0 0 1rem;
  letter-spacing: -0.04em;
  line-height: 1.18;
  color: var(--app-text);
}

.hero__title-accent {
  background: linear-gradient(120deg, #2563eb 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero__lead {
  font-size: 1rem;
  color: var(--app-muted);
  margin: 0 0 2rem;
  line-height: 1.72;
  max-width: 600px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem;
}

.hero__deco {
  position: absolute;
  right: 2rem;
  bottom: 1.5rem;
  z-index: 0;
  pointer-events: none;
}

/* ===== Buttons ===== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1.4rem;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;

  &:active { transform: scale(0.97); }

  &--primary {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    color: #fff;
    box-shadow: 0 4px 14px rgba(37,99,235,.35);

    &:hover {
      box-shadow: 0 6px 20px rgba(37,99,235,.45);
      transform: translateY(-1px);
    }
  }

  &--ghost {
    background: rgba(255,255,255,.85);
    color: var(--app-text-2);
    border: 1px solid var(--app-border);
    box-shadow: var(--app-shadow);

    &:hover {
      background: #fff;
      box-shadow: var(--app-shadow-md);
      transform: translateY(-1px);
    }
  }
}

/* ===== Features ===== */
.features-section {
  padding: 1.75rem 1.75rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.1rem;

  @media (max-width: 1200px) { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 880px)  { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 560px)  { grid-template-columns: 1fr; }
}

.feature {
  position: relative;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 1.2rem 1.1rem 1.1rem;
  background: #fafbff;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  cursor: default;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,.09);
    border-color: var(--feat-color, var(--app-primary));
  }

  &:hover .feature__bar {
    opacity: 1;
    transform: scaleX(1);
  }
}

.feature__icon {
  font-size: 1.6rem;
  margin-bottom: 0.6rem;
  line-height: 1;
}

.feature__title {
  font-weight: 700;
  margin-bottom: 0.4rem;
  color: var(--feat-color, var(--app-primary));
  font-size: 0.93rem;
}

.feature__text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--app-muted);
  line-height: 1.6;
}

.feature__bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--feat-color, var(--app-primary));
  opacity: 0;
  transform: scaleX(0.4);
  transform-origin: left;
  transition: opacity 0.2s ease, transform 0.25s ease;
  border-radius: 0 0 2px 2px;
}

/* ===== Steps ===== */
.steps-section {
  padding: 1.75rem;
}

.steps {
  display: flex;
  align-items: flex-start;
  gap: 0;
  flex-wrap: wrap;
  gap: 1rem;

  @media (max-width: 880px) { flex-direction: column; }
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
  min-width: 160px;
  position: relative;
}

.step__num {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--step-color, #2563eb), color-mix(in srgb, var(--step-color, #2563eb) 60%, #fff));
  color: #fff;
  font-weight: 800;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--step-color, #2563eb) 40%, transparent);
}

.step__body {
  flex: 1;
  padding-top: 0.1rem;
}

.step__title {
  font-weight: 700;
  font-size: 0.93rem;
  color: var(--app-text);
  margin-bottom: 0.3rem;
}

.step__desc {
  font-size: 0.83rem;
  color: var(--app-muted);
  line-height: 1.55;
}

.step__arrow {
  color: var(--app-muted-light);
  padding-top: 0.6rem;
  flex-shrink: 0;
  align-self: flex-start;

  @media (max-width: 880px) { display: none; }
}
</style>
