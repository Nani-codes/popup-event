"""Gemini-styled Café Concierge — Google Sign-In + ADK agent API."""

from __future__ import annotations

import base64
import binascii
import json
import os
import secrets
import tempfile
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.genai import types
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / "cafe_concierge" / ".env")
load_dotenv(ROOT / ".env.local")


def _materialize_gcp_credentials_from_env() -> None:
    """Coolify-safe: base64 of the SA JSON (multiline JSON breaks Coolify .env).

    Set GOOGLE_APPLICATION_CREDENTIALS_B64 to:
      base64 -w0 purplegrid-vertexai.json   # Linux
      base64 -i purplegrid-vertexai.json | tr -d '\\n'  # macOS
    """
    b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_B64", "").strip()
    raw = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()

    if b64:
        # Strip whitespace / accidental wrapping quotes
        if (b64.startswith("'") and b64.endswith("'")) or (
            b64.startswith('"') and b64.endswith('"')
        ):
            b64 = b64[1:-1].strip()
        b64 = "".join(b64.split())
        try:
            raw = base64.b64decode(b64, validate=False).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS_B64 is not valid base64"
            ) from exc
    elif not raw:
        return

    if (raw.startswith("'") and raw.endswith("'")) or (
        raw.startswith('"') and raw.endswith('"')
    ):
        raw = raw[1:-1].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Decoded credentials are not valid JSON "
            "(use GOOGLE_APPLICATION_CREDENTIALS_B64 for Coolify)"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Service account credentials must be a JSON object")

    fd, path = tempfile.mkstemp(prefix="gcp-sa-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path


_materialize_gcp_credentials_from_env()

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "purplegrid")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from cafe_concierge import context, db  # noqa: E402
from cafe_concierge.agent import root_agent  # noqa: E402
from cafe_concierge import tools as cafe_tools  # noqa: E402
from cafe_concierge.swiggy_mcp import (  # noqa: E402
    PROVIDER as SWIGGY_PROVIDER,
    ensure_swiggy_access_token,
    swiggy_enabled,
    swiggy_status,
)
from cafe_concierge.swiggy_oauth import (  # noqa: E402
    DEFAULT_REDIRECT,
    authorize_url,
    exchange_code,
    make_pkce,
    token_expiry,
)

APP_NAME = "cafe_concierge"
WEB_DIR = ROOT / "web"
GOOGLE_CLIENT_ID = (
    os.getenv("GOOGLE_CLIENT_ID", "").strip()
    or os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
)
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip() or secrets.token_hex(32)
COOKIE_NAME = "cafe_session"
SWIGGY_PENDING_COOKIE = "swiggy_oauth"

db.init_db()

session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)
signer = URLSafeSerializer(SESSION_SECRET, salt="cafe-concierge-auth")

# Per Google user → ADK session id
_user_sessions: dict[str, str] = {}

app = FastAPI(title="Café Concierge")
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=10)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ProfileUpdate(BaseModel):
    interests: list[str] | None = None
    opt_in_match: bool | None = None


class VibeAnswerRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    choice: str = Field(min_length=1, max_length=80)


class NotifyMatchRequest(BaseModel):
    matched_sub: str = Field(min_length=1, max_length=128)
    note: str = Field(default="", max_length=280)


class MarkNotificationsRequest(BaseModel):
    ids: list[int] = Field(default_factory=list)


def _vibe_required(user: dict[str, Any] | None) -> bool:
    if not user:
        return True
    prefs = user.get("prefs") or {}
    return not bool(prefs.get("personality"))


def _safe_tool_events(events: list) -> list[dict]:
    out: list[dict] = []
    for event in events:
        content = getattr(event, "content", None)
        parts = getattr(content, "parts", None) or []
        safe_parts = []
        for part in parts:
            fr = getattr(part, "function_response", None)
            if fr is None:
                continue
            response = getattr(fr, "response", None)
            if hasattr(response, "model_dump"):
                try:
                    response = response.model_dump(exclude_none=True)
                except Exception:  # noqa: BLE001
                    response = str(response)
            safe_parts.append(
                {
                    "functionResponse": {
                        "name": getattr(fr, "name", None),
                        "response": response,
                    }
                }
            )
        if safe_parts:
            out.append({"author": getattr(event, "author", None), "content": {"parts": safe_parts}})
    return out


def _set_session_cookie(response: Response, sub: str) -> None:
    token = signer.dumps({"sub": sub})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def _user_from_cookie(cafe_session: str | None) -> dict[str, Any] | None:
    if not cafe_session:
        return None
    try:
        data = signer.loads(cafe_session)
    except BadSignature:
        return None
    sub = data.get("sub")
    if not sub:
        return None
    return db.get_user(sub)


