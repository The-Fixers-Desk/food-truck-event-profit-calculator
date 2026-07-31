# Food Truck Event Profit Calculator

## Event Analysis Structure v0.1

### Status

Approved as the V1 product and domain-model basis for event analysis.

### Purpose

This document defines the information the application needs to describe an event,
estimate its revenue, calculate its costs, judge it against the owner's selected
profitability target, explain the major risks, and save multiple versions of the
same event.

It defines structure and behavior only. Database schema, forms, calculations, and
results presentation are implemented in later milestones.

---

## 1. Core concepts

### Event

An Event contains the identifying information shared by every version of that
event:

- event name
- event date
- start time
- location

These values help the customer recognize the event. They do not directly affect
financial calculations.

### Event scenario

An Event Scenario contains one complete set of assumptions for an Event.

A customer may save multiple scenarios for the same Event, such as:

- Original estimate
- Rain forecast
- Lower attendance
- Reduced vendor fee

Each saved scenario preserves the assumptions used for that version. Changing one
scenario must not silently change another scenario or the saved business defaults.

The application may provide an automatic scenario name, but the customer can edit
it when saving.

---

## 2. Event identity

Each Event contains:

- **Event name** — required
- **Event date** — required
- **Start time** — required
- **Location** — required

Only a start time is required for V1. End time is not required for identification.

Each Event Scenario also contains:

- **Scenario name** — customer-editable, with an application-provided default
- **Optional notes**

---

## 3. Attendance, demand, and competition

Each Event Scenario contains:

- **Estimated attendance**
- **Other competing food vendors**
- **Percentage of attendees expected to buy food**

The customer-facing interface must use plain language. It must not use the term
"capture rate."

The number of competing food vendors supports later vendor-density warnings. The
customer still controls the expected-buyer assumption.

---

## 4. Event protection and weather

### Event protection

The customer selects one:

- Fully indoors
- Covered with reliable seating
- Partially covered
- Fully outdoors

### Weather outlook

The customer selects one:

- Favorable / normal — 0% selected reduction
- Minor concern — 5% selected reduction
- Moderate adverse weather — 15% selected reduction
- Significant adverse weather — 30% selected reduction
- Severe disruption risk — 50% selected reduction
- Custom — customer-entered reduction

Weather reduces expected customers, not the average order sale amount.

### Protection adjustment

The selected weather reduction is moderated by event protection:

- Fully indoors — 15% of the selected weather reduction
- Covered with reliable seating — 50% of the selected weather reduction
- Partially covered — 75% of the selected weather reduction
- Fully outdoors — 100% of the selected weather reduction

A fully indoor event is not treated as completely protected because customers may
still avoid traveling through poor weather.

V1 does not retrieve weather automatically. The interface reminds the customer to
check the latest forecast.

---

## 5. Expected revenue method

The customer chooses one method.

### Method A — Estimate from attendance

This is the default method.

The scenario stores:

- Estimated attendance
- Percentage of attendees expected to buy food
- Average order sale amount

Expected revenue is later calculated from:

```text
Estimated attendance
× Percentage of attendees expected to buy food
× Average order sale amount
```

For this V1 method, one expected buyer is treated as one expected order.

### Method B — Enter expected sales manually

The scenario stores:

- Expected sales amount

The attendance and competition information may still be entered for context and
warnings, but the manual expected-sales amount controls the revenue calculation.

Only the selected revenue method and its matching revenue value control the
analysis.

---

## 6. Food and packaging cost method

The customer chooses one method on both the Defaults screen and the Event Inputs
screen.

### Method A — Average cost per order

This is the default method.

The customer enters:

- Average food and packaging cost per order

### Method B — Percentage of sales

The customer enters:

- Food and packaging cost percentage

### Method C — Manual event total

The customer enters:

- Total food and packaging cost for this event

Only the selected method and its matching value are displayed, saved, and used.
The unselected values remain empty and do not affect the analysis.

A new event scenario begins with the saved business-default method and value, but
the customer may override both for that scenario without changing Defaults.

---

## 7. Payment and organizer fees

Each Event Scenario may contain:

