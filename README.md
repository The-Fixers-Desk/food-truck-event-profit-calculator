# Food Truck Event Profit Calculator

A local, offline-first planning tool for estimating food-truck event revenue,
costs, profitability, and break-even attendance. This repository is currently
prepared for external QA; packaging and installers have not started.

## Requirements

- Python 3.12
- Windows or macOS for the supported desktop shell
- A current browser for Flask development use

## Clean setup

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or another POSIX shell, activate or invoke the virtual environment
using `.venv/bin/python` instead. No environment variables, credentials,
remote services, or developer-owned database are required.

## Launch

Desktop application:

```powershell
.\.venv\Scripts\python.exe desktop.py
```

Browser-based development:

```powershell
.\.venv\Scripts\python.exe -m flask --app app.py run
```

The first launch creates the local data directories and SQLite database and
applies all migrations automatically. Development data defaults to `data/`.
Use an isolated `DATA_ROOT` through the application factory for automated or
special-purpose testing; do not copy a developer database into a clean clone.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use isolated temporary databases. See [QA handoff](docs/qa-handoff.md)
for the formal test checklist, reset procedure, logs, defect-report format,
and known limitations.
