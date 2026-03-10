import requests
import json

results = {}

def test_webhook(endpoint):
    url = f"http://localhost:5678/webhook-test/{endpoint}"
    try:
        r = requests.post(url, json={"test": "data"}, timeout=5)
        results[endpoint] = {"status": r.status_code, "text": r.text}
    except Exception as e:
        results[endpoint] = {"error": str(e)}

test_webhook("book-doctor")
test_webhook("emergency-alert")
test_webhook("medication-reminder")

with open("webhook_test_results.json", "w") as f:
    json.dump(results, f, indent=2)
