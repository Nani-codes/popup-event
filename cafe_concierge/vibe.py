"""Quirky Hinglish vibe quiz → café personality for matching & drink tips."""

from __future__ import annotations

from typing import Any

# Each choice contributes tags + archetype weights.
QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "movie",
        "prompt": "Late-night rewatch, chai in hand — kaunsi movie energy hai tumhari?",
        "options": [
            {
                "id": "inception",
                "label": "Inception brain-maze",
                "emoji": "🌀",
                "tags": ["deep-conversations", "ai", "plot-twists"],
                "weights": {"plotter": 2, "builder": 1},
            },
            {
                "id": "ddlj",
                "label": "DDLJ train-wave romance",
                "emoji": "🚂",
                "tags": ["whimsy", "bollywood", "feel-good"],
                "weights": {"romantic": 2, "host": 1},
            },
            {
                "id": "3idiots",
                "label": "3 Idiots jugaad energy",
                "emoji": "🎒",
                "tags": ["jugaad", "friends", "startups"],
                "weights": {"builder": 2, "spark": 1},
            },
            {
                "id": "rrr",
                "label": "RRR mass entry",
                "emoji": "🔥",
                "tags": ["chaos-energy", "bold-ideas", "hype"],
                "weights": {"spark": 2, "host": 1},
            },
        ],
    },
    {
        "id": "weekend",
        "prompt": "Kondapur weekend plan — full scene kya hoga?",
        "options": [
            {
                "id": "hackathon",
                "label": "Hackathon + Maggi at 3am",
                "emoji": "💻",
                "tags": ["hackathons", "ai", "startups"],
                "weights": {"builder": 2, "plotter": 1},
            },
            {
                "id": "biryani",
                "label": "Biryani run, then chill",
                "emoji": "🍛",
                "tags": ["foodie", "hyderabad", "friends"],
                "weights": {"host": 2, "romantic": 1},
            },
            {
                "id": "bookstore",
                "label": "Bookstore + filter coffee",
                "emoji": "📚",
                "tags": ["books", "filter-coffee", "quiet-corners"],
                "weights": {"romantic": 2, "aesthete": 1},
            },
            {
                "id": "drive",
                "label": "ORR long drive + chai",
                "emoji": "🛣️",
                "tags": ["travel", "chai", "wind-down"],
                "weights": {"romantic": 1, "plotter": 1, "aesthete": 1},
            },
        ],
    },
    {
        "id": "playlist",
        "prompt": "Earbuds on, laptop open — abhi kya baja raha hai?",
        "options": [
            {
                "id": "lofi",
                "label": "Lo-fi / deep work",
                "emoji": "🎧",
                "tags": ["deep-work", "coffee", "headphones-on"],
                "weights": {"plotter": 2, "builder": 1},
            },
            {
                "id": "arijit",
                "label": "Arijit / soft Bollywood",
                "emoji": "🎤",
                "tags": ["bollywood", "feelings", "chai"],
                "weights": {"romantic": 2, "host": 1},
            },
            {
                "id": "rahman",
                "label": "Rahman / classic vibes",
                "emoji": "🎹",
                "tags": ["craft", "patience", "filter-coffee"],
                "weights": {"aesthete": 2, "romantic": 1},
            },
            {
                "id": "punjabi",
                "label": "Punjabi / party mix",
                "emoji": "🕺",
                "tags": ["chaos-energy", "parties", "friends"],
                "weights": {"spark": 2, "host": 1},
            },
        ],
    },
    {
        "id": "drink_alter_ego",
        "prompt": "Tumhara café alter-ego kaun? Be honest yaar.",
        "options": [
            {
                "id": "espresso",
                "label": "Double espresso, no bakwaas",
                "emoji": "⚡",
                "tags": ["espresso", "ship-fast", "direct"],
                "weights": {"builder": 2, "spark": 1},
            },
            {
                "id": "filter",
                "label": "South Indian filter coffee",
                "emoji": "☕",
                "tags": ["filter-coffee", "craft", "tradition"],
                "weights": {"aesthete": 2, "plotter": 1},
            },
            {
                "id": "cutting",
                "label": "Cutting chai + gossip",
                "emoji": "🫖",
                "tags": ["chai", "people", "adda"],
                "weights": {"host": 2, "romantic": 1},
            },
            {
                "id": "cold",
                "label": "Cold coffee / iced everything",
                "emoji": "🧊",
                "tags": ["cold-coffee", "chill", "summer"],
                "weights": {"spark": 1, "romantic": 1, "aesthete": 1},
            },
        ],
    },
    {
        "id": "party_role",
        "prompt": "Builder Pop-Up pe tum usually kaun ho?",
        "options": [
            {
                "id": "host",
                "label": "Connector — sabko milata hoon",
                "emoji": "🤝",
                "tags": ["networking", "introductions", "people"],
                "weights": {"host": 2, "spark": 1},
            },
            {
                "id": "corner",
                "label": "Corner wala deep talk",
                "emoji": "🧠",
                "tags": ["deep-conversations", "ideas", "quiet-corners"],
                "weights": {"plotter": 2, "romantic": 1},
            },
            {
                "id": "demo",
                "label": "Demo pe demo — ship karo",
                "emoji": "🚀",
                "tags": ["hackathons", "demos", "ai"],
                "weights": {"builder": 2, "spark": 1},
            },
            {
                "id": "snacks",
                "label": "Snack scout — samosa first",
                "emoji": "🥟",
                "tags": ["foodie", "pastries", "sharing"],
                "weights": {"host": 1, "aesthete": 1, "romantic": 1},
            },
        ],
    },
]

