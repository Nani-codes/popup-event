"""Swiggy MCP Food toolset (Builders Club) — OAuth Bearer via request context."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from cafe_concierge import context, db
from cafe_concierge.swiggy_oauth import (
    SWIGGY_FOOD_MCP,
    refresh_access_token,
    token_expiry,
)

logger = logging.getLogger("cafe_concierge.swiggy_mcp")

PROVIDER = "swiggy"


def swiggy_enabled() -> bool:
    return os.getenv("SWIGGY_MCP_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def swiggy_status(user_sub: str | None = None) -> dict[str, Any]:
    sub = user_sub or context.current_user_sub.get()
    token = db.get_oauth_token(sub, PROVIDER) if sub else None
    connected = bool(token and token.get("access_token"))
    expired = bool(
        token
        and token.get("expires_at")
        and float(token["expires_at"]) < time.time()
    )
    return {
        "status": "success",
        "provider": "swiggy",
        "enabled": swiggy_enabled(),
        "url": SWIGGY_FOOD_MCP,
        "connected": connected,
        "token_expired": expired,
        "connect_path": "/api/swiggy/connect",
        "docs": "https://builders.swiggy.com/",
        "capabilities_when_connected": [
            "Food discovery / search near you",
            "Restaurant menus",
            "Cart + checkout via Swiggy Food MCP tools",
        ],
        "message": (
            "Swiggy Food MCP is connected — use swiggy_* tools for live food actions."
            if connected and not expired
            else "Swiggy Food MCP needs OAuth. Ask the guest to click Connect Swiggy in the UI, "
            "or open /api/swiggy/connect while signed in."
        ),
    }


async def ensure_swiggy_access_token(user_sub: str) -> str | None:
    """Return a valid access token, refreshing if needed. Sets contextvar."""
    row = db.get_oauth_token(user_sub, PROVIDER)
    if not row:
        context.current_swiggy_token.set(None)
        return None

    access = row.get("access_token")
    expires_at = row.get("expires_at")
    if access and expires_at and float(expires_at) > time.time() + 30:
        context.current_swiggy_token.set(access)
        return access

    refresh = row.get("refresh_token")
    if not refresh:
        context.current_swiggy_token.set(access)
        return access

    try:
        payload = await refresh_access_token(refresh)
        access = payload["access_token"]
        db.upsert_oauth_token(
            user_sub=user_sub,
            provider=PROVIDER,
            access_token=access,
            refresh_token=payload.get("refresh_token") or refresh,
            expires_at=token_expiry(payload),
            scope=payload.get("scope") or row.get("scope"),
            raw=payload,
        )
        context.current_swiggy_token.set(access)
        return access
    except Exception as exc:  # noqa: BLE001
        logger.warning("Swiggy token refresh failed: %s", exc)
        context.current_swiggy_token.set(access)
        return access


def _swiggy_headers(_ctx) -> dict[str, str]:
    token = context.current_swiggy_token.get()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def build_swiggy_toolset():
    """Attach Swiggy Food MCP when enabled (tools need OAuth Bearer at call time)."""
    if not swiggy_enabled():
        logger.info("Swiggy MCP disabled (set SWIGGY_MCP_ENABLED=1).")
        return None

    from google.adk.tools.mcp_tool.mcp_session_manager import (
        StreamableHTTPConnectionParams,
    )
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

    logger.info("Attaching Swiggy Food MCP at %s", SWIGGY_FOOD_MCP)
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=SWIGGY_FOOD_MCP,
            timeout=60,
        ),
        tool_name_prefix="swiggy_",
        header_provider=_swiggy_headers,
        tool_list_cache_ttl_seconds=120,
    )
