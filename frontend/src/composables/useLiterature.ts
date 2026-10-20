import { reactive } from 'vue'

import { apiClient, ApiError } from '../api/client'
import type { Article, ArticleMeta, LiteratureSearchData } from '../types'
import type { BlockStatus } from './useKeywordSearch'

interface LiteratureState {
  articles: Article[]
  totalCount: number
  totalPages: number
  currentPage: number
  selectedPmids: string[]
  hasSearched: boolean
  status: BlockStatus
}

const state = reactive<LiteratureState>({
  articles: [],
  totalCount: 0,
  totalPages: 0,
  currentPage: 1,
  selectedPmids: [],
  hasSearched: false,
  status: 'idle'
})

const pagesCache = new Map<number, Article[]>()
let currentKeywords: string[] = []

export function useLiterature() {
  async function searchLiterature(
    keywords: string[]
  ): Promise<{ ok: boolean; message?: string }> {
    if (state.status === 'loading') {
      return { ok: false }
    }

    currentKeywords = [...keywords]
    state.status = 'loading'
    try {
      const data = await apiClient.postSearch<LiteratureSearchData>(
        '/api/literature/search',
        { keywords, page: 1 }
      )
      pagesCache.clear()
      pagesCache.set(data.page, data.articles)
      state.articles = data.articles
      state.totalCount = data.totalCount
      state.totalPages = data.totalPages
      state.currentPage = data.page
      state.selectedPmids = []
      state.hasSearched = true
      state.status = 'success'
      return { ok: true }
    } catch (error) {
      state.status = 'error'
      const message =
        error instanceof ApiError && error.message
          ? error.message
          : '文献检索失败，请稍后重试'
      return { ok: false, message }
    }
  }

  async function loadMore(): Promise<{ ok: boolean; message?: string }> {
    if (state.status === 'loading') {
      return { ok: false }
    }
    if (state.currentPage >= state.totalPages) {
      return { ok: false }
    }

    const nextPage = state.currentPage + 1
    state.status = 'loading'
    try {
      const data = await apiClient.postSearch<LiteratureSearchData>(
        '/api/literature/search',
        { keywords: currentKeywords, page: nextPage }
      )
      pagesCache.set(data.page, data.articles)
      state.articles = data.articles
      state.totalCount = data.totalCount
      state.totalPages = data.totalPages
      state.currentPage = data.page
      state.status = 'success'
      return { ok: true }
    } catch (error) {
      state.status = 'error'
      const message =
        error instanceof ApiError && error.message
          ? error.message
          : '文献检索失败，请稍后重试'
      return { ok: false, message }
    }
  }

  function toggleSelect(pmid: string): void {
    const index = state.selectedPmids.indexOf(pmid)
    if (index !== -1) {
      state.selectedPmids.splice(index, 1)
    } else {
      state.selectedPmids.push(pmid)
    }
  }

  function isSelected(pmid: string): boolean {
    return state.selectedPmids.includes(pmid)
  }

  function getSelectedMetas(): ArticleMeta[] {
    const metas: ArticleMeta[] = []
    for (const pmid of state.selectedPmids) {
      for (const articles of pagesCache.values()) {
        const found = articles.find((a) => a.pmid === pmid)
        if (found) {
          metas.push({
            pmid: found.pmid,
            titleEn: found.titleEn,
            authors: found.authors,
            pubDate: found.pubDate
          })
          break
        }
      }
    }
    return metas
  }

  function findArticleByPmid(pmid: string): Article | null {
    for (const articles of pagesCache.values()) {
      const found = articles.find((a) => a.pmid === pmid)
      if (found) {
        return found
      }
    }
    return null
  }

  return {
    state,
    searchLiterature,
    loadMore,
    toggleSelect,
    isSelected,
    getSelectedMetas,
    findArticleByPmid
  }
}