import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.pubmed_service import _base_params

print("DEEPSEEK_API_KEY:", f"{Config.DEEPSEEK_API_KEY[:8]}...{Config.DEEPSEEK_API_KEY[-4:]}" if Config.DEEPSEEK_API_KEY else "(未设置)")
print("DEEPSEEK_MODEL:", Config.DEEPSEEK_MODEL)
print("PUBMED_API_KEY:", f"{Config.PUBMED_API_KEY[:6]}...{Config.PUBMED_API_KEY[-4:]}" if Config.PUBMED_API_KEY else "(未设置，走无Key限频)")
print("PUBMED_RATE_LIMIT:", Config.PUBMED_RATE_LIMIT)
params = _base_params()
print("api_key in params:", "api_key" in params)