# Café Concierge — Design Spec

**Date:** 2026-10-11  
**Event:** H2O Builder Pop-Up hackathon (live at venue)  
**Venue usecase:** [Third Wave Coffee — Kondapura Hitech City](https://stores.thirdwavecoffeeroasters.com/store-pages/third-wave-coffee-kondapura-hitech-city-hyderabad) (Glacier Building, opposite Google, Serlingampally / Kondapur)  
**Stack:** Google ADK (Python), Gemini via Vertex, `adk web` for demo UI  

**Note:** Demo agent for the Builder Pop-Up — not an official Third Wave product. Menu items are inspired by specialty-café staples (cappuccino, filter coffee, cold coffee, pastries, work-friendly vibe) for hackathon demo realism.

## Goal

Build a single guest-facing AI café concierge for the live Third Wave Kondapur Pop-Up with strong demo awe: conversational ordering first, then room intelligence and people matching in the same session.

## Decisions

| Decision | Choice |
|---|---|
| Primary user | Guest (staff tips appear inside guest/room responses) |
| Demo opener | Order magic (“something cozy, not too sweet” → ticket + ETA) |
| Surface | ADK Dev UI (`adk web`) |
| Architecture | Approach A — single `root_agent` + tools + in-memory café world |
| Scope of “all three” | One spine (ordering) + two supporting moments (room pulse, match) |

## Product narrative

**Working name:** Café Concierge @ Third Wave Kondapur  

Guest chats in `adk web`. Demo script (~90s):

1. “Something cozy, not too sweet” at Kondapur TWC → menu match → confirm → `TWC-…` ticket + ETA  
2. “How’s the room?” → crowd/energy/wait + guest tip + staff tip  
3. “Anyone into AI + coffee?” → opt-in Pop-Up match + icebreaker line  

## Architecture

```
Guest (adk web)
  → root_agent (Gemini / ADK)
      → tools: browse_menu, place_order, get_order_status,
               get_room_pulse, find_connection
      → Café World (in-memory shared state)
```

No multi-agent routing in MVP. No real POS, payments, auth, or geolocation.

## Components

### Layout

```
popup-event/
  cafe_concierge/
    agent.py          # root_agent definition
    tools.py          # ADK tool functions
    cafe_state.py     # in-memory world
    menu.py           # static menu + preference tags
  docs/superpowers/specs/...
  pyproject.toml      # google-adk (+ test deps as needed)
  .env.local          # credentials (not committed)
```

### Café World (in-memory)

- **Menu:** items with tags (`cozy`, `sweet`, `dairy-free`, etc.)  
- **Orders:** id, items, mods, status, ETA minutes  
- **Room pulse:** crowd level, energy, avg wait, staff tip, guest tip  
- **Patrons:** opt-in list with handle, interests, availability for matching  

### Tools

1. `browse_menu(preferences?)` — filter/recommend from tags and free-text prefs  
2. `place_order(items, mods, guest_name?)` — create ticket; return id + ETA  
3. `get_order_status(order_id)` — readiness / remaining wait  
4. `get_room_pulse()` — mood/crowd/wait + guest tip + staff tip  
5. `find_connection(interests, guest_name?)` — best match + icebreaker  

### Agent behavior

- Warm, concise café host voice  
- Prefer tools over inventing menu/prices/ETAs  
- Order flow: clarify → recommend → confirm → place  
- Never invent real people; only match against seeded opt-in patrons  
- On empty match: broaden interests or offer a solo “cozy corner” tip  

## Data flow

1. User states preference → `browse_menu`  
2. User confirms → `place_order` → ticket + ETA  
3. Optional room question → `get_room_pulse`  
4. Optional social ask → `find_connection`  

## Errors

| Case | Behavior |
|---|---|
| Unknown menu item | Offer closest match; ask to confirm |
| Empty match set | Suggest broader interests or solo tip |
| Bad order id | Clear “not found” response |
| Tool exception | Friendly failure message; keep session alive |

## Testing

- Unit tests for café state + tools (menu filter, ETA, match scoring)  
- Manual gate: full demo script in `adk web`  

## Runtime

- Install: `google-adk` via `uv` / `pyproject.toml`  
- Auth: existing Vertex / `GOOGLE_APPLICATION_CREDENTIALS` (or ADK-supported Google API key if preferred)  
- Run: `adk web` against `cafe_concierge` package  

## Out of scope (MVP)

- Multi-agent workflow (Order/Room/Match specialists)  
- Live drifting simulator loop (nice-to-have if time remains)  
- Custom branded frontend, payments, real café integration  
- Persistent DB / user accounts  

## Success criteria

- Judge can see a full order ticket from a vague natural-language ask in one turn cycle  
- Same session answers room pulse and returns a plausible people match  
- Demo runs from `adk web` without crashing on happy path  