ARCHETYPES: dict[str, dict[str, Any]] = {
    "plotter": {
        "label": "Midnight Plotter",
        "blurb": (
            "Badi ideas, chhoti baatein, corner table with a plug — yeh tumhara zone hai. "
            "Deep chats, clever twists, filter coffee optional but recommended."
        ),
        "drink_hint": "Filter coffee lo, ya kuch cozy — zyada meetha mat.",
        "tags": ["deep-conversations", "ai", "filter-coffee"],
    },
    "builder": {
        "label": "Jugaad Builder",
        "blurb": (
            "Demo pe demo, Maggi at 3am, espresso-level focus. "
            "Tum fellow makers ke saath ship karte ho — ice melt hone se pehle."
        ),
        "drink_hint": "Double espresso ya strong cold coffee — sprint chalega.",
        "tags": ["hackathons", "startups", "espresso"],
    },
    "romantic": {
        "label": "Kondapur Softie",
        "blurb": (
            "Chhoti-chhoti khushiyaan notice karte ho — latte art, bookstore finds, "
            "aur woh person jo akela padh raha hai. Soft Bollywood soul, basically."
        ),
        "drink_hint": "Kuch cozy + pastry. DDLJ vibes, no judgment.",
        "tags": ["books", "bollywood", "feel-good"],
    },
    "aesthete": {
        "label": "Filter Coffee Aesthete",
        "blurb": (
            "Craft over chaos. Clean design, patient pours, aur baatein jo jazz solo jaisi "
            "lage. South Indian filter coffee is your love language."
        ),
        "drink_hint": "Filter coffee slow-sip, ya matcha if you're feeling fancy.",
        "tags": ["design", "craft", "filter-coffee"],
    },
    "spark": {
        "label": "Full Mass Spark",
        "blurb": (
            "High voltage. Room ka plot twist tum ho — bold ideas, loud playlists, "
            "zero boring tables. RRR entry energy, soft launch optional."
        ),
        "drink_hint": "Iced everything, ya jo bhi seasonal special chal raha hai.",
        "tags": ["chaos-energy", "music", "bold-ideas"],
    },
    "host": {
        "label": "Adda Host",
        "blurb": (
            "Strangers ko table bana dete ho. Intros, snacks, cutting-chai gossip — "
            "hackathon ko dinner party feel dilana tumhara soft skill hai."
        ),
        "drink_hint": "Shareable vibes — latte + pastry to split, ya cutting chai mood.",
        "tags": ["networking", "people", "chai"],
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
