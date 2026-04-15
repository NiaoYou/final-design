<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useBenchmarkStore } from '@/stores/benchmark'
import KpiCard from '@/components/KpiCard.vue'
import MetricCompareCard from '@/components/MetricCompareCard.vue'
import MethodStatusCard from '@/components/MethodStatusCard.vue'
import DownloadFileCard from '@/components/DownloadFileCard.vue'
import PcaImagePanel from '@/components/PcaImagePanel.vue'
import EvRatioChart from '@/components/EvRatioChart.vue'
import ImputationEvalCard from '@/components/ImputationEvalCard.vue'
import VolcanoPlotCard from '@/components/VolcanoPlotCard.vue'
import AnnotationTableCard from '@/components/AnnotationTableCard.vue'
import PathwayEnrichmentCard from '@/components/PathwayEnrichmentCard.vue'
import MetaKGCard from '@/components/MetaKGCard.vue'
import { evaluationDownloadUrl, evaluationPcaImageUrl, pcaBeforeAfterImageUrl } from '@/api/benchmark'
import { formatNumber, formatRatio } from '@/utils/format'
import type { BatchCorrectionMetrics } from '@/types/benchmark'

const store = useBenchmarkStore()
const {
  summary, report, metrics, files, pcaAfter,
  evaluationSummary, evaluationTable, evaluationPcas, evaluationFiles,
  imputationEvalSummary, imputationEvalFeatureRmse,
  loading, error,
} = storeToRefs(store)

onMounted(() => {
  void store.loadAll()
})

const pcaUrl = computed(() => pcaBeforeAfterImageUrl(String(store.loadedAt || Date.now())))
const evalPcaUrl = computed(() => evaluationPcaImageUrl(String(store.loadedAt || Date.now())))

const heuristicRows = computed(() => {
  const m = metrics.value as BatchCorrectionMetrics | null
  if (!m) return []
  return [
    {
      label: 'heuristic_mixing_improved_by_centroid',
      value: m.heuristic_mixing_improved_by_centroid,
    },
    {
      label: 'heuristic_group_overdistorted',
      value: m.heuristic_group_overdistorted,
    },
  ]
})

const interpretation = computed(() => {
  const m = metrics.value as BatchCorrectionMetrics | null
  const r = report.value
  const parts: string[] = []

  if (m) {
    // 质心距离
    parts.push(
      `批次质心距离（batch_centroid_separation_pc12）：` +
      `校正前 ${formatNumber(m.batch_centroid_separation_pc12_before)}，` +
      `校正后 ${formatNumber(m.batch_centroid_separation_pc12_after)}，` +
      `Δ=${formatNumber(m.delta_batch_centroid_separation)}。` +
      `批次间质心距离大幅下降，说明各批次的整体分布中心已显著对齐。`,
    )

    // silhouette(batch_id)
    if (m.silhouette_batch_id_pc12_before != null) {
      const d = m.delta_silhouette_batch_id
      const dir = d != null ? (d < 0 ? '下降（混合改善）' : '上升（批次分离未减弱）') : '—'
      parts.push(
        `批次轮廓系数（silhouette_batch_id_pc12）：` +
        `校正前 ${formatNumber(m.silhouette_batch_id_pc12_before)}，` +
        `校正后 ${formatNumber(m.silhouette_batch_id_pc12_after)}，` +
        `Δ=${formatNumber(d)}（${dir}）。` +
        `该指标越低越好，校正后越负表示批次间样本点难以区分。`,
      )
    }

    // silhouette(group_label)
    if (m.silhouette_group_label_pc12_before != null) {
      const d = m.delta_silhouette_group_label
      const dir = d != null ? (d > 0 ? '上升（生物学信号保留）' : '下降（需关注生物信号损失）') : '—'
      parts.push(
        `生物学分组轮廓系数（silhouette_group_label_pc12）：` +
        `校正前 ${formatNumber(m.silhouette_group_label_pc12_before)}，` +
        `校正后 ${formatNumber(m.silhouette_group_label_pc12_after)}，` +
        `Δ=${formatNumber(d)}（${dir}）。` +
        `该指标越高越好，反映校正后样本按组别聚集的程度（即生物学结构是否保留）。`,
      )
    }

    const notes = m.heuristic_mixing_notes
    if (notes?.length) parts.push(`综合判据：${notes.join('；')}`)
  }

  if (r?.baseline_batch_correction?.method_id) {
    const combatStatus = (r.strict_combat as { status?: string } | undefined)?.status
    const combatDesc = combatStatus === 'implemented'
      ? 'ComBat-like 校正（neuroCombat）已实现，可在下方方法对比区块查看其指标。'
      : 'ComBat-like 校正尚未实现，当前仅展示 baseline 结果。'
    parts.push(
      `本页主链路展示方法：${String(r.baseline_batch_correction.method_id)}（逐特征位置尺度对齐）。${combatDesc}`,
    )
  }

  return parts
})

