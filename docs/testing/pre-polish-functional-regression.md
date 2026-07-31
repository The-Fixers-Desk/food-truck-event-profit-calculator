# Pre-polish functional regression

This safety net covers server-side Event creation and atomic validation,
Scenario saving and management, restart persistence, Defaults overrides,
calculation outcomes, comparison, migrations, and backup/restore safeguards.
It also includes stress cases for long names and ordered repeatable rows.

Every pytest test receives a temporary database path from `tests/conftest.py`.
Restart tests close the current connection and create another application
instance against that same temporary path. Tests must never use, migrate,
replace, or delete `data/app.db` or real customer/development backups.

Run the focused pre-polish suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_pre_polish_functional_regression.py tests\test_event_analysis_persistence.py tests\test_saved_events_management.py tests\test_event_comparison.py tests\test_event_analysis_workspace.py tests\test_complete_event_inputs_workflow.py tests\test_data_safety.py -q
```

The later browser E2E milestone must still exercise real DOM interaction and
timing: rapid-response ordering, dirty-navigation confirmation choices,
dynamic add/remove controls, reset behavior, comparison filtering, download
handling, and restore confirmation/cancel flows. The packaged-platform
acceptance milestone must separately verify Windows and macOS installation,
application-data locations, permissions, native file dialogs, restart, backup,
restore, and recovery behavior.
