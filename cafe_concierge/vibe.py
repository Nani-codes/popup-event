"""Quirky vibe quiz → café personality for matching & drink tips."""

from __future__ import annotations

from typing import Any

# Each choice contributes tags + archetype weights.
QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "movie",
        "prompt": "If your life had a soundtrack movie, which energy wins?",
        "options": [
            {
                "id": "inception",
                "label": "Inception",
                "emoji": "🌀",
                "tags": ["deep-conversations", "ai", "plot-twists"],
                "weights": {"plotter": 2, "builder": 1},
            },
            {
                "id": "amelie",
                "label": "Amélie",
                "emoji": "🎬",
                "tags": ["whimsy", "people-watching", "small-joys"],
                "weights": {"romantic": 2, "host": 1},
            },
            {
                "id": "budapest",
                "label": "Grand Budapest",
                "emoji": "🏨",
                "tags": ["design", "wit", "pastel-chaos"],
                "weights": {"aesthete": 2, "host": 1},
            },
            {
                "id": "spiderverse",
                "label": "Spider-Verse",
                "emoji": "🕸️",
                "tags": ["chaos-energy", "comics", "bold-ideas"],
                "weights": {"spark": 2, "builder": 1},
            },
        ],
    },
    {
        "id": "weekend",
        "prompt": "Perfect Kondapur weekend — pick your vibe:",
        "options": [
            {
                "id": "hackathon",
                "label": "Hackathon blur",
                "emoji": "💻",
                "tags": ["hackathons", "ai", "startups"],
                "weights": {"builder": 2, "plotter": 1},
            },
            {
                "id": "bookstore",
                "label": "Bookstore crawl",
                "emoji": "📚",
                "tags": ["books", "filter-coffee", "quiet-corners"],
                "weights": {"romantic": 2, "aesthete": 1},
            },
            {
                "id": "gig",
                "label": "Live gig / open mic",
                "emoji": "🎸",
                "tags": ["music", "nightlife", "friends"],
                "weights": {"spark": 2, "host": 1},
            },
            {
                "id": "drive",
                "label": "Long drive + chai",
                "emoji": "🛣️",
                "tags": ["travel", "chai", "wind-down"],
                "weights": {"romantic": 1, "plotter": 1, "aesthete": 1},
            },
        ],
    },
    {
        "id": "playlist",
        "prompt": "What’s looping in your earbuds right now?",
        "options": [
            {
                "id": "lofi",
                "label": "Lo-fi focus",
                "emoji": "🎧",
                "tags": ["deep-work", "coffee", "headphones-on"],
                "weights": {"plotter": 2, "builder": 1},
            },
            {
                "id": "indie",
                "label": "Indie rock",
                "emoji": "🎸",
                "tags": ["music", "stories", "city-walks"],
                "weights": {"spark": 1, "romantic": 1, "aesthete": 1},
            },
            {
                "id": "classical",
                "label": "Classical / jazz",
                "emoji": "🎷",
                "tags": ["craft", "patience", "filter-coffee"],
                "weights": {"aesthete": 2, "romantic": 1},
            },
            {
                "id": "hyperpop",
                "label": "Chaos hyperpop",
                "emoji": "⚡",
                "tags": ["chaos-energy", "parties", "bold-ideas"],
                "weights": {"spark": 2, "host": 1},
            },
        ],
    },
    {
        "id": "drink_alter_ego",
        "prompt": "Your coffee alter ego walks in. Who is it?",
        "options": [
            {
                "id": "espresso",
                "label": "Double espresso",
                "emoji": "⚡",
                "tags": ["espresso", "ship-fast", "direct"],
                "weights": {"builder": 2, "spark": 1},
            },
            {
                "id": "pourover",
                "label": "Slow pour-over",
                "emoji": "☕",
                "tags": ["filter-coffee", "craft", "patience"],
                "weights": {"aesthete": 2, "plotter": 1},
            },
            {
                "id": "iced",
                "label": "Iced everything",
                "emoji": "🧊",
                "tags": ["cold-coffee", "chill", "summer"],
                "weights": {"spark": 1, "romantic": 1, "host": 1},
            },
            {
                "id": "matcha",
                "label": "Matcha diplomat",
                "emoji": "🍵",
                "tags": ["matcha", "design", "calm-focus"],
                "weights": {"aesthete": 1, "host": 2},
            },
        ],
    },
    {
        "id": "party_role",
        "prompt": "At a Builder Pop-Up mixer, you’re usually…",
        "options": [
            {
                "id": "host",
                "label": "The connector",
                "emoji": "🤝",
                "tags": ["networking", "introductions", "people"],
                "weights": {"host": 2, "spark": 1},
            },
            {
                "id": "corner",
                "label": "Corner philosopher",
                "emoji": "🧠",
                "tags": ["deep-conversations", "ideas", "quiet-corners"],
                "weights": {"plotter": 2, "romantic": 1},
            },
            {
                "id": "dance",
                "label": "Dance-floor energy",
                "emoji": "🪩",
                "tags": ["music", "parties", "chaos-energy"],
                "weights": {"spark": 2, "host": 1},
            },
            {
                "id": "snacks",
                "label": "Snack scout",
                "emoji": "🥐",
                "tags": ["pastries", "foodie", "sharing"],
                "weights": {"host": 1, "aesthete": 1, "romantic": 1},
            },
        ],
    },
]

