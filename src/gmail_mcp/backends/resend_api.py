"""Resend backend — HTTPS-only, works on cloud hosts that block SMTP."""

from __future__ import annotations

import os

import httpx


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"environment variable {name} is required for the Resend backend")
    return value


class ResendBackend:
    """Send via the Resend API.

    For unverified-domain testing Resend allows ``onboarding@resend.dev`` as
    the sender, but messages are restricted to the account-owner's address. To
    send to arbitrary recipients, verify a domain at
    https://resend.com/domains and set ``RESEND_FROM`` to e.g.
    ``"YourBot <bot@yourdomain.tld>"``.
    """

    api_url = "https://api.resend.com/emails"

    def __init__(self) -> None:
        self.api_key = _require("RESEND_API_KEY")
        self.from_address = os.environ.get(
            "RESEND_FROM",
            "JobSearcherBot <onboarding@resend.dev>",
        )
        self.timeout = float(os.environ.get("RESEND_TIMEOUT_SECONDS", "15"))
        self.sender_label = self.from_address

    def send(
        self,
        *,
        to: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> dict:
        payload: dict = {
            "from": self.from_address,
            "to": [to],
            "subject": subject,
            "text": body_text,
        }
        if body_html:
            payload["html"] = body_html
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if r.status_code >= 400:
            raise RuntimeError(
                f"Resend API error {r.status_code}: {r.text[:500]}"
            )
        data = r.json()
        return {
            "backend": "resend",
            "ok": True,
            "to": to,
            "subject": subject,
            "provider_message_id": data.get("id"),
        }
