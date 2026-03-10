import requests
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

results = {}

def test_webhook(endpoint):
    url = f"http://localhost:5678/webhook/{endpoint}"
    try:
        r = requests.post(url, json={"test": "data"}, timeout=5)
        results[endpoint] = {"status": r.status_code, "text": r.text}
    except Exception as e:
        results[endpoint] = {"error": str(e)}

test_webhook("book-doctor")
test_webhook("emergency-alert")
test_webhook("medication-reminder")

with open("webhook_results.json", "w") as f:
    json.dump(results, f, indent=2)
