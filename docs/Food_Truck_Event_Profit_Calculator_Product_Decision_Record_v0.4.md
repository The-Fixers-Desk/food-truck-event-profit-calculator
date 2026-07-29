# Food Truck Event Profit Calculator

## Product Decision Record (PDR) v0.4

### Status

Approved for V1 implementation. Supersedes PDR v0.3.

### Revision focus

Version 0.4 records the approved first-use flow, Dashboard, business-defaults, labor, travel-cost, profit-target, and V1 UI/UX decisions made during implementation.

### Investigation Question

What information does a food truck owner actually need to confidently decide whether an event is worth attending?

## FTC-PDR-001

The application should feel like a purpose-built desktop tool rather than a traditional spreadsheet.

---

## FTC-PDR-002

The application's primary goal is to help food truck owners make better event decisions while keeping the workflow as simple, intuitive, and fluid as possible.

---

## FTC-PDR-003

The calculator provides financial analysis and factual warnings to help customers make informed event decisions. The final decision always belongs to the customer.

---

## FTC-PDR-004

On first use, the application opens to a Welcome screen that briefly introduces the product before asking the customer to configure business defaults.

---

## FTC-PDR-005

After the customer completes the first business-defaults setup, the application guides them to the Dashboard. On later launches, the application opens to the Dashboard.

---

## FTC-PDR-006

The customer-facing application areas are Welcome, Dashboard, Defaults, Event Calculator, Saved Events, and Comparison. Each area serves a distinct purpose in the customer's workflow.

---

## FTC-PDR-007

Intermediate calculations and implementation details remain hidden from the customer. The calculation methodology is documented separately so customers can understand how every result is derived.

---

## FTC-PDR-008

Reusable business settings are stored in the Defaults screen.

---

## FTC-PDR-009

Every reusable default can be overridden for an individual event without changing the saved default.

---

## FTC-PDR-010

Changes made to reusable defaults must never silently overwrite event-specific overrides.

---

## FTC-PDR-011

Customers can save the results of individual event analyses for later review and comparison.

---

## FTC-PDR-012

Every saved event records the event title, date, time, and location solely to help the customer recognize and compare saved scenarios. This information does not participate in financial calculations.

---

## FTC-PDR-013

The Comparison area exists to allow customers to review and compare previously saved event analyses.

---

## FTC-PDR-014

The Product Decision Record is the authoritative source for approved product decisions. Architecture specifications, implementation documentation, and build instructions are derived from it rather than conversation history.

---

## FTC-PDR-015

The application architecture is written only after the major product and user-experience decisions have been approved and recorded in the Product Decision Record.

---

## FTC-PDR-016

The application never hides uncertainty. When customer inputs are estimates, calculated results are presented as estimates derived from those assumptions.

---

## FTC-PDR-017

Whenever practical, the application identifies the primary factors limiting profitability rather than only reporting the final profit or loss.

---

## FTC-PDR-018

Every customer-facing feature must directly support the question: 'Should I attend this event?' Features that do not materially improve that decision should not be included.

---

## FTC-PDR-019

The product is a standalone local application delivered through a local web interface rather than a cloud-hosted website.

---

## FTC-PDR-020

The application stores customer data locally on the customer's computer by default. Customer data is not transmitted to external servers as part of normal operation.

---

## FTC-PDR-021

Persistent application data is stored in a relational database rather than browser storage or manually managed data files.

---

## FTC-PDR-022

The application architecture separates the user interface, business logic, and data storage into distinct layers to support maintainability and future expansion.

---

## FTC-PDR-023

The user interface is delivered through standard web technologies (HTML, CSS, and JavaScript) rendered locally within the customer's application window.

---

## FTC-PDR-024

The application is served by a lightweight local application server running on the customer's computer. No internet connection is required for normal operation.

---

## FTC-PDR-025

The application's primary storage mechanism is independent of any specific web browser. Customer data remains available regardless of the supported local interface used to access the application.

---

## FTC-PDR-026

The application prioritizes offline reliability. Internet connectivity must never be required for the core workflow of evaluating, saving, reviewing, or comparing events.

---

## FTC-PDR-027

The Welcome screen presents the application as a four-step workflow: set business defaults, describe an event, review the analysis, and compare saved options.

---

## FTC-PDR-028

The Welcome screen guides the customer to Defaults. Completing the first valid Defaults setup guides the customer to the Dashboard rather than forcing them directly into a new event analysis.

---

## FTC-PDR-029

The Dashboard is the normal starting menu after setup. It provides direct access to analyze a new event, review saved events, compare events, and update business defaults.

---

## FTC-PDR-030

The Defaults screen uses the customer-facing term 'Average order sale amount.' It also stores the usual food and packaging cost percentage, percentage of sales paid by card, and card-processing fee percentage.

---

## FTC-PDR-031

Default travel cost is an optional flat amount for a typical event. The product does not require the customer to calculate or enter a vehicle cost per mile.

---

## FTC-PDR-032

Default employee labor is represented by one or more entries. Each entry records an hourly labor rate and the combined total hours paid at that rate for a typical event.

---

## FTC-PDR-033

The Defaults workflow does not use separate Paid staff, Setup time, or Cleanup time fields. Combined paid hours are entered directly for each labor rate.

---

## FTC-PDR-034

Default owner labor pay is an optional flat labor cost for a typical event. Owner labor pay is fundamentally separate from business profit.

---

## FTC-PDR-035

The customer must choose one profitability bottom line: a minimum acceptable profit amount or a minimum acceptable profit margin.

---

## FTC-PDR-036

Only the selected profitability target is displayed, saved, and used for future analysis and warnings. The unselected target is cleared and does not affect the analysis.

---

## FTC-PDR-037

The V1 product includes a dedicated user-interface and user-experience polish phase after the core workflows are functional, so all screens receive a consistent commercial presentation.

---
