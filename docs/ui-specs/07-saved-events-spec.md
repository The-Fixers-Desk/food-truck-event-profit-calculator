# Saved Events — Engineering Specification

## Document control

- **Product:** Food Truck Event Profit Calculator
- **Owner:** The Fixer’s Desk
- **Reference mockup:** `Saved Events charcoal mockup`
- **Status:** Implementation blueprint
- **Source of truth order:** approved mockup → this specification → existing business logic

## Purpose

Provide a searchable, filterable event library where users can reopen, compare, and manage previous work.

**Dominant task:** Open a saved event or compare its scenarios.

The approved mockup defines visual intent. This document removes implementation ambiguity for layout, spacing, typography, colors, component behavior, responsive behavior, and interaction rules.


## Shared design tokens

These tokens are normative across all ten screens. Do not substitute blue or navy surfaces.

| Token | Value | Use |
|---|---:|---|
| `color.canvas` | `#111315` | Application and presentation background |
| `color.sidebar` | `#121416` | Persistent navigation rail |
| `color.surface` | `#181B1D` | Default cards, fields, and panels |
| `color.surfaceElevated` | `#1E2123` | Hovered, selected, or emphasized surfaces |
| `color.surfaceInset` | `#151719` | Inset summaries and nested groups |
| `color.border` | `#34383A` | Default 1 px borders and dividers |
| `color.borderStrong` | `#4A4E50` | Focused and high-emphasis boundaries |
| `color.textPrimary` | `#F4F2EE` | Headlines and primary labels |
| `color.textSecondary` | `#B8B8B6` | Descriptions and metadata |
| `color.textMuted` | `#85898B` | Disabled, tertiary, and helper text |
| `color.copper` | `#C47A3A` | Primary accent and primary actions |
| `color.copperHover` | `#D48646` | Hover state for primary actions |
| `color.copperPressed` | `#A95F2C` | Pressed state for primary actions |
| `color.success` | `#4FAE5A` | Positive recommendations and saved states |
| `color.warning` | `#D9902F` | Borderline states and cautions |
| `color.danger` | `#C95545` | Destructive actions and negative outcomes |
| `radius.sm` | `8px` | Inputs, chips, and compact controls |
| `radius.md` | `12px` | Standard cards and panels |
| `radius.lg` | `16px` | Large feature panels only |
| `space.1` | `4px` | Micro spacing |
| `space.2` | `8px` | Icon gaps and compact padding |
| `space.3` | `12px` | Control padding and row gaps |
| `space.4` | `16px` | Card padding on compact layouts |
| `space.5` | `24px` | Standard card padding |
| `space.6` | `32px` | Section spacing and desktop gutters |
| `space.7` | `48px` | Large page rhythm |
| `shadow.focus` | `0 0 0 3px rgba(196,122,58,.28)` | Keyboard focus ring |

### Typography

Use Inter, system-ui, or the existing product sans-serif. Use tabular numerals for currency, counts, percentages, dates, and calculations.

| Style | Desktop | Weight | Line height |
|---|---:|---:|---:|
| Display / page title | 40px | 700 | 1.12 |
| Section title | 24px | 650 | 1.2 |
| Card title | 18px | 650 | 1.3 |
| Body | 15px | 400 | 1.55 |
| Label | 13px | 600 | 1.35 |
| Metadata | 12px | 400 | 1.4 |
| Eyebrow | 12px uppercase | 700 | 1.2 |

### Global interaction rules

- Every interactive element must have default, hover, pressed, focus-visible, disabled, and loading states.
- Focus-visible uses `shadow.focus`; never rely on color alone.
- Primary actions use copper fill and white text. Secondary actions use transparent or `surface` fill with a 1 px border.
- Icons are 20 px by default, 16 px in compact controls, and 24–32 px in feature or state illustrations.
- Default control height is 40 px; prominent primary buttons may be 44 px.
- Motion duration is 150–200 ms with ease-out. Respect `prefers-reduced-motion`.
- All destructive actions require explicit confirmation and describe the scope of deletion.



