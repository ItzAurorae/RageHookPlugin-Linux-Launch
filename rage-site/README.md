# RAGE Plugin Hook Linux Guide + OpenAI AI Support

This project serves the static guide and a small Flask API from the same Render web service. The browser never receives the OpenAI API key.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
python app.py
```

Open `http://127.0.0.1:8000` for the setup guide. AI Support is on its own page at `http://127.0.0.1:8000/ai-support.html`.

## Deploy to Render

1. Put this entire folder in a GitHub repository. Keep `.env` out of Git; `.gitignore` already excludes it.
2. In Render, create a **New + → Blueprint** service and connect the repository. Render reads `render.yaml`.
3. Open the service's **Environment** page and add `OPENAI_API_KEY` with your OpenAI API key as the value. Keep it secret; do not put it in the HTML, JavaScript, GitHub, or a public build variable.
4. Deploy/redeploy. Open the Render service URL. `/api/health` should report `assistant_configured: true` (it does not reveal the key).

The OpenAI API is usage-billed separately from a ChatGPT subscription. Set a project budget/usage alert in the OpenAI Platform and monitor usage.

## Configuration

- `OPENAI_API_KEY`: required, server-side secret.
- `OPENAI_MODEL`: optional; defaults to `gpt-6-luna`. Change it to a model available to your API project if needed.
- `RATELIMIT_STORAGE_URI`: optional; defaults to in-memory rate limiting. For multiple instances, configure a shared Redis-compatible store.

## Security notes

- The API key is read only by `app.py` from the server environment.
- The browser sends chat messages to the same-origin `/api/chat` endpoint; it does not call OpenAI directly.
- The backend limits each IP to 8 chat requests per minute, limits request size/history, and asks the Responses API not to store the response (`store=False`).
- This is a small public support endpoint, not a full abuse-prevention system. Before sharing it widely, add stronger bot protection (such as a CAPTCHA/Turnstile challenge), configure persistent rate limiting, and monitor API usage.
- Chat text is sent to OpenAI to generate replies. Tell visitors not to submit secrets or sensitive personal information.


## Protontricks installation choices

The guide now documents two alternatives:
- **Non-Sudo Install (recommended):** installs Protontricks in a Python virtual environment inside the GTA V folder.
- **Sudo Install (system-wide):** on Arch Linux / EndeavourOS, installs the distribution package with `sudo pacman -Syu protontricks`.

Choose one method and use the matching .NET and launch commands shown in the guide.
