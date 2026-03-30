<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    title: '多 sheet Excel 导入',
    text: '解析 injections / intensities 等工作表，对齐离子索引并完成跨 batch 合并。',
  },
  {
    title: '预处理与质控',
    text: '标准化、对数变换、缺失率阈值与样本过滤，形成可分析的数值矩阵。',
  },
  {
    title: '缺失值填充',
    text: '支持 mean、median、KNN 等策略，便于在稀疏代谢矩阵上继续建模。',
  },
  {
    title: 'baseline 批次校正',
    text: '当前实现 per-feature batch location-scale baseline 校正，并产出可下载矩阵与报告。',
  },
  {
    title: 'strict ComBat',
    text: '标准经验 Bayes ComBat 尚未实现；界面与报告中均与 baseline 明确区分。',
  },
  {
    title: '结果仪表盘',
    text: 'KPI、PCA 四宫格、校正前后指标与文件下载，适合答辩投屏演示。',
  },
]

const steps = [
  { title: '数据导入', desc: '上传长表或运行 benchmark 合并产出 merged 数据' },
  { title: '参数配置', desc: '预处理、填充与批次策略（通用任务链 / merged 流程）' },
  { title: '任务运行', desc: '执行流水线并记录步骤状态' },
  { title: '结果展示', desc: 'PCA、指标与解释，基于后端 JSON 实时展示' },
]
</script>

<template>
  <div class="page-container home">
    <section class="hero">
      <div class="hero__inner">
        <el-tag type="primary" effect="light" round>代谢组学 · Web 处理平台</el-tag>
        <h1 class="hero__title">面向代谢组学数据处理的 Web 平台</h1>
        <p class="hero__lead">
          支持原始多 sheet Excel 导入、跨 batch 合并、预处理、缺失值填充、<strong>baseline</strong> 批次校正与结果展示。本页所述能力与后端、报告 JSON
          一致；<strong>strict ComBat 尚未实现</strong>。
        </p>
        <div class="hero__actions">
          <el-button type="primary" size="large" @click="router.push('/import')">进入数据导入</el-button>
          <el-button size="large" @click="router.push('/result')">查看 merged 结果展示</el-button>
        </div>
      </div>
    </section>

    <section class="card-panel">
      <h2 class="section-title">技术亮点</h2>
      <div class="highlights">
        <div v-for="f in features" :key="f.title" class="feature">
          <div class="feature__title">{{ f.title }}</div>
          <p class="feature__text">{{ f.text }}</p>
        </div>
      </div>
    </section>

    <section class="card-panel">
      <h2 class="section-title">系统流程</h2>
      <el-timeline>
        <el-timeline-item
          v-for="(s, i) in steps"
          :key="s.title"
          :timestamp="`Step ${i + 1}`"
          placement="top"
        >
          <div class="step__t">{{ s.title }}</div>
          <div class="step__d">{{ s.desc }}</div>
        </el-timeline-item>
      </el-timeline>
    </section>
  </div>
</template>

<style scoped lang="scss">
.home .hero {
  background: linear-gradient(135deg, #eff6ff 0%, #fff 48%, #f8fafc 100%);
  border-radius: var(--app-radius);
  padding: 2.5rem 2rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--app-border);
  box-shadow: var(--app-shadow);
}

.hero__inner {
  max-width: 720px;
}

.hero__title {
  font-size: 2rem;
  margin: 1rem 0 0.75rem;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.hero__lead {
  font-size: 1.05rem;
  color: var(--app-muted);
  margin: 0 0 1.5rem;
  line-height: 1.65;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.section-title {
  margin: 0 0 1.25rem;
  font-size: 1.15rem;
}

.highlights {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;

  @media (max-width: 960px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.feature {
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 1rem;
  background: #fafbfc;
}

.feature__title {
  font-weight: 600;
  margin-bottom: 0.35rem;
  color: var(--app-primary);
}

.feature__text {
  margin: 0;
  font-size: 0.9rem;
  color: var(--app-muted);
  line-height: 1.55;
}

.step__t {
  font-weight: 600;
}

.step__d {
  color: var(--app-muted);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}
</style>
