# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: plain HTML/CSS/JS frontend + Python ADK agent API (`adk api_server` / existing `cafe_concierge`). Chosen for hackathon speed with room for a high-craft presentation surface; no React/Next scaffold required today.

## Users

Primary: Builder Pop-Up guests at Third Wave Coffee Kondapur who chat to order, check the room, and optionally find people to talk to. Secondary (same UI): judges and audience watching a stage demo — the interface must read clearly projected and feel event-native.

## Product Purpose

Café Concierge is an AI café host for the H2O Builder Pop-Up. Guests converse to get menu recommendations, place demo orders with ETAs, feel the room pulse, and get opt-in icebreakers. Success = a 90-second live demo that produces a real-looking ticket and a memorable “how did it know?” moment.

## Positioning

Not a generic chatbot and not an official Third Wave app — a Pop-Up concierge tied to this venue and this event, with tools for menu, orders, room intelligence, and people matching in one session.

## Operating Context

Live café / hackathon floor at Third Wave Coffee — Kondapura Hitech City (Glacier Building, opposite Google). Demo often projected or shared on a laptop. Backend: Google ADK Python agent on Vertex (`gemini-2.5-flash` for text). Presentation surface replaces `adk web` for the show.

## Capabilities and Constraints

- Capabilities: conversational browse/order, order status, room pulse, find connection, venue info (tool-backed).
- Constraints: demo menu/prices are synthetic INR; not real POS or payments; opt-in matches are seeded demo patrons; Live/mic uses a different Vertex model — presentation UI should use text chat.
- Open: exact deploy host for the custom UI (local laptop for today is fine).

## Brand Commitments

- Event: H2O Builder Pop-Up
- Venue reference: Third Wave Coffee Kondapur (usecase setting; not official TWC product)
- Product name: Café Concierge
- Voice: warm specialty-café host — concise, a bit magical, demo-friendly
- **Presentation UI (user-pinned):** Google Gemini product aesthetic — multicolor spark gradient, clean Material-like surfaces, light AI-product chrome. Not an official Google product; no Google/Gemini trademarks or logos as brand marks. Approximate the product language only.

## Evidence on Hand

- Agent package: `cafe_concierge/`
- Design spec: `docs/superpowers/specs/2026-10-11-cafe-concierge-design.md`
- Venue page: https://stores.thirdwavecoffeeroasters.com/store-pages/third-wave-coffee-kondapura-hitech-city-hyderabad
- No official H2O / Third Wave brand assets or logo files in-repo yet — do not invent trademarked marks; use event-native typography and color without claiming partnership.

## Product Principles

1. Demo-first: every screen serves a 90-second story (order → pulse → match).
2. Tool-truth: never invent menu, ETA, or people outside the agent tools.
3. Stage-legible: large type, clear hierarchy, readable from a few feet away.
4. Venue-honest: Kondapur / Pop-Up context is real; commercial claims stay labeled demo.
5. Fast craft: beautiful enough to win the room, simple enough to ship today.

## Accessibility & Inclusion

Prefer high contrast for projection; large touch targets for laptop/trackpad demo; no critical info only in color or motion.
