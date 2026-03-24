# Design System — Startup Research

## Product Context
- **What this is:** A web app that synthesizes everything known about a startup into a research brief
- **Who it's for:** Anyone curious about a startup — journalists, job seekers, founders, angel investors
- **Space/industry:** AI research tools (Perplexity, Exa, Harmonic) — but for the long tail, not VCs
- **Project type:** Web app with streaming report generation + shareable URLs

## Aesthetic Direction
- **Direction:** Editorial/Magazine — not a terminal, not a dashboard. A beautifully typeset document.
- **Decoration level:** Intentional — subtle texture on cards (fine noise grain), thin dividers. No gradients, no blobs, no atmospheric blurs.
- **Mood:** Reading a well-crafted analyst memo at night. Calm, authoritative, trustworthy. The content is the design.
- **Reference sites:** Stripe docs, The Verge (editorial feel). Deliberately NOT Bloomberg terminal or Harmonic's gradient fog.
- **Anti-patterns:** No purple gradients, no atmospheric blur effects, no 3-column icon grids, no centered-everything layouts, no decorative blobs.

## Typography
- **Display/Hero:** Instrument Serif — editorial authority, unexpected for a tech tool. Serifs signal "read me" not "use me." Our biggest creative risk.
- **Body:** Instrument Sans — pairs perfectly with Instrument Serif, clean at long reading lengths
- **UI/Labels:** Instrument Sans (same as body, weight 500-600 for emphasis)
- **Data/Tables:** Geist Mono — tabular-nums for funding amounts, dates, metrics
- **Code:** Geist Mono
- **Loading:** Google Fonts `https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital,wght@0,400;1,400&display=swap`
- **Scale:**
  - Hero: 48px / 1.1 line-height / -0.02em tracking
  - Section title: 14px / 600 weight
  - Body: 14px / 1.6 line-height
  - Mono data: 13px / 0.02em tracking
  - Labels: 11px / uppercase / 0.06-0.08em tracking
  - Section numbers: 11px mono / var(--text-faint)

## Color

### Dark Mode (default)
- **Approach:** Restrained — 1 warm accent + warm grays. Not blue-black (cold/corporate), but charcoal-warm (inviting).
- **Background:** #0f0f0f (near-black, warm)
- **Surface:** #1a1a1a (cards, section cards)
- **Surface hover:** #222222
- **Border:** #2a2a2a (subtle dividers)
- **Primary text:** #e8e4de (warm off-white, NOT pure #ffffff)
- **Muted text:** #8a8478 (warm gray)
- **Faint text:** #5a5650 (section numbers, tertiary info)
- **Accent:** #d4a853 (warm gold — signals quality/authority)
- **Accent hover:** #e0ba6a
- **Accent subtle:** rgba(212, 168, 83, 0.1) (badge backgrounds)
- **Semantic:** success #4a9e6b, warning #c4943a, error #c45c4a, info #5a8fb8

### Light Mode
- **Background:** #f5f3ef
- **Surface:** #ffffff
- **Surface hover:** #f0ede8
- **Border:** #e0dcd5
- **Primary text:** #1a1a1a
- **Muted text:** #6b6560
- **Faint text:** #a09a92
- **Accent:** #b08930
- **Accent hover:** #967425
- **Accent subtle:** rgba(176, 137, 48, 0.08)

## Spacing
- **Base unit:** 8px
- **Density:** Comfortable — sections breathe, not cramped like a dashboard
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)
- **Section card padding:** 16px vertical, 20px horizontal
- **Section gap:** 16px between cards
- **Major section dividers:** 48px margin + 1px border line

## Layout
- **Approach:** Grid-disciplined, single column
- **Report content width:** max 720px (like a great article)
- **Wide container:** max 960px (for landing/hero)
- **Grid:** Single column for reports. No sidebar.
- **Border radius:** sm: 4px (inputs, badges), md: 8px (cards, buttons), lg: 12px (search box, hero elements)

## Motion
- **Approach:** Minimal-functional — quiet and purposeful
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) hover states, short(150ms) collapse/expand, medium(200ms) section fade-in, long(300ms) theme transition
- **Section streaming:** Sections fade in with 200ms ease-out as they arrive via SSE
- **Collapsible sections:** 150ms height transition
- **No:** scroll-driven animations, bouncing, parallax, decorative motion

## Component Patterns

### Search Box
- Surface background, 1px border, lg border-radius
- Input + button side by side
- Border turns accent color on focus
- Button: accent background, dark text, 600 weight

### Section Cards
- Surface background, 1px border, md border-radius
- Section number (mono, faint) + title (sans, 600 weight)
- Chevron indicator for collapse state
- Hover: border lightens to #3a3a3a

### Funding Tables
- Full width, collapse borders
- Header: muted text, 11px uppercase, 0.06em tracking
- Amount column: mono font, accent color
- Date column: mono font, muted color
- 1px border-bottom on rows

### Verdict Badges
- Inline-block, sm border-radius, 12px 600 weight
- Strong: success color on success-subtle bg
- Growing: warning color on warning-subtle bg
- Early: info color on info-subtle bg

### Rate Limit Message
- Centered layout, muted text
- Countdown: mono font, 24px, accent color
- Reference to last completed report

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-23 | Editorial/Magazine aesthetic | Differentiate from terminal-style AI tools; audience is general public, not VCs |
| 2026-03-23 | Instrument Serif for display | Creative risk — serifs rare in AI tools, signals editorial trust |
| 2026-03-23 | Warm gold accent #d4a853 | Quality/authority signal without gaming connotation; warm palette cohesion |
| 2026-03-23 | No atmospheric effects | Content IS the design; deliberately opposite of Harmonic's gradient fog |
| 2026-03-23 | 720px content width | Optimal reading length for long-form research briefs |
