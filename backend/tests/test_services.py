import pytest

from services import pubmed_service
from services.deepseek_service import _parse_json_content
from services.search_orchestrator import _build_search_term


# ============ deepseek_service JSON 解析容错 ============

def test_parse_json_content_plain():
    data = _parse_json_content('{"keywords": ["a", "b", "c"]}')
    assert data == {"keywords": ["a", "b", "c"]}


def test_parse_json_content_fenced():
    content = '```json\n{"keywords": ["a", "b", "c"]}\n```'
    data = _parse_json_content(content)
    assert data == {"keywords": ["a", "b", "c"]}


def test_parse_json_content_fenced_no_lang():
    content = '```\n{"keywords": ["a"]}\n```'
    data = _parse_json_content(content)
    assert data == {"keywords": ["a"]}


def test_parse_json_content_empty():
    with pytest.raises(ValueError):
        _parse_json_content("")


def test_parse_json_content_invalid():
    with pytest.raises(ValueError):
        _parse_json_content("not a json")


def test_parse_json_content_not_dict():
    with pytest.raises(ValueError):
        _parse_json_content('["array"]')


# ============ deepseek_service 重试逻辑 ============

def test_chat_json_retry_then_success(monkeypatch):
    import services.deepseek_service as ds

    calls = []

    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": '{"keywords": ["a", "b", "c"]}'}}]}

    def fake_post_first_fail(*a, **kw):
        calls.append(1)

        class BadResp:
            status_code = 200

            def json(self):
                return {"choices": [{"message": {"content": "not json"}}]}

        if len(calls) == 1:
            return BadResp()
        return FakeResp()

    monkeypatch.setattr(ds.requests, "post", fake_post_first_fail)
    data = ds.chat_json([{"role": "user", "content": "x"}], 5, "test-op")
    assert data == {"keywords": ["a", "b", "c"]}
    assert len(calls) == 2


# ============ pubmed_service API Key 附加 ============

def test_base_params_with_api_key(monkeypatch):
    import services.pubmed_service as ps

    monkeypatch.setattr(ps.Config, "PUBMED_API_KEY", "test-key-123", raising=False)
    params = ps._base_params()
    assert params["api_key"] == "test-key-123"
    assert params["tool"] == "MedSearch"
    assert "email" in params


def test_base_params_without_api_key(monkeypatch):
    import services.pubmed_service as ps

    monkeypatch.setattr(ps.Config, "PUBMED_API_KEY", "", raising=False)
    params = ps._base_params()
    assert "api_key" not in params
    assert params["tool"] == "MedSearch"
    assert "email" in params


def test_chat_json_timeout_failure(monkeypatch):
    import services.deepseek_service as ds

    def fake_timeout(*a, **kw):
        raise ds.requests.exceptions.Timeout()

    monkeypatch.setattr(ds.requests, "post", fake_timeout)
    with pytest.raises(ds.DeepSeekError):
        ds.chat_json([{"role": "user", "content": "x"}], 1, "test-op")


# ============ pubmed_service 参数构造与 XML 解析 ============

def test_esearch_params(monkeypatch):
    import services.pubmed_service as ps

    captured = {}

    class FakeResp:
        status_code = 200

        def json(self):
            return {"esearchresult": {"count": "42", "idlist": ["111", "222"]}}

    def fake_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        return FakeResp()

    monkeypatch.setattr(ps.requests, "get", fake_get)
    count, ids = ps.esearch("lung cancer AND EGFR", 9, 15)

    assert count == 42
    assert ids == ["111", "222"]
    assert captured["params"]["term"] == "lung cancer AND EGFR"
    assert captured["params"]["sort"] == "relevance"
    assert captured["params"]["retstart"] == 9
    assert captured["params"]["retmax"] == 15
    assert captured["params"]["tool"] == "MedSearch"
    assert "email" in captured["params"]


EFETCH_XML = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <JournalIssue><PubDate><Year>2024</Year><Month>Jan</Month><Day>15</Day></PubDate></JournalIssue>
        </Journal>
        <ArticleTitle>EGFR mutation in lung adenocarcinoma</ArticleTitle>
        <AuthorList>
          <Author><LastName>Zhang</LastName><ForeName>San</ForeName></Author>
          <Author><LastName>Li</LastName><ForeName>Si</ForeName></Author>
          <Author><LastName>Wang</LastName><ForeName>Wu</ForeName></Author>
          <Author><LastName>Chen</LastName><ForeName>Liu</ForeName></Author>
        </AuthorList>
        <Abstract>
          <AbstractText>Background: This study explores EGFR mutation.</AbstractText>
          <AbstractText>Methods: Cohort analysis.</AbstractText>
        </Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


