import pytest

from services.deepseek_service import DeepSeekError
from services.search_orchestrator import SearchOrchestrationError


VALID_KEYWORDS = {"keywords": ["肺腺癌", "EGFR突变", "预后"]}


def test_keywords_generate_success(client, monkeypatch):
    import routes.keyword_routes as kr

    monkeypatch.setattr(kr, "chat_json", lambda *a, **kw: VALID_KEYWORDS)
    resp = client.post(
        "/api/keywords/generate", json={"description": "肺腺癌的EGFR突变与预后相关性研究"}
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == 0
    assert body["data"]["keywords"] == ["肺腺癌", "EGFR突变", "预后"]


def test_keywords_generate_invalid_short(client, monkeypatch):
    resp = client.post("/api/keywords/generate", json={"description": "肺腺癌"})
    body = resp.get_json()
    assert body["code"] == 1001
    assert body["message"] == "请输入 10-300 字符的疾病描述"


def test_keywords_generate_invalid_long(client, monkeypatch):
    resp = client.post("/api/keywords/generate", json={"description": "肺" * 301})
    body = resp.get_json()
    assert body["code"] == 1001


def test_keywords_generate_ai_failure(client, monkeypatch):
    import routes.keyword_routes as kr

    def raise_err(*a, **kw):
        raise DeepSeekError("DeepSeek 调用失败")

    monkeypatch.setattr(kr, "chat_json", raise_err)
    resp = client.post(
        "/api/keywords/generate", json={"description": "肺腺癌的EGFR突变与预后相关性研究"}
    )
    body = resp.get_json()
    assert body["code"] == 2001
    assert body["message"] == "关键词生成失败，请稍后重试"


def test_keywords_generate_bad_format(client, monkeypatch):
    import routes.keyword_routes as kr

    monkeypatch.setattr(
        kr, "chat_json", lambda *a, **kw: {"keywords": ["肺腺癌", "EGFR突变"]}
    )
    resp = client.post(
        "/api/keywords/generate", json={"description": "肺腺癌的EGFR突变与预后相关性研究"}
    )
    body = resp.get_json()
    assert body["code"] == 2001


def test_literature_search_success(client, monkeypatch):
    import routes.literature_routes as lr

    data = {
        "totalCount": 128,
        "page": 1,
        "pageSize": 9,
        "totalPages": 15,
        "articles": [
            {
                "pmid": "12345678",
                "titleZh": "肺腺癌EGFR突变研究",
                "titleEn": "EGFR mutation in lung adenocarcinoma",
                "authors": ["Zhang S", "Li W", "Wang H", "Chen L"],
                "pubDate": "2024-Jan",
                "shortSummary": "该研究探讨EGFR突变与肺腺癌预后的关系。",
                "titleDegraded": False,
            }
        ]
        * 1,
    }
    monkeypatch.setattr(lr, "search_literature", lambda keywords, page: data)
    resp = client.post(
        "/api/literature/search", json={"keywords": ["肺腺癌", "EGFR突变"], "page": 1}
    )
    body = resp.get_json()
    assert body["code"] == 0
    assert body["data"]["totalCount"] == 128
    assert body["data"]["pageSize"] == 9


def test_literature_search_empty_keywords(client):
    resp = client.post("/api/literature/search", json={"keywords": [], "page": 1})
    body = resp.get_json()
    assert body["code"] == 1002
    assert body["message"] == "请先生成或添加关键词"


def test_literature_search_too_many_keywords(client):
    resp = client.post(
        "/api/literature/search",
        json={"keywords": ["a", "b", "c", "d", "e", "f"], "page": 1},
    )
    body = resp.get_json()
    assert body["code"] == 1002


def test_literature_search_duplicate_keywords(client):
    resp = client.post(
        "/api/literature/search",
        json={"keywords": ["肺腺癌", "肺腺癌"], "page": 1},
    )
    body = resp.get_json()
    assert body["code"] == 1002


def test_literature_search_failure(client, monkeypatch):
    import routes.literature_routes as lr

    def raise_err(keywords, page):
        raise SearchOrchestrationError("PubMed 检索失败")

    monkeypatch.setattr(lr, "search_literature", raise_err)
    resp = client.post(
        "/api/literature/search", json={"keywords": ["肺腺癌"], "page": 1}
    )
    body = resp.get_json()
    assert body["code"] == 2002
    assert body["message"] == "检索失败，请稍后重试"



def test_summary_generate_success(client, monkeypatch):
    import routes.summary_routes as sr

    def fake_generate_single(meta):
        return {
            "pmid": meta["pmid"],
            "keyFindings": "关键发现内容",
            "researchTrends": "研究趋势内容",
            "clinicalSignificance": "临床意义内容",
            "status": "success",
        }

    monkeypatch.setattr(sr, "_generate_single", fake_generate_single)
    resp = client.post(
        "/api/summary/generate",
        json={
            "articles": [
                {"pmid": "111", "titleEn": "Study A", "authors": ["A"], "pubDate": "2024"},
                {"pmid": "222", "titleEn": "Study B", "authors": ["B"], "pubDate": "2024"},
            ]
        },
    )
    body = resp.get_json()
    assert body["code"] == 0
    assert len(body["data"]["summaries"]) == 2
    assert body["data"]["summaries"][0]["status"] == "success"


def test_summary_generate_empty(client):
    resp = client.post("/api/summary/generate", json={"articles": []})
    body = resp.get_json()
    assert body["code"] == 1003
    assert body["message"] == "请先勾选文献"


def test_summary_generate_partial_failure(client, monkeypatch):
    import routes.summary_routes as sr

    def fake_generate_single(meta):
        if meta["pmid"] == "111":
            return {
                "pmid": "111",
                "keyFindings": "关键发现",
                "researchTrends": "研究趋势",
                "clinicalSignificance": "临床意义",
                "status": "success",
            }
        return {"pmid": "222", "keyFindings": "", "researchTrends": "", "clinicalSignificance": "", "status": "error"}

    monkeypatch.setattr(sr, "_generate_single", fake_generate_single)
    resp = client.post(
        "/api/summary/generate",
        json={
            "articles": [
                {"pmid": "111", "titleEn": "Study A", "authors": [], "pubDate": "2024"},
                {"pmid": "222", "titleEn": "Study B", "authors": [], "pubDate": "2024"},
            ]
        },
    )
    body = resp.get_json()
    assert body["code"] == 0
    summaries = body["data"]["summaries"]
    by_pmid = {s["pmid"]: s for s in summaries}
    assert by_pmid["111"]["status"] == "success"
    assert by_pmid["222"]["status"] == "error"


def test_summary_generate_all_failure(client, monkeypatch):
    import routes.summary_routes as sr

    def fake_generate_single(meta):
        return {
            "pmid": meta["pmid"],
            "keyFindings": "",
            "researchTrends": "",
            "clinicalSignificance": "",
            "status": "error",
        }

    monkeypatch.setattr(sr, "_generate_single", fake_generate_single)
    resp = client.post(
        "/api/summary/generate",
        json={
            "articles": [
                {"pmid": "111", "titleEn": "Study A", "authors": [], "pubDate": "2024"}
            ]
        },
    )
    body = resp.get_json()
    assert body["code"] == 2003