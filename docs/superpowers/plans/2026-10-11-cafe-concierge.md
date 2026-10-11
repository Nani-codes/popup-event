# Café Concierge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a single ADK Python café concierge agent (order magic → room pulse → people match) demoable via `adk web`.

**Architecture:** One `root_agent` with five tools over a shared in-memory Café World (menu, orders, room pulse, opt-in patrons). No multi-agent routing, no real POS.

**Tech Stack:** Python 3.11+, `uv`, `google-adk`, Gemini on Vertex AI, `pytest`, ADK Dev UI (`adk web`).

## Global Constraints

- Package name: `cafe_concierge` (ASCII; ADK discovers via `__init__.py` + `root_agent`)
- Follow design spec: `docs/superpowers/specs/2026-10-11-cafe-concierge-design.md`
- Never invent menu prices/ETAs/people — tools + seeded state only
- Do not commit secrets (`.env`, `*.json` service accounts, `.env.local`)
- Vertex: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT=purplegrid`, `GOOGLE_CLOUD_LOCATION=us-central1`, plus existing `GOOGLE_APPLICATION_CREDENTIALS`
- Demo surface: `adk web` from repo root (parent of `cafe_concierge/`)
- Model: `gemini-2.0-flash` (or `gemini-2.5-flash` if available in project)

## File Structure

| File | Responsibility |
|---|---|
| `cafe_concierge/__init__.py` | `from . import agent` for ADK discovery |
| `cafe_concierge/menu.py` | Static menu items + tags |
| `cafe_concierge/cafe_state.py` | In-memory world: orders, pulse, patrons, reset helper |
| `cafe_concierge/tools.py` | Five tool functions returning `dict` payloads |
| `cafe_concierge/agent.py` | `root_agent` wiring + instructions |
| `cafe_concierge/.env` | Vertex env (gitignored; created locally) |
| `tests/test_menu.py` | Menu filter tests |
| `tests/test_cafe_state.py` | Order + match + pulse tests |
| `tests/test_tools.py` | Tool wrapper tests |
| `pyproject.toml` | deps: `google-adk`, `pytest` |
| `.gitignore` | secrets, venv, caches |
| `README.md` | How to run demo script |
| `main.py` | Optional pointer / leave alone |

---

### Task 1: Project deps, gitignore, menu data

**Files:**
- Modify: `pyproject.toml`
- Create: `.gitignore`
- Create: `cafe_concierge/menu.py`
- Create: `tests/test_menu.py`
- Modify: `README.md` (minimal run notes later; stub ok here)

**Interfaces:**
- Consumes: none
- Produces: `MENU: list[dict]` with keys `id`, `name`, `category`, `price`, `tags: list[str]`, `description`; `filter_menu(preferences: str | None) -> list[dict]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_menu.py
from cafe_concierge.menu import MENU, filter_menu


def test_menu_has_cozy_and_not_only_sweet_options():
    assert len(MENU) >= 6
    cozy = filter_menu("cozy not too sweet")
    assert cozy
    assert all("cozy" in item["tags"] or "comfort" in item["tags"] for item in cozy)
    # Prefer items that are not tagged sweet-only
    assert any("sweet" not in item["tags"] for item in cozy)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/nani/Desktop/Exp/ai/popup-event && uv run pytest tests/test_menu.py -v`  
Expected: FAIL (module/package missing or import error)

- [ ] **Step 3: Update pyproject + gitignore + implement menu**

```toml
# pyproject.toml
[project]
name = "popup-event"
version = "0.1.0"
description = "Café Concierge — H2O Builder Pop-Up ADK agent"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "google-adk>=1.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```gitignore
# .gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
.env.local
cafe_concierge/.env
*.json
!pyproject.toml
.DS_Store
uv.lock
```

Note: if locking `uv.lock` is desired for reproducibility, remove `uv.lock` from `.gitignore` and instead ignore only credential JSON files explicitly (`purplegrid-vertexai.json`, `*-credentials.json`). Prefer explicit credential ignores over blanket `*.json` if the team wants a committed lockfile.

```python
# cafe_concierge/menu.py
from __future__ import annotations

