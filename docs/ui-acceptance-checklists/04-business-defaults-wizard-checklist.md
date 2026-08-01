# Business Defaults Wizard — Acceptance Checklist

## Document control

- **Product:** Food Truck Event Profit Calculator
- **Owner:** The Fixer’s Desk
- **Artifact:** Acceptance checklist / definition of done
- **Reference:** Approved Business Defaults Wizard mockup and corresponding engineering specification
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


## Business Defaults Wizard-specific acceptance criteria

- [ ] **PASS / FAIL:** `Business defaults` is the active sidebar item.
- [ ] **PASS / FAIL:** The first-use progress indicator shows Setup completed, Defaults active, and Dashboard upcoming.
- [ ] **PASS / FAIL:** The wizard contains exactly five sections in the specified order: Revenue assumptions, Food cost method, Profit rule, Operating assumptions, Review.
- [ ] **PASS / FAIL:** Completed, active, and upcoming steps use the approved success, copper, and neutral treatments.
- [ ] **PASS / FAIL:** The desktop step column is 312 px, the form panel is at least 560 px, and the gap is 20 px.
- [ ] **PASS / FAIL:** Revenue and food-cost methods use mutually exclusive card-radio controls.
- [ ] **PASS / FAIL:** The Profit Rule question and its two options match the specification exactly.
- [ ] **PASS / FAIL:** Only the input associated with the selected profit rule is visible.
- [ ] **PASS / FAIL:** The app never persists both profit-rule values simultaneously.
- [ ] **PASS / FAIL:** Switching profit-rule options follows the specified clearing and confirmation behavior.
- [ ] **PASS / FAIL:** Invalid values remain visible after failed submission and show associated validation messages.
- [ ] **PASS / FAIL:** Currency accepts non-negative values and formats to two decimals; percentage accepts 0–100 inclusive.
- [ ] **PASS / FAIL:** The Current Default Snapshot shows Average ticket, Food cost, Crew size, and Travel rate.
- [ ] **PASS / FAIL:** Snapshot values update only from valid persisted values, not uncommitted invalid text.
- [ ] **PASS / FAIL:** Valid progress auto-saves and displays `Progress saved automatically`.
- [ ] **PASS / FAIL:** `Continue` validates before advancing; `Back` preserves valid changes.
- [ ] **PASS / FAIL:** `Save and finish later` saves valid values, preserves the active step, and returns to Dashboard.
- [ ] **PASS / FAIL:** Review groups values by section and each Edit action returns to the correct step.
- [ ] **PASS / FAIL:** Completion writes a versioned defaults record, marks onboarding defaults complete, and routes to Dashboard.
- [ ] **PASS / FAIL:** On mobile, the form is single-column, `Step n of 5` is visible, and Continue remains accessible in the sticky bottom action area.

## Final acceptance

- [ ] **PASS / FAIL:** No unresolved visual deviations remain when the implementation is reviewed side by side with the approved mockup.
- [ ] **PASS / FAIL:** No functional regression exists in any workflow touched by this screen.
- [ ] **PASS / FAIL:** All automated tests, keyboard checks, responsive checks, and manual acceptance checks pass.
- [ ] **PASS / FAIL:** The screen feels visually and behaviorally cohesive with the other nine product screens.
- [ ] **PASS / FAIL:** Product owner approval has been recorded.