- **Percentage of sales paid by card**
- **Card-processing percentage**
- **Optional fixed card-processing fee**
- **Vendor or booking fee**
- **Optional organizer commission or revenue-share percentage**

Defaults may prefill applicable values. Event-specific changes do not update the
saved defaults.

---

## 8. Employee labor

Employee labor is an ordered, addable list.

Each labor entry contains:

- Hourly labor rate
- Combined total hours paid at that rate

Combined paid hours include all paid employee time relevant to the event,
including setup and cleanup when applicable.

The model does not use separate Paid staff, Setup time, or Cleanup time fields.

A new scenario begins with copied labor defaults. The customer may add, remove, or
change entries for that scenario without changing Defaults.

---

## 9. Owner labor pay

Each Event Scenario may contain:

- **Owner labor pay** — optional flat amount for the event

Owner labor pay is a labor expense and is fundamentally separate from business
profit.

A new scenario begins with the saved default owner labor pay when one exists.

---

## 10. Travel and additional event costs

Each Event Scenario may contain:

- **Travel cost** — optional flat amount
- **Additional event costs** — ordered, addable list

Each additional event-cost entry contains:

- Cost name
- Amount

Examples include parking, permits, generator fuel, utilities, and other event-
specific costs.

The product does not require mileage or vehicle-cost-per-mile calculations.

---

## 11. Profitability target

Each Event Scenario contains one selected profitability target:

- Minimum acceptable profit amount, or
- Minimum acceptable profit margin

Only the selected target and its matching value are displayed, saved, and used for
analysis and warnings. The unselected target remains empty.

A new scenario begins with the saved business-default target, but the customer may
override it for that scenario without changing Defaults.

---

## 12. Estimate information

The application must clearly explain that uncertain inputs produce estimated
results.

This explanation is not a permanently visible form section. A clear control near
the top of the Event Inputs screen, such as **About estimates**, reveals the
information when requested.

Inputs that are inherently assumptions may be marked automatically in the
interface without requiring the customer to classify each field manually.

---

## 13. Input and results workflow

Event inputs and results are presented on separate screens.

### Event Inputs screen

The Event Inputs screen gathers and validates the full event and scenario
information.

### Event Results screen

The Event Results screen focuses on:

- the variable assumptions the customer is most likely to test
- updated sales, costs, owner pay, business profit, and margin
- break-even information
- profitability constraints
- factual warnings

The customer may adjust useful scenario variables from the Results screen and save
the result as another scenario for the same Event.

Saving a new version must not silently overwrite an existing scenario.

---

## 14. Proposed domain-model shape

The exact Python names may be adjusted to match project conventions, but the model
should separate the following responsibilities:

```text
Event
├── EventIdentity
└── one or more EventScenario records

EventScenario
├── DemandAssumptions
├── WeatherAssumptions
├── RevenueAssumptions
├── FoodCostAssumptions
├── PaymentAndOrganizerFees
├── EmployeeLaborEntry list
├── OwnerLaborPay
├── AdditionalEventCost list
└── ProfitTarget
```

The event-analysis model represents customer inputs and valid assumptions.
Calculated results are added by the Calculation Engine milestone rather than being
embedded prematurely in this input-model milestone.

---

## 15. Model-level validation

The domain model must reject invalid or contradictory states, including:

- blank required event identity fields
- negative attendance or competing-vendor counts
- percentages outside 0% through 100%
- invalid event-protection or weather choices
- a custom weather choice without a custom reduction
- a value populated for an unselected revenue method
- a missing value for the selected revenue method
- a value populated for an unselected food-cost method
- a missing value for the selected food-cost method
- negative money values
- negative labor rates or paid hours
- unnamed additional event costs
- an invalid or contradictory profitability target

Domain validation raises `ValueError`. Customer-facing error wording remains in
the form layer.

---

## 16. Defaults and overrides

When a new Event Scenario is created, reusable values are copied from Business
Defaults.

After copying:

- the scenario owns its values
- changing the scenario does not change Defaults
- changing Defaults does not silently change an existing scenario
- saving another scenario does not silently overwrite the first

This preserves the exact assumptions behind every saved analysis.
