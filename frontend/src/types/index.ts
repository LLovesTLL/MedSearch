export interface Article {
  pmid: string
  titleZh: string
  titleEn: string
  authors: string[]
  pubDate: string
  shortSummary: string
  titleDegraded: boolean
}

export interface ArticleSummary {
  pmid: string
  keyFindings: string
  researchTrends: string
  clinicalSignificance: string
  status: 'success' | 'error'
}

export interface LiteraturePage {
  totalCount: number
  page: number
  pageSize: number
  totalPages: number
}

export interface KeywordGenerateRequest {
  description: string
}

export interface KeywordGenerateData {
  keywords: string[]
}

export interface LiteratureSearchRequest {
  keywords: string[]
  page: number
}

export interface LiteratureSearchData extends LiteraturePage {
  articles: Article[]
}

export interface ArticleMeta {
  pmid: string
  titleEn: string
  authors: string[]
  pubDate: string
}

export interface SummaryGenerateRequest {
  articles: ArticleMeta[]
}

export interface SummaryGenerateData {
  summaries: ArticleSummary[]
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}