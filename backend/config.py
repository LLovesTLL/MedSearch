import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

    KEYWORD_TIMEOUT = 15
    SEARCH_TIMEOUT = 30
    SUMMARY_TIMEOUT = 60

    PAGE_SIZE = 9
    MAX_KEYWORDS = 5

    _pubmed_api_key = ""
    for _name in ("PUDMED_E-UTILITIES_API", "PUBMED_API_KEY"):
        _pubmed_api_key = os.environ.get(_name, "")
        if _pubmed_api_key:
            break
    PUBMED_API_KEY = _pubmed_api_key
    PUBMED_RATE_LIMIT = 10 if PUBMED_API_KEY else 3
    CANDIDATE_EXTRA = 6

    PUBMED_TOOL = "MedSearch"
    PUBMED_EMAIL = "medsearch@example.com"

    PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    KEYWORD_COUNT = 3
    SHORT_SUMMARY_MAX_CHARS = 100
    SUMMARY_DIMENSIONS = ["keyFindings", "researchTrends", "clinicalSignificance"]
    SUMMARY_CONCURRENCY = 2