import json
import logging
import math

from config import Config
from services import pubmed_service
from services.deepseek_service import DeepSeekError, chat_json
from utils.call_logger import log_content_warning

logger = logging.getLogger("medsearch.orchestrator")


class SearchOrchestrationError(Exception):
    """检索编排失败（翻译失败/PubMed 失败/超时）。"""


_TRANSLATE_SYSTEM_PROMPT = (
    "你是医学文献检索专家。将下列中文医学关键词翻译为对应的英文医学术语，"
    "用于 PubMed 检索。保持顺序一致，逐项翻译。"
    '仅输出 JSON，格式为 {"translations": [{"zh": "中文关键词", "en": "English term"}]}。'
)

_REWRITE_SYSTEM_PROMPT = (
    "你是医学文献编辑。为下列英文文献逐篇生成："
    "1) titleZh：文献标题的准确中文翻译（不超过 60 字）；"
    "2) shortSummary：文献核心内容的中文短摘要（不超过 100 字），"
    "基于英文摘要提炼，不要直接照抄英文。"
    '仅输出 JSON，格式为 {"items": [{"pmid": "...", "titleZh": "...", "shortSummary": "..."}]}。'
)


def _translate_keywords(keywords: list[str]) -> list[str]:
    """DeepSeek 批量翻译中文关键词为英文，保持顺序。"""
    user_content = "中文关键词列表：" + json_join(keywords)
    messages = [
        {"role": "system", "content": _TRANSLATE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    data = chat_json(messages, Config.SEARCH_TIMEOUT, "keyword-translate")
    translations = data.get("translations")
    if not isinstance(translations, list) or len(translations) != len(keywords):
        log_content_warning("keyword-translate", f"翻译条目数不符: {translations}")
        raise SearchOrchestrationError("关键词翻译返回格式不符")

    en_list: list[str] = []
    for item in translations:
        if not isinstance(item, dict):
            raise SearchOrchestrationError("关键词翻译条目格式不符")
        en = item.get("en")
        if not isinstance(en, str) or not en.strip():
            raise SearchOrchestrationError("关键词翻译缺少英文结果")
        en_list.append(en.strip())
    return en_list


def json_join(items: list[str]) -> str:

    return json.dumps(items, ensure_ascii=False)


def _build_search_term(english_keywords: list[str]) -> str:
    return " AND ".join(f"({kw})" for kw in english_keywords)


def _process_articles(meta_articles: list[dict]) -> list[dict]:
    """DeepSeek 单次批量调用完成标题翻译与 100 字内中文短摘要。"""
    items = [
        {"pmid": a["pmid"], "titleEn": a["titleEn"], "abstract": a["abstractEn"][:1500]}
        for a in meta_articles
    ]
    user_content = "文献列表：" + json_join(items)
    messages = [
        {"role": "system", "content": _REWRITE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    data = chat_json(messages, Config.SEARCH_TIMEOUT, "article-rewrite")
    items_out = data.get("items")
    if not isinstance(items_out, list):
        log_content_warning("article-rewrite", "返回 items 缺失")
        raise SearchOrchestrationError("文献加工返回格式不符")

    processed: dict[str, dict] = {}
    for item in items_out:
        if isinstance(item, dict) and isinstance(item.get("pmid"), str):
            processed[item["pmid"]] = item
    return [processed.get(a["pmid"], {}) for a in meta_articles]


def search_literature(keywords: list[str], page: int) -> dict:
    """检索编排：翻译→检索→元数据→改写→完备性过滤→组装分页数据。

    返回 LiteratureSearchData 结构；失败抛出 SearchOrchestrationError。
    """
    try:
        english_keywords = _translate_keywords(keywords)
    except DeepSeekError as e:
        raise SearchOrchestrationError(f"关键词翻译失败: {e}") from e

    term = _build_search_term(english_keywords)
    retstart = (page - 1) * Config.PAGE_SIZE
    retmax = Config.PAGE_SIZE + Config.CANDIDATE_EXTRA

    try:
        total_count, pmid_list = pubmed_service.esearch(term, retstart, retmax)
    except pubmed_service.PubMedError as e:
        raise SearchOrchestrationError(f"PubMed 检索失败: {e}") from e

    total_pages = math.ceil(total_count / Config.PAGE_SIZE)
    if total_count == 0 or not pmid_list:
        return {
            "totalCount": 0,
            "page": page,
            "pageSize": Config.PAGE_SIZE,
            "totalPages": 0,
            "articles": [],
        }

    try:
        meta_articles = pubmed_service.efetch(pmid_list)
    except pubmed_service.PubMedError as e:
        raise SearchOrchestrationError(f"PubMed 元数据获取失败: {e}") from e

    try:
        processed = _process_articles(meta_articles)
    except DeepSeekError as e:
        raise SearchOrchestrationError(f"文献标题翻译与摘要生成失败: {e}") from e

    # 数据完备性过滤：短摘要失败剔除并由候补顶替；标题翻译失败降级英文标题不剔除
    complete_articles: list[dict] = []
    for meta, proc in zip(meta_articles, processed):
        title_zh = proc.get("titleZh")
        short_summary = proc.get("shortSummary")
        if not isinstance(short_summary, str) or not short_summary.strip():
            log_content_warning(
                "article-rewrite", f"pmid={meta['pmid']} 短摘要缺失，剔除并由候补顶替"
            )
            continue
        if not isinstance(title_zh, str) or not title_zh.strip():
            complete_articles.append(
                {
                    "pmid": meta["pmid"],
                    "titleZh": meta["titleEn"],
                    "titleEn": meta["titleEn"],
                    "authors": meta["authors"],
                    "pubDate": meta["pubDate"],
                    "shortSummary": short_summary.strip(),
                    "titleDegraded": True,
                }
            )
            continue
        complete_articles.append(
            {
                "pmid": meta["pmid"],
                "titleZh": title_zh.strip(),
                "titleEn": meta["titleEn"],
                "authors": meta["authors"],
                "pubDate": meta["pubDate"],
                "shortSummary": short_summary.strip(),
                "titleDegraded": False,
            }
        )
        if len(complete_articles) >= Config.PAGE_SIZE:
            break

    return {
        "totalCount": total_count,
        "page": page,
        "pageSize": Config.PAGE_SIZE,
        "totalPages": total_pages,
        "articles": complete_articles[: Config.PAGE_SIZE],
    }