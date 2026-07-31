# V1 design system

The interface is a calm, information-rich desktop business tool. Components
exist to clarify decisions, status and next actions—not to decorate screens.
Use established primitives before adding screen-specific CSS.

## Foundations

Tokens live in `app/static/css/tokens.css`.

- Typography: `--text-xs` through `--text-3xl`, three line-height tokens and
  regular, medium and bold weights. Use `.type-page-title`,
  `.type-section-title`, `.type-card-title`, `.type-supporting`, `.type-label`
  and `.type-numeric` according to meaning rather than appearance.
- Spacing: `--space-1` through `--space-8` form the 4px-based spacing scale.
  Prefer `.stack`, `.cluster`, `.grid`, `.split-layout` and `.page-container`.
- Colors: use semantic background, surface, border, text, primary, secondary,
  success, warning, danger, information, disabled, focus and selected tokens.
  Never use color as the only status cue.
- Shape: use the XS, small, medium, large and pill radii. Inputs and buttons use
  small; cards use medium; dialogs use large; badges use pill.
- Elevation: `--shadow-1` is a bordered surface, `--shadow-2` an elevated card,
  and `--shadow-3` a modal. Avoid heavier or decorative shadows.
- Controls: standard controls are 44px high, with small and large variants.
  Focus uses the shared focus token and remains visible in every state.

## Component catalog

Reusable components live in `components.css`; small layout helpers live in
`utilities.css`.

- Buttons: `.button`, `.button-secondary`, `.button-tertiary`,
  `.button-destructive`, `.button-icon`, plus small/large/loading states.
- Inputs: `.form-input`, native checkbox/radio styling, `.switch`, invalid,
  warning and disabled states.
- Navigation: `.tabs`, `.tab` and the compatible `.section-switcher` pattern.
- Surfaces: `.card`, compact/elevated variants, `.metric-card` and the existing
  form, saved-event, placeholder and comparison surfaces.
- Messages: success, warning, danger and information `.alert` variants,
  compatible status/flash/contextual/error messages, helper and inline errors.
- Badges: `.badge` and semantic variants; existing Estimate, From defaults and
  Changed indicators inherit the same primitive.
- Data: `.data-table`, numeric alignment, selected rows, and compatible
  comparison tables with tabular numerals.
- Empty states: `.empty-state`, icon, title, explanation and action slots.
- Loading: `.loading-indicator`, `.progress`, `.skeleton` and button loading;
  motion is removed when requested by the operating system.
- Dialogs: native `dialog`, `.dialog`, existing Scenario Save dialog and
  `.dialog__actions` share sizing, elevation and responsive constraints.
- Icons: use one local inline-SVG/current-color system with `.icon` size
  variants. Do not add remote icon fonts or mix visual families.

## Usage rules

Keep one obvious primary action per decision area. Use secondary for safe
alternatives, tertiary for low-emphasis actions and destructive only for
irreversible work. Use progressive disclosure for secondary complexity.
Preserve semantic HTML, logical source order, visible labels and keyboard
focus. Numeric decision data should use tabular numerals and right alignment in
dense tables. At narrow widths, grids collapse to one column without changing
DOM order.

Future screen milestones should assemble these primitives and add new shared
components only when a genuinely new interaction is needed. They should not
redefine colors, spacing, button states, cards, alerts, badges, tables or
dialogs locally.
