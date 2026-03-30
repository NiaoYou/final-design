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
import { evaluationDownloadUrl, evaluationPcaImageUrl, pcaBeforeAfterImageUrl } from '@/api/benchmark'
import { formatNumber, formatRatio } from '@/utils/format'
import type { BatchCorrectionMetrics } from '@/types/benchmark'

const store = useBenchmarkStore()
const { summary, report, metrics, files, pcaAfter, evaluationSummary, evaluationTable, evaluationPcas, loading, error } =
  storeToRefs(store)
const { evaluationFiles } = storeToRefs(store)

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
  const m = metrics.value
  const r = report.value
  const parts: string[] = []
  if (m) {
    parts.push(
      `batch_centroid_separation_pc12：校正前 ${formatNumber(m.batch_centroid_separation_pc12_before)}，` +
        `校正后 ${formatNumber(m.batch_centroid_separation_pc12_after)}，` +
        `Δ=${formatNumber(m.delta_batch_centroid_separation)}。`,
    )
    const notes = m.heuristic_mixing_notes
    if (notes?.length) parts.push(`启发式备注（来自 metrics）：${notes.join('；')}`)
  }
  if (r?.baseline_batch_correction?.method_id) {
    parts.push(
      `batch_correction_method_report.json 记载 baseline method_id=${String(r.baseline_batch_correction.method_id)}；` +
        `strict_combat.status=${String((r.strict_combat as { status?: string } | undefined)?.status ?? '—')}。` +
        ' 因此本页展示的是 baseline 可复现校正，不是 strict ComBat。',
    )
  }
  return parts
})

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
    <p class="page-sub">
      数据来自后端 <code>/api/benchmark/merged/*</code> 与产物目录 JSON；不做手填指标。
      <strong>当前实现的是 baseline 批次校正；strict ComBat 尚未实现。</strong>
      请勿将 baseline 称为 ComBat。
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
      />
      <KpiCard
        label="特征数"
        :value="summary?.merged_feature_count ?? '—'"
      />
      <KpiCard label="batch 数" :value="summary?.batch_count ?? '—'" />
      <KpiCard
        label="合并后缺失率"
        :value="formatRatio(summary?.missing_ratio_after_merge, 2)"
      />
    </section>

    <MethodStatusCard :report="report" :loading="loading && !report" />

    <div class="grid-2">
      <PcaImagePanel :src="pcaUrl" />
      <EvRatioChart :ratios="pcaAfter?.explained_variance_ratio as number[] | undefined" />
    </div>

    <section class="card-panel">
      <h3 class="block-title">指标摘要（batch_correction_metrics.json）</h3>
      <div class="metric-grid" v-if="metrics">
        <MetricCompareCard
          title="batch_centroid_separation_pc12"
          :before="metrics.batch_centroid_separation_pc12_before"
          :after="metrics.batch_centroid_separation_pc12_after"
          :delta="metrics.delta_batch_centroid_separation"
        />
        <MetricCompareCard
          title="silhouette(batch_id)"
          :before="metrics.silhouette_batch_id_pc12_before"
          :after="metrics.silhouette_batch_id_pc12_after"
          :delta="metrics.delta_silhouette_batch_id"
        />
        <MetricCompareCard
          title="silhouette(group_label)"
          :before="metrics.silhouette_group_label_pc12_before"
          :after="metrics.silhouette_group_label_pc12_after"
          :delta="metrics.delta_silhouette_group_label"
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
      <h3 class="block-title">结果解释（数值与状态均引用自 JSON）</h3>
      <p v-for="(p, i) in interpretation" :key="i" class="interp">{{ p }}</p>
      <p v-if="!interpretation.length" class="interp muted">加载报告与 metrics 后可自动生成解释句段。</p>
    </section>

    <section class="card-panel">
      <h3 class="block-title">文件下载</h3>
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
          其中 <strong>combat-like</strong> 为简化对齐方法（用于对比），不代表 strict ComBat 已实现。
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
      <h3 class="block-title">方法对比实验（evaluation）</h3>
      <p class="interp muted">
        本区块读取 <code>benchmark_merged/_pipeline/evaluation</code> 下的评估产物。
        其中 <strong>combat-like</strong> 为简化对齐方法（用于对比），不代表 strict ComBat 已实现。
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
            <el-table-column prop="silhouette_batch_id_pc12" label="silhouette(batch_id)" min-width="160" />
            <el-table-column prop="silhouette_group_label_pc12" label="silhouette(group_label)" min-width="170" />
            <el-table-column prop="batch_centroid_separation_pc12" label="batch centroid distance" min-width="190" />
          </el-table>
          <el-empty v-else description="暂无 evaluation_table.csv（请先运行 merged pipeline）" />
        </div>

        <div class="card-panel card-panel--flat">
          <div class="subhead">PCA 对比图（evaluation/pca_before_vs_after.png）</div>
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
          <el-tag type="warning" effect="plain" v-if="evalMethodOptions.find(o => o.internal===selectedEvalMethod)?.display==='combat-like'">
            combat-like（非 strict ComBat）
          </el-tag>
        </div>
        <pre class="jsondump jsondump--light" v-if="selectedEvalPca">{{ JSON.stringify(selectedEvalPca, null, 2).slice(0, 1800) }}{{ (JSON.stringify(selectedEvalPca).length > 1800) ? '\n…' : '' }}</pre>
        <el-empty v-else description="暂无该方法 PCA JSON（请确认 evaluation 产物存在）" />
      </div>
    </section>

    <section v-if="summary?.raw_merge_report" class="card-panel card-panel--flat">
      <h3 class="block-title">合并报告摘要（raw_merge_report 节选）</h3>
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
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;

  @media (max-width: 960px) {
    grid-template-columns: 1fr;
  }
}

.block-title {
  margin: 0 0 1rem;
  font-size: 1.05rem;
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
  margin: 0 0 0.65rem;
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
