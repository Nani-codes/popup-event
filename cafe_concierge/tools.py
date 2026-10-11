from __future__ import annotations

import time

from cafe_concierge import context, db
from cafe_concierge.cafe_state import (
    create_order,
    find_match,
    get_order,
    get_room_pulse as room_pulse,
    get_venue,
)
from cafe_concierge.menu import filter_menu
from cafe_concierge.vibe import (
    QUESTIONS,
    next_question,
    option_by_id,
    question_by_id,
    score_answers,
)


def get_cafe_info() -> dict:
    """Return venue details for Third Wave Coffee Kondapur (Builder Pop-Up)."""
    try:
        return {"status": "success", **get_venue()}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Venue info unavailable: {exc}"}


def get_my_profile() -> dict:
    """Return the signed-in guest profile, prefs, personality, and recent orders."""
    try:
        sub = context.current_user_sub.get()
        if not sub:
            return {"status": "error", "message": "Not signed in."}
        user = db.get_user(sub)
        if not user:
            return {"status": "error", "message": "Profile not found."}
        orders = db.list_orders_for_user(sub, limit=5)
        prefs = user.get("prefs") or {}
        return {
            "status": "success",
            "name": user.get("name"),
            "email": user.get("email"),
            "interests": user.get("interests"),
            "prefs": prefs,
            "personality": prefs.get("personality"),
            "vibe_complete": bool(prefs.get("personality")),
            "opt_in_match": user.get("opt_in_match"),
            "recent_orders": orders,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Profile failed: {exc}"}


def _vibe_answers(user: dict) -> dict[str, str]:
    prefs = user.get("prefs") or {}
    progress = prefs.get("vibe_progress") or {}
    answers = progress.get("answers") or {}
    # Also accept completed personality answers as keys → option ids
    if not answers and prefs.get("personality", {}).get("answers"):
        raw = prefs["personality"]["answers"]
        return {k: v.get("option_id", v) if isinstance(v, dict) else v for k, v in raw.items()}
    return dict(answers)


def start_vibe_check(reset: bool = False) -> dict:
    """Start (or resume) the quirky vibe quiz. Returns the next multiple-choice question.

    Present the prompt and options A–D to the guest. When they pick, call
    answer_vibe_question with question_id and choice (option id or A/B/C/D).
    """
    try:
        sub = context.current_user_sub.get()
        if not sub:
            return {"status": "error", "message": "Sign in with Google first."}
        user = db.get_user(sub)
        if not user:
            return {"status": "error", "message": "Profile not found."}

        prefs = dict(user.get("prefs") or {})
        if reset:
            prefs["vibe_progress"] = {"answers": {}}
            prefs.pop("personality", None)
            db.update_profile(sub, prefs=prefs)
            user = db.get_user(sub) or user

        answers = {} if reset else _vibe_answers(user)

        existing = (user.get("prefs") or {}).get("personality")
        if existing and not reset:
            return {
                "status": "success",
                "phase": "complete",
                "personality": existing,
                "message": (
                    f"Already vibed as **{existing.get('label')}**. "
                    "Call start_vibe_check with reset=true to re-roll, "
                    "or find_connection to meet someone with your vibe."
                ),
            }

        q = next_question(answers)
        if q is None:
            personality = score_answers(answers)
            personality["completed_at"] = time.time()
            return _persist_personality(sub, user, answers, personality)

        # Ensure progress row exists
        prefs = dict(user.get("prefs") or {})
        progress = dict(prefs.get("vibe_progress") or {})
        progress["answers"] = answers
        prefs["vibe_progress"] = progress
        db.update_profile(sub, prefs=prefs)

        return {
            "status": "success",
            "phase": "question",
            "question": q,
            "message": (
                f"Vibe check {q['index']}/{q['total']}: {q['prompt']} "
                "Show the options and wait for their pick."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Vibe check failed: {exc}"}


def answer_vibe_question(question_id: str, choice: str) -> dict:
    """Record one vibe-quiz answer. choice = option id (e.g. inception) or A/B/C/D.

    Returns the next question, or the saved personality when the quiz finishes.
    """
    try:
        sub = context.current_user_sub.get()
        if not sub:
            return {"status": "error", "message": "Sign in with Google first."}
        user = db.get_user(sub)
        if not user:
            return {"status": "error", "message": "Profile not found."}

        q = question_by_id(question_id.strip())
        if not q:
            return {
                "status": "error",
                "message": f"Unknown question_id '{question_id}'. Call start_vibe_check.",
            }

        raw = choice.strip()
        option_id = raw.lower()
        # Allow A/B/C/D
        if len(raw) == 1 and raw.upper() in "ABCD":
            idx = ord(raw.upper()) - 65
            if 0 <= idx < len(q["options"]):
                option_id = q["options"][idx]["id"]
        opt = option_by_id(q, option_id)
        if not opt:
            # Fuzzy: match label
            for o in q["options"]:
                if o["label"].lower() == raw.lower() or o["id"].lower() == raw.lower():
                    opt = o
                    option_id = o["id"]
                    break
        if not opt:
            return {
                "status": "error",
                "message": f"Invalid choice '{choice}'. Use an option id or A/B/C/D.",
                "question": next_question(_vibe_answers(user)),
            }

        answers = _vibe_answers(user)
        answers[q["id"]] = option_id

        nxt = next_question(answers)
        if nxt is None:
            personality = score_answers(answers)
            personality["completed_at"] = time.time()
            return _persist_personality(sub, user, answers, personality)

        prefs = dict(user.get("prefs") or {})
        prefs["vibe_progress"] = {"answers": answers}
        db.update_profile(sub, prefs=prefs)

        return {
            "status": "success",
            "phase": "question",
            "recorded": {"question_id": q["id"], "choice": option_id, "label": opt["label"]},
            "question": nxt,
            "message": (
                f"Nice — {opt['label']}. Next ({nxt['index']}/{nxt['total']}): "
                f"{nxt['prompt']}"
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Could not save vibe answer: {exc}"}


def _persist_personality(
    sub: str, user: dict, answers: dict[str, str], personality: dict
) -> dict:
    prefs = dict(user.get("prefs") or {})
    prefs["personality"] = {
        "archetype": personality["archetype"],
        "label": personality["label"],
        "blurb": personality["blurb"],
        "drink_hint": personality["drink_hint"],
        "tags": personality["tags"],
        "answers": personality["answers"],
        "completed_at": personality.get("completed_at", time.time()),
    }
    prefs["vibe_progress"] = {"answers": answers, "complete": True}

    # Merge vibe tags into interests for matching
    existing = list(user.get("interests") or [])
    merged: list[str] = []
    seen: set[str] = set()
    for t in existing + list(personality["tags"]):
        key = t.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(t.strip())

    updated = db.update_profile(
        sub, prefs=prefs, interests=merged[:16], opt_in_match=True
    )
    saved = (updated or {}).get("prefs", {}).get("personality") or prefs["personality"]
    return {
        "status": "success",
        "phase": "complete",
        "personality": saved,
        "interests": (updated or {}).get("interests") or merged,
        "message": (
            f"Personality locked: **{saved['label']}**. {saved['blurb']} "
            f"Drink tip: {saved['drink_hint']}"
        ),
    }


def save_interests(interests: str, opt_in_match: bool = True) -> dict:
    """Save comma-separated interests for people-matching (opt-in)."""
    try:
        sub = context.current_user_sub.get()
        if not sub:
            return {"status": "error", "message": "Sign in with Google first."}
        tags = [part.strip() for part in interests.split(",") if part.strip()]
        user = db.update_profile(sub, interests=tags, opt_in_match=opt_in_match)
        return {
            "status": "success",
            "interests": user.get("interests") if user else tags,
            "opt_in_match": opt_in_match,
            "message": "Interests saved — you're discoverable to other signed-in guests.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Could not save interests: {exc}"}


def browse_menu(preferences: str = "") -> dict:
    """Recommend menu items from guest preferences (e.g. 'cozy not too sweet')."""
    try:
        prefs = preferences
        sub = context.current_user_sub.get()
        if not prefs and sub:
            user = db.get_user(sub)
            last = (user or {}).get("prefs", {}).get("last_item_ids")
            if last:
                prefs = " ".join(last)
        items = filter_menu(prefs or None)
        return {
            "status": "success",
            "preferences": prefs,
            "items": items[:5],
            "currency": "INR",
            "disclaimer": "Pop-Up concierge menu — confirm at counter for real pricing.",
            "message": f"Found {min(5, len(items))} suggestion(s).",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Menu lookup failed: {exc}"}


def place_order(
    item_ids: str, mods: str = "", guest_name: str = ""
) -> dict:
    """Place an order. item_ids is a comma-separated list of menu ids from browse_menu."""
    try:
        ids = [part.strip() for part in item_ids.split(",") if part.strip()]
        name = guest_name or context.current_user_name.get() or "Guest"
        return create_order(ids, mods=mods, guest_name=name)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Could not place order: {exc}"}


def get_order_status(order_id: str) -> dict:
    """Check readiness / details for an order id like TWC-101."""
    try:
        order = get_order(order_id)
        if not order:
            return {"status": "error", "message": f"Order {order_id} not found."}
        return {
            "status": "success",
            "order": order,
            "message": (
                f"{order['order_id']} is {order['status']} — "
                f"about {order['eta_minutes']} min remaining. "
                f"Pickup: {order.get('pickup', 'counter')}."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Status check failed: {exc}"}


def get_room_pulse() -> dict:
    """Café pulse from live open tickets: crowd, wait, guest tip, staff tip."""
    try:
        pulse = room_pulse()
        return {"status": "success", **pulse}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Pulse unavailable: {exc}"}


def find_connection(interests: str = "", guest_name: str = "") -> dict:
    """Find an opt-in signed-in guest with shared interests / vibe tags; returns icebreaker.

    If interests is empty, uses the guest's saved personality tags + interests.
    """
    try:
        tags = [part.strip() for part in interests.split(",") if part.strip()]
        sub = context.current_user_sub.get()
        if sub:
            user = db.get_user(sub)
            if user:
                if not tags:
                    personality = (user.get("prefs") or {}).get("personality") or {}
                    tags = list(personality.get("tags") or []) + list(
                        user.get("interests") or []
                    )
                elif tags:
                    db.update_profile(sub, interests=tags, opt_in_match=True)
        if not tags:
            return {
                "status": "empty",
                "suggestion": (
                    "Run start_vibe_check first (or share interests) so I know who to match you with."
                ),
            }
        return find_match(tags, guest_name=guest_name)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Match failed: {exc}"}
