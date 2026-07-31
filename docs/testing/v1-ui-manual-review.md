# V1 UI manual review

Review with an isolated test database; never use `data/app.db`.

- Normal desktop window: inspect the shell, navigation, compact page headers,
  focus visibility, and sticky controls.
- Event Inputs: visit all six stages; test Back, Continue, blocked required
  fields, server errors, review summaries and Edit actions, labor rows,
  additional-cost rows, and final Analyze event submission.
- Business Defaults: switch all four sections, exercise conditional food and
  profit controls, trigger errors in each section, and confirm Save remains
  reachable.
- Event Analysis: switch every assumption group, verify key results stay
  visible, edit valid and invalid assumptions, observe live recalculation,
  reset, save as new, overwrite, and dirty-navigation confirmation.
- Saved Events: inspect empty state, several Events, many Scenarios, long names,
  rename controls, delete confirmations, and opening an analysis.
- Comparison: review two, three and four Scenarios; change baseline and the
  differences-only control; inspect long names and warnings.
- Welcome and Dashboard: confirm primary actions and essential status fit in a
  normal desktop view.
- Data Safety and recovery: inspect backup, restore, confirmations, errors and
  expandable safety information.
- Error pages and dialogs: verify not-found, application-error, validation,
  success, warning, loading and destructive states.
- Repeat at narrow widths down to 320 CSS pixels. Check wrapping, logical
  keyboard order, dialogs, repeatable rows, long validation messages, no
  page-wide horizontal scrolling, and sticky controls not covering content.
