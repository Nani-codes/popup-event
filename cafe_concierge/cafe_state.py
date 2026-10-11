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
    """Match only against real signed-in guests (no seed/fake profiles)."""
    del guest_name  # kept for tool signature compatibility
    wanted = {i.strip().lower() for i in interests if i and i.strip()}
    if not wanted:
        return {
            "status": "empty",
            "suggestion": (
                "Pehle vibe check finish karo, ya interests share karo — "
                "phir asli guests se match dikhega. Meanwhile, cozy solo corner le lo."
            ),
            "matches": [],
        }

    exclude = context.current_user_sub.get() or ""
    try:
        live_matches = db.find_matches(list(wanted), exclude_sub=exclude)
    except Exception:  # noqa: BLE001
        live_matches = []

    if not live_matches:
        return {
            "status": "empty",
            "suggestion": (
                "Abhi koi live match nahi mila — kisi aur guest ko Sign in + vibe check "
                "karne ko bolo, ya corner table claim karo. Seed / fake profiles band."
            ),
            "matches": [],
            "source": "signed_in_guests",
        }

    me = db.get_user(exclude) if exclude else None
    my_name = (me or {}).get("name") or "A guest"
    my_vibe = ((me or {}).get("prefs") or {}).get("personality", {}).get("label")

    cards: list[dict] = []
    for top in live_matches:
        shared_list = list(top.get("shared") or [])
        shared = ", ".join(shared_list)
        handle = top.get("name") or top.get("email", "Guest").split("@")[0]
        vibe = top.get("personality_label")
        score = len(shared_list)
        matched_sub = top.get("sub")
        if exclude and matched_sub:
            db.upsert_vibe_match(
                user_sub=exclude,
                matched_sub=matched_sub,
                shared=shared_list,
                score=score,
            )
            # Reverse so they can see you too
            their_wanted = {t.lower() for t in (top.get("interests") or [])}
            their_pers = (top.get("prefs") or {}).get("personality") or {}
            their_wanted |= {t.lower() for t in (their_pers.get("tags") or [])}
            reverse_shared = sorted(wanted & their_wanted) or shared_list
            db.upsert_vibe_match(
                user_sub=matched_sub,
                matched_sub=exclude,
                shared=reverse_shared,
                score=len(reverse_shared),
            )

        cards.append(
            {
                "sub": matched_sub,
                "handle": handle,
                "email": top.get("email"),
                "interests": top.get("interests"),
                "personality": vibe,
                "shared": shared_list,
                "picture": top.get("picture"),
                "score": score,
            }
        )

    top = cards[0]
    vibe_bit = f" ({top['personality']})" if top.get("personality") else ""
    shared = ", ".join(top.get("shared") or [])
    return {
        "status": "success",
        "source": "signed_in_guests",
        "venue": VENUE["name"],
        "match": top,
        "matches": cards,
        "icebreaker": (
            f"{top['handle']}{vibe_bit} se vibe match — common ground: {shared}. "
            f"Notify bhejo agar unhe batana hai ke {my_name}"
            f"{f' ({my_vibe})' if my_vibe else ''} ne ping kiya. "
            "Say hi IRL at Third Wave — asli guest hai, koi fake profile nahi."
        ),
    }
