"""Firebase Cloud Messaging via the HTTP v1 API.

The legacy ``fcm/send`` + server-key API the old Flask backend used was shut
down by Google in 2024. v1 needs a service account: set
FIREBASE_SERVICE_ACCOUNT to the JSON (or a path to the JSON file).
"""
import json
import logging
import os

import httpx

log = logging.getLogger(__name__)
_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_credentials = None


def _load_credentials():
    global _credentials
    if _credentials is not None:
        return _credentials
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if not raw:
        return None
    from google.oauth2 import service_account

    info = json.loads(raw) if raw.startswith("{") else json.load(open(raw, encoding="utf-8"))
    _credentials = service_account.Credentials.from_service_account_info(info, scopes=[_SCOPE])
    return _credentials


def is_configured() -> bool:
    return bool(os.getenv("FIREBASE_SERVICE_ACCOUNT"))


def send(token: str, title: str, body: str, link: str | None = None) -> dict:
    if not token or token in ("dummy-token", "browser-only"):
        return {"success": False, "reason": "no device token"}
    try:
        creds = _load_credentials()
        if creds is None:
            return {"success": False, "reason": "FCM not configured"}
        from google.auth.transport.requests import Request

        if not creds.valid:
            creds.refresh(Request())
        message = {
            "token": token,
            "notification": {"title": title, "body": body},
            "webpush": {"notification": {"requireInteraction": True, "icon": "/logo.png"}},
        }
        if link:
            message["webpush"]["fcm_options"] = {"link": link}
        r = httpx.post(
            f"https://fcm.googleapis.com/v1/projects/{creds.project_id}/messages:send",
            headers={"Authorization": f"Bearer {creds.token}"},
            json={"message": message},
            timeout=10,
        )
        if r.status_code >= 400:
            log.warning("FCM send failed %s: %s", r.status_code, r.text[:300])
            return {"success": False, "status": r.status_code}
        return {"success": True}
    except Exception as e:  # never let a push failure break the API call
        log.warning("FCM error: %s", e)
        return {"success": False, "error": str(e)}
