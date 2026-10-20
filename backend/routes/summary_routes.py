import logging
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, request

from config import Config
from services.deepseek_service import DeepSeekError, chat_json
from utils.call_logger import log_content_warning

logger = logging.getLogger("medsearch.summary")

summary_bp = Blueprint("summary", __name__)

_SUMMARY_SYSTEM_PROMPT = (
    "你是医学文献分析专家。基于给定的文献英文标题、作者与发布日期，"
    "从以下三个维度分别生成专业、客观的总结，每个维度 2-4 句话："
    "1) keyFindings：该文献的核心研究结果、数据结论与实验证据；"
    "2) researchTrends：该研究方向的发展脉络与未来趋势；"
    "3) clinicalSignificance：对临床实践与诊疗的潜在意义。"
    '仅输出 JSON，格式为 {"keyFindings": "...", "researchTrends": "...", "clinicalSignificance": "..."}。'
)


def _generate_single(article_meta: dict) -> dict:
    """单篇文献独立调用 DeepSeek 生成三维度总结，返回 ArticleSummary 结构。"""
    pmid = article_meta.get("pmid", "")
    authors = article_meta.get("authors", [])
    user_content = (
        f"文献英文标题：{article_meta.get('titleEn', '')}\n"
        f"作者：{', '.join(authors) if authors else '未知'}\n"
        f"发布日期：{article_meta.get('pubDate', '未知')}\n"
        f"PMID：{pmid}"
    )
    messages = [
        {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    base = {"pmid": pmid, "keyFindings": "", "researchTrends": "", "clinicalSignificance": ""}
    try:
        data = chat_json(messages, Config.SUMMARY_TIMEOUT, "summary-generate")
    except DeepSeekError as e:
        logger.warning("[summary] pmid=%s 总结生成失败: %s", pmid, e)
        return {**base, "status": "error"}

    dimensions = {k: data.get(k) for k in Config.SUMMARY_DIMENSIONS}
    valid = all(isinstance(v, str) and v.strip() for v in dimensions.values())
    if not valid:
        log_content_warning("summary-generate", f"pmid={pmid} 三维度字段缺失或为空")
        return {**base, "status": "error"}

    return {
        "pmid": pmid,
        "keyFindings": dimensions["keyFindings"].strip(),
        "researchTrends": dimensions["researchTrends"].strip(),
        "clinicalSignificance": dimensions["clinicalSignificance"].strip(),
        "status": "success",
    }


@summary_bp.post("/api/summary/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    articles = payload.get("articles")

    if not isinstance(articles, list) or len(articles) == 0:
        return jsonify({"code": 1003, "message": "请先勾选文献", "data": None}), 400

    valid_metas = [
        a
        for a in articles
        if isinstance(a, dict) and isinstance(a.get("pmid"), str) and a.get("pmid").strip()
    ]
    if not valid_metas:
        return jsonify({"code": 1003, "message": "请先勾选文献", "data": None}), 400

    # 逐篇独立调用，并发限流 2，实现失败隔离
    with ThreadPoolExecutor(max_workers=Config.SUMMARY_CONCURRENCY) as executor:
        results = list(executor.map(_generate_single, valid_metas))

    summaries = []
    for meta, result in zip(valid_metas, results):
        result = {**result, "pmid": meta.get("pmid", "")}
        summaries.append(result)

    success_count = sum(1 for r in summaries if r["status"] == "success")
    if success_count == 0:
        return jsonify({"code": 2003, "message": "总结生成超时/失败，请重试", "data": None}), 200

    return jsonify({"code": 0, "message": "ok", "data": {"summaries": summaries}})