MENU: list[dict] = [
    {
        "id": "flat-white",
        "name": "Flat White",
        "category": "coffee",
        "price": 4.5,
        "tags": ["cozy", "comfort", "coffee", "dairy"],
        "description": "Silky espresso with steamed milk — warm, not sweet.",
    },
    {
        "id": "oat-latte",
        "name": "Oat Latte",
        "category": "coffee",
        "price": 5.0,
        "tags": ["cozy", "comfort", "coffee", "dairy-free"],
        "description": "Creamy oat milk latte; soft and mellow.",
    },
    {
        "id": "chai",
        "name": "Spiced Chai",
        "category": "tea",
        "price": 4.75,
        "tags": ["cozy", "comfort", "spiced", "sweet"],
        "description": "House chai with gentle sweetness and spice.",
    },
    {
        "id": "americano",
        "name": "Americano",
        "category": "coffee",
        "price": 3.75,
        "tags": ["coffee", "bold"],
        "description": "Clean espresso and hot water — no sweetness.",
    },
    {
        "id": "avocado-toast",
        "name": "Avocado Toast",
        "category": "food",
        "price": 9.0,
        "tags": ["savory", "comfort", "food"],
        "description": "Sourdough, smashed avo, chili flake.",
    },
    {
        "id": "brownie",
        "name": "Dark Chocolate Brownie",
        "category": "food",
        "price": 4.25,
        "tags": ["sweet", "dessert", "food"],
        "description": "Rich cocoa brownie — clearly sweet.",
    },
    {
        "id": "matcha",
        "name": "Iced Matcha",
        "category": "tea",
        "price": 5.25,
        "tags": ["fresh", "dairy-free", "tea"],
        "description": "Bright ceremonial matcha over ice.",
    },
]


def filter_menu(preferences: str | None = None) -> list[dict]:
    if not preferences or not preferences.strip():
        return list(MENU)

    text = preferences.lower()
    want_cozy = any(w in text for w in ("cozy", "comfort", "warm", "hug"))
    avoid_sweet = any(
        phrase in text
        for phrase in ("not too sweet", "not sweet", "no sweet", "less sweet", "unsweet")
    )
    want_dairy_free = any(w in text for w in ("dairy-free", "dairy free", "oat", "vegan"))

    scored: list[tuple[int, dict]] = []
    for item in MENU:
        tags = set(item["tags"])
        score = 0
        if want_cozy and (tags & {"cozy", "comfort"}):
            score += 3
        if avoid_sweet and "sweet" in tags:
            score -= 2
        if want_dairy_free and "dairy-free" in tags:
            score += 2
        for word in text.replace(",", " ").split():
            if word in tags or word in item["name"].lower():
                score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored] or list(MENU)
```

Also create empty package init for imports:

```python
# cafe_concierge/__init__.py
# Populated in Task 4 with: from . import agent
```

For Task 1 only, leave `__init__.py` empty (or omit agent import until agent exists).

- [ ] **Step 4: Install deps and run tests**

Run:
```bash
cd /Users/nani/Desktop/Exp/ai/popup-event
uv sync --group dev
uv run pytest tests/test_menu.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/nani/Desktop/Exp add \
  ai/popup-event/pyproject.toml \
  ai/popup-event/.gitignore \
  ai/popup-event/cafe_concierge/__init__.py \
  ai/popup-event/cafe_concierge/menu.py \
  ai/popup-event/tests/test_menu.py
