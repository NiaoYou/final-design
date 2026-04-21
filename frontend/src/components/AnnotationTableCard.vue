<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { fetchAnnotationSummary, fetchAnnotationFeatures } from '@/api/benchmark'
import { fetchDatasetAnnotationSummary, fetchDatasetAnnotationFeatures } from '@/api/dataset'
import type { AnnotatedFeature, AnnotationSummary } from '@/types/benchmark'

// ---- Props ----
const props = withDefaults(defineProps<{ dataset?: string }>(), { dataset: 'benchmark' })
const isBenchmark = computed(() => props.dataset === 'benchmark')

// ---- 状态 ----
const summary = ref<(AnnotationSummary & { annotation_source?: string }) | null>(null)
const features = ref<AnnotatedFeature[]>([])
const total = ref(0)
const loading = ref(false)
const pageLoading = ref(false)
const errorMsg = ref<string | null>(null)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(50)

// ---- 初始加载 ----
async function loadSummary() {
  loading.value = true
  errorMsg.value = null
  // 切换数据集时重置
  summary.value = null
  features.value = []
  total.value = 0
  currentPage.value = 1
  searchText.value = ''
  try {
    summary.value = isBenchmark.value
      ? await fetchAnnotationSummary()
      : await fetchDatasetAnnotationSummary(props.dataset)
    await loadPage()
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '注释数据加载失败，请刷新重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => void loadSummary())

// 数据集切换时重新加载
watch(() => props.dataset, () => void loadSummary())

async function loadPage() {
  pageLoading.value = true
  errorMsg.value = null
  try {
    const offset = (currentPage.value - 1) * pageSize.value
    const resp = isBenchmark.value
      ? await fetchAnnotationFeatures(offset, pageSize.value, searchText.value || undefined)
      : await fetchDatasetAnnotationFeatures(props.dataset, offset, pageSize.value, searchText.value || undefined)
    if (resp) {
      features.value = resp.features
      total.value = resp.total
    }
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ?? '分页加载失败，请重试。'
  } finally {
    pageLoading.value = false
  }
}

async function onSearch() {
  currentPage.value = 1
  await loadPage()
}

// 监听分页切换
watch(currentPage, loadPage)
// searchText 通过 @clear / @keyup.enter / 搜索按钮触发 onSearch，无需额外 watch

// bioheart/mi 的字段名：用 feature 代替 feature_col，且无 ion_mz / ion_mode
// 统一从 row 中取合适的显示值
function getFeatureName(row: any): string {
  return row.feature_col ?? row.feature ?? '—'
}

// 是否需要"注释名称"列（仅当 bioheart/mi 中 metabolite_name 与 feature 不同时才显示）
const showAnnotationNameColumn = computed(() =>
  !isBenchmark.value && features.value.some(
    (f: any) => f.metabolite_name && f.metabolite_name !== f.feature
  )
)
</script>

<template>
  <div class="ann">
    <!-- 错误提示 -->
    <el-alert
      v-if="errorMsg"
      type="error"
      :title="errorMsg"
      :closable="false"
      show-icon
      style="margin-bottom: 0.75rem"
    />

    <!-- 汇总统计 -->
    <div v-if="summary" class="ann__stats">
      <span class="ann__stat">
        总特征 <strong>{{ summary.n_features }}</strong>
      </span>
      <span class="ann__stat ann__stat--ok">
        已注释 <strong>{{ summary.n_annotated }}</strong>
        （{{ summary.coverage_pct != null ? summary.coverage_pct + '%' : (summary.n_features ? ((summary.n_annotated / summary.n_features * 100).toFixed(1) + '%') : '—') }}）
      </span>
      <span class="ann__stat">
        HMDB <strong>{{ summary.n_with_hmdb ?? '—' }}</strong>
      </span>
      <span class="ann__stat">
        KEGG <strong>{{ summary.n_with_kegg }}</strong>
      </span>
      <span v-if="summary.annotation_source" class="ann__stat ann__stat--src">
        来源：{{ summary.annotation_source }}
      </span>
    </div>

    <!-- 搜索栏 -->
    <div class="ann__search-row">
      <el-input
        v-model="searchText"
        placeholder="搜索代谢物名 / 分子式 / KEGG ID / HMDB ID"
        clearable
        size="small"
        style="width: 340px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      >
        <template #suffix>
          <el-button link @click="onSearch">搜索</el-button>
        </template>
      </el-input>
      <span class="ann__hint">共 {{ total }} 条</span>
    </div>

    <!-- 注释表格 -->
    <el-table
      v-loading="loading || pageLoading"
      :data="features"
      size="small"
      stripe
      border
      max-height="480"
    >
      <!-- 特征标识：benchmark 显示 Ion 编号，bioheart/mi 显示代谢物名 -->
      <el-table-column :label="isBenchmark ? 'Ion' : '代谢物名称'" :min-width="isBenchmark ? 60 : 160">
        <template #default="{ row }">
          <span class="ann__name">{{ getFeatureName(row) }}</span>
        </template>
      </el-table-column>

      <!-- m/z（仅 benchmark 有） -->
      <el-table-column v-if="isBenchmark" label="m/z" width="100">
        <template #default="{ row }">
          <span class="ann__mz">{{ row.ion_mz != null ? row.ion_mz.toFixed(4) : '—' }}</span>
        </template>
      </el-table-column>

      <!-- 代谢物名（仅 benchmark 显示，bioheart/mi 已在第一列） -->
      <el-table-column v-if="isBenchmark" label="代谢物名称" min-width="160">
        <template #default="{ row }">
          <span v-if="row.metabolite_name" class="ann__name">{{ row.metabolite_name }}</span>
          <span v-else class="ann__na">未注释</span>
        </template>
      </el-table-column>

      <!-- bioheart/mi 的注释名（若有独立 metabolite_name 字段则展示） -->
      <el-table-column v-if="showAnnotationNameColumn" label="注释名称" min-width="160">
        <template #default="{ row }">
          <span v-if="(row as any).metabolite_name && (row as any).metabolite_name !== (row as any).feature" class="ann__name">{{ (row as any).metabolite_name }}</span>
          <span v-else class="ann__na">—</span>
        </template>
      </el-table-column>

      <!-- 分子式 -->
      <el-table-column label="分子式" min-width="100">
        <template #default="{ row }">
          <span class="ann__formula">{{ row.formula ?? '—' }}</span>
        </template>
      </el-table-column>

      <!-- 离子模式（仅 benchmark 有） -->
      <el-table-column v-if="isBenchmark" label="离子模式" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.ion_mode" size="small" type="info" effect="plain">
            {{ row.ion_mode }}
          </el-tag>
          <span v-else>—</span>
        </template>
      </el-table-column>

      <!-- HMDB IDs（bioheart/mi 可能有多个） -->
      <el-table-column v-if="!isBenchmark" label="HMDB" min-width="130">
        <template #default="{ row }">
          <div class="ann__links">
            <template v-if="(row as any).hmdb_ids?.length">
              <a
                v-for="hid in (row as any).hmdb_ids.slice(0, 2)"
                :key="hid"
                :href="`https://hmdb.ca/metabolites/${hid}`"
                target="_blank"
                class="ann__link ann__link--hmdb"
              >{{ hid }}</a>
              <span v-if="(row as any).hmdb_ids.length > 2" class="ann__na">+{{ (row as any).hmdb_ids.length - 2 }}</span>
            </template>
            <span v-else class="ann__na">—</span>
          </div>
        </template>
      </el-table-column>

      <!-- KEGG IDs（bioheart/mi 可能有多个） -->
      <el-table-column v-if="!isBenchmark" label="KEGG" min-width="120">
        <template #default="{ row }">
          <div class="ann__links">
            <template v-if="(row as any).kegg_ids?.length">
              <a
                v-for="kid in (row as any).kegg_ids.slice(0, 2)"
                :key="kid"
                :href="`https://www.kegg.jp/entry/${kid}`"
                target="_blank"
                class="ann__link ann__link--kegg"
              >{{ kid }}</a>
              <span v-if="(row as any).kegg_ids.length > 2" class="ann__na">+{{ (row as any).kegg_ids.length - 2 }}</span>
            </template>
            <span v-else class="ann__na">—</span>
          </div>
        </template>
      </el-table-column>

      <!-- 数据库链接（仅 benchmark，已有 hmdb_url / kegg_url 字段） -->
      <el-table-column v-if="isBenchmark" label="数据库" min-width="120">
        <template #default="{ row }">
          <div class="ann__links">
            <a
              v-if="row.hmdb_url"
              :href="row.hmdb_url"
              target="_blank"
              class="ann__link ann__link--hmdb"
            >
              HMDB
            </a>
            <a
              v-if="row.kegg_url"
              :href="row.kegg_url"
              target="_blank"
              class="ann__link ann__link--kegg"
            >
              KEGG
            </a>
            <span v-if="!row.hmdb_url && !row.kegg_url" class="ann__na">—</span>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="ann__pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        small
        background
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.ann__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.2rem;
  font-size: 0.84rem;
  color: var(--app-muted);
  margin-bottom: 0.9rem;
  padding: 0.55rem 0.9rem;
  background: rgba(37, 99, 235, 0.03);
  border: 1px solid rgba(37, 99, 235, 0.1);
  border-radius: 8px;
}

.ann__stat strong {
  color: var(--app-text);
  margin-left: 2px;
}

.ann__stat--ok strong {
  color: #059669;
}

.ann__stat--src {
  color: #7c3aed;
  font-style: italic;
}

.ann__search-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.ann__hint {
  font-size: 0.82rem;
  color: var(--app-muted);
}

.ann__mz {
  font-family: 'Courier New', monospace;
  font-size: 0.82rem;
  color: #475569;
}

.ann__name {
  font-weight: 500;
  color: var(--app-text);
}

.ann__na {
  color: var(--app-muted);
  font-size: 0.8rem;
}

.ann__formula {
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: #64748b;
}

.ann__links {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.ann__link {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 600;
  text-decoration: none;

  &--hmdb {
    background: #dbeafe;
    color: #1d4ed8;
    &:hover { background: #bfdbfe; }
  }

  &--kegg {
    background: #dcfce7;
    color: #15803d;
    &:hover { background: #bbf7d0; }
  }
}

.ann__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}
</style>
