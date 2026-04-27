# gmail-mcp

A minimal MCP server that sends email through Gmail SMTP using a Google App
Password. Designed as the email leg of an LLM agent pipeline (e.g.
JobSearcherBot) where the agent needs to deliver structured briefings to its
operator's inbox.

Two tools:

- `send_email(subject, body_markdown, to=None, body_html=None)` — sends an
  email. `to` defaults to `GMAIL_DEFAULT_TO` (or the sender address).
- `whoami()` — returns the configured sender identity (no secrets).

Transport: streamable HTTP at `/mcp`, port `8090` by default.

## Why SMTP + App Password (not OAuth)

For "agent sends mail as me" the App Password path is one secret, no browser
flow, no refresh-token storage, and the scope is exactly "send mail" — the
agent can't read the inbox or change labels. If you need read access, swap to
a Gmail-API MCP server with OAuth instead.

## Quick start

1. Enable 2-Step Verification on the Gmail account.
2. Generate an App Password at <https://myaccount.google.com/apppasswords>.
3. Copy the env template and fill it in:

    ```sh
    cp .env.example .env
    # edit .env: GMAIL_USER, GMAIL_APP_PASSWORD
    ```

4. Start the service:

    ```sh
    docker compose up -d --build
    ```

5. Probe it:

    ```sh
    curl -s -X POST http://localhost:8090/mcp \
      -H 'Content-Type: application/json' \
      -H 'Accept: application/json, text/event-stream' \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}'
    ```

## Wiring into an OpenClaw agent

```sh
openclaw mcp set gmail '{"url":"http://gmail-mcp:8090/mcp","transport":"streamable-http"}'
```

Then in any agent run:

> Use the `gmail__send_email` tool to send a test email with subject "ping" and body "hello".

## Environment

| Var                  | Required | Default                | Notes                                    |
| -------------------- | -------- | ---------------------- | ---------------------------------------- |
| `GMAIL_USER`         | yes      | —                      | Sender Gmail address.                    |
| `GMAIL_APP_PASSWORD` | yes      | —                      | 16-char App Password. Spaces stripped.   |
| `GMAIL_FROM_NAME`    | no       | `JobSearcherBot`       | Display name in `From:` header.          |
| `GMAIL_DEFAULT_TO`   | no       | `GMAIL_USER`           | Fallback recipient if `to` is omitted.   |
| `SMTP_HOST`          | no       | `smtp.gmail.com`       |                                          |
| `SMTP_PORT`          | no       | `465`                  | Implicit TLS.                            |
| `PORT`               | no       | `8090`                 | HTTP bind port.                          |
| `MCP_PATH`           | no       | `/mcp`                 | HTTP path for the MCP endpoint.          |

## Development

```sh
pip install -e .
GMAIL_USER=... GMAIL_APP_PASSWORD=... python -m gmail_mcp.main
```

## Roadmap (open to PRs)

- attachments
- HTML templates with jinja2
- DKIM check / send-only health probe
- per-tool rate limiting (Gmail SMTP caps ~500 sends/day)
- multi-account support

## License

MIT.