git -C /Users/nani/Desktop/Exp commit -m "feat: add café menu filter and project deps"
```

---

### Task 2: Café World state (orders, pulse, patrons)

**Files:**
- Create: `cafe_concierge/cafe_state.py`
- Create: `tests/test_cafe_state.py`

**Interfaces:**
- Consumes: `MENU` / item ids from `menu.py`
- Produces:
  - `reset_cafe() -> None`
  - `create_order(item_ids: list[str], mods: str = "", guest_name: str = "Guest") -> dict`
  - `get_order(order_id: str) -> dict | None`
  - `get_room_pulse() -> dict`
  - `find_match(interests: list[str], guest_name: str = "") -> dict`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cafe_state.py
from cafe_concierge import cafe_state


def setup_function():
    cafe_state.reset_cafe()


def test_create_order_returns_ticket_with_eta():
    order = cafe_state.create_order(["flat-white"], mods="oat milk", guest_name="Nani")
    assert order["status"] == "success"
    assert order["order_id"].startswith("H2O-")
    assert order["eta_minutes"] >= 1
    assert "Flat White" in order["items"][0]["name"]


def test_unknown_item_fails_gracefully():
    order = cafe_state.create_order(["nope-drink"])
    assert order["status"] == "error"
    assert "not found" in order["message"].lower()


def test_get_order_missing():
    assert cafe_state.get_order("H2O-999") is None


def test_room_pulse_has_tips():
    pulse = cafe_state.get_room_pulse()
    assert pulse["crowd"] in {"quiet", "steady", "busy"}
    assert pulse["staff_tip"]
    assert pulse["guest_tip"]


def test_find_match_by_interest():
    result = cafe_state.find_match(["ai", "coffee"], guest_name="Nani")
    assert result["status"] == "success"
    assert result["match"]["handle"]
    assert result["icebreaker"]


def test_find_match_empty_suggests_solo():
    result = cafe_state.find_match(["underwater-basket-weaving-xyz"])
    assert result["status"] == "empty"
    assert "cozy" in result["suggestion"].lower() or "solo" in result["suggestion"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cafe_state.py -v`  
Expected: FAIL (import / missing functions)

- [ ] **Step 3: Implement cafe_state.py**

