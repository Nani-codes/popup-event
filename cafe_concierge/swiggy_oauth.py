"""Swiggy MCP OAuth 2.1 + PKCE (Builders Club / mcp.swiggy.com)."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

SWIGGY_AUTH = "https://mcp.swiggy.com/auth"
SWIGGY_AUTHORIZE = f"{SWIGGY_AUTH}/authorize"
SWIGGY_TOKEN = f"{SWIGGY_AUTH}/token"
SWIGGY_REGISTER = f"{SWIGGY_AUTH}/register"
SWIGGY_RESOURCE = "https://mcp.swiggy.com"
SWIGGY_FOOD_MCP = os.getenv("SWIGGY_MCP_URL", "https://mcp.swiggy.com/food").strip()

DEFAULT_REDIRECT = os.getenv(
    "SWIGGY_REDIRECT_URI", "http://localhost:5173/auth/swiggy/callback"
).strip()
CLIENT_ID = os.getenv("SWIGGY_CLIENT_ID", "swiggy-mcp").strip()
SCOPES = "mcp:tools mcp:resources mcp:prompts"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_pkce() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def authorize_url(*, state: str, code_challenge: str, redirect_uri: str = DEFAULT_REDIRECT) -> str:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "resource": SWIGGY_RESOURCE,
    }
    return f"{SWIGGY_AUTHORIZE}?{urlencode(params)}"


async def exchange_code(
    *,
    code: str,
    code_verifier: str,
    redirect_uri: str = DEFAULT_REDIRECT,
) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier,
        "resource": SWIGGY_RESOURCE,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            SWIGGY_TOKEN,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Swiggy token exchange failed ({r.status_code}): {r.text[:400]}")
        return r.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "resource": SWIGGY_RESOURCE,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            SWIGGY_TOKEN,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Swiggy refresh failed ({r.status_code}): {r.text[:400]}")
        return r.json()


def token_expiry(token_payload: dict[str, Any]) -> float:
    expires_in = int(token_payload.get("expires_in") or 3600)
    return time.time() + max(60, expires_in - 60)
