# Food Truck Event Profit Calculator

## Architecture Decision Record (ADR) v0.3

### Status

Approved for V1 implementation. Supersedes ADR v0.2.

### Revision focus

Version 0.3 incorporates the approved event-analysis domain structure, selectable
revenue and food-cost methods, weather behavior, Event-to-Scenario relationship,
and separate Event Inputs and Event Results workflows.

### Purpose

This document records the approved technical architecture for the Food Truck
Event Profit Calculator. It translates the product requirements in the Product
Decision Record into implementation constraints and technical choices.

The Product Decision Record remains authoritative for product behavior. This
Architecture Decision Record remains authoritative for the approved V1
technical architecture.

---

## FTC-ADR-001 - Local desktop application architecture

The product will operate as a standalone local desktop application.

Its interface will be implemented with web technologies and served by a local
application server running on the customer's computer. The product will not
depend on cloud hosting for normal use.

---

## FTC-ADR-002 - Shared cross-platform codebase

Windows and macOS versions will use one shared application codebase.

Operating-system-specific packaging and installation code may differ, but core
application behavior, calculations, workflows, terminology, and stored data
structures will remain shared.

---

## FTC-ADR-003 - Application backend

Python 3.12 and Flask will provide the local application backend.

The Flask application will use the application-factory pattern and Blueprints
to support modularity, testing, and future expansion.

---

## FTC-ADR-004 - User interface

The user interface will use:

- HTML
- modular CSS
- vanilla JavaScript
- Jinja templates

Shared templates, navigation, reusable visual components, and page-specific CSS
modules will be used to keep the interface consistent and maintainable.

A larger client-side framework will not be introduced unless a demonstrated
product requirement makes it necessary.

---

## FTC-ADR-005 - Persistent storage

SQLite will be the application's primary persistent data store.

The database will be stored locally on the customer's computer and will not be
tied to a particular browser.

Browser storage, cookies, and manually managed JSON files will not be used as
the authoritative store for customer data.

---

## FTC-ADR-006 - Application layers

The implementation will maintain clear separation between:

1. presentation and user-interface code
2. application routes and workflow coordination
3. domain models and model-level validation
4. calculation and business-rule logic
5. database access and persistence
6. desktop launch and packaging behavior

Routes and templates will not contain SQL or storage-unit conversion logic.
Calculation logic must not depend on HTML templates or database implementation
details.

---

## FTC-ADR-007 - Local server

Flask's development server will be used only during development.

The packaged application will use Waitress, or an approved replacement with
equivalent cross-platform local-server behavior, for normal customer use.

The server will bind only to the local computer unless a future approved
product decision requires network access.

---

## FTC-ADR-008 - Desktop application window

The packaged product will open in a dedicated desktop application window.

Customers will not be required to open a browser manually, enter a local
address, or interact with browser tabs or an address bar.

The specific desktop-window technology will be selected and documented before
packaging begins.

---

## FTC-ADR-009 - Application startup and shutdown

Launching the desktop application will:

1. start the local application server
2. wait until the server is ready
3. open the dedicated application window

Closing the application will safely stop application-owned local processes
without corrupting stored data.

---

## FTC-ADR-010 - Customer data location

Customer data will be stored separately from installed application files.

Each packaged version will use the operating system's expected application-data
location:

- Windows: the appropriate user application-data directory
- macOS: the appropriate user Library application-support directory

Development data may remain in the repository's local `data` directory.

---

## FTC-ADR-011 - Packaging

Windows and macOS will receive separate installation packages produced from the
same source code.

The packaged application will include Python and all runtime dependencies.
Customers will not be required to install Python, Flask, SQLite, Waitress, or
developer tools separately.

The final packaging technology will be documented in a later ADR before
distribution work begins.

---

## FTC-ADR-012 - Offline operation

The core workflows must operate without an internet connection:

- complete first-use setup
- configure defaults
- use the Dashboard
- evaluate an event
- save an event analysis
- reopen a saved analysis
- compare saved analyses
- back up and restore customer data

External network services must not be required for these workflows.

---

## FTC-ADR-013 - Database evolution

The database will include schema-version tracking.

Future structural changes will be performed through explicit migrations rather
than silently replacing or rebuilding customer databases.

Database writes that affect multiple related records will use transactions.

---

## FTC-ADR-014 - Testing

The architecture must support automated testing of:

- calculation rules
- form and model validation
- database persistence
- application routes
- complete workflows

Core calculation and domain-model tests will not require a browser or running
desktop window. Pytest is the approved automated-test framework.

---

## FTC-ADR-015 - Technical restraint

V1 will favor the smallest reliable implementation that satisfies the Product
Decision Record.

New frameworks, services, abstractions, dependencies, and infrastructure will
be added only when they solve a demonstrated requirement.

---

## FTC-ADR-016 - Exact numeric representation

Exact business values will not be stored or calculated with binary floating
point.

Python domain and application code will use `Decimal` for money and percentage
values. SQLite will store scaled integers with explicit unit names:

- money in cents
- percentages in basis points
- time in minutes

Conversion between customer-facing units and storage units will occur at the
persistence boundary.

---

## FTC-ADR-017 - Business-defaults storage structure

Reusable business defaults are represented by one active `business_defaults`
record.

Repeatable employee-labor defaults are stored as ordered child records. Each
child record contains an hourly rate in cents and combined paid time in minutes.
This avoids fixed columns for a predetermined number of labor rates.

