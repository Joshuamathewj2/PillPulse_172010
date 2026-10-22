import os
import sys
import tempfile
from pathlib import Path

# Isolated database and no real AI providers, set before the app is imported.
_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
for key in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_URL", "FIREBASE_SERVICE_ACCOUNT", "N8N_BASE_URL"):
    os.environ.pop(key, None)
os.environ["PRESCRIPTION_ENGINES"] = "gemini,claude"  # keep a locally installed Tesseract out of tests
os.environ.setdefault("APP_TIMEZONE", "Asia/Kolkata")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app

    return TestClient(app)
