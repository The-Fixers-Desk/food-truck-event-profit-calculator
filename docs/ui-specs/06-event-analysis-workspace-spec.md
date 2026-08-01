# Event Analysis Workspace — Engineering Specification

## Document control

- **Product:** Food Truck Event Profit Calculator
- **Owner:** The Fixer’s Desk
- **Reference mockup:** `Event Analysis Workspace charcoal mockup`
- **Status:** Implementation blueprint
- **Source of truth order:** approved mockup → this specification → existing business logic

## Purpose

Evaluate one scenario through transparent revenue, cost, profit, margin, break-even, recommendation, and sensitivity information.

**Dominant task:** Decide whether the current event scenario is worth accepting.

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


## Header and scenario controls

- Breadcrumb: Saved events → event → Analysis.
- Header contains event name, explanatory copy, scenario selector, Duplicate scenario, and Compare scenarios.
- Scenario selector changes the active scenario without leaving the page.
- Duplicate creates a copy with `Copy` appended and opens it in edit mode.

## Workspace grid

Desktop uses a 280 px left information rail and a flexible analysis column with 16 px gap.

Left rail sections:

- Scenarios list with recommendation badges and `+ New scenario`.
- Event snapshot.
- Input summary with `Edit inputs`.

Analysis column:

- Five metric cards: Estimated revenue, Total costs, Estimated profit, Profit margin, Break-even buyers.
- Profitability summary.
- Decision checks.
- What changes the result.
- Sticky action bar.

## Calculation presentation

- Currency uses locale formatting with two decimals only when cents are meaningful; prominent totals may omit `.00`.
- Profit margin shows one decimal place.
- Break-even buyers always rounds up to the next whole buyer.
- Recommendation text is derived from the configured profit rule and must match the saved scenario result.
- Do not recompute with display-rounded inputs; use full-precision stored values.

## Profitability summary

- Positive state uses success border, check icon, and `Worth accepting`.
- Borderline and negative states use warning/danger variants with equivalent structure.
- Show the amount above or below the configured target.
- Cost breakdown is a segmented horizontal bar where segment widths are proportional to revenue.
- Each segment has label, amount, and percent. Net profit is visually distinct from costs.
- The visualization must have a textual equivalent for screen readers.

## Decision checks

Show minimum target, profit above/below target, margin status when applicable, and break-even attendance estimate. Values must be traceable to current inputs.

## Sensitivity panel

- Rank the highest drivers from strongest to weakest.
- Bars indicate relative influence, not absolute financial scale.
- Include plain-language impact labels such as High or Medium and an explanatory note.

## Actions and persistence

- `Edit scenario` returns to Event Inputs Wizard with current values preserved.
- Auto-save status appears only after successful local persistence.
- `Save scenario` forces an immediate save.
- `Duplicate` duplicates current scenario.
- `Compare` opens Scenario Comparison with current event preselected.

## Responsive behavior

- Tablet stacks left-rail cards above the analysis or uses a collapsible summary rail.
- Mobile shows event/scenario selector, metric strip, recommendation card, then detailed sections. Compare scenarios is the dominant bottom action.



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
