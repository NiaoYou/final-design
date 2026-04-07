<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { fetchAnnotationSummary, fetchAnnotationFeatures } from '@/api/benchmark'
import type { AnnotatedFeature, AnnotationSummary } from '@/types/benchmark'

// ---- 状态 ----
const summary = ref<AnnotationSummary | null>(null)
const features = ref<AnnotatedFeature[]>([])
const total = ref(0)
const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(50)

// ---- 初始加载 ----
onMounted(async () => {
  loading.value = true
  try {
    summary.value = await fetchAnnotationSummary()
    await loadPage()
  } finally {
    loading.value = false
  }
})

async function loadPage() {
  const offset = (currentPage.value - 1) * pageSize.value
  const resp = await fetchAnnotationFeatures(offset, pageSize.value, searchText.value || undefined)
  if (resp) {
    features.value = resp.features
    total.value = resp.total
  }
}

async function onSearch() {
  currentPage.value = 1
  await loadPage()
}

watch(currentPage, loadPage)
</script>

<template>
  <div class="ann">
    <!-- 汇总统计 -->
    <div v-if="summary" class="ann__stats">
      <span class="ann__stat">
        总特征 <strong>{{ summary.n_features }}</strong>
      </span>
      <span class="ann__stat ann__stat--ok">
        已注释 <strong>{{ summary.n_annotated }}</strong>
        （{{ summary.coverage_pct }}%）
      </span>
      <span class="ann__stat">
        HMDB <strong>{{ summary.n_with_hmdb }}</strong>
      </span>
      <span class="ann__stat">
        KEGG <strong>{{ summary.n_with_kegg }}</strong>
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
      v-loading="loading"
      :data="features"
      size="small"
      stripe
      border
      max-height="480"
    >
      <!-- Ion -->
      <el-table-column label="Ion" prop="feature_col" width="60" align="center" />

      <!-- m/z -->
      <el-table-column label="m/z" width="100">
        <template #default="{ row }">
          <span class="ann__mz">{{ row.ion_mz.toFixed(4) }}</span>
        </template>
      </el-table-column>

      <!-- 代谢物名 -->
      <el-table-column label="代谢物名称" min-width="160">
        <template #default="{ row }">
          <span v-if="row.metabolite_name" class="ann__name">{{ row.metabolite_name }}</span>
          <span v-else class="ann__na">未注释</span>
        </template>
      </el-table-column>

      <!-- 分子式 -->
      <el-table-column label="分子式" min-width="100">
        <template #default="{ row }">
          <span class="ann__formula">{{ row.formula ?? '—' }}</span>
        </template>
      </el-table-column>

      <!-- 离子模式 -->
      <el-table-column label="离子模式" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.ion_mode" size="small" type="info" effect="plain">
            {{ row.ion_mode }}
          </el-tag>
          <span v-else>—</span>
        </template>
      </el-table-column>

      <!-- 数据库链接 -->
      <el-table-column label="数据库" min-width="120">
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
