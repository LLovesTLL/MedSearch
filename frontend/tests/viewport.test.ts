import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'

import App from '../src/App.vue'
import { resetState } from './helpers'

let wrapper: VueWrapper

beforeEach(() => {
  resetState()
})

afterEach(() => {
  vi.unstubAllGlobals()
  wrapper?.unmount()
})

const VIEWPORT_WIDTHS = [360, 375, 414, 480, 600, 768]

describe('8.4 移动端兼容性（360-768px 自动化部分）', () => {
  for (const width of VIEWPORT_WIDTHS) {
    it(`视口 ${width}px 下四板块完整渲染无异常`, () => {
      window.innerWidth = width
      window.innerHeight = 800
      wrapper = mount(App)
      const text = wrapper.text()
      expect(text).toContain('MedSearch检索关键词')
      expect(text).toContain('文献列表')
      expect(text).toContain('文献详情')
      expect(text).toContain('MedSearch - PubMed医学文献AI查询系统')
    })
  }

  it('全局样式含 360px 与 600px 媒体查询断点', () => {
    const css = readCss('main.css')
    expect(css).toContain('@media (max-width: 360px)')
    expect(css).toContain('@media (min-width: 600px)')
  })

  it('页面容器限宽 768px 且禁止横向滚动', () => {
    const css = readCss('main.css')
    expect(css).toContain('max-width: 768px')
    expect(css).toContain('overflow-x: hidden')
  })

  it('刘海屏安全视口（safe-area-inset）已处理', () => {
    const css = readCss('main.css')
    expect(css).toContain('env(safe-area-inset-left)')
    expect(css).toContain('env(safe-area-inset-right)')
    expect(css).toContain('env(safe-area-inset-bottom)')
  })

  it('HTML 入口含移动端 viewport 与 theme-color 配置', () => {
    const html = readFileSync(resolve(import.meta.dirname, '../index.html'), 'utf-8')
    expect(html).toContain('width=device-width, initial-scale=1.0')
    expect(html).toContain('viewport-fit=cover')
    expect(html).toContain('theme-color')
  })
})

function readCss(name: string): string {
  return readFileSync(resolve(import.meta.dirname, `../src/styles/${name}`), 'utf-8')
}