```python
# cafe_concierge/cafe_state.py
from __future__ import annotations

from copy import deepcopy

from cafe_concierge.menu import MENU

_ORDERS: dict[str, dict] = {}
_ORDER_SEQ = 100

_ROOM = {
    "crowd": "steady",
    "energy": "warm chatter",
    "avg_wait_minutes": 6,
    "staff_tip": "Two drinks deep in queue — batch milk steams.",
    "guest_tip": "Grab a seat by the window; drinks landing in ~6 min.",
}

_PATRONS = [
    {
        "handle": "Maya",
        "interests": ["ai", "coffee", "design"],
        "available": True,
        "bio": "Designer tinkering with agents between pour-overs.",
    },
    {
        "handle": "Leo",
        "interests": ["music", "latte-art", "travel"],
        "available": True,
        "bio": "Traveler collecting café playlists.",
    },
    {
        "handle": "Priya",
        "interests": ["startups", "matcha", "books"],
        "available": True,
        "bio": "Founder on a matcha break with a paperback.",
    },
]


def reset_cafe() -> None:
    global _ORDERS, _ORDER_SEQ
    _ORDERS = {}
    _ORDER_SEQ = 100


def _menu_by_id() -> dict[str, dict]:
    return {item["id"]: item for item in MENU}


def create_order(
    item_ids: list[str], mods: str = "", guest_name: str = "Guest"
) -> dict:
    global _ORDER_SEQ
    catalog = _menu_by_id()
    items: list[dict] = []
    missing: list[str] = []
    for item_id in item_ids:
        item = catalog.get(item_id)
        if not item:
            missing.append(item_id)
        else:
            items.append(deepcopy(item))
    if missing:
        return {
            "status": "error",
            "message": f"Item(s) not found: {', '.join(missing)}. Use browse_menu first.",
        }
    if not items:
        return {"status": "error", "message": "No items provided."}

    _ORDER_SEQ += 1
    order_id = f"H2O-{_ORDER_SEQ}"
    eta = max(3, 2 + 2 * len(items) + (1 if mods else 0))
    order = {
        "order_id": order_id,
        "guest_name": guest_name or "Guest",
        "items": items,
        "mods": mods or "",
        "eta_minutes": eta,
        "status": "queued",
    }
    _ORDERS[order_id] = order
    return {
        "status": "success",
        "order_id": order_id,
        "guest_name": order["guest_name"],
        "items": items,
        "mods": order["mods"],
        "eta_minutes": eta,
        "message": f"Order {order_id} queued — ready in about {eta} minutes.",
    }


def get_order(order_id: str) -> dict | None:
    order = _ORDERS.get(order_id)
    return deepcopy(order) if order else None


def get_room_pulse() -> dict:
    open_orders = len(_ORDERS)
    crowd = "busy" if open_orders >= 3 else "steady" if open_orders else "quiet"
    avg_wait = 4 + open_orders * 2
    return {
        "crowd": crowd,
        "energy": _ROOM["energy"],
        "avg_wait_minutes": avg_wait,
        "open_orders": open_orders,
        "staff_tip": (
            "Queue picking up — call out ready tickets loud."
            if crowd == "busy"
            else _ROOM["staff_tip"]
        ),
        "guest_tip": (
            f"Room feels {crowd}; average wait ~{avg_wait} min. "
            "Best time for a slow chat is after your drink lands."
        ),
    }


def find_match(interests: list[str], guest_name: str = "") -> dict:
    wanted = {i.strip().lower() for i in interests if i and i.strip()}
    if not wanted:
        return {
            "status": "empty",
            "suggestion": "Share an interest (AI, coffee, music…) or enjoy a cozy solo corner by the window.",
        }

    best = None
    best_score = 0
    for patron in _PATRONS:
        if not patron["available"]:
            continue
        if guest_name and patron["handle"].lower() == guest_name.lower():
            continue
        overlap = wanted & {t.lower() for t in patron["interests"]}
        score = len(overlap)
        if score > best_score:
            best_score = score
            best = (patron, overlap)

    if not best or best_score == 0:
        return {
            "status": "empty",
            "suggestion": "No overlap right now — try broader interests, or claim the cozy solo corner by the plants.",
        }

    patron, overlap = best
    shared = ", ".join(sorted(overlap))
    return {
        "status": "success",
        "match": {
            "handle": patron["handle"],
            "interests": patron["interests"],
            "bio": patron["bio"],
            "shared": list(overlap),
        },
        "icebreaker": (
            f"Hey {patron['handle']} — you both light up around {shared}. "
            f"Ask what brought them to the Builder Pop-Up today."
        ),
    }
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cafe_state.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/nani/Desktop/Exp add \
  ai/popup-event/cafe_concierge/cafe_state.py \
  ai/popup-event/tests/test_cafe_state.py
git -C /Users/nani/Desktop/Exp commit -m "feat: add in-memory café world state"
```

---

### Task 3: Tool functions

**Files:**
- Create: `cafe_concierge/tools.py`
- Create: `tests/test_tools.py`

**Interfaces:**
- Consumes: `filter_menu`, `cafe_state.*`
- Produces (all return `dict`):
  - `browse_menu(preferences: str = "") -> dict`
  - `place_order(item_ids: str, mods: str = "", guest_name: str = "Guest") -> dict`  
    (`item_ids` comma-separated for LLM-friendly tool schema)
  - `get_order_status(order_id: str) -> dict`
  - `get_room_pulse() -> dict`
  - `find_connection(interests: str, guest_name: str = "") -> dict`  
    (`interests` comma-separated)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tools.py
from cafe_concierge import cafe_state
from cafe_concierge import tools


def setup_function():
    cafe_state.reset_cafe()


def test_browse_menu_tool():
    result = tools.browse_menu("cozy not too sweet")
    assert result["status"] == "success"
    assert result["items"]


