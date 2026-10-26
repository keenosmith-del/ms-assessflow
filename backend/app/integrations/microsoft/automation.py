"""Approval delivery boundary. No invocation happens at import or startup."""

import hashlib
import hmac
import json
import time
import httpx
from app.core.config import settings
from app.integrations.microsoft.providers import ProviderError


class AutomationProvider:
    def start(self, request_id: str, approver_id: str) -> str:
        cfg = settings()
        if not cfg.workflow_start_url.startswith("https://") or not cfg.workflow_callback_secret:
            raise ProviderError("HTTPS workflow URL and callback secret are required")
        raw = json.dumps(
            {"request_id": request_id, "approver_id": approver_id, "idempotency_key": request_id},
            sort_keys=True,
        ).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(
            cfg.workflow_callback_secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256
        ).hexdigest()
        try:
            with httpx.Client(timeout=15, follow_redirects=False) as client:
                response = client.post(
                    cfg.workflow_start_url,
                    content=raw,
                    headers={
                        "Content-Type": "application/json",
                        "X-Workflow-Timestamp": timestamp,
                        "X-Workflow-Signature": signature,
                        "Idempotency-Key": request_id,
                    },
                )
            response.raise_for_status()
            return str(response.json()["execution_id"])[:100]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderError(
                "Workflow start failed; remote must deduplicate by request ID"
            ) from exc
