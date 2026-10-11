# Café Concierge — Third Wave Kondapur

ADK Python agent for the H2O Builder Pop-Up, demoed live at
[Third Wave Coffee — Kondapura Hitech City](https://stores.thirdwavecoffeeroasters.com/store-pages/third-wave-coffee-kondapura-hitech-city-hyderabad)
(Glacier Building, opposite Google).

Hackathon demo only — not an official Third Wave product.

## Setup

```bash
uv sync --group dev
# cafe_concierge/.env should have Vertex project + GOOGLE_APPLICATION_CREDENTIALS
```

## Tests

```bash
uv run pytest -v
```

## Presentation UI (Gemini-styled + Google Sign-In)

What’s **live** vs still Pop-Up:
- **Live:** Google Sign-In, per-guest profile, saved orders, interests, matching among signed-in guests, queue-based room pulse
- **Pop-Up (not café POS):** menu catalog & prices — confirm at the Third Wave counter

### 1. Create a Google OAuth Web client

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → project `purplegrid`
2. **Create credentials → OAuth client ID → Web application**
3. Authorized JavaScript origins: `http://localhost:5173`
4. Authorized redirect URIs: `http://localhost:5173`
5. Paste into `.env.local` as `GOOGLE_CLIENT_ID=....apps.googleusercontent.com`

### 2. Run

```bash
uv sync
uv run python server.py
```

Open **http://localhost:5173** → **Sign in with Google** → chat.

Requires Vertex credentials + OAuth client ID in `cafe_concierge/.env`.

## Zomato MCP (optional live ordering)

Manifest: [Zomato/mcp-server-manifest](https://github.com/Zomato/mcp-server-manifest) · endpoint `https://mcp-server.zomato.com/mcp`

**What it would unlock near Kondapur:** restaurant discovery, real menus, cart, order tracking, QR payment — so the agent is not stuck on our Pop-Up mock menu.

**Why it’s off by default:** Zomato currently blocks third-party apps on this MCP, OAuth redirects are only whitelisted for Claude / ChatGPT / VS Code / Postman, and unauthenticated calls return **401**. Request access via their [developer form](https://forms.eternal.com/form/ja8hap2tpm), ask them to whitelist `http://localhost:5173`, then:

```bash
# cafe_concierge/.env
ZOMATO_MCP_ENABLED=1
# ZOMATO_MCP_AUTH_HEADER=Bearer <token>   # if they provide one
```

Ask the agent: “What’s the Zomato status?” — it calls `get_zomato_status`.

### Fallback: ADK Dev UI

```bash
uv run adk web cafe_concierge
```

Use **text chat only** (not mic / Live). Or: `uv run adk run cafe_concierge`

### 90s script

1. "I'm at Third Wave Kondapur — something cozy, not too sweet."
2. Confirm the suggestion → watch `TWC-…` ticket + ETA + counter pickup.
3. "How's the room looking for the baristas?"
4. "Anyone here into AI and coffee?"
