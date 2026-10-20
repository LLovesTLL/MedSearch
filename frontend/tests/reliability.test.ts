import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'

import App from '../src/App.vue'
import {
  makeArticles,
  makeSummary,
  mockFetch,
  mockFetchPending,
  mockFetchReject,
  resetState,
} from './helpers'

let wrapper: VueWrapper

beforeEach(() => {
  resetState()
})

afterEach(() => {
  vi.unstubAllGlobals()
  wrapper?.unmount()
})

function findButton(w: VueWrapper, text: string) {
  return w.findAll('button').find((b) => b.text().includes(text))
}

async function prepareSearchedState(w: VueWrapper): Promise<void> {
  mockFetch({
    '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
    '/api/literature/search': () => ({
      totalCount: 2869,
      page: 1,
      pageSize: 9,
      totalPages: 319,
      articles: makeArticles(9),
    }),
  })
  await w.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
  await findButton(w, '生成关键词')!.trigger('click')
  await flushPromises()
  await findButton(w, '开始检索文献')!.trigger('click')
  await flushPromises()
}

describe('7.3 加载状态联动与防重复触发', () => {
  it('关键词生成中：按钮禁用且展示加载文案', async () => {
    mockFetchPending()
    wrapper = mount(App)
    await wrapper.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    const btn = findButton(wrapper, '生成关键词')!
    await btn.trigger('click')
    await flushPromises()
    expect(btn.attributes('disabled')).toBeDefined()
    expect(btn.text()).toContain('生成中…')
    expect(findButton(wrapper, '开始检索文献')!.attributes('disabled')).toBeDefined()
  })

  it('检索进行中：检索/总结/更多文献按钮全部禁用，板块展示加载提示', async () => {
    mockFetch({
      '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
      '/api/literature/search': () => ({
        totalCount: 2869,
        page: 1,
        pageSize: 9,
        totalPages: 319,
        articles: makeArticles(9),
      }),
    })
    wrapper = mount(App)
    await wrapper.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    await findButton(wrapper, '生成关键词')!.trigger('click')
    await flushPromises()
    await findButton(wrapper, '开始检索文献')!.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.literature-item')).toHaveLength(9)

    vi.unstubAllGlobals()
    mockFetchPending()
    await wrapper.find('.literature-actions .btn-secondary').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('正在检索 PubMed 文献，请稍候…')
    expect(wrapper.find('.literature-actions .btn-secondary').text()).toContain('加载中…')
    expect(wrapper.findAll('.literature-item')).toHaveLength(9)
    expect(wrapper.find('.action-row .btn-primary').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.literature-actions .btn-primary').attributes('disabled')).toBeDefined()
    expect(wrapper.find('.literature-actions .btn-secondary').attributes('disabled')).toBeDefined()
  })
})

describe('8.7 可靠性验证（断网模拟）', () => {
  it('断网时关键词生成失败：页面不崩溃、错误提示明确、已生成内容保持', async () => {
    wrapper = mount(App)
    await prepareWithKeywordsFirst(wrapper)

    expect(wrapper.findAll('.keyword-tag')).toHaveLength(3)

    vi.unstubAllGlobals()
    mockFetchReject()
    await findButton(wrapper, '开始检索文献')!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.summary-section').exists()).toBe(true)
    expect(wrapper.find('.toast-message').text()).toBe('网络异常，请检查网络后重试')
    expect(wrapper.findAll('.keyword-tag')).toHaveLength(3)
  })

  it('总结生成断网失败后可重新触发并成功', async () => {
    wrapper = mount(App)
    await prepareSearchedStateFull(wrapper)

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')
    await checkboxes[1].trigger('change')

    vi.unstubAllGlobals()
    mockFetchReject()
    await findButton(wrapper, '生成AI总结')!.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.summary-card')).toHaveLength(0)
    expect(wrapper.find('.toast-message').text()).toBe('网络异常，请检查网络后重试')

    vi.unstubAllGlobals()
    mockFetch({
      '/api/summary/generate': (body) => {
        const articles = body.articles as Array<{ pmid: string }>
        return { summaries: articles.map((a) => makeSummary(a.pmid)) }
      },
    })
    await findButton(wrapper, '生成AI总结')!.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.summary-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('100 的关键发现内容')
  })

  it('总结部分失败（status=error）展示失败卡片而非整页报错', async () => {
    wrapper = mount(App)
    await prepareSearchedStateFull(wrapper)

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')
    await checkboxes[1].trigger('change')

    vi.unstubAllGlobals()
    mockFetch({
      '/api/summary/generate': (body) => {
        const articles = body.articles as Array<{ pmid: string }>
        return {
          summaries: articles.map((a, i) =>
            i === 0 ? makeSummary(a.pmid) : { ...makeSummary(a.pmid), status: 'error' }
          ),
        }
      },
    })
    await findButton(wrapper, '生成AI总结')!.trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.summary-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('该文献总结生成失败，可单独重试。')
    expect(wrapper.text()).toContain('100 的关键发现内容')
  })

  async function prepareWithKeywordsFirst(w: VueWrapper): Promise<void> {
    mockFetch({
      '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
    })
    await w.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    await findButton(w, '生成关键词')!.trigger('click')
    await flushPromises()
  }

  async function prepareSearchedStateFull(w: VueWrapper): Promise<void> {
    mockFetch({
      '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
      '/api/literature/search': () => ({
        totalCount: 2869,
        page: 1,
        pageSize: 9,
        totalPages: 319,
        articles: makeArticles(9),
      }),
    })
    await w.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    await findButton(w, '生成关键词')!.trigger('click')
    await flushPromises()
    await findButton(w, '开始检索文献')!.trigger('click')
    await flushPromises()
  }
})