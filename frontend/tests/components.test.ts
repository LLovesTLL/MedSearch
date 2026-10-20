import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'

import App from '../src/App.vue'
import { useKeywordSearch } from '../src/composables/useKeywordSearch'
import {
  makeArticles,
  makeSummary,
  mockFetch,
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

describe('8.3 组件渲染与核心交互（7.2 自动化全流程）', () => {
  it('四板块标题自上而下完整渲染', () => {
    wrapper = mount(App)
    const text = wrapper.text()
    expect(text).toContain('MedSearch检索关键词')
    expect(text).toContain('文献列表')
    expect(text).toContain('文献详情')
    expect(wrapper.find('.site-name').text()).toBe('MedSearch - PubMed医学文献AI查询系统')
  })

  it('全流程：生成关键词→增删标签→检索→勾选→AI总结→查看原文', async () => {
    const fetchFn = mockFetch({
      '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
      '/api/literature/search': () => ({
        totalCount: 2869,
        page: 1,
        pageSize: 9,
        totalPages: 319,
        articles: makeArticles(9),
      }),
      '/api/summary/generate': (body) => {
        const articles = body.articles as Array<{ pmid: string }>
        return { summaries: articles.map((a) => makeSummary(a.pmid)) }
      },
    })
    wrapper = mount(App)

    await wrapper.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    await findButton(wrapper, '生成关键词')!.trigger('click')
    await flushPromises()
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/keywords/generate',
      expect.objectContaining({ method: 'POST' })
    )
    expect(wrapper.findAll('.keyword-tag')).toHaveLength(3)

    await wrapper.find('.new-keyword-input').setValue('靶向治疗')
    await findButton(wrapper, '添加')!.trigger('click')
    expect(wrapper.findAll('.keyword-tag')).toHaveLength(4)

    await wrapper.find('.tag-remove').trigger('click')
    expect(wrapper.findAll('.keyword-tag')).toHaveLength(3)

    await findButton(wrapper, '开始检索文献')!.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.literature-item')).toHaveLength(9)
    expect(wrapper.text()).toContain('检索到2869条PubMed医学文献')
    expect(wrapper.text()).toContain('当前第 1 页，共 319 页')

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')
    await checkboxes[1].trigger('change')
    expect(wrapper.text()).toContain('已选择 2 篇文献')

    await findButton(wrapper, '生成AI总结')!.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.summary-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('100 的关键发现内容')

    const originalLink = wrapper.find('.btn-original')
    expect(originalLink.attributes('href')).toBe('https://pubmed.ncbi.nlm.nih.gov/100/')
    expect(originalLink.text()).toBe('查看原文')
  })

  it('作者超出 3 位以...截断，不超过 3 位全量展示', async () => {
    mockFetch({
      '/api/keywords/generate': () => ({ keywords: ['肺腺癌', 'EGFR突变', '预后'] }),
      '/api/literature/search': () => ({
        totalCount: 100,
        page: 1,
        pageSize: 9,
        totalPages: 12,
        articles: makeArticles(9),
      }),
      '/api/summary/generate': (body) => {
        const articles = body.articles as Array<{ pmid: string }>
        return { summaries: articles.map((a) => makeSummary(a.pmid)) }
      },
    })
    wrapper = mount(App)

    await wrapper.find('textarea').setValue('肺腺癌的EGFR突变与预后相关性')
    await findButton(wrapper, '生成关键词')!.trigger('click')
    await flushPromises()
    await findButton(wrapper, '开始检索文献')!.trigger('click')
    await flushPromises()
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')
    await findButton(wrapper, '生成AI总结')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Zhang S, Li W, Wang H...')
    expect(wrapper.text()).not.toContain('Chen L')
  })

  it('短描述触发校验提示且不发起请求', async () => {
    const fetchFn = mockFetch({})
    wrapper = mount(App)
    await wrapper.find('textarea').setValue('肺腺癌')
    await findButton(wrapper, '生成关键词')!.trigger('click')
    await flushPromises()
    expect(fetchFn).not.toHaveBeenCalled()
    expect(wrapper.find('.toast-message').text()).toBe('请输入 10-300 字符的疾病描述')
  })

  it('关键词达到 5 个上限后拒绝添加', async () => {
    wrapper = mount(App)
    const { addKeyword } = useKeywordSearch()
    for (const k of ['a', 'b', 'c', 'd', 'e']) {
      addKeyword(k)
    }
    await wrapper.find('.new-keyword-input').setValue('f')
    await findButton(wrapper, '添加')!.trigger('click')
    expect(wrapper.find('.toast-message').text()).toBe('关键词最多 5 个')
    expect(wrapper.findAll('.keyword-tag')).toHaveLength(5)
  })

  it('重复关键词拒绝添加', async () => {
    wrapper = mount(App)
    const { addKeyword } = useKeywordSearch()
    addKeyword('肺腺癌')
    await wrapper.find('.new-keyword-input').setValue('肺腺癌')
    await findButton(wrapper, '添加')!.trigger('click')
    expect(wrapper.find('.toast-message').text()).toBe('该关键词已存在')
  })
})