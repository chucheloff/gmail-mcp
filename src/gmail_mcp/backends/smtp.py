"""SMTP backend (Gmail by default)."""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"environment variable {name} is required for the SMTP backend")
    return value


class SMTPBackend:
    """Send via raw SMTP. Works for Gmail when the host can reach :465."""

    def __init__(self) -> None:
        self.host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.environ.get("SMTP_PORT", "465"))
        self.user = _require("GMAIL_USER")
        self.password = _require("GMAIL_APP_PASSWORD").replace(" ", "")
        self.from_name = os.environ.get("GMAIL_FROM_NAME", "JobSearcherBot")
        self.sender_label = f"{self.from_name} <{self.user}>"

    def send(
        self,
        *,
        to: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> dict:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_label
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.host, self.port, context=ctx) as conn:
            conn.login(self.user, self.password)
            conn.sendmail(self.user, [to], msg.as_string())
        return {"backend": "smtp", "ok": True, "to": to, "subject": subject}
