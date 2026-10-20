<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useLiterature } from '../composables/useLiterature'
import { useSummary } from '../composables/useSummary'
import { useToast } from '../composables/useToast'
import BlockLoading from './common/BlockLoading.vue'
import EmptyState from './common/EmptyState.vue'

const { state, goToPage, goPrev, goNext, toggleSelect, isSelected, getSelectedMetas } =
  useLiterature()
const { state: summaryState, generateSummaries } = useSummary()
const { showToast } = useToast()

const subtitle = computed(() =>
  `检索到${state.totalCount}条PubMed医学文献，已为您筛选 9 篇相关文献，请勾选文献，MedSearch将为您生成专业的总结报告。`
)

const literatureLoading = computed(() => state.status === 'loading')

const actionsDisabled = computed(
  () => literatureLoading.value || summaryState.status === 'loading'
)

const canGoPrev = computed(() => state.currentPage > 1)

const canGoNext = computed(() => state.currentPage < state.totalPages)

const pageInput = ref(String(state.currentPage))

watch(
  () => state.currentPage,
  (page) => {
    pageInput.value = String(page)
  }
)

async function handleGoToPage(): Promise<void> {
  const target = Number.parseInt(pageInput.value, 10)
  const result = await goToPage(target)
  if (!result.ok && result.message) {
    showToast(result.message)
  }
  pageInput.value = String(state.currentPage)
}

async function handlePrev(): Promise<void> {
  if (!canGoPrev.value || actionsDisabled.value) {
    return
  }
  const result = await goPrev()
  if (!result.ok && result.message) {
    showToast(result.message)
  }
}

async function handleNext(): Promise<void> {
  if (!canGoNext.value || actionsDisabled.value) {
    return
  }
  const result = await goNext()
  if (!result.ok && result.message) {
    showToast(result.message)
  }
}

async function handleGenerateSummary(): Promise<void> {
  const metas = getSelectedMetas()
  if (metas.length === 0) {
    showToast('请先勾选文献')
    return
  }
  const result = await generateSummaries(metas)
  if (!result.ok) {
    if (result.message) {
      showToast(result.message)
    }
    return
  }
  if (result.partFailed) {
    showToast('部分文献总结生成失败，可在详情卡片中单独重试')
  }
}
</script>

<template>
  <section class="block-card literature-section">
    <div class="block-header">
      <h2 class="block-title">文献列表</h2>
      <p v-if="state.hasSearched" class="block-subtitle">{{ subtitle }}</p>
      <p v-else class="block-subtitle">
        生成或添加关键词并开始检索后，PubMed 文献将展示在此处。
      </p>
    </div>

    <BlockLoading
      v-if="state.status === 'loading' && state.articles.length === 0"
      text="正在检索文献，请稍候…"
    />

    <EmptyState
      v-else-if="state.hasSearched && state.totalCount === 0"
      text="未检索到相关文献，请调整关键词后重试"
    />

    <template v-else-if="state.articles.length > 0">
      <ul class="literature-list">
        <li
          v-for="(article, index) in state.articles"
          :key="article.pmid"
          class="literature-item"
          :class="{ selected: isSelected(article.pmid) }"
        >
          <label class="item-row">
            <span class="item-index">{{ index + 1 }}</span>
            <input
              class="item-checkbox"
              type="checkbox"
              :checked="isSelected(article.pmid)"
              @change="toggleSelect(article.pmid)"
            />
            <span class="item-title">{{ article.titleZh }}</span>
            <span class="item-pmid">PMID: {{ article.pmid }}</span>
          </label>
        </li>
      </ul>

      <div class="select-info">
        <span class="select-count">已选择 {{ state.selectedPmids.length }} 篇文献</span>
        <span class="page-info">当前第 {{ state.currentPage }} 页，共 {{ state.totalPages }} 页</span>
      </div>

      <div class="pagination" role="navigation" aria-label="文献分页">
        <button
          class="btn-secondary pagination-btn"
          type="button"
          :disabled="!canGoPrev || actionsDisabled"
          @click="handlePrev"
        >
          {{ literatureLoading ? '加载中…' : '上一页' }}
        </button>
        <div class="page-jump">
          <span class="page-jump-label">第</span>
          <input
            v-model="pageInput"
            class="page-input"
            type="text"
            inputmode="numeric"
            :disabled="actionsDisabled"
            :aria-label="`页码定位，共 ${state.totalPages} 页`"
            @keyup.enter="handleGoToPage"
          />
          <span class="page-jump-label">/ {{ state.totalPages }} 页</span>
        </div>
        <button
          class="btn-secondary pagination-btn"
          type="button"
          :disabled="!canGoNext || actionsDisabled"
          @click="handleNext"
        >
          {{ literatureLoading ? '加载中…' : '下一页' }}
        </button>
      </div>

      <div class="literature-actions">
        <button
          class="btn-primary"
          type="button"
          :disabled="summaryState.status === 'loading' || literatureLoading"
          @click="handleGenerateSummary"
        >
          {{ summaryState.status === 'loading' ? '生成中…' : '生成AI总结' }}
        </button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.literature-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.literature-item {
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
  transition: background var(--duration-fast) var(--ease-out);
}

.literature-item:last-child {
  border-bottom: none;
}

.literature-item.selected {
  background: rgba(0, 82, 255, 0.05);
}

.item-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  min-width: 0;
}

.item-index {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-muted-foreground);
  width: 20px;
  flex-shrink: 0;
  text-align: center;
}

.item-checkbox {
  width: 17px;
  height: 17px;
  accent-color: var(--color-accent);
  flex-shrink: 0;
  cursor: pointer;
}

.item-title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-pmid {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-muted-foreground);
  flex-shrink: 0;
}

.select-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
  font-size: 12px;
  color: var(--color-muted-foreground);
}

.select-count {
  color: var(--color-accent);
  font-weight: 600;
}

.literature-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.literature-actions .btn-primary {
  flex: 1;
}

.pagination {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.pagination-btn {
  flex-shrink: 0;
  min-width: 76px;
}

.page-jump {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-muted-foreground);
}

.page-jump-label {
  flex-shrink: 0;
}

.page-input {
  width: 48px;
  height: 32px;
  padding: 0;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-foreground);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-out);
}

.page-input:focus {
  border-color: var(--color-accent);
}

.page-input:disabled {
  opacity: 0.6;
}
</style>