def _require_user(cafe_session: str | None) -> dict[str, Any]:
    user = _user_from_cookie(cafe_session)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in with Google to continue.")
    return user


async def _ensure_adk_session(user_sub: str) -> str:
    existing = _user_sessions.get(user_sub)
    if existing:
        return existing
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_sub,
        session_id=f"u-{user_sub[-12:]}-{uuid.uuid4().hex[:6]}",
    )
    _user_sessions[user_sub] = session.id
    return session.id


@app.get("/api/config")
async def public_config() -> dict:
    return {
        "google_client_id": GOOGLE_CLIENT_ID,
        "auth_configured": bool(GOOGLE_CLIENT_ID),
        "venue": "Third Wave Coffee — Kondapura Hitech City",
        "swiggy_enabled": swiggy_enabled(),
    }


@app.post("/api/auth/google")
async def auth_google(body: GoogleAuthRequest, response: Response) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_CLIENT_ID is not set. Add it to .env.local or cafe_concierge/.env",
        )
    try:
        info = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {exc}") from exc

    if info.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    sub = info["sub"]
    user, created = db.upsert_user(
        sub=sub,
        email=info.get("email", ""),
        name=info.get("name"),
        picture=info.get("picture"),
    )
    _set_session_cookie(response, sub)
    public = _public_user(user)
    return {
        "status": "ok",
        "user": public,
        "is_new": created,
        "vibe_required": bool(public and public.get("vibe_required")),
    }


@app.get("/api/me")
async def me(cafe_session: str | None = Cookie(default=None)) -> dict:
    user = _user_from_cookie(cafe_session)
    if not user:
        return {"authenticated": False}
    orders = db.list_orders_for_user(user["sub"], limit=5)
    public = _public_user(user)
    return {
        "authenticated": True,
        "user": public,
        "recent_orders": orders,
        "swiggy": swiggy_status(user["sub"]),
        "vibe_required": bool(public and public.get("vibe_required")),
        "is_new": False,
    }


@app.post("/api/vibe/start")
async def api_vibe_start(cafe_session: str | None = Cookie(default=None)) -> dict:
    """Start/resume mandatory vibe quiz (no LLM — direct tool)."""
    user = _require_user(cafe_session)
    token = context.current_user_sub.set(user["sub"])
    try:
        return cafe_tools.start_vibe_check()
    finally:
        context.current_user_sub.reset(token)


@app.post("/api/vibe/answer")
async def api_vibe_answer(
    body: VibeAnswerRequest, cafe_session: str | None = Cookie(default=None)
) -> dict:
    user = _require_user(cafe_session)
    token = context.current_user_sub.set(user["sub"])
    try:
        return cafe_tools.answer_vibe_question(body.question_id, body.choice)
    finally:
        context.current_user_sub.reset(token)


@app.get("/api/matches")
async def api_matches(cafe_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cafe_session)
    if _vibe_required(user):
        raise HTTPException(status_code=403, detail="Finish vibe check first.")
    return {
        "status": "ok",
        "matches": db.list_vibe_matches(user["sub"]),
    }


@app.post("/api/matches/notify")
async def api_notify_match(
    body: NotifyMatchRequest, cafe_session: str | None = Cookie(default=None)
) -> dict:
    user = _require_user(cafe_session)
    if _vibe_required(user):
        raise HTTPException(status_code=403, detail="Finish vibe check first.")
    token = context.current_user_sub.set(user["sub"])
    try:
        result = cafe_tools.notify_match(body.matched_sub, body.note)
    finally:
        context.current_user_sub.reset(token)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Notify failed"))
    return result


@app.get("/api/notifications")
async def api_notifications(cafe_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cafe_session)
    return {
        "status": "ok",
        "notifications": db.list_unread_notifications(user["sub"]),
    }


@app.post("/api/notifications/read")
async def api_notifications_read(
    body: MarkNotificationsRequest, cafe_session: str | None = Cookie(default=None)
) -> dict:
    user = _require_user(cafe_session)
    db.mark_notifications_read(user["sub"], body.ids)
    return {"status": "ok"}


@app.get("/api/swiggy/status")
async def api_swiggy_status(cafe_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cafe_session)
    return swiggy_status(user["sub"])


@app.get("/api/swiggy/connect")
async def swiggy_connect(
    cafe_session: str | None = Cookie(default=None),
) -> RedirectResponse:
    user = _require_user(cafe_session)
    verifier, challenge = make_pkce()
    state = secrets.token_urlsafe(24)
    pending = signer.dumps(
        {
            "sub": user["sub"],
            "verifier": verifier,
            "state": state,
        }
    )
    redirect = RedirectResponse(authorize_url(state=state, code_challenge=challenge))
    redirect.set_cookie(
        key=SWIGGY_PENDING_COOKIE,
        value=pending,
        httponly=True,
        samesite="lax",
        max_age=600,
        path="/",
    )
    return redirect


