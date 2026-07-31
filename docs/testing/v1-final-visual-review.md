# V1 final visual and interaction review

Review every item with isolated application data. Repeat at common desktop
widths, medium windows, and the narrowest supported width.

Automated structural, interaction, accessibility, responsive, wording, and
workflow checks pass. Pixel-level rendering, operating-system reduced-motion
behavior, native file dialogs, and visual focus appearance remain manual because
the project intentionally has no browser automation dependency.

- **Typography and spacing:** Check Welcome, Dashboard, Business Defaults,
  Event Inputs, Event Analysis, Saved Events, comparison, Data Safety, recovery,
  not-found and error states for one focal point, consistent headings, compact
  metadata, aligned controls, deliberate section rhythm and no wrapper-card clutter.
- **Actions and wording:** Confirm one dominant action per screen, specific verbs,
  quiet secondary actions, deliberate destructive actions, consistent Event and
  Scenario terminology, and no raw timestamps or technical failure language.
- **Forms and feedback:** Complete both guided forms with keyboard only. Check
  inline errors, error-stage focus, contextual warnings, preserved repeatable
  rows, success messages, disabled controls and sticky actions.
- **Event Analysis:** Exercise immediate recalculation, reset, Save, Save as new,
  overwrite, failure recovery, dirty navigation, multiple warnings and every
  expandable calculation section. Confirm stale responses never win.
- **Saved work and comparison:** Test empty/no-results states, many Events,
  search/sort, two-to-four selections, baseline changes, differences only,
  warning-heavy comparisons, long names and all rename/delete confirmations.
- **Data Safety and recovery:** Download repeatedly, reject invalid restore,
  complete restore, verify the recovery snapshot, and inspect restricted recovery
  navigation without exposing implementation details.
- **Interaction states:** Inspect hover, strong visible focus, selected, disabled,
  loading, saving, success, warning, danger, unavailable and recovery states.
  Confirm duplicate submissions are blocked while work is active.
- **Dialogs and motion:** Verify focus entry/restoration, Cancel and Escape,
  destructive wording, safe dialog sizing, subtle transitions, and reduced-motion
  behavior with the operating-system preference enabled.
- **Stress layouts:** Use long Event, Scenario, location and additional-cost names;
  multiple labor/additional-cost rows; multiple warnings; dense saved work; and a
  four-Scenario comparison. Confirm wrapping, reachable actions, localized table
  scrolling, unobscured focus and no accidental page-wide overflow.
