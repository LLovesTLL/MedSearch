<script setup lang="ts">
import { computed } from 'vue'

import type { Article } from '../types'
import { formatAuthors as formatAuthorList, pubmedUrl } from '../utils/format'
import { useLiterature } from '../composables/useLiterature'
import { useSummary } from '../composables/useSummary'
import { useToast } from '../composables/useToast'
import BlockLoading from './common/BlockLoading.vue'
import EmptyState from './common/EmptyState.vue'

const { findArticleByPmid } = useLiterature()
const { state: summaryState, retrySummary } = useSummary()
const { showToast } = useToast()

const pmids = computed(() => Object.keys(summaryState.summaries))

function articleOf(pmid: string): Article | null {
  return findArticleByPmid(pmid)
}

function formatAuthors(article: Article | null): string {
  return formatAuthorList(article?.authors ?? [])
}

async function handleRetry(pmid: string): Promise<void> {
  const article = articleOf(pmid)
  if (!article) {
    showToast('文献数据缺失，无法重试')
    return
  }
  const result = await retrySummary({
    pmid: article.pmid,
    titleEn: article.titleEn,
    authors: article.authors,
    pubDate: article.pubDate
  })
  if (!result.ok && result.message) {
    showToast(result.message)
  }
}
</script>

<template>
  <section class="block-card summary-section">
    <div class="block-header">
      <h2 class="block-title">文献详情</h2>
      <p class="block-subtitle">MedSearch已为您检索的文献生成专业总结</p>
    </div>

    <BlockLoading
      v-if="summaryState.status === 'loading'"
      text="正在生成AI总结，请稍候…"
    />

    <EmptyState
      v-else-if="pmids.length === 0"
      text="勾选文献并点击「生成AI总结」后，逐篇文献的专业总结将展示在此处。"
    />

    <template v-else>
      <transition-group name="fade" tag="div" class="summary-list">
        <article
          v-for="pmid in pmids"
          :key="pmid"
          class="summary-card"
        >
          <template v-if="summaryState.summaries[pmid].status === 'success'">
            <h3 class="card-title-zh">{{ articleOf(pmid)?.titleZh ?? summaryState.summaries[pmid].pmid }}</h3>
            <p class="card-title-en">{{ articleOf(pmid)?.titleEn }}</p>
            <div class="card-meta">
              <span class="meta-authors">{{ formatAuthors(articleOf(pmid)) }}</span>
              <span class="meta-divider">｜</span>
              <span class="meta-date">{{ articleOf(pmid)?.pubDate || '未知日期' }}</span>
              <span class="meta-divider">｜</span>
              <span class="meta-pmid">PMID: {{ pmid }}</span>
              <a
                class="btn-original"
                :href="pubmedUrl(pmid)"
                target="_blank"
                rel="noopener noreferrer"
              >
                查看原文
              </a>
            </div>

            <div class="dimensions">
              <div class="dimension">
                <h4 class="dimension-title">
                  <span class="dimension-icon icon-finding"></span>关键发现
                </h4>
                <p class="dimension-content">{{ summaryState.summaries[pmid].keyFindings }}</p>
              </div>
              <div class="dimension">
                <h4 class="dimension-title">
                  <span class="dimension-icon icon-trend"></span>研究趋势
                </h4>
                <p class="dimension-content">{{ summaryState.summaries[pmid].researchTrends }}</p>
              </div>
              <div class="dimension">
                <h4 class="dimension-title">
                  <span class="dimension-icon icon-clinic"></span>临床意义
                </h4>
                <p class="dimension-content">{{ summaryState.summaries[pmid].clinicalSignificance }}</p>
              </div>
            </div>
          </template>

          <template v-else>
            <h3 class="card-title-zh">{{ articleOf(pmid)?.titleZh ?? '总结生成失败' }}</h3>
            <div class="card-failed">
              <p class="failed-text">该文献总结生成失败，可单独重试。</p>
              <button class="btn-secondary" type="button" @click="handleRetry(pmid)">
                重试
              </button>
            </div>
          </template>
        </article>
      </transition-group>
    </template>
  </section>
</template>

<style scoped>
.summary-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.summary-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-card);
  transition: box-shadow var(--duration-normal) var(--ease-out);
}

.summary-card:hover {
  box-shadow: var(--shadow-lg);
}

.card-title-zh {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.5;
  letter-spacing: -0.01em;
}

.card-title-en {
  margin-top: var(--space-1);
  font-size: 13px;
  color: var(--color-muted-foreground);
  font-style: italic;
  line-height: 1.5;
}

.card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-top: var(--space-3);
  font-size: 12px;
  color: var(--color-muted-foreground);
}

.meta-divider {
  opacity: 0.5;
}

.meta-authors {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-original {
  margin-left: auto;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--color-accent);
  color: var(--color-accent);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}

.btn-original:hover {
  background: var(--color-accent);
  color: var(--color-accent-foreground);
}

.dimensions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px dashed var(--color-border);
}

.dimension-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-body);
}

.dimension-icon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.icon-finding {
  background: var(--color-accent);
}

.icon-trend {
  background: var(--color-accent-secondary);
}

.icon-clinic {
  background: var(--color-success);
}

.dimension-content {
  margin-top: var(--space-1);
  font-size: 13px;
  color: var(--color-foreground);
  line-height: 1.7;
}

.card-failed {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.2);
}

.failed-text {
  font-size: 13px;
  color: var(--color-danger);
}
</style>