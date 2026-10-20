import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

from app import app

client = app.test_client()

print("=" * 60)
print("端到端全链路验证（真实 DeepSeek + PubMed 调用）")
print("=" * 60)

# --- 步骤 1：关键词生成 ---
t0 = time.perf_counter()
r1 = client.post(
    "/api/keywords/generate",
    json={"description": "肺腺癌的EGFR突变与预后相关性"},
)
e1 = time.perf_counter() - t0
b1 = r1.get_json()
print(f"\n[1] 关键词生成: HTTP {r1.status_code} code={b1['code']} 耗时 {e1:.1f}s")
print(f"    关键词: {b1['data']['keywords'] if b1['code'] == 0 else b1['message']}")

if b1["code"] != 0:
    sys.exit(1)

# --- 步骤 2：文献检索 ---
t0 = time.perf_counter()
r2 = client.post(
    "/api/literature/search",
    json={"keywords": b1["data"]["keywords"], "page": 1},
)
e2 = time.perf_counter() - t0
b2 = r2.get_json()
print(f"\n[2] 文献检索: HTTP {r2.status_code} code={b2['code']} 耗时 {e2:.1f}s")
if b2["code"] == 0:
    d = b2["data"]
    print(f"    totalCount={d['totalCount']} totalPages={d['totalPages']} 本页={len(d['articles'])} 篇")
    for a in d["articles"][:3]:
        print(f"    - [{a['pmid']}] {a['titleZh'][:30]}（降级={a['titleDegraded']}）")
    articles = d["articles"]
else:
    print(f"    失败: {b2['message']}")
    sys.exit(1)

if not articles:
    print("检索结果为空，跳过总结步骤")
    sys.exit(0)

# --- 步骤 3：AI 总结生成（取前 2 篇）---
metas = [
    {"pmid": a["pmid"], "titleEn": a["titleEn"], "authors": a["authors"], "pubDate": a["pubDate"]}
    for a in articles[:2]
]
t0 = time.perf_counter()
r3 = client.post("/api/summary/generate", json={"articles": metas})
e3 = time.perf_counter() - t0
b3 = r3.get_json()
print(f"\n[3] AI总结生成（{len(metas)} 篇）: HTTP {r3.status_code} code={b3['code']} 耗时 {e3:.1f}s")
if b3["code"] == 0:
    for s in b3["data"]["summaries"]:
        print(f"    - [{s['pmid']}] status={s['status']}")
        if s["status"] == "success":
            print(f"      关键发现: {s['keyFindings'][:60]}...")
            print(f"      临床意义: {s['clinicalSignificance'][:60]}...")
else:
    print(f"    失败: {b3['message']}")

print("\n" + "=" * 60)
print(f"性能汇总: 关键词 {e1:.1f}s (≤15s) | 检索 {e2:.1f}s (≤30s) | 总结 {e3:.1f}s (≤60s)")
print("=" * 60)

# --- 可观测性：调用日志统计 ---
from utils.call_logger import get_stats

print("\n调用日志统计（操作-状态-耗时）:")
for row in get_stats():
    print(f"    {row['operation']:<22} {row['status']:<20} count={row['count']} avg={row['avg_ms']}ms")