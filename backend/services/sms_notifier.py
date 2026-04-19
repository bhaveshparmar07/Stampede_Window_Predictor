"""
Authority SMS escalation — backup when dashboard audio is missed.

Uses a local Android SMS Gateway (HTTP JSON API), not Twilio.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Set, TypedDict

import requests

logger = logging.getLogger(__name__)

_sent_alert_ids: Set[int] = set()

DEFAULT_GATEWAY_URL = "http://192.168.1.53:8080/send-sms"
DEFAULT_TIMEOUT_SEC = 15.0
DEFAULT_AUTHORITY_SMS_NUMBERS = "+917698331412"


class SendSmsResult(TypedDict, total=False):
    success: bool
    status_code: Optional[int]
    response_text: Optional[str]
    error: Optional[str]


def _truthy_env(name: str) -> bool:
    val = os.environ.get(name, "").strip().lower()
    return val in ("1", "true", "yes", "on")


def _parse_recipients() -> List[str]:
    raw = os.environ.get("AUTHORITY_SMS_NUMBERS", DEFAULT_AUTHORITY_SMS_NUMBERS).strip()
    if raw.lower() in ("", "none", "off"):
        return []
    out: List[str] = []
    for part in raw.split(","):
        n = part.strip().replace(" ", "")
        if not n:
            continue
        if n.startswith("+"):
            out.append(n)
        elif n.isdigit() and len(n) == 10:
            out.append("+91" + n)
        else:
            out.append(n)
    return out


def _gateway_url() -> str:
    return os.environ.get("SMS_GATEWAY_URL", DEFAULT_GATEWAY_URL).strip()


def send_sms(phone: str, message: str) -> SendSmsResult:
    url = _gateway_url()
    if not url:
        return {"success": False, "error": "SMS_GATEWAY_URL is empty"}

    payload = {"phone": phone, "message": message or ""}
    try:
        resp = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT_SEC)
        if 200 <= resp.status_code < 300:
            return {"success": True, "status_code": resp.status_code}
        return {"success": False, "status_code": resp.status_code, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_message(alert: Dict[str, Any]) -> str:
    loc = alert.get("location", "?")
    p = alert.get("pressure_index", 0)
    cls = alert.get("classification", "")
    return f"[CRITICAL] Stampede Alert: {loc}. Pressure: {p:.1f}. Status: {cls}. Please check dashboard."


def notify_authority_sms_for_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "enabled": True, # Hardcoded True for Demo
        "sent": False,
        "recipient_count": 0,
        "error": None
    }

    # If environment explicitly says OFF, then respect it, otherwise default ON
    if os.environ.get("SMS_ESCALATION_ENABLED") == "0":
        result["enabled"] = False
        return result

    alert_id = alert.get("id")
    if alert_id in _sent_alert_ids:
        return {"sent": True, "deduped": True}

    recipients = _parse_recipients()
    result["recipient_count"] = len(recipients)
    message = _build_message(alert)

    if not recipients:
        result["error"] = "No recipients"
        return result

    for to in recipients:
        one = send_sms(to, message)
        if one.get("success"):
            result["sent"] = True

    if result["sent"]:
        _sent_alert_ids.add(int(alert_id))
    
    return result
