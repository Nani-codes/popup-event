from __future__ import annotations

# Demo menu inspired by specialty-café staples at Third Wave Kondapur.
# Not an official Third Wave menu — for Builder Pop-Up hackathon demo only.

MENU: list[dict] = [
    {
        "id": "cappuccino",
        "name": "Cappuccino",
        "category": "coffee",
        "price": 220,
        "tags": ["cozy", "comfort", "coffee", "dairy", "classic"],
        "description": "Signature cappuccino — foamy, warm, not too sweet.",
    },
    {
        "id": "flat-white",
        "name": "Flat White",
        "category": "coffee",
        "price": 230,
        "tags": ["cozy", "comfort", "coffee", "dairy"],
        "description": "Silky espresso with steamed milk — soft and mellow.",
    },
    {
        "id": "filter-coffee",
        "name": "South Indian Filter Coffee",
        "category": "coffee",
        "price": 150,
        "tags": ["coffee", "filter", "classic", "bold"],
        "description": "Authentic filter coffee — bold, aromatic, café classic.",
    },
    {
        "id": "oat-latte",
        "name": "Oat Latte",
        "category": "coffee",
        "price": 260,
        "tags": ["cozy", "comfort", "coffee", "dairy-free"],
        "description": "Creamy oat milk latte — plant-based comfort.",
    },
    {
        "id": "cold-coffee",
        "name": "Cold Coffee",
        "category": "coffee",
        "price": 250,
        "tags": ["coffee", "cold", "sweet", "classic"],
        "description": "Chilled classic cold coffee — sweet and refreshing.",
    },
    {
        "id": "americano",
        "name": "Americano",
        "category": "coffee",
        "price": 180,
        "tags": ["coffee", "bold"],
        "description": "Clean espresso and hot water — no sweetness.",
    },
    {
        "id": "matcha-latte",
        "name": "Iced Matcha Latte",
        "category": "tea",
        "price": 280,
        "tags": ["fresh", "dairy-free", "tea", "cold"],
        "description": "Bright matcha over ice — light and focused.",
    },
    {
        "id": "croissant",
        "name": "Butter Croissant",
        "category": "food",
        "price": 180,
        "tags": ["savory", "comfort", "food", "pastry", "breakfast"],
        "description": "Flaky pastry — perfect with a cappuccino for a work session.",
    },
    {
        "id": "brownie",
        "name": "Dark Chocolate Brownie",
        "category": "food",
        "price": 160,
        "tags": ["sweet", "dessert", "food"],
        "description": "Rich cocoa brownie — clearly sweet.",
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
    want_dairy_free = any(
        w in text for w in ("dairy-free", "dairy free", "oat", "vegan")
    )
    want_cold = any(w in text for w in ("cold", "iced", "chilled"))
    want_work = any(
        w in text for w in ("work", "laptop", "meeting", "study", "focus")
    )

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
        if want_cold and "cold" in tags:
            score += 2
        if want_work and tags & {"classic", "coffee", "comfort"}:
            score += 1
        for word in text.replace(",", " ").split():
            if word in tags or word in item["name"].lower():
                score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored] or list(MENU)
