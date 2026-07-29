# Food Truck Event Profit Calculator

## Architecture Decision Record (ADR) v0.1

### Status

Approved for V1 implementation.

### Purpose

This document records the approved technical architecture for the Food Truck
Event Profit Calculator. It translates the product requirements in the Product
Decision Record into implementation constraints and technical choices.

The Product Decision Record remains authoritative for product behavior. This
Architecture Decision Record remains authoritative for the approved V1
technical architecture.

---

## FTC-ADR-001 — Local desktop application architecture

The product will operate as a standalone local desktop application.

Its interface will be implemented with web technologies and served by a local
application server running on the customer's computer. The product will not
depend on cloud hosting for normal use.

---

## FTC-ADR-002 — Shared cross-platform codebase

Windows and macOS versions will use one shared application codebase.

Operating-system-specific packaging and installation code may differ, but core
application behavior, calculations, workflows, terminology, and stored data
structures will remain shared.

---

## FTC-ADR-003 — Application backend

Python and Flask will provide the local application backend.

The Flask application will use the application-factory pattern and Blueprints
to support modularity, testing, and future expansion.

---

## FTC-ADR-004 — User interface

The user interface will use:

- HTML
- CSS
- vanilla JavaScript
- Jinja templates

A larger client-side framework will not be introduced unless a demonstrated
product requirement makes it necessary.

---

## FTC-ADR-005 — Persistent storage

SQLite will be the application's primary persistent data store.

The database will be stored locally on the customer's computer and will not be
tied to a particular browser.

Browser storage, cookies, and manually managed JSON files will not be used as
the authoritative store for customer data.

---

## FTC-ADR-006 — Application layers

The implementation will maintain clear separation between:

1. presentation and user-interface code
2. application routes and workflow coordination
3. calculation and business-rule logic
4. database access and persistence
5. desktop launch and packaging behavior

Calculation logic must not depend on HTML templates or database implementation
details.

---

## FTC-ADR-007 — Local server

Flask's development server will be used only during development.

The packaged application will use Waitress, or an approved replacement with
equivalent cross-platform local-server behavior, for normal customer use.

The server will bind only to the local computer unless a future approved
product decision requires network access.

---

## FTC-ADR-008 — Desktop application window

The packaged product will open in a dedicated desktop application window.

Customers will not be required to open a browser manually, enter a local
address, or interact with browser tabs or an address bar.

The specific desktop-window technology will be selected and documented before
packaging begins.

---

## FTC-ADR-009 — Application startup and shutdown

Launching the desktop application will:

1. start the local application server
2. wait until the server is ready
3. open the dedicated application window

Closing the application will safely stop application-owned local processes
without corrupting stored data.

---

## FTC-ADR-010 — Customer data location

Customer data will be stored separately from installed application files.

Each packaged version will use the operating system's expected application-data
location:

- Windows: the appropriate user application-data directory
- macOS: the appropriate user Library application-support directory

Development data may remain in the repository's local `data` directory.

---

## FTC-ADR-011 — Packaging

Windows and macOS will receive separate installation packages produced from the
same source code.

The packaged application will include Python and all runtime dependencies.
Customers will not be required to install Python, Flask, SQLite, Waitress, or
developer tools separately.

The final packaging technology will be documented in a later ADR before
distribution work begins.

---

## FTC-ADR-012 — Offline operation

The core workflows must operate without an internet connection:

- configure defaults
- evaluate an event
- save an event analysis
- reopen a saved analysis
- compare saved analyses
- back up and restore customer data

External network services must not be required for these workflows.

---

## FTC-ADR-013 — Database evolution

The database will include schema-version tracking.

Future structural changes will be performed through explicit migrations rather
than silently replacing or rebuilding customer databases.

Database writes that affect multiple related records will use transactions.

---

## FTC-ADR-014 — Testing

The architecture must support automated testing of:

- calculation rules
- validation
- database persistence
- application routes
- complete workflows

Core calculation tests will not require a browser or running desktop window.

---

## FTC-ADR-015 — Technical restraint

V1 will favor the smallest reliable implementation that satisfies the Product
Decision Record.

New frameworks, services, abstractions, dependencies, and infrastructure will
be added only when they solve a demonstrated requirement.
