import { vi } from 'vitest'

import { useKeywordSearch } from '../src/composables/useKeywordSearch'
import { useLiterature } from '../src/composables/useLiterature'
import { useSummary } from '../src/composables/useSummary'
import { useToast } from '../src/composables/useToast'
import type { Article, ArticleSummary } from '../src/types'

export function resetState(): void {
  const kw = useKeywordSearch().state
  kw.keywords = []
  kw.status = 'idle'
  const lit = useLiterature().state
  lit.articles = []
  lit.totalCount = 0
  lit.totalPages = 0
  lit.currentPage = 1
  lit.selectedPmids = []
  lit.hasSearched = false
  lit.status = 'idle'
  const sum = useSummary().state
  sum.summaries = {}
  sum.status = 'idle'
  const toast = useToast().state
  toast.toasts.splice(0, toast.toasts.length)
}

export function jsonResponse(data: unknown, code = 0): object {
  return {
    ok: true,
    status: 200,
    json: async () => ({ code, message: 'ok', data }),
  }
}

type RouteHandler = (body: Record<string, unknown>) => unknown

export function mockFetch(routes: Record<string, RouteHandler>) {
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const handler = routes[url]
    if (!handler) {
      throw new Error(`unexpected fetch url: ${url}`)
    }
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {}
    return jsonResponse(handler(body))
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function mockFetchReject(): ReturnType<typeof vi.fn> {
  const fn = vi.fn(async () => {
    throw new TypeError('Failed to fetch')
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function mockFetchPending(): ReturnType<typeof vi.fn> {
  const fn = vi.fn(() => new Promise<never>(() => {}))
  vi.stubGlobal('fetch', fn)
  return fn
}

export function makeArticle(pmid: string, index: number): Article {
  return {
    pmid,
    titleZh: `肺腺癌EGFR突变研究${index}`,
    titleEn: `EGFR mutation study ${index}`,
    authors: ['Zhang S', 'Li W', 'Wang H', 'Chen L'],
    pubDate: '2024-Jan',
    shortSummary: `该研究探讨EGFR突变与肺腺癌预后的关系${index}。`,
    titleDegraded: false,
  }
}

export function makeArticles(count: number): Article[] {
  return Array.from({ length: count }, (_, i) => makeArticle(String(100 + i), i + 1))
}

export function makeSummary(pmid: string): ArticleSummary {
  return {
    pmid,
    keyFindings: `${pmid} 的关键发现内容`,
    researchTrends: `${pmid} 的研究趋势内容`,
    clinicalSignificance: `${pmid} 的临床意义内容`,
    status: 'success',
  }
}