def test_place_and_status():
    placed = tools.place_order("flat-white", mods="extra hot", guest_name="Judge")
    assert placed["status"] == "success"
    status = tools.get_order_status(placed["order_id"])
    assert status["status"] == "success"
    assert status["order"]["order_id"] == placed["order_id"]


def test_get_order_status_missing():
    status = tools.get_order_status("H2O-missing")
    assert status["status"] == "error"


def test_room_and_connection_tools():
    pulse = tools.get_room_pulse()
    assert pulse["status"] == "success"
    match = tools.find_connection("ai, coffee", guest_name="Judge")
    assert match["status"] == "success"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tools.py -v`  
Expected: FAIL

- [ ] **Step 3: Implement tools.py**

```python
# cafe_concierge/tools.py
from __future__ import annotations

from cafe_concierge.cafe_state import (
    create_order,
    find_match,
    get_order,
    get_room_pulse as room_pulse,
)
from cafe_concierge.menu import filter_menu


def browse_menu(preferences: str = "") -> dict:
    """Recommend menu items from guest preferences (e.g. 'cozy not too sweet')."""
    try:
        items = filter_menu(preferences or None)
        return {
            "status": "success",
            "preferences": preferences,
            "items": items[:5],
            "message": f"Found {min(5, len(items))} suggestion(s).",
        }
    except Exception as exc:  # noqa: BLE001 — keep adk web session alive
        return {"status": "error", "message": f"Menu lookup failed: {exc}"}


def place_order(
    item_ids: str, mods: str = "", guest_name: str = "Guest"
) -> dict:
    """Place an order. item_ids is a comma-separated list of menu ids from browse_menu."""
    try:
        ids = [part.strip() for part in item_ids.split(",") if part.strip()]
        return create_order(ids, mods=mods, guest_name=guest_name)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Could not place order: {exc}"}


