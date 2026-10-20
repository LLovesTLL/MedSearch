import type { ApiResponse } from '../types'

type TimeoutType = 'keyword' | 'search' | 'summary'

const TIMEOUT_MS: Record<TimeoutType, number> = {
  keyword: 15000,
  search: 30000,
  summary: 60000
}

export class ApiError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.code = code
    this.name = 'ApiError'
  }
}

async function post<T>(
  url: string,
  body: unknown,
  timeoutType: TimeoutType
): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(
    () => controller.abort(),
    TIMEOUT_MS[timeoutType]
  )

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal
    })

    if (!response.ok) {
      let message = `请求失败（HTTP ${response.status}）`
      try {
        const payload = (await response.json()) as ApiResponse<T>
        if (payload && payload.message) {
          message = payload.message
        }
      } catch {
        // 保留默认错误消息
      }
      throw new ApiError(response.status, message)
    }

    const payload = (await response.json()) as ApiResponse<T>
    if (payload.code !== 0) {
      throw new ApiError(payload.code, payload.message || '请求失败，请稍后重试')
    }
    return payload.data as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(-1, '请求超时，请稍后重试')
    }
    throw new ApiError(-2, '网络异常，请检查网络后重试')
  } finally {
    window.clearTimeout(timer)
  }
}

export const apiClient = {
  postKeyword<T>(url: string, body: unknown): Promise<T> {
    return post<T>(url, body, 'keyword')
  },
  postSearch<T>(url: string, body: unknown): Promise<T> {
    return post<T>(url, body, 'search')
  },
  postSummary<T>(url: string, body: unknown): Promise<T> {
    return post<T>(url, body, 'summary')
  }
}