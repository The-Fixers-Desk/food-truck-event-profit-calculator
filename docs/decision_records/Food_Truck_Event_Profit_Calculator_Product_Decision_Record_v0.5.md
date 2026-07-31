# Food Truck Event Profit Calculator

## Product Decision Record (PDR) v0.5

### Status

Approved for V1 implementation. Supersedes PDR v0.4.

### Revision focus

Version 0.5 records the approved event-analysis structure, revenue and food-cost methods, weather behavior, scenario workflow, and separation of Event Inputs from Event Results.

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

Customers can save one or more scenarios for the same event for later review and comparison. Each scenario preserves its own assumptions and results.

---

## FTC-PDR-012

Every Event records its event title, date, start time, and location solely to help the customer recognize it. Each saved Event Scenario records one complete set of assumptions and results for that Event. Event identity does not participate directly in financial calculations.

---

## FTC-PDR-013

The Comparison area exists to allow customers to review and compare saved Event Scenarios, including multiple versions of the same Event or scenarios from different Events.

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

The Defaults screen uses the customer-facing term 'Average order sale amount.' It stores the usual percentage of sales paid by card and card-processing fee percentage. Food and packaging cost defaults use a selectable method whose default is Average cost per order, with Percentage of sales and Manual event total available as alternatives.

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

## FTC-PDR-038

An Event and an Event Scenario are distinct product concepts. The Event contains shared identifying information. Each Event Scenario contains one complete set of assumptions and results. Customers may save multiple scenarios for the same Event without silently overwriting earlier versions.

---

## FTC-PDR-039

Event identity consists of event name, event date, start time, and location. V1 does not require an end time for identification.

---

## FTC-PDR-040

The event model records other competing food vendors, estimated attendance, and
the percentage of attendees expected to buy food. The competitor count excludes
the customer's own business. Expected food buyers are divided by the total food
vendor count, including the customer, to provide an even-split estimate.
Customer-facing wording must not use the term 'capture rate.'

---

## FTC-PDR-041

The customer chooses how expected revenue is entered. The default method estimates revenue from attendance, expected percentage of attendees who buy, and average order sale amount. The alternative method allows the customer to enter expected sales manually. Only the selected method controls the revenue calculation.

---

## FTC-PDR-042

For the default attendance-based revenue method, one expected buyer is treated as one expected order in V1.

---

## FTC-PDR-043

Food and packaging cost uses one selected method: Average cost per order, Percentage of sales, or Manual event total. Average cost per order is the default. Only the selected method and its matching value are displayed, saved, and used. The selection is available on both Defaults and Event Inputs.

---

## FTC-PDR-044

Weather outlook is selected manually in V1. The available standard reductions are Favorable or normal at 0%, Minor concern at 5%, Moderate adverse weather at 15%, Significant adverse weather at 30%, Severe disruption risk at 50%, and a customer-entered Custom reduction.

---

## FTC-PDR-045

Weather reduces expected customers rather than average order sale amount. Event protection moderates the selected weather reduction: Fully indoors applies 15%, Covered with reliable seating applies 50%, Partially covered applies 75%, and Fully outdoors applies 100%.

---

## FTC-PDR-046

V1 does not retrieve weather automatically. The application reminds the customer to check the latest forecast and select the appropriate weather outlook.

---

## FTC-PDR-047

Additional event costs use an addable named list. Each entry contains a cost name and amount. Parking, permits, generator fuel, utilities, and other event-specific costs may be represented through this list.

---

## FTC-PDR-048

Event Inputs and Event Results are separate screens. The Inputs screen gathers the complete event and scenario information. The Results screen emphasizes the variable assumptions the customer is most likely to test, together with updated results and warnings.

---

## FTC-PDR-049

The customer may adjust useful assumptions from the Results screen and save the result as another scenario for the same Event. Saving a new version must not silently overwrite an existing scenario.

---

## FTC-PDR-050

Information explaining estimated inputs and estimated results is available through a clear control near the top of the Event Inputs screen. It is not displayed as a permanently open Estimate Status section.

---

## FTC-PDR-051

New Event Scenarios begin with copied Business Defaults. Event-specific overrides do not change saved Defaults, and later changes to Defaults do not silently change existing scenarios.

---

## FTC-PDR-052

The approved event-analysis structure is recorded in Event Analysis Structure v0.1 and is the implementation basis for the event domain model, event-input workflow, results workflow, saved scenarios, and comparison behavior.

---
