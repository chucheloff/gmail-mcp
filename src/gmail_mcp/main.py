"""gmail-mcp — minimal MCP server that delivers email for an LLM agent.

Despite the name, the server supports multiple backends:

- ``smtp``   — Gmail SMTP via App Password. Fails on hosts that block egress 25/465/587 (most cloud providers).
- ``resend`` — Resend HTTP API (port 443). Recommended for cloud deployments.

Backend selection: ``MAILER_BACKEND`` env var (``smtp`` | ``resend``). When
unset, Resend wins if ``RESEND_API_KEY`` is present; otherwise SMTP is used.

Per-backend env vars are documented in the README and ``.env.example``.

The MCP server itself binds to ``PORT`` (default 8090) on path ``MCP_PATH``
(default ``/mcp``) using FastMCP streamable HTTP transport.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from .backends import load_backend


_backend = load_backend()
DEFAULT_TO = os.environ.get("MAIL_DEFAULT_TO") or os.environ.get("GMAIL_DEFAULT_TO") or os.environ.get("GMAIL_USER", "")

mcp = FastMCP("gmail-mcp")


@mcp.tool()
def send_email(
    subject: str,
    body_markdown: str,
    to: str | None = None,
    body_html: str | None = None,
) -> dict:
    """Send an email via the configured backend.

    Parameters
    ----------
    subject:
        Email subject line.
    body_markdown:
        Plain-text / markdown body (always attached as text/plain).
    to:
        Recipient address. Defaults to ``MAIL_DEFAULT_TO`` (or legacy
        ``GMAIL_DEFAULT_TO`` / ``GMAIL_USER``).
    body_html:
        Optional ``text/html`` alternative.
    """
    recipient = to or DEFAULT_TO
    if not recipient:
        raise RuntimeError(
            "no recipient: pass `to` or set MAIL_DEFAULT_TO / GMAIL_DEFAULT_TO env"
        )
    return _backend.send(
        to=recipient,
        subject=subject,
        body_text=body_markdown,
        body_html=body_html,
    )


@mcp.tool()
def whoami() -> dict:
    """Return the configured sender identity (no secrets)."""
    return {
        "backend": _backend.__class__.__name__,
        "sender": _backend.sender_label,
        "default_to": DEFAULT_TO or None,
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
