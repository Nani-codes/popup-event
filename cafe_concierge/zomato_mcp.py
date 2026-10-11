"""Optional Zomato MCP toolset for live restaurant discovery / ordering.

Source: https://github.com/Zomato/mcp-server-manifest
Endpoint: https://mcp-server.zomato.com/mcp

Current blockers (from Zomato's README):
- Third-party apps are not allowed on Zomato MCP yet — request access via their form.
- OAuth redirect URIs are only whitelisted for Claude / ChatGPT / VS Code / Postman.
  Our Café Concierge UI (localhost:5173) is not on that list until Zomato enables it.
- Unauthenticated calls return HTTP 401.

When access + OAuth work, set:
  ZOMATO_MCP_ENABLED=1
  ZOMATO_MCP_URL=https://mcp-server.zomato.com/mcp
  ZOMATO_MCP_AUTH_HEADER=Bearer <token>   # if they issue a PAT / session token
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("cafe_concierge.zomato_mcp")

ZOMATO_MCP_URL = os.getenv(
    "ZOMATO_MCP_URL", "https://mcp-server.zomato.com/mcp"
).strip()


def zomato_status() -> dict[str, Any]:
    """Explain Zomato MCP availability for the Pop-Up agent."""
    enabled = os.getenv("ZOMATO_MCP_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return {
        "status": "success",
        "enabled": enabled,
        "url": ZOMATO_MCP_URL,
        "manifest": "https://github.com/Zomato/mcp-server-manifest",
        "capabilities_when_live": [
            "Restaurant discovery near Kondapur / HITEC City",
            "Real menus with prices",
            "Cart + food ordering",
            "QR code payment",
            "Order tracking / reorder",
        ],
        "blockers": [
            "Zomato currently disallows third-party apps on this MCP (security/legal).",
            "OAuth redirects are only whitelisted for Claude, ChatGPT, VS Code, Postman — not Café Concierge yet.",
            "Unauthenticated MCP calls return 401 Unauthorized.",
        ],
        "next_steps": [
            "Request personal developer access: https://forms.eternal.com/form/ja8hap2tpm",
            "Ask Zomato to whitelist http://localhost:5173 (or your deploy URL) as an OAuth redirect.",
            "Then set ZOMATO_MCP_ENABLED=1 and restart the server.",
        ],
        "message": (
            "Zomato MCP would replace our mock menu with live discovery + cart + QR pay "
            "near Third Wave Kondapur — but access/OAuth must be granted first."
        ),
    }


def build_zomato_toolset():
    """Return an ADK McpToolset if enabled, else None.

    Connection is attempted lazily by ADK when tools are listed. Auth header is
    optional — most Zomato flows use interactive OAuth in host apps.
    """
    enabled = os.getenv("ZOMATO_MCP_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not enabled:
        logger.info("Zomato MCP disabled (set ZOMATO_MCP_ENABLED=1 to try).")
        return None

    from google.adk.tools.mcp_tool.mcp_session_manager import (
        StreamableHTTPConnectionParams,
    )
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

    headers: dict[str, str] = {}
    auth = os.getenv("ZOMATO_MCP_AUTH_HEADER", "").strip()
    if auth:
        # Accept full "Bearer xxx" or raw token
        headers["Authorization"] = (
            auth if auth.lower().startswith("bearer ") else f"Bearer {auth}"
        )

    logger.info("Attaching Zomato MCP toolset at %s", ZOMATO_MCP_URL)
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=ZOMATO_MCP_URL,
            headers=headers or None,
        ),
        tool_name_prefix="zomato_",
    )
