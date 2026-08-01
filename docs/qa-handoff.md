# QA handoff

## Product status

The application is a pre-package QA build. Its current internal application
version is `0.1.0`, and SQLite schema version is `3`.

Implemented workflows include first-use onboarding, Business Defaults, Event
Inputs, calculation and warnings, saved Event/Scenario management, Scenario
comparison, local profile and notifications, Data Safety backup/restore and
recovery, the Help Center, and the pywebview desktop shell.

Intentionally not implemented: installers, signed packages, automatic
updates, cloud sync, authentication, telemetry, licensing, payment handling,
or release-store distribution. Packaging has not started.

## Setup and launch

1. Install Python 3.12.
2. From a clean clone, create `.venv` and install `requirements.txt` as shown
   in the root README.
3. Run `.\.venv\Scripts\python.exe desktop.py` on Windows. For browser-based
   development, run `.\.venv\Scripts\python.exe -m flask --app app.py run`.
4. The application creates its directories, initializes SQLite, and runs all
   migrations on first launch. No seed database, secret, or account is needed.
5. Run `.\.venv\Scripts\python.exe -m pytest -q` for automated verification.

## Clean test data and reset

For an ordinary QA pass, open **Data Safety** and use **Clear app data**, enter
`CLEAR ALL DATA`, and confirm. This clears customer-created Defaults, Events,
Scenarios, profile, notifications, and the last-export marker. It does not
delete downloaded backup files.

For a truly fresh isolated desktop pass, close the app and launch the desktop
entry point with a newly created empty data-root path through
`app.desktop.run_desktop(path)`. Never point a test at another person&rsquo;s data
directory. Do not commit `data/*.db`, recovery snapshots, logs, staging files,
or `.ftbackup` exports.

## Logs and defect reports

Runtime logs are under the configured local application-data root in `logs/`.
Use the Help Center&rsquo;s **Copy support information** action for privacy-safe
environment metadata; do not attach a database unless explicitly requested
through a secure process.

For every defect, record:

- screen and workflow;
- clean or existing-data starting state;
- exact reproduction steps;
- expected behavior;
- actual behavior and visible error text;
- whether refresh or restart changes the result;
- screenshot when useful;
- copied support information and relevant log timestamp.

Do not include private Event details, financial assumptions, secrets, raw
database contents, or unrelated personal information.

## Recommended QA coverage

- [ ] Fresh launch: Welcome, setup deferral, required setup guard, and restart.
- [ ] Business Defaults: all three food-cost methods, both profit targets,
      repeatable labor, optional owner/travel values, invalid and boundary data.
- [ ] Event Inputs: identity, demand, all weather/protection combinations,
      calculated/custom sales, all food-cost methods, employee/owner labor,
      fees, operating and additional costs, hidden-field clearing, and errors.
- [ ] Analysis: live recalculation, result details, warnings, break-even,
      profit target status, refresh, and back/forward navigation.
- [ ] Saved work: initial Scenario, new Scenario, overwrite, duplicate, rename,
      delete safeguards, search/filter, restart, and missing-record handling.
- [ ] Comparison: selection limits, two to four Scenarios, cross-Event context,
      result consistency, and links back to saved work.
- [ ] Dashboard: empty/populated states, recent Events, counts, and navigation.
- [ ] Data Safety: export, valid import, invalid/incompatible import, recovery,
      delete Events, reset Defaults, clear-all confirmation, and restart.
- [ ] Local profile and notifications: create/edit, validation, unread/read,
      dismissal, actionable links, backup reminder, persistence, and clear/reset
      interactions.
- [ ] Help: offline content, section navigation, diagnostics copy, privacy
      exclusions, contact details, and configured/unconfigured external support.
- [ ] Accessibility/responsive: keyboard-only use, visible focus, dialogs,
      announcements, Escape behavior, and supported desktop/narrow sizes.
- [ ] Desktop shell: loading, second launch, offline use, close/reopen, window
      resizing, startup failure, recovery mode, and external navigation safety.

For numeric fields, include empty, zero, negative, decimal, over-precision,
very large, and documented minimum/maximum values. Confirm invalid submissions
preserve applicable entries and never partially overwrite saved records.

## Calculation checks

Use the hand-checkable examples in `tests/test_calculations.py`. Verify revenue,
weather-adjusted demand, food cost, card fees, commission, employee and owner
labor, fixed/additional costs, total cost, business profit, margin, break-even,
targets, warnings, zero-sales behavior, negative profit, and exact Decimal
behavior. Display rounding must not be treated as intermediate calculation
rounding.

## Known limitations

- The product is not packaged; QA launches it from the documented Python
  environment.
- Final Windows/macOS application-data locations, signing, icons, installers,
  and WebView prerequisite handling belong to later packaging milestones.
- The external support URL is configurable and may be unavailable; bundled
  Help and email support remain available offline.
- Native-window clipboard, external-browser opening, and platform rendering
  require manual Windows/macOS verification even though lifecycle behavior is
  covered headlessly.
- This tool provides estimates, not tax, legal, financial, event-planning, or
  business-assumption validation advice.