## Shell requirements

- Desktop sidebar width: **280 px**.
- Desktop top bar height: **64 px**.
- Main content maximum width: **1280 px**, centered within available shell space.
- Desktop horizontal content padding: **32 px**; compact desktop/tablet: **24 px**; mobile: **16 px**.
- Standard vertical section spacing: **32 px**.
- Sidebar branding remains at the top and user menu remains pinned to the bottom.
- Top bar places breadcrumbs on the left and search, notifications, and help on the right.
- At widths below 1024 px, replace the persistent sidebar with a top app bar and drawer.


## Header and controls

- Sidebar active item: Saved events.
- Eyebrow: `EVENT LIBRARY`.
- Title: `Your saved events`.
- Header controls: Filters, Sort, New analysis.
- Search may use the global top-bar search; filters are local to this page.

## Status filters

- Chips: All events, Worth it, Borderline, Not worth it.
- Each chip displays a count.
- Active chip uses copper fill; inactive chips use bordered surfaces.
- Multiple recommendation filters are not combined; one status filter is active at a time.

## Summary panel

Show Saved events, Total scenarios, and Recently updated. Counts derive from the same filtered dataset only when explicitly labeled; the approved mockup uses library-wide totals.

## Desktop table

Columns:

1. Event name
2. Date
3. Location
4. Scenarios
5. Last updated
6. Recommendation
7. Actions

- Header remains visible when the table scrolls within a constrained viewport.
- Event row minimum height: 56 px.
- Event name may wrap to two lines; all other cells remain compact.
- Recommendation uses text + icon + status color.
- Actions: Open, Compare, chevron/details.
- Compare is disabled or hidden for events with fewer than two scenarios.

## Sorting and pagination

- Default sort: Last updated descending.
- Support Event date, Event name, Last updated, and Recommendation.
- Page size: 25 by default; mockup may show 5 rows for presentation.
- Preserve filter, search, sort, and page in the URL query string.

## Empty states

- No library data: `No saved events yet` with `Start first analysis`.
- No filter results: `No events match these filters` with `Clear filters`.
- Search term remains visible when no results are found.

## Responsive behavior

- Tablet uses a reduced table or stacked rows with primary metadata visible.
- Mobile converts each event into a card showing name, date/location, scenario count, updated time, recommendation, and chevron. Open is the card action; Compare appears in an overflow menu when valid.



## Responsive breakpoints

- **Desktop:** `>= 1280 px` — full shell, maximum content width, multi-column layout.
- **Compact desktop / tablet:** `768–1279 px` — drawer or narrow rail as space requires; reduce columns and card density.
- **Mobile:** `< 768 px` — single-column content, top app bar, full-width primary actions, stacked controls.
- Do not horizontally scroll the page. Only comparison tables or data grids may use an explicitly labeled horizontal scroll region when no accessible stacked alternative is viable.



## Accessibility requirements

- Meet WCAG 2.2 AA contrast for text, icons, borders that convey state, and focus indicators.
- All controls are keyboard reachable in visual order.
- Provide accessible names for icon-only controls and announce dynamic calculation/status changes with a polite live region.
- Tables must retain semantic headers on desktop; mobile transformations must preserve row labels programmatically.
- Recommendation states must include text labels in addition to color and iconography.
- Validation messages must be associated with their fields using `aria-describedby` and announced on submit.


## Implementation constraints

- Preserve all existing routes, calculations, persistence, imports/exports, and workflows unless this specification explicitly changes presentation behavior.
- Build reusable shell, button, card, field, badge, status, data-row, and responsive-layout components.
- Do not introduce new dependencies solely to reproduce simple visual effects.
- The implementation must not invent content, actions, or states that are absent from the approved mockup or this specification.