@app.get("/auth/swiggy/callback")
async def swiggy_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    swiggy_oauth: str | None = Cookie(default=None, alias="swiggy_oauth"),
    cafe_session: str | None = Cookie(default=None),
) -> RedirectResponse:
    if error:
        return RedirectResponse(f"/?swiggy=error&reason={quote(error)}")
    if not code or not state:
        return RedirectResponse("/?swiggy=error&reason=missing_code")
    if not swiggy_oauth:
        return RedirectResponse("/?swiggy=error&reason=missing_pending")
    try:
        pending = signer.loads(swiggy_oauth)
    except BadSignature:
        return RedirectResponse("/?swiggy=error&reason=bad_pending")
    if pending.get("state") != state:
        return RedirectResponse("/?swiggy=error&reason=state_mismatch")

    user = _user_from_cookie(cafe_session)
    if not user or user["sub"] != pending.get("sub"):
        return RedirectResponse("/?swiggy=error&reason=session_mismatch")

    try:
        payload = await exchange_code(
            code=code,
            code_verifier=pending["verifier"],
            redirect_uri=DEFAULT_REDIRECT,
        )
    except Exception as exc:  # noqa: BLE001
        return RedirectResponse(f"/?swiggy=error&reason={quote(str(exc)[:180])}")

    db.upsert_oauth_token(
        user_sub=user["sub"],
        provider=SWIGGY_PROVIDER,
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_at=token_expiry(payload),
        scope=payload.get("scope"),
        raw=payload,
    )
    redirect = RedirectResponse("/?swiggy=connected")
    redirect.delete_cookie(SWIGGY_PENDING_COOKIE, path="/")
    return redirect


@app.post("/api/swiggy/disconnect")
async def swiggy_disconnect(cafe_session: str | None = Cookie(default=None)) -> dict:
    user = _require_user(cafe_session)
    db.delete_oauth_token(user["sub"], SWIGGY_PROVIDER)
    return {"status": "ok", "swiggy": swiggy_status(user["sub"])}


@app.post("/api/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@app.patch("/api/me")
async def update_me(
    body: ProfileUpdate, cafe_session: str | None = Cookie(default=None)
) -> dict:
    user = _require_user(cafe_session)
    updated = db.update_profile(
        user["sub"],
        interests=body.interests,
        opt_in_match=body.opt_in_match,
    )
    return {"status": "ok", "user": _public_user(updated)}


def _public_user(user: dict | None) -> dict | None:
    if not user:
        return None
    prefs = user.get("prefs") or {}
    personality = prefs.get("personality")
    return {
        "name": user.get("name"),
        "email": user.get("email"),
        "picture": user.get("picture"),
        "interests": user.get("interests") or [],
        "opt_in_match": user.get("opt_in_match", True),
        "prefs": prefs,
        "personality": personality,
        "vibe_required": not bool(personality),
    }


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/styles.css")
async def styles() -> FileResponse:
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def app_js() -> FileResponse:
    return FileResponse(WEB_DIR / "app.js", media_type="text/javascript")


@app.post("/api/chat")
async def chat(
    body: ChatRequest, cafe_session: str | None = Cookie(default=None)
) -> dict:
    user = _require_user(cafe_session)
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")

    if _vibe_required(user):
        raise HTTPException(
            status_code=403,
            detail="Finish your vibe check first — pick an option below to unlock the café.",
        )

    sub = user["sub"]
    name = user.get("name") or "Guest"
    session_id = await _ensure_adk_session(sub)
    await ensure_swiggy_access_token(sub)

    token_sub = context.current_user_sub.set(sub)
    token_name = context.current_user_name.set(name)
    events = []
    try:
        new_message = types.Content(role="user", parts=[types.Part(text=text)])
        async for event in runner.run_async(
            user_id=sub,
            session_id=session_id,
            new_message=new_message,
        ):
            events.append(event)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        context.current_user_sub.reset(token_sub)
        context.current_user_name.reset(token_name)
        context.current_swiggy_token.set(None)

    reply_parts: list[str] = []
    for event in events:
        if getattr(event, "author", None) == "user":
            continue
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            part_text = getattr(part, "text", None)
            if part_text:
                reply_parts.append(part_text)

    reply = "\n\n".join(p.strip() for p in reply_parts if p and p.strip()).strip()
    return {
        "reply": reply
        or "I placed that with the café tools — check the live ticket panel.",
        "events": _safe_tool_events(events),
        "session_id": session_id,
        "user": _public_user(user),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=5173, reload=False)
