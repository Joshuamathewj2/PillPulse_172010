import requests
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:8b"

def generate(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return "Sorry, I am currently unable to process your request."

async def generate_async(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
    except Exception as e:
        print(f"Error calling Ollama (async): {e}")
        return "Sorry, I am currently unable to process your request."

