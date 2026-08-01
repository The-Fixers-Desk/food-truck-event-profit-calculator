# Viewport composition review

## Evidence

Fresh isolated-data captures were inspected at 1180×760, 1600×1000, and
2400×1350. Baseline and revised captures are stored in
`docs/testing/viewport-composition/`.

## Refinements

- Shared content widths now use fluid outer gutters and a larger desktop
  ceiling, so ultra-wide monitors gain useful canvas without creating
  unreadably long text.
- Dashboard hero typography, action spacing, and recent-work spacing scale with
  the viewport. At ultra-wide widths the two tasks share a balanced two-column
  composition; smaller desktops retain the established vertical reading order.
- The sidebar width, identity spacing, navigation rhythm, icon alignment, and
  selected state scale proportionally. The active destination is integrated
  into the rail rather than rendered as a separate card.
- Saved-work rows use a consistent compact height and fluid toolbar spacing.
- Event Analysis gains more room on large displays through proportional
  assumption/result columns and a fluid inter-column gap, while collapsing to
  one column at the existing breakpoint.
- Page headers, descriptions, and main padding now follow shared proportional
  rules instead of fixed page-by-page spacing.

## Manual review checklist

Inspect Welcome, Dashboard, Defaults, Event Inputs, Event Analysis, Saved
Events, Comparison, and Data Safety at small-laptop, medium-desktop, large, and
ultra-wide widths. Confirm balanced whitespace, clear hierarchy, readable line
lengths, unclipped controls, no page-wide overflow, visible focus, reduced
motion, and unchanged workflow order.

Screenshot review cannot establish full assistive-technology compatibility;
semantic structure, focus styling, reduced motion, and responsive containment
remain covered by automated regression tests.
