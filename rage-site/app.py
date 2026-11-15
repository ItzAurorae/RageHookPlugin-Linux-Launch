import os
from flask import Flask, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI, OpenAIError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

# In-memory rate limiting is suitable for a small single-instance deployment.
# Use a persistent limiter backend if scaling to multiple instances.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SYSTEM_INSTRUCTIONS = """You are the Linux RAGE Plugin Hook Support Assistant for a practical guide focused on GTA V Legacy on Linux.

Help visitors troubleshoot GTA V Legacy, RAGE Plugin Hook, LSPDFR, Steam, Proton/GE-Proton, Protontricks, Wine prefixes, Windows-version settings, .NET Framework, and common Linux gaming issues.

Known example setup in the guide (not universal): EndeavourOS; Steam at /opt/games/Steam; GTA V Legacy Steam AppID 271590; game folder /opt/games/Steam/steamapps/common/Grand Theft Auto V; prefix /opt/games/Steam/steamapps/compatdata/271590/pfx; GE-Proton11-1 at /opt/games/Steam/compatibilitytools.d/GE-Proton11-1; Protontricks may be installed in the game's .tools/protontricks virtual environment.

Give clear, numbered, copy/paste-ready steps. Ask one focused question when essential information is missing. Explain what commands do. Prefer diagnostic/read-only checks before modifications. Avoid sudo because this guide's owner prefers commands that do not require administrator privileges. Never recommend deleting/rebuilding a prefix, reinstalling GTA, or removing mods as an initial step. Preserve user files and existing mods. Back up configuration before risky changes. Do not claim a command has been run or that you can inspect the visitor's computer.

Do not ask users to paste API keys, passwords, Rockstar credentials, tokens, or other secrets. Warn users to redact personal paths/usernames if they want privacy, and redact credentials from logs. Never request their OpenAI API key: it is configured privately by the site operator on the server.

You cannot execute commands, access the user's machine, inspect files unless they paste content, or guarantee that Windows-only mods work on Linux. Do not invent compatibility claims, version numbers, or download links. If a question depends on current OpenAI, Proton, RAGE Plugin Hook, Rockstar, or mod information, say it needs checking against the official current source rather than guessing. Be practical, concise, and technically precise."""


def get_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key, timeout=45.0, max_retries=1)


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "rage_plugin_hook_linux_guide.html")


@app.get("/ai-support.html")
def ai_support_page():
    return send_from_directory(BASE_DIR, "ai-support.html")


@app.get("/api/health")
@limiter.limit("30 per minute")
def health():
    return jsonify({"ok": True, "assistant_configured": bool(os.getenv("OPENAI_API_KEY", "").strip())})


@app.post("/api/chat")
@limiter.limit("8 per minute")
def chat():
    client = get_client()
    if client is None:
        return jsonify({"error": "AI Support is not configured yet. The site operator must add OPENAI_API_KEY to the server environment."}), 503

    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Send at least one message."}), 400
    if len(messages) > 12:
        return jsonify({"error": "This chat contains too much history. Start a new chat and try again."}), 400

    cleaned = []
    for item in messages:
        if not isinstance(item, dict):
            return jsonify({"error": "Invalid message format."}), 400
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            return jsonify({"error": "Messages must contain a user/assistant role and text content."}), 400
        content = content.strip()
        if not content or len(content) > 6000:
            return jsonify({"error": "Each message must contain 1–6000 characters."}), 400
        cleaned.append({"role": role, "content": content})

    if cleaned[-1]["role"] != "user":
        return jsonify({"error": "The latest message must be from the user."}), 400

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=cleaned,
            max_output_tokens=1000,
            store=False,
        )
        answer = (response.output_text or "").strip()
        if not answer:
            answer = "I couldn't produce a response. Please try asking in a different way."
        return jsonify({"reply": answer, "model": MODEL})
    except OpenAIError as exc:
        # Avoid returning provider internals or request details to public visitors.
        app.logger.warning("OpenAI API request failed: %s", type(exc).__name__)
        return jsonify({"error": "The AI service could not complete that request. Check the server's API configuration and usage limits, then try again."}), 502
    except Exception as exc:
        app.logger.exception("Unexpected AI Support error: %s", type(exc).__name__)
        return jsonify({"error": "The support service encountered an unexpected error. Please try again later."}), 500


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Your request is too large. Shorten the pasted log and try again."}), 413


@app.errorhandler(429)
def rate_limited(_error):
    return jsonify({"error": "Too many requests. Please wait a minute before trying again."}), 429


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