def get_order_status(order_id: str) -> dict:
    """Check readiness / details for an order id like H2O-101."""
    try:
        order = get_order(order_id)
        if not order:
            return {"status": "error", "message": f"Order {order_id} not found."}
        return {
            "status": "success",
            "order": order,
            "message": (
                f"{order['order_id']} is {order['status']} — "
                f"about {order['eta_minutes']} min remaining."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Status check failed: {exc}"}


def get_room_pulse() -> dict:
    """Live-ish café pulse: crowd, wait, guest tip, and staff tip."""
    try:
        pulse = room_pulse()
        return {"status": "success", **pulse}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Pulse unavailable: {exc}"}


def find_connection(interests: str, guest_name: str = "") -> dict:
    """Find an opt-in patron with shared interests; returns icebreaker. interests comma-separated."""
    try:
        tags = [part.strip() for part in interests.split(",") if part.strip()]
        return find_match(tags, guest_name=guest_name)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Match failed: {exc}"}
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_tools.py tests/test_cafe_state.py tests/test_menu.py -v`  
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/nani/Desktop/Exp add \
  ai/popup-event/cafe_concierge/tools.py \
  ai/popup-event/tests/test_tools.py
git -C /Users/nani/Desktop/Exp commit -m "feat: add café concierge ADK tools"
```

---

### Task 4: root_agent + Vertex env + adk web smoke

**Files:**
- Create: `cafe_concierge/agent.py`
- Modify: `cafe_concierge/__init__.py`
- Create: `cafe_concierge/.env` (local only; do not commit)
- Modify: `README.md`

**Interfaces:**
- Consumes: tools from `tools.py`
- Produces: module-level `root_agent` for ADK CLI

- [ ] **Step 1: Wire agent package**

```python
# cafe_concierge/__init__.py
from . import agent
```

```python
# cafe_concierge/agent.py
from google.adk.agents.llm_agent import Agent

from cafe_concierge.tools import (
    browse_menu,
    find_connection,
    get_order_status,
    get_room_pulse,
    place_order,
)

root_agent = Agent(
    model="gemini-2.0-flash",
    name="cafe_concierge",
    description=(
        "H2O Builder Pop-Up café concierge: conversational ordering, "
        "wait ETAs, room pulse, and opt-in people matching."
    ),
    instruction="""
You are Café Concierge for the H2O Builder Pop-Up café — warm, concise, a bit magical.

Rules:
- Always use tools for menu, orders, ETAs, room pulse, and people matches. Never invent them.
- Ordering flow: clarify vibe → browse_menu → propose 1–2 items → confirm → place_order with menu ids.
- After placing an order, celebrate with order_id + eta_minutes.
- For room questions, call get_room_pulse and share guest_tip; also mention staff_tip briefly ("for the baristas…").
- For social asks, call find_connection with comma-separated interests. Only introduce opt-in matches from the tool. If empty, offer the solo cozy-corner suggestion.
- Keep replies short enough for a live demo (a few sentences + the ticket details).
""",
    tools=[
        browse_menu,
        place_order,
        get_order_status,
        get_room_pulse,
        find_connection,
    ],
)
```

- [ ] **Step 2: Create local Vertex `.env` (do not commit)**

Create `cafe_concierge/.env` with (adjust credentials path to the machine’s real file):

```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=purplegrid
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/Users/nani/Desktop/Exp/ai/purplegrid-34afb6866620.json
```

If `GOOGLE_GENAI_USE_ENTERPRISE` is required by the installed ADK version, set that to `TRUE` as well (newer docs rename the Vertex switch).

- [ ] **Step 3: Update README with demo script**

```markdown
# Café Concierge (Builder Pop-Up)

ADK Python agent for the H2O café hackathon challenge.

## Setup

```bash
uv sync --group dev
# Ensure cafe_concierge/.env has Vertex project + GOOGLE_APPLICATION_CREDENTIALS
```

## Tests

```bash
uv run pytest -v
```

## Demo (`adk web`)

```bash
uv run adk web cafe_concierge
```

Open http://localhost:8000 — select `cafe_concierge`.

### 90s script

1. "I want something cozy, not too sweet."
2. Confirm the suggestion → watch ticket + ETA.
3. "How's the room looking for the baristas?"
4. "Anyone here into AI and coffee?"
```

- [ ] **Step 4: Manual smoke**

Run:
```bash
cd /Users/nani/Desktop/Exp/ai/popup-event
uv run adk web cafe_concierge
```
Expected: UI loads; agent listed; demo script produces tool calls without crash.

If model id fails, switch `agent.py` model to a Vertex-available Gemini flash id and retry.

- [ ] **Step 5: Commit (no secrets)**

```bash
git -C /Users/nani/Desktop/Exp add \
  ai/popup-event/cafe_concierge/__init__.py \
  ai/popup-event/cafe_concierge/agent.py \
  ai/popup-event/README.md \
  ai/popup-event/.gitignore
git -C /Users/nani/Desktop/Exp commit -m "feat: wire Café Concierge root_agent for adk web"
```

Verify `cafe_concierge/.env` and credential JSON are **not** staged.

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| Single root_agent + tools | Task 4 |
| browse_menu / place_order / get_order_status / get_room_pulse / find_connection | Task 3 |
| In-memory menu, orders, pulse, patrons | Tasks 1–2 |
| Order-first demo + room + match | Task 4 README script |
| Errors: unknown item, empty match, bad order id | Tasks 2–3 |
| Unit tests | Tasks 1–3 |
| `adk web` + Vertex creds | Task 4 |
| Out of scope multi-agent / custom UI / payments | Not planned |

## Self-review notes

- No TBD placeholders in task steps  
- Tool param names consistent (`item_ids`, `interests` as comma-separated strings for LLM tools)  
- Package discovery matches ADK: `__init__.py` imports `agent`; `root_agent` defined  
- Secrets stay local via `.gitignore`  
