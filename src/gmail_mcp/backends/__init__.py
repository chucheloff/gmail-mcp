"""Pluggable mail backends."""

from __future__ import annotations

import os
from typing import Protocol


class Backend(Protocol):
    """A backend knows how to deliver one email."""

    sender_label: str

    def send(
        self,
        *,
        to: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> dict: ...


def load_backend() -> Backend:
    """Pick a backend from env.

    ``MAILER_BACKEND`` selects explicitly (``smtp`` | ``resend``). When unset,
    Resend wins if ``RESEND_API_KEY`` is present, otherwise SMTP.
    """
    explicit = os.environ.get("MAILER_BACKEND", "").strip().lower()
    if explicit == "resend":
        from .resend_api import ResendBackend

        return ResendBackend()
    if explicit == "smtp":
        from .smtp import SMTPBackend

        return SMTPBackend()
    if os.environ.get("RESEND_API_KEY"):
        from .resend_api import ResendBackend

        return ResendBackend()
    from .smtp import SMTPBackend

    return SMTPBackend()
