# Business Event Inputs Wizard — Acceptance Checklist

## Document control

- **Product:** Food Truck Event Profit Calculator
- **Owner:** The Fixer’s Desk
- **Artifact:** Acceptance checklist / definition of done
- **Reference:** Approved Business Event Inputs Wizard mockup and corresponding engineering specification
- **Result rule:** Every item must pass before the screen is accepted.

## How to use this checklist

Evaluate each line as an objective **PASS** or **FAIL** against the approved reference mockup, engineering specification, and functioning build. A visual approximation is not sufficient. Any failure requires correction and re-review.

## Global visual and implementation checks

- [ ] **PASS / FAIL:** The implemented screen matches the approved reference mockup in structure, visual hierarchy, density, and overall composition.
- [ ] **PASS / FAIL:** No navy or blue cast appears in the canvas, sidebar, cards, fields, gradients, shadows, or overlays.
- [ ] **PASS / FAIL:** The charcoal token family is used: canvas `#111315`, sidebar `#121416`, surface `#181B1D`, elevated surface `#1E2123`, inset surface `#151719`.
- [ ] **PASS / FAIL:** Copper `#C47A3A` is the primary accent; green, warning, and danger colors are reserved for their semantic states.
- [ ] **PASS / FAIL:** Text hierarchy, type weights, line heights, and tabular numerals match the specification.
- [ ] **PASS / FAIL:** Standard radii, borders, dividers, spacing tokens, and control heights are consistent with the shared design system.
- [ ] **PASS / FAIL:** Every interactive control has visible default, hover, pressed, focus-visible, disabled, and loading states where applicable.
- [ ] **PASS / FAIL:** Keyboard focus uses a clearly visible copper focus ring and never relies on color alone.
- [ ] **PASS / FAIL:** Motion is 150–200 ms, uses ease-out, and respects `prefers-reduced-motion`.
- [ ] **PASS / FAIL:** Existing calculations, routes, persistence, imports/exports, and workflows remain functional unless the specification explicitly changes them.
- [ ] **PASS / FAIL:** Reusable shell, button, card, field, badge, status, and responsive-layout components are used rather than duplicated one-off markup.
- [ ] **PASS / FAIL:** No new content, actions, or states have been invented beyond the approved mockup and specification.

## Shared shell checks

- [ ] **PASS / FAIL:** At desktop widths, the sidebar is 280 px wide and the top bar is 64 px high.
- [ ] **PASS / FAIL:** Main content is centered and does not exceed 1280 px.
- [ ] **PASS / FAIL:** Desktop content padding is 32 px, compact desktop/tablet padding is 24 px, and mobile padding is 16 px.
- [ ] **PASS / FAIL:** Sidebar branding remains at the top and the user menu remains pinned to the bottom.
- [ ] **PASS / FAIL:** Breadcrumbs appear on the left of the top bar; search, notifications, and help appear on the right.
- [ ] **PASS / FAIL:** Below 1024 px, the persistent sidebar is replaced by the approved top app bar and drawer pattern.
- [ ] **PASS / FAIL:** The page never introduces unintended horizontal scrolling.

## Accessibility and responsive checks

- [ ] **PASS / FAIL:** Text, icons, state borders, and focus indicators meet WCAG 2.2 AA contrast.
- [ ] **PASS / FAIL:** All interactive controls are keyboard reachable in visual order.
- [ ] **PASS / FAIL:** Icon-only controls have accessible names.
- [ ] **PASS / FAIL:** Dynamic status, save, validation, and calculation changes are announced through an appropriate polite live region.
- [ ] **PASS / FAIL:** Validation messages are programmatically associated with fields and announced on submission.
- [ ] **PASS / FAIL:** Recommendation and status states include text labels in addition to color and iconography.
- [ ] **PASS / FAIL:** Desktop (`>=1280 px`), tablet (`768–1279 px`), and mobile (`<768 px`) layouts match the specified transformations.
- [ ] **PASS / FAIL:** Full-width primary actions and stacked controls are used on mobile where specified.


## Event Inputs Wizard-specific acceptance criteria

- [ ] **PASS / FAIL:** `New analysis` is the active sidebar item.
- [ ] **PASS / FAIL:** The wizard contains Event basics, Revenue inputs, Operating costs, Conditions, and Review in that order.
- [ ] **PASS / FAIL:** Step 1 displays completed styling and Revenue inputs displays active styling in the reference state.
- [ ] **PASS / FAIL:** The page title, description, and `Step 2 of 5` indicator match the approved hierarchy.
- [ ] **PASS / FAIL:** Revenue method options are mutually exclusive: `Use average ticket × buyers` and `Use custom total sales`.
- [ ] **PASS / FAIL:** Only fields relevant to the selected revenue method are shown.
- [ ] **PASS / FAIL:** Scenario name and event name remain separate and persist independently.
- [ ] **PASS / FAIL:** Event date, attendance, average ticket, conversion rate, expected buyers, and service hours validate according to the specification.
- [ ] **PASS / FAIL:** Expected buyers and derived revenue use the approved rounding and calculation rules.
- [ ] **PASS / FAIL:** Invalid submissions preserve entered values and selected options.
- [ ] **PASS / FAIL:** The Current Scenario Snapshot displays estimated revenue, food-cost method, crew size, and travel distance.
- [ ] **PASS / FAIL:** Snapshot values reflect valid persisted scenario data and update after valid changes.
- [ ] **PASS / FAIL:** The event-specific note clearly states that these inputs apply only to this scenario and multiple scenarios may be saved for one event.
- [ ] **PASS / FAIL:** Draft progress auto-saves locally and restores to the same event, scenario, and active step.
- [ ] **PASS / FAIL:** `Save as draft` persists the incomplete scenario without marking analysis complete.
- [ ] **PASS / FAIL:** `Continue` validates before moving forward and `Back` never discards valid data.
- [ ] **PASS / FAIL:** Review presents all event-specific assumptions before final calculation.
- [ ] **PASS / FAIL:** Mobile uses a single-column form, compact progress, and sticky full-width Continue action.

## Final acceptance

- [ ] **PASS / FAIL:** No unresolved visual deviations remain when the implementation is reviewed side by side with the approved mockup.
- [ ] **PASS / FAIL:** No functional regression exists in any workflow touched by this screen.
- [ ] **PASS / FAIL:** All automated tests, keyboard checks, responsive checks, and manual acceptance checks pass.
- [ ] **PASS / FAIL:** The screen feels visually and behaviorally cohesive with the other nine product screens.
- [ ] **PASS / FAIL:** Product owner approval has been recorded.