def test_efetch_xml_parse(monkeypatch):
    import services.pubmed_service as ps

    class FakeResp:
        status_code = 200
        content = EFETCH_XML

    monkeypatch.setattr(ps.requests, "get", lambda *a, **kw: FakeResp())
    articles = ps.efetch(["12345678"])

    assert len(articles) == 1
    a = articles[0]
    assert a["pmid"] == "12345678"
    assert a["titleEn"] == "EGFR mutation in lung adenocarcinoma"
    assert a["authors"] == ["Zhang San", "Li Si", "Wang Wu", "Chen Liu"]
    assert a["pubDate"] == "2024-Jan-15"
    assert "EGFR mutation" in a["abstractEn"]


# ============ search_orchestrator 过滤与分页 ============

def _mock_orchestrator(monkeypatch, processed_map):
    import services.search_orchestrator as so

    monkeypatch.setattr(
        so,
        "_translate_keywords",
        lambda keywords: ["lung adenocarcinoma", "EGFR"],
    )
    monkeypatch.setattr(
        so.pubmed_service,
        "esearch",
        lambda term, retstart, retmax: (18, [f"PM{i}" for i in range(1, 16)]),
    )
    meta_articles = [
        {
            "pmid": f"PM{i}",
            "titleEn": f"Title {i}",
            "authors": ["A"],
            "pubDate": "2024",
            "abstractEn": "abstract text",
        }
        for i in range(1, 16)
    ]
    monkeypatch.setattr(so.pubmed_service, "efetch", lambda pmids: meta_articles)

    def fake_process(articles):
        return [processed_map.get(a["pmid"], {}) for a in articles]

    monkeypatch.setattr(so, "_process_articles", fake_process)


def test_orchestrator_completeness_filter_substitute(monkeypatch):
    """短摘要失败剔除并由候补顶替，最终返回恰好 9 篇。"""
    # PM1 短摘要缺失（剔除），PM2-PM11 完整 → 取前 9 篇：PM2..PM10
    processed_map = {f"PM{i}": {"pmid": f"PM{i}", "titleZh": f"标题{i}", "shortSummary": f"摘要{i}"} for i in range(2, 12)}
    _mock_orchestrator(monkeypatch, processed_map)

    from services.search_orchestrator import search_literature

    data = search_literature(["肺腺癌"], 1)
    assert data["totalCount"] == 18
    assert data["pageSize"] == 9
    assert len(data["articles"]) == 9
    assert data["articles"][0]["pmid"] == "PM2"


def test_orchestrator_title_degrade(monkeypatch):
    """标题翻译失败仅降级英文标题，不剔除该篇。"""
    processed_map = {}
    for i in range(1, 11):
        if i == 3:
            processed_map[f"PM{i}"] = {"pmid": f"PM{i}", "titleZh": "", "shortSummary": f"摘要{i}"}
        else:
            processed_map[f"PM{i}"] = {"pmid": f"PM{i}", "titleZh": f"标题{i}", "shortSummary": f"摘要{i}"}
    _mock_orchestrator(monkeypatch, processed_map)

    from services.search_orchestrator import search_literature

    data = search_literature(["肺腺癌"], 1)
    assert len(data["articles"]) == 9
    degraded = [a for a in data["articles"] if a["titleDegraded"]]
    assert len(degraded) == 1
    assert degraded[0]["pmid"] == "PM3"
    assert degraded[0]["titleZh"] == "Title 3"


def test_orchestrator_empty_result(monkeypatch):
    import services.search_orchestrator as so

    monkeypatch.setattr(so, "_translate_keywords", lambda keywords: ["lung cancer"])
    monkeypatch.setattr(so.pubmed_service, "esearch", lambda term, retstart, retmax: (0, []))

    from services.search_orchestrator import search_literature

    data = search_literature(["罕见病"], 1)
    assert data["totalCount"] == 0
    assert data["articles"] == []
    assert data["totalPages"] == 0


def test_build_search_term():
    term = _build_search_term(["lung adenocarcinoma", "EGFR mutation"])
    assert term == "(lung adenocarcinoma) AND (EGFR mutation)"