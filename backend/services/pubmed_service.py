import logging
import threading
import time
import xml.etree.ElementTree as ET

import requests

from config import Config
from utils.call_logger import Timer, log_call

logger = logging.getLogger("medsearch.pubmed")

_rate_lock = threading.Lock()
_last_call_ts = 0.0
_MIN_INTERVAL = 1.0 / Config.PUBMED_RATE_LIMIT

REQUEST_TIMEOUT = 15


class PubMedError(Exception):
    """PubMed 调用失败/超时/解析失败。"""


def _throttle() -> None:
    """串行化调用并保证频率 ≤ PUBMED_RATE_LIMIT 次/秒。"""
    global _last_call_ts
    with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()


def _base_params() -> dict:
    params = {"tool": Config.PUBMED_TOOL, "email": Config.PUBMED_EMAIL}
    if Config.PUBMED_API_KEY:
        params["api_key"] = Config.PUBMED_API_KEY
    return params


def esearch(term: str, retstart: int, retmax: int) -> tuple[int, list[str]]:
    """调用 esearch.fcgi，返回 (命中总数, PMID 列表)，按相关度排序。"""
    params = _base_params()
    params.update(
        {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "sort": "relevance",
            "retstart": retstart,
            "retmax": retmax,
        }
    )

    _throttle()
    with Timer() as timer:
        try:
            resp = requests.get(Config.PUBMED_ESEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout as e:
            log_call("pubmed", "esearch", f"retstart={retstart} retmax={retmax}", REQUEST_TIMEOUT * 1000, "failure(timeout)")
            raise PubMedError("PubMed esearch 请求超时") from e
        except requests.exceptions.RequestException as e:
            log_call("pubmed", "esearch", f"retstart={retstart} retmax={retmax}", timer.elapsed_ms, "failure(network)")
            raise PubMedError(f"PubMed esearch 网络异常: {e}") from e

    if resp.status_code != 200:
        log_call("pubmed", "esearch", f"retstart={retstart} retmax={retmax}", timer.elapsed_ms, f"failure({resp.status_code})")
        raise PubMedError(f"PubMed esearch HTTP {resp.status_code}")

    try:
        body = resp.json()
        result = body["esearchresult"]
        count = int(result["count"])
        id_list = list(result.get("idlist", []))
    except (ValueError, KeyError, TypeError) as e:
        log_call("pubmed", "esearch", f"retstart={retstart} retmax={retmax}", timer.elapsed_ms, "failure(parse)")
        raise PubMedError(f"PubMed esearch 响应解析失败: {e}") from e

    log_call("pubmed", "esearch", f"term_len={len(term)} count={count} retstart={retstart} retmax={retmax}", timer.elapsed_ms, "success")
    return count, id_list


def _extract_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def _parse_pub_date(article: ET.Element) -> str:
    journal = article.find("Journal/JournalIssue/PubDate")
    if journal is not None:
        year = _extract_text(journal.find("Year"))
        month = _extract_text(journal.find("Month"))
        day = _extract_text(journal.find("Day"))
        if year:
            date = year
            if month:
                date += f"-{month}"
                if day:
                    date += f"-{day}"
            return date
        medline_date = _extract_text(journal.find("MedlineDate"))
        if medline_date:
            return medline_date
    medline_date = _extract_text(article.find("ArticleDate/Year"))
    return medline_date


def _parse_authors(article: ET.Element) -> list[str]:
    author_list = article.find("AuthorList")
    if author_list is None:
        return []
    authors: list[str] = []
    for author in author_list.findall("Author"):
        collective = _extract_text(author.find("CollectiveName"))
        if collective:
            authors.append(collective)
            continue
        last = _extract_text(author.find("LastName"))
        first = _extract_text(author.find("ForeName"))
        if last:
            authors.append(f"{last} {first}".strip())
        elif first:
            authors.append(first)
    return authors


def _parse_abstract(article: ET.Element) -> str:
    abstract = article.find("Abstract")
    if abstract is None:
        return ""
    parts = [_extract_text(t) for t in abstract.findall("AbstractText")]
    return " ".join(p for p in parts if p)


def efetch(pmids: list[str]) -> list[dict]:
    """调用 efetch.fcgi，解析 XML 返回结构化文献元数据列表。"""
    params = _base_params()
    params.update(
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
    )

    _throttle()
    with Timer() as timer:
        try:
            resp = requests.get(Config.PUBMED_EFETCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout as e:
            log_call("pubmed", "efetch", f"pmids={len(pmids)}", REQUEST_TIMEOUT * 1000, "failure(timeout)")
            raise PubMedError("PubMed efetch 请求超时") from e
        except requests.exceptions.RequestException as e:
            log_call("pubmed", "efetch", f"pmids={len(pmids)}", timer.elapsed_ms, "failure(network)")
            raise PubMedError(f"PubMed efetch 网络异常: {e}") from e

    if resp.status_code != 200:
        log_call("pubmed", "efetch", f"pmids={len(pmids)}", timer.elapsed_ms, f"failure({resp.status_code})")
        raise PubMedError(f"PubMed efetch HTTP {resp.status_code}")

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        log_call("pubmed", "efetch", f"pmids={len(pmids)}", timer.elapsed_ms, "failure(parse)")
        raise PubMedError(f"PubMed efetch XML 解析失败: {e}") from e

    articles: list[dict] = []
    for pubmed_article in root.findall("PubmedArticle"):
        citation = pubmed_article.find("MedlineCitation")
        if citation is None:
            continue
        pmid = _extract_text(citation.find("PMID"))
        article = citation.find("Article")
        if not pmid or article is None:
            continue
        articles.append(
            {
                "pmid": pmid,
                "titleEn": _extract_text(article.find("ArticleTitle")),
                "authors": _parse_authors(article),
                "pubDate": _parse_pub_date(article),
                "abstractEn": _parse_abstract(article),
            }
        )

    log_call("pubmed", "efetch", f"pmids={len(pmids)} parsed={len(articles)}", timer.elapsed_ms, "success")
    return articles