ARCHETYPES: dict[str, dict[str, Any]] = {
    "plotter": {
        "label": "Midnight Plotter",
        "blurb": (
            "You brew big ideas with a quiet cup. Deep chats, clever twists, "
            "and a corner table with an outlet — that’s home."
        ),
        "drink_hint": "Try a filter coffee or something cozy, not too sweet.",
        "tags": ["deep-conversations", "ai", "filter-coffee"],
    },
    "builder": {
        "label": "Ship-It Barista",
        "blurb": (
            "You’re here to build — demos, PRs, and espresso-level focus. "
            "Match you with fellow makers who ship before the ice melts."
        ),
        "drink_hint": "Double espresso or a strong cold coffee keeps the sprint alive.",
        "tags": ["hackathons", "startups", "espresso"],
    },
    "romantic": {
        "label": "Amélie of Kondapur",
        "blurb": (
            "You notice the little magic — latte foam hearts, bookstore finds, "
            "and the person reading alone who might want company."
        ),
        "drink_hint": "Something cozy with a pastry — Amélie would approve.",
        "tags": ["books", "whimsy", "people-watching"],
    },
    "aesthete": {
        "label": "Pour-Over Aesthete",
        "blurb": (
            "Craft over chaos. Clean design, patient pours, and conversations "
            "that sound like jazz solos."
        ),
        "drink_hint": "Slow pour-over or matcha — savor the ritual.",
        "tags": ["design", "craft", "filter-coffee"],
    },
    "spark": {
        "label": "Hyperpop Spark",
        "blurb": (
            "High voltage. You’re the plot twist in the room — bold ideas, "
            "loud playlists, zero boring tables."
        ),
        "drink_hint": "Iced everything or a fun seasonal special.",
        "tags": ["chaos-energy", "music", "bold-ideas"],
    },
    "host": {
        "label": "Table Host",
        "blurb": (
            "You turn strangers into a table. Intros, snacks, and the soft skill "
            "of making a hackathon feel like a dinner party."
        ),
        "drink_hint": "Shareable vibes — latte + a pastry to split.",
        "tags": ["networking", "people", "pastries"],
    },
}


def question_by_id(qid: str) -> dict[str, Any] | None:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    return None


def option_by_id(question: dict[str, Any], oid: str) -> dict[str, Any] | None:
    for opt in question["options"]:
        if opt["id"] == oid:
            return opt
    return None


def public_question(question: dict[str, Any], *, index: int, total: int) -> dict[str, Any]:
    return {
        "id": question["id"],
        "prompt": question["prompt"],
        "index": index,
        "total": total,
        "options": [
            {
                "id": o["id"],
                "label": o["label"],
                "emoji": o.get("emoji", ""),
                "choice_key": chr(65 + i),  # A, B, C, D
            }
            for i, o in enumerate(question["options"])
        ],
    }


def score_answers(answers: dict[str, str]) -> dict[str, Any]:
    weights: dict[str, int] = {}
    tags: list[str] = []
    detail: dict[str, dict[str, str]] = {}

    for q in QUESTIONS:
        oid = answers.get(q["id"])
        if not oid:
            continue
        opt = option_by_id(q, oid)
        if not opt:
            continue
        detail[q["id"]] = {
            "option_id": oid,
            "label": opt["label"],
        }
        tags.extend(opt.get("tags") or [])
        for arch, w in (opt.get("weights") or {}).items():
            weights[arch] = weights.get(arch, 0) + int(w)

    if not weights:
        arch_key = "host"
    else:
        arch_key = max(weights.items(), key=lambda kv: (kv[1], kv[0]))[0]

    arch = ARCHETYPES[arch_key]
    # Dedupe tags, keep order, fold archetype tags first
    seen: set[str] = set()
    ordered_tags: list[str] = []
    for t in list(arch.get("tags") or []) + tags:
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered_tags.append(t)

    return {
        "archetype": arch_key,
        "label": arch["label"],
        "blurb": arch["blurb"],
        "drink_hint": arch["drink_hint"],
        "tags": ordered_tags[:12],
        "answers": detail,
        "weights": weights,
    }


def next_question(answers: dict[str, str]) -> dict[str, Any] | None:
    for i, q in enumerate(QUESTIONS):
        if q["id"] not in answers:
            return public_question(q, index=i + 1, total=len(QUESTIONS))
    return None
