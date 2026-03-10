import requests
import json
import time

API_URL = "http://localhost:8000/api"

def test_automation(endpoint_type):
    url = f"{API_URL}/test-automation"
    print(f"Testing automation: {endpoint_type}")
    try:
        r = requests.post(url, json={"type": endpoint_type}, timeout=10)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_chat(message):
    url = f"{API_URL}/chat"
    print(f"\nTesting chat: '{message}'")
    try:
        r = requests.post(url, json={"session_id": "test_session_123", "message": message}, timeout=120)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Waiting a bit for the server to reload...")
    time.sleep(2)
    
    print("\n--- STEP 6: TEST AUTOMATION API ---")
    test_automation("doctor_booking")
    test_automation("emergency")
    test_automation("medication_reminder")
    
    print("\n--- STEP 7: FULL PIPELINE TEST ---")
    test_chat("I need to book a doctor")
    test_chat("I have severe chest pain")
    test_chat("Remind me to take paracetamol at 8pm")
