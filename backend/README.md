# MedSearch Backend

MedSearch - PubMed医学文献AI查询系统 后端服务。作为唯一的外部服务出口，负责 DeepSeek AI 调用与 PubMed E-utilities 检索的代理编排，向前端提供 REST/JSON 接口。

## 技术栈

- Python 3.13 + Flask 3
- flask-cors（跨域）
- requests（外部服务调用）
- python-dotenv（环境变量注入）
- pytest（测试）

## 目录结构

```
backend/
├── app.py                        # Flask 入口、CORS 配置、蓝图注册
├── config.py                     # 全部核心配置常量（.env 注入密钥）
├── requirements.txt
├── .env                          # DEEPSEEK_API_KEY（严禁入库）
├── routes/
│   ├── keyword_routes.py         # POST /api/keywords/generate
│   ├── literature_routes.py      # POST /api/literature/search
│   └── summary_routes.py         # POST /api/summary/generate
├── services/
│   ├── deepseek_service.py       # DeepSeek 统一客户端（JSON 解析容错/重试）
│   ├── pubmed_service.py         # esearch/efetch 客户端（限频 ≤3 次/秒）
│   └── search_orchestrator.py    # 检索编排（翻译→检索→改写→过滤→分页）
├── utils/
│   └── call_logger.py            # 外部调用日志（摘要/耗时/状态/统计）
└── tests/
    ├── conftest.py               # pytest fixtures
    ├── test_routes.py            # 接口测试（正常/异常路径，mock 外部服务）
    ├── test_services.py          # 服务层单测
    ├── smoke_check.py            # 接口冒烟脚本（test_client）
    └── integration_check.py      # 本机联通验证脚本
```

## 快速开始

```bash
cd backend

# 创建虚拟环境（首次）
python -m venv venv

# 安装依赖（本机代理受限环境请加 NO_PROXY="*" 并使用镜像源）
NO_PROXY="*" no_proxy="*" ./venv/Scripts/pip.exe install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置密钥：编辑 .env，填入真实 DeepSeek API Key
#   DEEPSEEK_API_KEY=sk-xxxxxxxx
#   DEEPSEEK_MODEL=deepseek-chat

# 启动服务（:5000）
./venv/Scripts/python.exe app.py

# 运行测试（不依赖真实外部网络）
./venv/Scripts/python.exe -m pytest tests/test_routes.py tests/test_services.py -v

# 接口冒烟验证
./venv/Scripts/python.exe tests/smoke_check.py
```

## 配置说明

密钥经 `.env` 注入（已被根目录 `.gitignore` 排除），业务常量定义于 `config.py`：

| 配置项 | 取值 | 说明 |
|--------|------|------|
| DEEPSEEK_API_KEY | 环境变量注入 | 仅服务端持有，禁止入库；系统环境变量优先于 `.env` |
| DEEPSEEK_MODEL | `deepseek-flash` | DeepSeek 模型名（`backend/.env` 配置；官方支持的模型为 `deepseek-flash` / `deepseek-v4-pro`） |
| KEYWORD_TIMEOUT | 15s | 关键词生成超时 |
| SEARCH_TIMEOUT | 30s | 检索编排超时 |
| SUMMARY_TIMEOUT | 60s | 单篇总结超时 |
| PAGE_SIZE | 9 | 每页文献数 |
| MAX_KEYWORDS | 5 | 关键词上限 |
| PUBMED_API_KEY | 环境变量注入（可选） | 从系统环境变量 `PUDMED_E-UTILITIES_API`（或标准命名 `PUBMED_API_KEY`）读取；配置后 E-utilities 限额由 3 次/秒提升至 10 次/秒（自动生效） |
| PUBMED_RATE_LIMIT | 10（有 Key）/ 3（无 Key） | PubMed 调用频率上限（串行化保证） |
| CANDIDATE_EXTRA | 6 | 检索候补超额数（数据完备性过滤顶替用） |

## API 接口

统一响应信封：`{ code, message, data }`，`code=0` 为成功；HTTP 状态仅区分 200（成功/业务失败）、400（参数错误）、500（内部错误）。

### POST /api/keywords/generate

疾病描述 → 3 个中文关键词。

- 请求：`{ "description": string }`（10-300 字符）
- 响应 data：`{ "keywords": string[] }`（恰好 3 个）
- 错误码：`1001` 描述长度不合法；`2001` AI 调用失败/超时/格式不符

### POST /api/literature/search

中文关键词 → 分页文献列表（内部完成关键词翻译 → 检索策略构建 → PubMed 检索 → 标题翻译 + 100 字内短摘要 → 完备性过滤）。

- 请求：`{ "keywords": string[], "page": number }`（1-5 个互不相同关键词，页码从 1 开始）
- 响应 data：`{ totalCount, page, pageSize, totalPages, articles: Article[] }`
- 错误码：`1002` 关键词列表为空/超限/含重复；`2002` 翻译或 PubMed 调用失败/超时
- 降级规则：短摘要生成失败的文献剔除并由候补顶替；标题翻译失败仅降级展示英文标题（`titleDegraded=true`）

### POST /api/summary/generate

勾选文献 → 逐篇三维度总结（关键发现/研究趋势/临床意义），逐篇独立调用、并发限流 2、失败隔离。

- 请求：`{ "articles": [{ pmid, titleEn, authors, pubDate }] }`
- 响应 data：`{ "summaries": [{ pmid, keyFindings, researchTrends, clinicalSignificance, status }] }`（与请求按 pmid 一一对应，`status: 'success' | 'error'`）
- 错误码：`1003` 勾选列表为空；`2003` 全部篇失败

### GET /api/health

健康检查，返回 `{ code: 0, data: { status: "up" } }`。

## 安全与可观测性

- **安全**：DeepSeek API Key 仅存服务端进程环境；前端仅经 `/api/*` 代理访问，响应不含任何凭证；CORS 仅允许 `localhost:5173` 开发源；无数据持久化（会话内有效）
- **可观测性**：`call_logger` 按统一结构记录每次外部调用的目标服务、请求摘要（不含用户原文全文）、耗时、结果状态；AI 返回内容异常记录告警日志；`get_stats()` 输出"操作类型-结果状态-耗时"维度统计

## 核心流程

1. **关键词生成**：二次校验描述长度（10-300）→ DeepSeek 生成恰好 3 个非空中文关键词 → 数量/非空校验，格式不符视为失败（code=2001）
2. **文献检索编排**（`search_orchestrator.py`）：DeepSeek 批量翻译中文关键词为英文 → AND 组合构建检索策略 → esearch（`sort=relevance`，retmax=9+6 候补）→ 命中 0 返回空结果 → efetch 获取元数据 → DeepSeek 单次批量完成标题翻译与短摘要 → 完备性过滤 → 组装 9 篇 + totalCount/totalPages
3. **总结生成**：逐篇独立调用 DeepSeek（并发限流 2）→ 三维度任一为空视为该篇失败 → 部分失败在 code=0 中按状态标记返回，实现失败隔离