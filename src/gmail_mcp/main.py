"""Gmail MCP server.

Exposes a minimal MCP HTTP service backed by Gmail SMTP and a Google App
Password. Designed for the JobSearcherBot pipeline: an LLM agent calls
``send_email`` to deliver job briefings to the operator's inbox.

Environment variables:

- ``GMAIL_USER``           — Gmail address used as sender (required).
- ``GMAIL_APP_PASSWORD``   — 16-character Google App Password (required).
- ``GMAIL_FROM_NAME``      — display name in the From header (default: ``JobSearcherBot``).
- ``GMAIL_DEFAULT_TO``     — fallback recipient when the tool is called without ``to`` (default: ``GMAIL_USER``).
- ``SMTP_HOST``            — SMTP server (default: ``smtp.gmail.com``).
- ``SMTP_PORT``            — SMTP port over implicit TLS (default: ``465``).
- ``PORT``                 — HTTP port the MCP server binds (default: ``8090``).
- ``MCP_PATH``             — HTTP path for the MCP endpoint (default: ``/mcp``).
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastmcp import FastMCP


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"environment variable {name} is required")
    return value


SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
GMAIL_USER = _require_env("GMAIL_USER")
GMAIL_APP_PASSWORD = _require_env("GMAIL_APP_PASSWORD")
DEFAULT_FROM_NAME = os.environ.get("GMAIL_FROM_NAME", "JobSearcherBot")
DEFAULT_TO = os.environ.get("GMAIL_DEFAULT_TO", GMAIL_USER)

mcp = FastMCP("gmail-mcp")


@mcp.tool()
def send_email(
    subject: str,
    body_markdown: str,
    to: str | None = None,
    body_html: str | None = None,
) -> dict:
    """Send an email via Gmail SMTP.

    Parameters
    ----------
    subject:
        Email subject line.
    body_markdown:
        Plain-text / markdown body. Always attached as ``text/plain``.
    to:
        Recipient address. Defaults to ``GMAIL_DEFAULT_TO`` (or ``GMAIL_USER``).
    body_html:
        Optional ``text/html`` alternative. Mail clients prefer this when present.
    """
    recipient = to or DEFAULT_TO
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{DEFAULT_FROM_NAME} <{GMAIL_USER}>"
    msg["To"] = recipient
    msg.attach(MIMEText(body_markdown, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as conn:
        conn.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        conn.sendmail(GMAIL_USER, [recipient], msg.as_string())
    return {"ok": True, "to": recipient, "subject": subject}


@mcp.tool()
def whoami() -> dict:
    """Return the configured sender identity (no secrets)."""
    return {
        "sender": GMAIL_USER,
        "from_name": DEFAULT_FROM_NAME,
        "default_to": DEFAULT_TO,
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
    }


def run() -> None:
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8090")),
        path=os.environ.get("MCP_PATH", "/mcp"),
    )


if __name__ == "__main__":
    run()
