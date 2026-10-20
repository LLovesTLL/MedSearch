import { reactive } from 'vue'

import { apiClient, ApiError } from '../api/client'
import type { KeywordGenerateData } from '../types'

export type BlockStatus = 'idle' | 'loading' | 'error' | 'success'

export const MIN_DESCRIPTION_LENGTH = 10
export const MAX_DESCRIPTION_LENGTH = 300
export const MAX_KEYWORDS = 5

interface KeywordSearchState {
  keywords: string[]
  status: BlockStatus
}

const state = reactive<KeywordSearchState>({
  keywords: [],
  status: 'idle'
})

export function isValidDescription(description: string): boolean {
  const length = description.trim().length
  return length >= MIN_DESCRIPTION_LENGTH && length <= MAX_DESCRIPTION_LENGTH
}

export function useKeywordSearch() {
  async function generateKeywords(
    description: string
  ): Promise<{ ok: boolean; message?: string }> {
    if (!isValidDescription(description)) {
      return { ok: false, message: '请输入 10-300 字符的疾病描述' }
    }
    if (state.status === 'loading') {
      return { ok: false }
    }

    state.status = 'loading'
    try {
      const data = await apiClient.postKeyword<KeywordGenerateData>(
        '/api/keywords/generate',
        { description: description.trim() }
      )
      state.keywords = data.keywords
      state.status = 'success'
      return { ok: true }
    } catch (error) {
      state.status = 'error'
      const message =
        error instanceof ApiError && error.message
          ? error.message
          : '关键词生成失败，请稍后重试'
      return { ok: false, message }
    }
  }

  function addKeyword(keyword: string): { ok: boolean; message?: string } {
    const trimmed = keyword.trim()
    if (!trimmed) {
      return { ok: false, message: '请输入关键词' }
    }
    if (state.keywords.includes(trimmed)) {
      return { ok: false, message: '该关键词已存在' }
    }
    if (state.keywords.length >= MAX_KEYWORDS) {
      return { ok: false, message: '关键词最多 5 个' }
    }
    state.keywords.push(trimmed)
    return { ok: true }
  }

  function removeKeyword(keyword: string): void {
    const index = state.keywords.indexOf(keyword)
    if (index !== -1) {
      state.keywords.splice(index, 1)
    }
  }

  return { state, generateKeywords, addKeyword, removeKeyword }
}