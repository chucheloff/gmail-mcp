# gmail-mcp

A minimal MCP server that lets an LLM agent send email. Despite the name, the
server supports two backends:

| Backend  | Transport | When to use                                                   |
| -------- | --------- | ------------------------------------------------------------- |
| `smtp`   | port 465  | Local dev, or hosts that allow outbound SMTP.                 |
| `resend` | port 443  | Cloud deployments. Most cloud providers block SMTP by default. |

Two MCP tools exposed over streamable HTTP at `/mcp`:

- `send_email(subject, body_markdown, to=None, body_html=None)`
- `whoami()` — returns active backend + sender identity (no secrets).

## Backend selection

`MAILER_BACKEND` env (`smtp` | `resend`). When unset, **Resend wins if
`RESEND_API_KEY` is present, otherwise SMTP.**

## Quick start — Resend (recommended for cloud)

1. Sign up at <https://resend.com> (no card on the free tier).
2. Get an API key from <https://resend.com/api-keys>.
3. Configure:

    ```sh
    cp .env.example .env
    # set: RESEND_API_KEY, MAIL_DEFAULT_TO
    # MAILER_BACKEND can stay empty — Resend will be auto-selected.
    ```

4. Start:

    ```sh
    docker compose up -d --build
    ```

> **Sandbox sender (`onboarding@resend.dev`) only delivers to the Resend
> account-owner's verified email.** To send to other recipients, verify a
> domain at <https://resend.com/domains> and set `RESEND_FROM` to e.g.
> `"YourBot <bot@yourdomain.tld>"`.

## Quick start — SMTP (local / unblocked hosts)

1. Enable 2-Step Verification on the Gmail account.
2. Generate an App Password at <https://myaccount.google.com/apppasswords>.
3. Configure:

    ```sh
    cp .env.example .env
    # set: GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_DEFAULT_TO
    # MAILER_BACKEND=smtp  (or leave empty — SMTP is the fallback)
    ```

4. `docker compose up -d --build`

> **Cloud-host caveat:** DigitalOcean, Linode, Hetzner, AWS EC2 (default), GCP,
> and Azure all block egress on ports 25/465/587 unless you request an unblock.
> If `send_email` returns "Network is unreachable", that's the issue —
> use the Resend backend.

## Wiring into an OpenClaw agent

```sh
openclaw mcp set gmail '{"url":"http://gmail-mcp:8090/mcp","transport":"streamable-http"}'
```

Then in any agent run:

> Use the `gmail__send_email` tool to send a test email with subject "ping".

## Environment

### Shared

| Var                | Required | Default | Notes                                       |
| ------------------ | -------- | ------- | ------------------------------------------- |
| `MAILER_BACKEND`   | no       | auto    | `smtp` or `resend`. Auto = `resend` if `RESEND_API_KEY` set. |
| `MAIL_DEFAULT_TO`  | no       | —       | Fallback recipient. Falls back to `GMAIL_DEFAULT_TO` then `GMAIL_USER`. |
| `PORT`             | no       | `8090`  | HTTP bind port.                             |
| `MCP_PATH`         | no       | `/mcp`  | HTTP path for the MCP endpoint.             |

### Resend backend

| Var                       | Required | Default                                  |
| ------------------------- | -------- | ---------------------------------------- |
| `RESEND_API_KEY`          | yes      | —                                        |
| `RESEND_FROM`             | no       | `JobSearcherBot <onboarding@resend.dev>` |
| `RESEND_TIMEOUT_SECONDS`  | no       | `15`                                     |

### SMTP backend

| Var                  | Required | Default          |
| -------------------- | -------- | ---------------- |
| `GMAIL_USER`         | yes      | —                |
| `GMAIL_APP_PASSWORD` | yes      | —                |
| `GMAIL_FROM_NAME`    | no       | `JobSearcherBot` |
| `SMTP_HOST`          | no       | `smtp.gmail.com` |
| `SMTP_PORT`          | no       | `465`            |

## Roadmap (open to PRs)

- attachments
- HTML templates with jinja2
- per-tool rate limiting
- additional backends: SendGrid, Mailgun, AWS SES, Postmark
- Gmail OAuth2 backend (for true `from: you@gmail.com` without SMTP)

## License

MIT.
