# MedSearch Frontend

MedSearch - PubMed医学文献AI查询系统 前端应用。面向医生和医学生的 H5（移动端网页）AI 助手，用于检索疾病相关的 PubMed 医学文献，并基于检索结果生成 AI 专业总结。

## 技术栈

- Vue 3（Composition API + `<script setup>`）
- Vite 6 + TypeScript（strict 模式，禁用 `any`）
- 无 UI 框架依赖，纯手写组件与样式

## 目录结构

```
frontend/
├── index.html                    # 入口 HTML（含移动端 viewport 配置）
├── vite.config.ts                # Vite 配置（含 /api 开发代理）
├── package.json
├── tsconfig.json
└── src/
    ├── main.ts                   # 应用入口
    ├── App.vue                   # 四板块纵向布局骨架
    ├── vite-env.d.ts
    ├── styles/
    │   ├── tokens.css            # 设计令牌（色彩/间距/圆角/阴影/字体）
    │   └── main.css              # 全局样式与移动端适配（360-768px）
    ├── types/index.ts            # 领域类型契约（与后端同构对齐）
    ├── api/client.ts             # 统一请求封装（信封解析/超时/错误归一）
    ├── composables/
    │   ├── useKeywordSearch.ts   # 关键词生成与管理全局状态
    │   ├── useLiterature.ts      # 文献分页/勾选全局状态
    │   ├── useSummary.ts         # 总结生成全局状态
    │   └── useToast.ts           # 轻提示全局调用入口
    ├── components/
    │   ├── HeaderSection.vue     # 板块一：页头
    │   ├── SearchSection.vue     # 板块二：检索关键词
    │   ├── LiteratureSection.vue # 板块三：文献列表
    │   ├── SummarySection.vue    # 板块四：文献详情
    │   └── common/               # BlockLoading / EmptyState / Toast
    └── tests/
        └── useKeywordSearch.test.mjs  # 关键词逻辑测试（Node 原生断言）
```

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务（:5173，/api 请求代理至 http://localhost:5000）
npm run dev

# 生产构建（含 vue-tsc 类型检查）
npm run build

# 仅类型检查
npm run typecheck

# 运行关键词逻辑测试（需先用 esbuild 编译 TS）
node node_modules/esbuild/bin/esbuild src/composables/useKeywordSearch.ts \
  --bundle --format=esm --external:vue --outfile=tests/uk_compiled.mjs
node tests/useKeywordSearch.test.mjs
```

> 前置条件：后端 Flask 服务需在 `:5000` 运行，详见 `../backend/README.md`。

## 页面结构（自上而下四个板块）

| 板块 | 组件 | 功能 |
|------|------|------|
| HeaderSection | 页头 | 展示网站名称与 PubMed/AI 标识徽章 |
| SearchSection | 检索关键词 | 疾病描述输入（2 行/300 字）→ AI 生成 3 个中文关键词 → 标签增删（上限 5 个）→ 开始检索文献 |
| LiteratureSection | 文献列表 | 每页 9 篇（序号+复选框+中文标题+PMID）、分页浏览、勾选多篇、更多文献、生成AI总结 |
| SummarySection | 文献详情 | 逐篇卡片（中英文标题/作者前 3 位/日期/PMID/查看原文）+ 关键发现/研究趋势/临床意义三维度总结 |

## 接口约定

前端所有请求经由同源 `/api/*`（开发环境由 Vite 代理转发至 Flask），**禁止直连** DeepSeek / PubMed 等外部服务。

统一响应信封：`{ code, message, data }`，`code=0` 为成功。超时策略：

- 关键词生成：15s（`apiClient.postKeyword`）
- 文献检索：30s（`apiClient.postSearch`）
- 总结生成：60s（`apiClient.postSummary`）

接口契约详见 `frontend/src/types/index.ts` 与 `../.codeartsdoer/specs/medsearch_pubmed/design.md`。

## 设计规范

采用 Minimalist Modern 风格（Electric Blue 渐变 + 双字体 + 微交互），全部设计令牌定义于 `src/styles/tokens.css`：

- 主色：`--color-accent: #0052FF`，渐变：`--gradient-accent`
- 背景：`#FAFAFA` 暖白画布，卡片纯白 + 细边框 + 分层阴影
- 字体：Display（Plus Jakarta Sans / PingFang SC）+ Body（Inter / Noto Sans SC）+ Mono（JetBrains Mono）
- 移动优先响应式，360-768px 适配，安全视口（`env(safe-area-inset-*)`）处理，任意宽度无横向滚动