Optional values, including default travel cost and owner labor pay, are stored
as nullable values rather than invented zero-value assumptions.

Food and packaging defaults use a method discriminator plus one matching value.
The allowed methods are average cost per order, percentage of sales, and manual
event total. The selected value is stored and unselected values remain null.

---

## FTC-ADR-018 - Layered validation

Validation is enforced at multiple boundaries:

1. form validation provides customer-facing feedback and preserves submitted
   values when correction is required
2. immutable domain models reject invalid or contradictory states during
   construction
3. SQLite constraints provide a final persistence safeguard

Domain-model validation raises `ValueError` for invalid construction. Customer-
facing error wording remains outside the domain model.

---

## FTC-ADR-019 - Atomic business-defaults persistence

Saving business defaults and their related labor entries is one logical write
operation and will be protected by a database transaction.

A failed or invalid save must not partially replace previously stored defaults
or labor entries.

---

## FTC-ADR-020 - Profit-target representation

The profitability bottom line is represented by a target type plus one matching
value.

The allowed target types are minimum profit amount and minimum profit margin.
The selected value is stored and the unselected value remains null. The domain
model and database must reject contradictory target combinations.

---

## FTC-ADR-021 - First-use and normal-launch routing

The application distinguishes incomplete first-use setup from normal use using
authoritative local application data rather than browser-only state.

Incomplete setup routes the customer through Welcome and Defaults. After valid
initial defaults are saved, the Dashboard becomes the normal application entry
point.

---

## FTC-ADR-022 - Application-wide logging and error handling

The application uses centralized logging and custom error pages so unexpected
failures are recorded and customers receive a controlled, understandable error
state.

Error handling must not expose internal implementation details to the customer.

---

## FTC-ADR-023 - Milestone-based implementation workflow

Development proceeds through focused milestones. Each milestone has a defined
goal, includes appropriate automated tests, and is completed with a focused Git
commit before dependent work begins.

Unrelated refactoring and speculative infrastructure are excluded from a
milestone unless they are required to complete it safely.

---

## FTC-ADR-024 - Event and scenario domain separation

The event domain distinguishes an `Event` from an `EventScenario`.

An Event contains shared identifying information: event name, event date, start
time, and location. An EventScenario contains one complete set of assumptions for
that Event and later receives one corresponding set of calculated results.

One Event may own multiple EventScenario records. Saving a new scenario must not
silently overwrite an existing scenario.

---

## FTC-ADR-025 - Event-analysis domain composition

The event-analysis domain will use small immutable models rather than one
unstructured mapping.

The structure will separate event identity, demand assumptions, weather
assumptions, revenue assumptions, food-cost assumptions, payment and organizer
fees, repeatable employee labor, repeatable additional event costs, owner labor
pay, and the selected profit target.

Exact class names may follow project conventions, but boundaries must preserve
clear validation and readable calculation inputs.

---

## FTC-ADR-026 - Method discriminator and matching value pattern

Revenue method and food-cost method will use the same explicit representation
pattern already approved for profit targets:

1. store one allowed method type
2. store only the value or values required by that method
3. leave values for unselected methods null
4. reject contradictory combinations in domain validation and database constraints

Revenue methods are attendance-based estimation and manual expected sales.
Food-cost methods are average cost per order, percentage of sales, and manual
event total.

---

## FTC-ADR-027 - Repeatable scenario child records

Employee labor entries and additional event costs are repeatable ordered child
records of an EventScenario.

Each labor record stores an hourly rate in cents and combined paid time in minutes.
Each additional-cost record stores a customer-facing name and an amount in cents.

These records will not be represented by a fixed number of columns.

---

## FTC-ADR-028 - Weather assumptions and calculation constants

Event protection and weather outlook are explicit domain values.

Standard weather reductions and protection multipliers are calculation rules,
not template constants. They will be implemented in the calculation or business-
rule layer and covered by unit tests.

The approved protection multipliers are:

- fully indoors: 15%
- covered with reliable seating: 50%
- partially covered: 75%
- fully outdoors: 100%

V1 stores the customer's selected weather outlook or custom reduction and does not
require an external weather service.

---

## FTC-ADR-029 - Defaults copied into independent scenarios

Creating a new EventScenario copies applicable Business Defaults into the new
domain object.

After creation, scenario values are independent. Changing a scenario does not
change Defaults, and changing Defaults does not mutate an existing scenario.

Persistence must preserve the exact assumptions used by each saved scenario.

---

## FTC-ADR-030 - Separate input and results workflows

Event Inputs and Event Results will use separate routes and templates or equivalent
separate application views.

The Inputs workflow gathers and validates the complete scenario. The Results
workflow presents calculated outputs and exposes only the variable assumptions
approved for convenient what-if changes.

Results-page changes update the working scenario and may be saved as a new scenario
without overwriting the source scenario unless the customer explicitly chooses an
edit-and-resave action.

---

## FTC-ADR-031 - Estimate information disclosure

Estimate guidance will be available through a clear disclosure control near the
top of the Event Inputs view.

The guidance is not modeled as a permanently visible Estimate Status section and
does not require customers to classify every field manually. The interface may
mark known assumption fields automatically.

---

## FTC-ADR-032 - Event-analysis specification authority

Event Analysis Structure v0.1 is the approved detailed design basis for the event
domain-model milestone.

The Product Decision Record remains authoritative for product behavior. The Event
Analysis Structure document provides the approved field grouping and model shape,
and this ADR defines the technical constraints used to implement it.

---
