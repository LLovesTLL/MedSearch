import { reactive } from 'vue'

import { apiClient, ApiError } from '../api/client'
import type { ArticleMeta, ArticleSummary, SummaryGenerateData } from '../types'
import type { BlockStatus } from './useKeywordSearch'

interface SummaryState {
  summaries: Record<string, ArticleSummary>
  status: BlockStatus
}

const state = reactive<SummaryState>({
  summaries: {},
  status: 'idle'
})

export function useSummary() {
  async function generateSummaries(
    articles: ArticleMeta[]
  ): Promise<{ ok: boolean; partFailed?: boolean; message?: string }> {
    if (articles.length === 0) {
      return { ok: false, message: '请先勾选文献' }
    }
    if (state.status === 'loading') {
      return { ok: false }
    }

    state.status = 'loading'
    try {
      const data = await apiClient.postSummary<SummaryGenerateData>(
        '/api/summary/generate',
        { articles }
      )
      for (const summary of data.summaries) {
        state.summaries[summary.pmid] = summary
      }
      const partFailed = data.summaries.some((s) => s.status === 'error')
      state.status = 'success'
      return { ok: true, partFailed }
    } catch (error) {
      state.status = 'error'
      const message =
        error instanceof ApiError && error.message
          ? error.message
          : '总结生成超时/失败，请重试'
      return { ok: false, message }
    }
  }

  async function retrySummary(
    article: ArticleMeta
  ): Promise<{ ok: boolean; message?: string }> {
    if (state.status === 'loading') {
      return { ok: false }
    }

    try {
      const data = await apiClient.postSummary<SummaryGenerateData>(
        '/api/summary/generate',
        { articles: [article] }
      )
      for (const summary of data.summaries) {
        state.summaries[summary.pmid] = summary
      }
      return { ok: true }
    } catch (error) {
      const message =
        error instanceof ApiError && error.message
          ? error.message
          : '总结生成超时/失败，请重试'
      return { ok: false, message }
    }
  }

  return { state, generateSummaries, retrySummary }
}