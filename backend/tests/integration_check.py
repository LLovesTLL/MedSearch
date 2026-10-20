import os
import sys

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import requests

results = []
for name, url in [
    ("vite-proxy-health", "http://localhost:5173/api/health"),
    ("flask-direct-health", "http://localhost:5000/api/health"),
    ("vite-proxy-keywords-invalid", "http://localhost:5173/api/keywords/generate"),
]:
    try:
        if "keywords" in url:
            resp = requests.post(url, json={"description": "lung"}, timeout=5)
        else:
            resp = requests.get(url, timeout=5)
        results.append(f"{name}: HTTP {resp.status_code} body={resp.text[:120]}")
    except Exception as e:
        results.append(f"{name}: FAILED - {type(e).__name__}: {e}")

print("\n".join(results))