/** 格式化 evaluation 表格中的数值（处理科学记数法字符串，统一保留 4 位有效小数） */
function fmtEvalNum(val: string | null | undefined): string {
  if (val == null || val === '') return '—'
  const n = Number(val)
  if (isNaN(n)) return String(val)
  // centroid separation 接近 0 时（< 1e-8）显示为 ≈0
  if (Math.abs(n) < 1e-8) return '≈0'
  return n.toFixed(4)
}

const selectedEvalMethod = ref<string>('baseline')

const evalMethodOptions = computed(() => {
  const es = evaluationSummary.value
  if (!es?.methods_order?.length) return []
  return es.methods_order.map((internal) => ({
    internal,
    display: es.methods_display_names?.[internal] ?? internal,
  }))
})

watch(
  evalMethodOptions,
  (opts) => {
    if (!opts.length) return
    if (!opts.find((o) => o.internal === selectedEvalMethod.value)) {
      selectedEvalMethod.value = opts[0].internal
    }
    void store.loadEvaluationPca(selectedEvalMethod.value)
  },
  { immediate: true },
)

watch(
  selectedEvalMethod,
  (m) => {
    void store.loadEvaluationPca(m)
  },
  { immediate: false },
)

const selectedEvalPca = computed(() => evaluationPcas.value[selectedEvalMethod.value] ?? null)
</script>

