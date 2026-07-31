# Desktop application shell

Run the desktop shell from the project environment with:

```powershell
.\.venv\Scripts\python.exe desktop.py
```

The normal Flask development entrypoint remains `app.py`; importing
`app.desktop` starts neither a server nor a window.

The shell resolves the configured application-data root, takes an advisory
operating-system lock at `application.lock`, initializes Flask and its database
migrations/recovery mode, starts a managed Werkzeug server on an operating-
system-selected `127.0.0.1` port, waits for readiness, and replaces a bundled
offline loading screen with the application. Closing the one pywebview window
shuts down and joins the server thread before releasing the lock. Repeated
shutdown calls are harmless, and stale unlocked lock files do not prevent a
later launch.

Startup failures use a local, nontechnical error page and the existing logs;
partial servers and locks are cleaned up without deleting the database. A
second launch displays an already-open message and starts no server. Primary
window navigation is restricted to the generated loopback origin. No remote
assets, telemetry, authentication, or internet service is required.

Mutable database, log, recovery, staging, shell-temporary, and lock files all
resolve beneath `DATA_ROOT`. Development defaults remain in `data/`; packaging
milestones must pass the final platform-specific root when invoking
`app.desktop.run_desktop`.

## Manual verification

- Launch with a fresh data root and with existing data; observe the loading
  screen, Dashboard navigation and live Event Analysis recalculation.
- Exercise backup download and restore, then relaunch and verify persistence.
- Attempt a second launch and confirm it starts no second server/window.
- Close during ordinary use and verify the process and loopback server stop.
- Simulate a database startup failure and confirm the friendly recovery/error
  experience preserves the damaged database.
- Disconnect external networking, launch, navigate, calculate, back up and
  restore successfully.
- Resize from the normal desktop size to the supported minimum and verify all
  controls remain reachable.
