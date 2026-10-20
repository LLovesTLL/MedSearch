import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

client = app.test_client()

r1 = client.get("/api/health")
print("health:", r1.status_code, r1.get_json())

r2 = client.post("/api/keywords/generate", json={"description": "lung"})
print("keywords_invalid:", r2.status_code, r2.get_json())

r3 = client.post("/api/literature/search", json={"keywords": [], "page": 1})
print("literature_empty:", r3.status_code, r3.get_json())

r4 = client.post("/api/summary/generate", json={"articles": []})
print("summary_empty:", r4.status_code, r4.get_json())