<template>
  <div class="page-container dash">
    <p class="page-title">结果展示 · Benchmark Merged</p>
    <p class="page-sub" style="margin-bottom:1.25rem">
      数据来自后端 <code>/api/benchmark/merged/*</code> 与产物目录 JSON；不做手填指标。
      主链路 KPI / PCA 展示 <strong>baseline</strong>（逐特征位置尺度对齐）批次校正结果；
      <strong>ComBat-like 校正（neuroCombat）已实现</strong>，可在下方「方法对比实验」区块查看对比数据。
    </p>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      :closable="false"
      class="dash__alert"
    />

    <div class="dash__toolbar">
      <el-button type="primary" :loading="loading" @click="store.loadAll()">刷新数据</el-button>
      <el-tag v-if="summary && !summary.available" type="warning">merged 摘要不可用（请先产出 merge_report）</el-tag>
    </div>

    <section class="kpi-row">
      <KpiCard
        label="样本数"
        :value="summary?.merged_sample_count ?? '—'"
        hint="merge_report.json"
        color="#3b82f6"
      />
      <KpiCard
        label="特征数"
        :value="summary?.merged_feature_count ?? '—'"
        color="#06b6d4"
      />
      <KpiCard label="batch 数" :value="summary?.batch_count ?? '—'" color="#8b5cf6" />
      <KpiCard
        label="合并后缺失率"
        :value="formatRatio(summary?.missing_ratio_after_merge, 2)"
        color="#f59e0b"
      />
    </section>

    <MethodStatusCard :report="report" :loading="loading && !report" />

    <div class="grid-2">
      <PcaImagePanel :src="pcaUrl" />
      <EvRatioChart :ratios="pcaAfter?.explained_variance_ratio as number[] | undefined" />
    </div>

    <section class="card-panel">
      <h3 class="section-heading">指标摘要（batch_correction_metrics.json）</h3>
      <div class="metric-grid" v-if="metrics">
        <!-- batch_centroid_separation：越低越好，delta<0 为绿 -->
        <MetricCompareCard
          title="batch_centroid_separation_pc12"
          :before="metrics.batch_centroid_separation_pc12_before"
          :after="metrics.batch_centroid_separation_pc12_after"
          :delta="metrics.delta_batch_centroid_separation"
          hint="PC1–PC2 上各批次质心间平均欧氏距离。越小说明批次间分布越接近（混合越好）。"
        />
        <!-- silhouette(batch_id)：越低越好，delta<0 为绿（batch 难以区分 = 混合好） -->
        <MetricCompareCard
          title="silhouette(batch_id)"
          :before="metrics.silhouette_batch_id_pc12_before"
          :after="metrics.silhouette_batch_id_pc12_after"
          :delta="metrics.delta_silhouette_batch_id"
          hint="以 batch_id 为标签计算的 Silhouette 分数。校正后应下降（越负越好），说明批次间样本点不再可区分。"
        />
        <!-- silhouette(group_label)：越高越好，delta>0 为绿（生物信号保留） -->
        <MetricCompareCard
          title="silhouette(group_label)"
          :before="metrics.silhouette_group_label_pc12_before"
          :after="metrics.silhouette_group_label_pc12_after"
          :delta="metrics.delta_silhouette_group_label"
          :positive-is-good="true"
          hint="以 group_label 为标签计算的 Silhouette 分数。校正后应上升（越高越好），说明生物学分组结构得到保留。"
        />
      </div>
      <el-skeleton v-else-if="loading" :rows="4" animated />
      <el-empty v-else description="暂无 metrics（请先运行 merged baseline 流程）" />

      <div v-if="metrics" class="heur">
        <div v-for="row in heuristicRows" :key="row.label" class="heur__row">
          <span class="heur__k">{{ row.label }}</span>
          <span class="heur__v">{{ row.value == null ? '—' : String(row.value) }}</span>
        </div>
      </div>
    </section>

    <section class="card-panel">
      <h3 class="section-heading">指标解读（数值直接引用自 batch_correction_metrics.json）</h3>
      <p v-for="(p, i) in interpretation" :key="i" class="interp">{{ p }}</p>
      <p v-if="!interpretation.length" class="interp muted">加载报告与 metrics 后可自动生成解释句段。</p>
    </section>

    <!-- ======== 缺失值填充评估区块 ======== -->
    <section class="card-panel">
      <h3 class="section-heading">缺失值填充方法评估（Mask-then-Impute）</h3>
      <p class="interp muted">
        在已填充矩阵上随机遮蔽
        <strong>{{ imputationEvalSummary?.config?.mask_ratio != null ? ((imputationEvalSummary.config.mask_ratio * 100).toFixed(0) + '%') : '…' }}</strong>
        的值，共
        <strong>{{ imputationEvalSummary?.config?.n_repeats ?? '…' }}</strong>
        次重复，计算 RMSE / MAE / NRMSE，量化各填充方法精度。
        最优方法：<strong>{{ imputationEvalSummary?.best_method ?? '（加载中）' }}</strong>。
      </p>
      <ImputationEvalCard
        :summary="imputationEvalSummary"
        :feature-rmse="imputationEvalFeatureRmse"
        :loading="loading && !imputationEvalSummary"
      />
    </section>

    <!-- ======== 差异代谢物分析区块 ======== -->
    <section class="card-panel">
      <h3 class="section-heading">差异代谢物分析（Differential Analysis）</h3>
      <p class="interp muted">
        基于批次校正后矩阵，对任意两组样本执行独立双样本 <strong>t-test</strong>，
        并经 <strong>BH-FDR</strong> 多重校正，计算 <strong>log2 Fold Change</strong>。
        火山图中红色表示显著上调，蓝色表示显著下调，灰色为无显著差异特征。
      </p>
      <VolcanoPlotCard />
    </section>

    <!-- ======== 通路富集分析区块 ======== -->
    <section class="card-panel">
      <h3 class="section-heading">通路富集分析（KEGG Pathway Enrichment）</h3>
      <p class="interp muted">
        基于差异显著代谢物（<strong>label ∈ {上调, 下调}</strong>）的 KEGG Compound ID，
        以全部含注释特征为背景集执行<strong>超几何检验</strong>（等价 Fisher's exact test），
        经 <strong>BH-FDR</strong> 校正筛选富集通路；结果以气泡图与力导向网络图展示。
        KEGG 数据来自 <a href="https://rest.kegg.jp" target="_blank" style="color:#7c3aed">rest.kegg.jp</a>，
        首次运行自动下载并缓存。
      </p>
      <PathwayEnrichmentCard />
    </section>

    <!-- ======== MetaKG 知识图谱溯源区块 ======== -->
    <section class="card-panel">
      <h3 class="section-heading">MetaKG 知识图谱溯源</h3>
      <p class="interp muted">
        基于 <strong>MetaKG</strong> 多库整合知识图谱（KEGG / SMPDB / HMDB），展示本项目代谢物
        与通路、反应、酶之间的一跳关联网络（节点数与边数见下方统计条）。
        节点可拖拽交互，支持关键词高亮搜索，可按节点类型与关系类型动态过滤。
      </p>
      <MetaKGCard />
    </section>

    <!-- ======== 特征注释区块 ======== -->
    <section class="card-panel">
      <h3 class="section-heading">特征注释（Feature Annotation）</h3>
      <p class="interp muted">
        基于各批次 <strong>annotation.csv</strong> 中的 m/z 精确质量匹配，
        映射代谢物名称，并附 <strong>HMDB</strong> 与 <strong>KEGG</strong> 数据库链接，支持关键词搜索。
        （特征总数与覆盖率见下方统计条）
      </p>
      <AnnotationTableCard />
    </section>

    <section class="card-panel">
      <h3 class="section-heading">文件下载</h3>
      <template v-if="files?.files?.length">
        <DownloadFileCard
          v-for="f in files.files"
          :key="f.name"
          :name="f.name"
          :purpose="f.purpose"
          :size-bytes="f.size_bytes"
        />
      </template>
      <el-empty v-else description="暂无可下载文件列表" />

      <div v-if="evaluationFiles?.files?.length" class="dl-split">
        <div class="subhead">Evaluation 产物下载（方法对比实验）</div>
        <p class="interp muted">
          包含 mean / median / knn / baseline / <strong>combat-like</strong>（neuroCombat）各方法的 PCA 坐标 JSON 与评估汇总表。
        </p>
        <DownloadFileCard
          v-for="f in evaluationFiles.files"
          :key="`eval-${f.name}`"
          :name="f.name"
          :purpose="f.purpose"
          :size-bytes="f.size_bytes"
          :href="evaluationDownloadUrl(f.name)"
        />
      </div>
    </section>

    <section class="card-panel">
      <h3 class="section-heading">方法对比实验（evaluation）</h3>
      <p class="interp muted">
        本区块读取 <code>benchmark_merged/_pipeline/evaluation</code> 下的评估产物，
        对比 <strong>mean / median / knn</strong>（仅填充，无批次校正）、
        <strong>baseline</strong>（per-feature location-scale 逐特征位置尺度对齐）与
        <strong>combat-like</strong>（neuroCombat，经验 Bayes 实现，参考 Johnson et al., 2007）三类方法的指标表现。
        图中 "before" 对应 <strong>knn 填充未校正</strong>，"after" 对应 <strong>baseline 校正</strong>结果。
      </p>

      <el-alert
        v-if="evaluationSummary?.note"
        type="info"
        :closable="false"
        show-icon
        class="mb"
        :title="evaluationSummary.note"
      />

      <div class="grid-2">
        <div class="card-panel card-panel--flat">
          <div class="subhead">对比表（evaluation_table.csv）</div>
          <el-table
            v-if="evaluationTable?.rows?.length"
            :data="evaluationTable.rows"
            size="small"
            stripe
            border
            height="320"
          >
            <el-table-column prop="method" label="方法（对外）" min-width="140" />
            <el-table-column prop="method_internal" label="内部 key" width="120" />
            <el-table-column
              prop="silhouette_batch_id_pc12"
              label="silhouette(batch_id)"
              min-width="160"
              :formatter="(r: Record<string,string>) => fmtEvalNum(r.silhouette_batch_id_pc12)"
            />
            <el-table-column
              prop="silhouette_group_label_pc12"
              label="silhouette(group_label)"
              min-width="170"
              :formatter="(r: Record<string,string>) => fmtEvalNum(r.silhouette_group_label_pc12)"
            />
            <el-table-column
              prop="batch_centroid_separation_pc12"
              label="batch centroid distance"
              min-width="190"
              :formatter="(r: Record<string,string>) => fmtEvalNum(r.batch_centroid_separation_pc12)"
            />
          </el-table>
          <el-empty v-else description="暂无 evaluation_table.csv（请先运行 merged pipeline）" />
        </div>

        <div class="card-panel card-panel--flat">
          <div class="subhead">PCA 对比图（knn 填充 vs baseline 校正）</div>
          <div class="img-frame">
            <img :src="evalPcaUrl" alt="evaluation pca before vs after" class="img" loading="lazy" />
          </div>
        </div>
      </div>

      <div class="card-panel card-panel--flat">
        <div class="subhead">单方法 PCA 数据（pca_{method}.json）</div>
        <div class="row">
          <el-select v-model="selectedEvalMethod" style="width: 240px" placeholder="选择方法">
            <el-option
              v-for="o in evalMethodOptions"
              :key="o.internal"
              :label="`${o.display}（${o.internal}）`"
              :value="o.internal"
            />
          </el-select>
          <el-tag
            v-if="selectedEvalMethod === 'combat'"
            type="success"
            effect="light"
          >
            ComBat-like（neuroCombat 经验 Bayes）
          </el-tag>
          <el-tag
            v-else-if="selectedEvalMethod === 'baseline'"
            type="primary"
            effect="light"
          >
            per-feature location-scale 基线校正
          </el-tag>
        </div>
        <pre class="jsondump jsondump--light" v-if="selectedEvalPca">{{ JSON.stringify(selectedEvalPca, null, 2).slice(0, 1800) }}{{ (JSON.stringify(selectedEvalPca).length > 1800) ? '\n…' : '' }}</pre>
        <el-empty v-else description="暂无该方法 PCA JSON（请确认 evaluation 产物存在）" />
      </div>
    </section>

    <section v-if="summary?.raw_merge_report" class="card-panel card-panel--flat">
      <h3 class="section-heading">合并报告摘要（raw_merge_report 节选）</h3>
      <pre class="jsondump">{{ JSON.stringify(summary.raw_merge_report, null, 2).slice(0, 2500) }}{{ (JSON.stringify(summary.raw_merge_report).length > 2500) ? '\n…' : '' }}</pre>
    </section>
  </div>
</template>

<style scoped lang="scss">
.dash__alert {
  margin-bottom: 1rem;
}

.dash__toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.25rem;

  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;

  @media (max-width: 960px) {
    grid-template-columns: 1fr;
  }
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.heur {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--app-border);
}

.heur__row {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  padding: 0.25rem 0;
}

.heur__k {
  color: var(--app-muted);
  font-family: ui-monospace, monospace;
}

.interp {
  margin: 0 0 0.75rem;
  line-height: 1.65;
  font-size: 0.92rem;

  &.muted {
    color: var(--app-muted);
  }
}

.jsondump {
  margin: 0;
  font-size: 0.75rem;
  background: #0f172a;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  overflow: auto;
  max-height: 320px;
  word-break: break-word;
  white-space: pre-wrap;
}

.jsondump--light {
  background: #0b1220;
  max-height: 360px;
}

.mb {
  margin-bottom: 0.75rem;
}

.subhead {
  font-weight: 600;
  margin-bottom: 0.6rem;
  color: var(--app-text);
}

.img-frame {
  border: 1px solid var(--app-border);
  border-radius: 10px;
  background: #fafafa;
  padding: 0.75rem;
  text-align: center;
}

.img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
}

.row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.dl-split {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--app-border);
}
</style>
