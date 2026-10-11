# Design System — Café Concierge

<!-- impeccable:design-schema 1 -->

## Overview

Presentation UI for the Builder Pop-Up café agent, user-pinned to a **Google Gemini product** aesthetic: light Material-like chrome, multicolor spark gradient, stage-legible chat with a live ticket panel. Demo venue context is Third Wave Kondapur; not an official Google or Third Wave product.

## Color

| Role | Value | Use |
|---|---|---|
| Canvas | `#F8F9FA` | Page ground |
| Surface | `#FFFFFF` | Chat panel, cards |
| Ink | `#202124` | Primary text |
| Secondary | `#5F6368` | Meta, venue chip |
| Line | `#E8EAED` | Borders |
| Gemini blue | `#4285F4` | Spark stop |
| Gemini purple | `#9B72CB` | Spark / send |
| Gemini coral | `#D96570` | Spark stop |
| Gemini amber | `#F4B400` | Spark stop |
| Teal | `#34A853` | Live venue dot |

**Strategy:** Restrained neutrals + Gemini multicolor as the only saturated system (spark, send, wordmark clip, ticket id). Soft mesh washes on the canvas.

## Typography

- **UI / body:** Roboto Flex + Roboto (Google product association; intentional over “distinctive indie” faces).
- Product title uses gradient clip on the same family at ~1.25rem / 600.
- Ticket body leans mono-feel via Roboto Flex for receipt clarity.

## Layout

- **Mobile-first (phone-primary):** chat owns the viewport; sticky compact topbar; composer in the thumb zone with safe-area insets; Live ticket + Room pulse open as a bottom sheet from a fixed peek bar.
- Account actions (Connect Swiggy / Sign out) live in an avatar menu — not a crowded chip row.
- Tablet (≥720px): sheet chrome hides; chat stays full-width.
- Desktop (≥960px): max width ~1200px; chat (1fr) + side rail (300px) with ticket + pulse visible.
- Chat panel: rounded glass-white card; horizontal-scroll suggestion chips on phone; wrap on larger screens.

## Components

- **Spark:** SVG 4-point starburst with Gemini gradient (not a Google trademark logo).
- **Chips:** pill suggestions for demo script.
- **Composer:** pill field; focus ring is Gemini gradient; circular gradient send.
- **Bubbles:** assistant white card; user soft blue `#E8F0FE`.
- **Ticket:** dashed receipt plate; order id gradient text.

## Motion

- Spark entrance (scale/rotate/blur settle).
- Panel and message fade/slide with cubic ease-out.
- Chip hover lift; send scale on hover.

## Voice

Warm café host in product copy; UI chrome is Google AI calm. Fine print discloses demo / non-official status.
