# Accessibility and responsive review

## Implementation rules

- Prefer landmarks, headings, fieldsets, labels, buttons, links and native
  dialogs before ARIA. Keep one `h1` and a descriptive title on every page.
- Preserve DOM order across widths. CSS may change columns, but must not change
  reading or keyboard meaning.
- Every interaction needs a visible `:focus-visible` indicator. Dynamic rows
  receive numbered accessible names; add/remove actions move focus predictably
  and announce the change.
- Submitted errors use a focused page-level summary plus associated inline
  errors. Live analysis uses one polite status message after each debounced
  response and retains the latest valid results while inputs are invalid.
- Use polite live regions for ordinary updates. Reserve alerts for errors that
  require immediate correction; never announce an entire results panel.
- Comparison data uses captioned tables, scoped headers and a named,
  keyboard-focusable local overflow region. Baseline, ties, direction and units
  must be textual.
- Meet AA contrast through shared tokens. Color is supplementary to labels,
  borders, icons and explicit status text.

## Required manual release review

Keyboard:

- Complete onboarding, Defaults, Event creation, live analysis, Scenario save
  and overwrite, rename/delete, two-to-four Scenario comparison, backup,
  invalid restore, valid restore and recovery without a mouse.
- Verify Tab and Shift+Tab order, skip link, visible focus, conditional fields,
  added/removed rows, dialog containment, Escape cancellation and restored
  opener focus.

Screen reader:

- Verify titles, landmarks, heading hierarchy, current navigation, labels,
  hints, error summary and inline errors, live calculation statuses, warnings,
  Scenario management, selection count, comparison headers, backup/restore and
  recovery announcements.

Visual and responsive:

- Check every component state for contrast and non-color meaning at normal
  desktop sizes, 200% zoom, increased OS text, and widths down to 320 CSS
  pixels.
- Exercise long Event/Scenario names and validation messages, repeatable rows,
  workspace stacking, dialogs, navigation, comparison overflow, profit/loss,
  warnings and errors. Confirm no page-wide horizontal scrolling or obscured
  focused content.

Automated semantic assertions are a regression aid, not accessibility
certification. Complete this manual review before release.
