<script setup lang="ts">
import { ref } from 'vue'

import { useKeywordSearch } from '../composables/useKeywordSearch'
import { useLiterature } from '../composables/useLiterature'
import { useToast } from '../composables/useToast'
import BlockLoading from './common/BlockLoading.vue'

const { state: keywordState, generateKeywords, addKeyword, removeKeyword } =
  useKeywordSearch()
const { state: literatureState, searchLiterature } = useLiterature()
const { showToast } = useToast()

const description = ref('')
const newKeyword = ref('')

async function handleGenerate(): Promise<void> {
  const result = await generateKeywords(description.value)
  if (!result.ok && result.message) {
    showToast(result.message)
  }
}

function handleAdd(): void {
  const result = addKeyword(newKeyword.value)
  if (!result.ok) {
    if (result.message) {
      showToast(result.message)
    }
    return
  }
  newKeyword.value = ''
}

async function handleSearch(): Promise<void> {
  if (keywordState.keywords.length === 0) {
    showToast('请先生成或添加关键词')
    return
  }
  const result = await searchLiterature([...keywordState.keywords])
  if (!result.ok && result.message) {
    showToast(result.message)
  }
}
</script>

<template>
  <section class="block-card search-section">
    <div class="block-header">
      <h2 class="block-title">MedSearch检索关键词</h2>
      <p class="block-subtitle">
        输入疾病/病理/研究方向，MedSearch将自动提取核心关键词并构建PubMed检索策略。
        示例：肺腺癌的EGFR突变与预后相关性
      </p>
    </div>

    <div class="search-row">
      <textarea
        v-model="description"
        class="search-input"
        placeholder="输入疾病/病理/研究方向描述"
        maxlength="300"
        rows="2"
      ></textarea>
      <button
        class="btn-primary"
        :disabled="keywordState.status === 'loading'"
        @click="handleGenerate"
      >
        {{ keywordState.status === 'loading' ? '生成中…' : '生成关键词' }}
      </button>
    </div>

    <div class="tag-area">
      <template v-if="keywordState.keywords.length > 0">
        <span
          v-for="keyword in keywordState.keywords"
          :key="keyword"
          class="keyword-tag"
        >
          <span class="tag-text">{{ keyword }}</span>
          <button
            class="tag-remove"
            type="button"
            :aria-label="`删除关键词 ${keyword}`"
            @click="removeKeyword(keyword)"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6">
              <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" />
            </svg>
          </button>
        </span>
      </template>
      <span v-else class="tag-placeholder">
        AI 生成的关键词将展示在此处（最多 5 个）
      </span>
    </div>

    <div class="action-row">
      <input
        v-model="newKeyword"
        class="new-keyword-input"
        type="text"
        placeholder="新的关键词"
        maxlength="30"
        @keyup.enter="handleAdd"
      />
      <button
        class="btn-secondary"
        type="button"
        :disabled="keywordState.status === 'loading'"
        @click="handleAdd"
      >
        添加
      </button>
      <button
        class="btn-primary"
        type="button"
        :disabled="
          literatureState.status === 'loading' || keywordState.status === 'loading'
        "
        @click="handleSearch"
      >
        {{ literatureState.status === 'loading' ? '检索中…' : '开始检索文献' }}
      </button>
    </div>

    <BlockLoading
      v-if="literatureState.status === 'loading'"
      text="正在检索 PubMed 文献，请稍候…"
    />
  </section>
</template>

<style scoped>
.search-section {
  border-top: 3px solid transparent;
  background:
    linear-gradient(var(--color-card), var(--color-card)) padding-box,
    var(--gradient-accent) border-box;
}

.search-row {
  display: flex;
  gap: var(--space-3);
  align-items: stretch;
}

.search-input {
  flex: 1;
  min-height: 62px;
  max-height: 96px;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-muted);
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}

.search-input::placeholder {
  color: var(--color-muted-foreground);
  opacity: 0.7;
}

.search-input:focus {
  border-color: var(--color-ring);
  box-shadow: 0 0 0 3px rgba(0, 82, 255, 0.12);
  background: var(--color-card);
}

.tag-area {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--gradient-tag);
  min-height: 52px;
  align-items: center;
  box-shadow: var(--shadow-accent);
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 5px 6px 5px 12px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: var(--color-accent-foreground);
  font-size: 13px;
  font-weight: 600;
  animation: tag-in var(--duration-normal) var(--ease-out) both;
}

.tag-text {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.8);
  transition: all var(--duration-fast) var(--ease-out);
}

.tag-remove:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.tag-remove svg {
  width: 12px;
  height: 12px;
}

.tag-placeholder {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}

.action-row {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

.new-keyword-input {
  flex: 1;
  min-width: 0;
  padding: 10px var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-muted);
  font-size: 14px;
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}

.new-keyword-input::placeholder {
  color: var(--color-muted-foreground);
  opacity: 0.7;
}

.new-keyword-input:focus {
  border-color: var(--color-ring);
  box-shadow: 0 0 0 3px rgba(0, 82, 255, 0.12);
  background: var(--color-card);
}

@keyframes tag-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 400px) {
  .search-row,
  .action-row {
    flex-wrap: wrap;
  }

  .action-row .btn-primary {
    flex: 1;
  }
}
</style>