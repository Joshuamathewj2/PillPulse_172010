import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def test_db():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        print("[OK] PostgreSQL Database")
        conn.close()
    except Exception as e:
        print(f"[FAIL] PostgreSQL Database: {e}")

def test_ollama():
    try:
        r = requests.get("http://localhost:11434/", timeout=5)
        if r.status_code == 200:
            print("[OK] Ollama API")
        else:
            print(f"[FAIL] Ollama API: {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Ollama API: {e}")

def test_n8n():
    try:
        r = requests.get("http://localhost:5678/", timeout=5)
        print("[OK] n8n (is reachable)")
    except Exception as e:
        print(f"[FAIL] n8n (unreachable): {e}")

def test_webhook(endpoint):
    url = f"http://localhost:5678/webhook/{endpoint}"
    try:
        r = requests.post(url, json={"test": "data"}, timeout=5)
        if r.status_code == 200:
            print(f"[OK] Webhook {endpoint}")
        else:
            print(f"[FAIL] Webhook {endpoint}: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[FAIL] Webhook {endpoint}: {e}")

def test_fastapi():
    try:
        r = requests.get("http://localhost:8000/", timeout=5)
        if r.status_code == 200:
            print("[OK] FastAPI backend")
        else:
            print(f"[FAIL] FastAPI backend: {r.status_code}")
    except Exception as e:
        print(f"[FAIL] FastAPI backend: {e}")

if __name__ == "__main__":
    print("--- DIAGNOSTICS ---")
    test_db()
    test_ollama()
    test_n8n()
    test_fastapi()
    print("\n--- WEBHOOKS ---")
    test_webhook("book-doctor")
    test_webhook("emergency-alert")
    test_webhook("medication-reminder")
