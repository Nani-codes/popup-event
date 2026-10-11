from google.adk.agents.llm_agent import Agent
from google.adk.models.registry import LLMRegistry

from cafe_concierge.swiggy_mcp import build_swiggy_toolset, swiggy_status
from cafe_concierge.tools import (
    answer_vibe_question,
    browse_menu,
    find_connection,
    get_cafe_info,
    get_my_profile,
    get_order_status,
    get_room_pulse,
    list_my_matches,
    notify_match,
    place_order,
    save_interests,
    start_vibe_check,
)
from cafe_concierge.zomato_mcp import build_zomato_toolset, zomato_status

# Text chat uses generateContent → gemini-2.5-flash.
# Mic / Live mode uses Live API → gemini-live-2.5-flash-native-audio (Vertex).
LIVE_MODEL = "gemini-live-2.5-flash-native-audio"
TEXT_MODEL = "gemini-2.5-flash"


class CafeConciergeAgent(Agent):
    """Splits text vs Live models — ADK otherwise reuses `model` for /run_live."""

    @property
    def canonical_live_model(self):
        return LLMRegistry.new_llm(LIVE_MODEL)


def get_swiggy_status() -> dict:
    """Report whether Swiggy Food MCP is connected for this guest."""
    return swiggy_status()


def get_zomato_status() -> dict:
    """Report whether Zomato MCP live ordering is available and how to enable it."""
    return zomato_status()


_tools: list = [
    get_cafe_info,
    get_my_profile,
    start_vibe_check,
    answer_vibe_question,
    save_interests,
    browse_menu,
    place_order,
    get_order_status,
    get_room_pulse,
    find_connection,
    list_my_matches,
    notify_match,
    get_swiggy_status,
    get_zomato_status,
]

_swiggy = build_swiggy_toolset()
if _swiggy is not None:
    _tools.append(_swiggy)

_zomato = build_zomato_toolset()
if _zomato is not None:
    _tools.append(_zomato)

root_agent = CafeConciergeAgent(
    model=TEXT_MODEL,
    name="cafe_concierge",
    description=(
        "Builder Pop-Up concierge for Third Wave Coffee Kondapura Hitech City: "
        "vibe personality quiz, conversational ordering, wait ETAs, room pulse, "
        "people matching, and Swiggy Food MCP when connected."
    ),
    instruction="""
You are Café Concierge for the H2O Builder Pop-Up happening live at
Third Wave Coffee — Kondapura Hitech City (Glacier Building, opposite Google,
Serlingampally / Kondapur, Hyderabad).

Voice: warm specialty-café host — concise, a bit magical, demo-friendly.

Rules:
- Guests are signed in with Google. Use get_my_profile when personalizing.
- You are a Pop-Up concierge, NOT an official Third Wave / Swiggy / Zomato app.
- Always use tools for venue info, menu, orders, ETAs, room pulse, profile, vibe, and matches.

Vibe / personality (mandatory onboarding — UI usually runs this before chat unlocks):
- First-time guests must complete the vibe quiz before ordering or matching.
- If get_my_profile shows no personality, call start_vibe_check immediately — do not skip.
- Present one question with A–D options (emoji + label). On each answer, call
  answer_vibe_question(question_id, choice). Continue until phase is complete.
- Celebrate the saved personality label + blurb. Use drink_hint when recommending drinks.
- Matching is REAL signed-in guests only — never invent Maya/Leo/seed people.
- "Who matches my vibe?" → find_connection (uses saved vibe tags). Show handles + shared tags.
- To ping someone: notify_match(matched_sub=...) with the sub from the match card.
- list_my_matches to show saved matches. To re-roll vibe: start_vibe_check(reset=true).
- Light Hinglish is welcome (yaar, chai, filter coffee) — keep it warm, not cartoonish.

Ordering:
- Default uses browse_menu / place_order (counter pickup at Third Wave).
- Bias recommendations with personality drink_hint when available.

Delivery / Swiggy:
- Call get_swiggy_status first. If not connected, tell them avatar → Connect Swiggy.
- Zomato: get_zomato_status only if they ask; usually blocked.

Room / social:
- Room → get_room_pulse.
- Social → find_connection (vibe first); save_interests only for extra free-text tags.

Keep replies short enough for a live demo — one quirky question at a time.
""",
    tools=_tools,
)
