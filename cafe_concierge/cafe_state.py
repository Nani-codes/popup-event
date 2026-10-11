from __future__ import annotations

from copy import deepcopy

from cafe_concierge import context, db
from cafe_concierge.menu import MENU

VENUE = {
    "name": "Third Wave Coffee — Kondapura Hitech City",
    "address": (
        "Flat No 1-2, Glacier Building, Circle No 20, "
        "Opposite Google Premises, Serlingampally Village, Hyderabad"
    ),
    "vibe": "specialty coffee, work-friendly, conversations over cups",
    "hours": "Open ~8:00 AM – midnight",
    "store_url": (
        "https://stores.thirdwavecoffeeroasters.com/store-pages/"
        "third-wave-coffee-kondapura-hitech-city-hyderabad"
    ),
}

_ORDERS: dict[str, dict] = {}
_ORDER_SEQ = 100

_ROOM = {
    "crowd": "steady",
    "energy": "laptop hum + espresso chatter near HITEC City",
    "avg_wait_minutes": 6,
    "staff_tip": "Two drinks deep — batch milk steams; call out ready tickets.",
    "guest_tip": "Grab a seat toward the quieter side; drinks ~6 min.",
}

# Fallback patrons only when no signed-in matches exist yet
_PATRONS = [
    {
        "handle": "Maya",
        "interests": ["ai", "coffee", "design"],
        "available": True,
        "bio": "Designer tinkering with agents between pour-overs at Kondapur TWC.",
    },
    {
        "handle": "Leo",
        "interests": ["music", "latte-art", "travel"],
        "available": True,
        "bio": "Traveler collecting café playlists — here for the Builder Pop-Up.",
    },
    {
        "handle": "Priya",
        "interests": ["startups", "filter-coffee", "books"],
        "available": True,
        "bio": "Founder on a filter-coffee break with a paperback.",
    },
    {
        "handle": "Arjun",
        "interests": ["ai", "hackathons", "cold-coffee"],
        "available": True,
        "bio": "Hackathon regular — usually by the power outlets with a cold coffee.",
    },
]


def reset_cafe() -> None:
    global _ORDERS, _ORDER_SEQ
    _ORDERS = {}
    _ORDER_SEQ = 100


def get_venue() -> dict:
    return dict(VENUE)


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

    name = guest_name or context.current_user_name.get() or "Guest"
    _ORDER_SEQ += 1
    order_id = f"TWC-{_ORDER_SEQ}"
    eta = max(3, 2 + 2 * len(items) + (1 if mods else 0))
    order = {
        "order_id": order_id,
        "guest_name": name,
        "items": items,
        "mods": mods or "",
        "eta_minutes": eta,
        "status": "queued",
        "pickup": "Counter — Third Wave Kondapur (Glacier Building)",
    }
    _ORDERS[order_id] = order

    user_sub = context.current_user_sub.get()
    if user_sub:
        try:
            db.save_order(
                order_id=order_id,
                user_sub=user_sub,
                guest_name=name,
                items=items,
                mods=mods or "",
                eta_minutes=eta,
                status="queued",
            )
            # Remember last drink prefs for next visit
            prefs = {"last_item_ids": item_ids, "last_mods": mods or ""}
            db.update_profile(user_sub, prefs=prefs)
        except Exception:  # noqa: BLE001
            pass

    return {
        "status": "success",
        "order_id": order_id,
        "guest_name": order["guest_name"],
        "items": items,
        "mods": order["mods"],
        "eta_minutes": eta,
        "pickup": order["pickup"],
        "persisted": bool(user_sub),
        "message": (
            f"Order {order_id} queued at Third Wave Kondapur — "
            f"ready in about {eta} minutes. Pickup at the counter."
        ),
    }


def get_order(order_id: str) -> dict | None:
    order = _ORDERS.get(order_id)
    if order:
        return deepcopy(order)
    try:
        stored = db.get_order(order_id)
        if stored:
            stored["pickup"] = "Counter — Third Wave Kondapur (Glacier Building)"
            return stored
    except Exception:  # noqa: BLE001
        pass
    return None


def get_room_pulse() -> dict:
    try:
        open_orders = max(len(_ORDERS), db.open_order_count())
    except Exception:  # noqa: BLE001
        open_orders = len(_ORDERS)
    crowd = "busy" if open_orders >= 3 else "steady" if open_orders else "quiet"
    avg_wait = 4 + open_orders * 2
    return {
        "venue": VENUE["name"],
        "crowd": crowd,
        "energy": _ROOM["energy"],
        "avg_wait_minutes": avg_wait,
        "open_orders": open_orders,
        "live_queue": True,
        "staff_tip": (
            "Pop-Up rush — batch milk, keep the pass clear, smile for demos."
            if crowd == "busy"
            else _ROOM["staff_tip"]
        ),
        "guest_tip": (
            f"Room at Kondapur TWC feels {crowd}; average wait ~{avg_wait} min "
            f"based on {open_orders} open ticket(s). "
            "Power outlets fill up fast near HITEC City."
        ),
    }


def find_match(interests: list[str], guest_name: str = "") -> dict:
    wanted = {i.strip().lower() for i in interests if i and i.strip()}
    if not wanted:
        return {
            "status": "empty",
            "suggestion": (
                "Share an interest (AI, coffee, filter-coffee, music…) "
                "or enjoy a cozy solo corner near the quieter tables."
            ),
        }

    exclude = context.current_user_sub.get() or ""
    try:
        live_matches = db.find_matches(list(wanted), exclude_sub=exclude)
    except Exception:  # noqa: BLE001
        live_matches = []

    if live_matches:
        top = live_matches[0]
        shared = ", ".join(top.get("shared") or [])
        handle = top.get("name") or top.get("email", "Guest").split("@")[0]
        vibe = top.get("personality_label")
        vibe_bit = f" ({vibe})" if vibe else ""
        return {
            "status": "success",
            "source": "signed_in_guests",
            "venue": VENUE["name"],
            "match": {
                "handle": handle,
                "email": top.get("email"),
                "interests": top.get("interests"),
                "personality": vibe,
                "shared": top.get("shared"),
                "picture": top.get("picture"),
            },
            "icebreaker": (
                f"Hey {handle}{vibe_bit} — you both light up around {shared}. "
                f"They're signed in at the Pop-Up — say hi and ask what brought them today."
            ),
        }

    # Fallback seed patrons so the demo still works with few signups
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
            "suggestion": (
                "No signed-in matches yet — invite someone to Sign in with Google "
                "and add interests, or claim a cozy solo corner."
            ),
        }

    patron, overlap = best
    shared = ", ".join(sorted(overlap))
    return {
        "status": "success",
        "source": "seed_fallback",
        "venue": VENUE["name"],
        "match": {
            "handle": patron["handle"],
            "interests": patron["interests"],
            "bio": patron["bio"],
            "shared": list(overlap),
        },
        "icebreaker": (
            f"Hey {patron['handle']} — you both light up around {shared}. "
            f"(Seed profile — more live matches appear as guests sign in.)"
        ),
    }
