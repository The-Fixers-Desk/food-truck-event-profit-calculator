# Business Event Inputs Wizard — Design Rationale

## Document control

- **Product:** Food Truck Event Profit Calculator
- **Owner:** The Fixer’s Desk
- **Artifact:** Design rationale
- **Status:** Approved design intent
- **Source of truth:** Approved reference mockup, supported by the engineering specification and acceptance checklist

## Product-wide design principles

This screen belongs to a cohesive desktop-product system built around a neutral charcoal and warm graphite palette. Copper identifies primary actions, active navigation, and important structural emphasis. Green, warning amber, and red are reserved for semantic states rather than decoration.

The interface favors clear hierarchy, restrained surfaces, predictable placement, and explicit labels. The product is intended to help food-truck operators make financial decisions, so visual polish must support trust, comprehension, and speed rather than novelty.

Across the product:

- every screen has one dominant task;
- the persistent shell reduces relearning;
- reusable cards, controls, status treatments, and spacing create continuity;
- calculations and recommendation states remain transparent;
- responsive adaptations preserve task order rather than merely shrinking the desktop layout;
- local storage, offline use, and user control are communicated plainly.

## Purpose

The Event Inputs Wizard captures assumptions for one specific event and one scenario before profitability is calculated.

## Dominant task

Enter or confirm the current step’s event assumptions and continue.

## Why this flow mirrors the defaults wizard

Using the same wizard pattern reduces relearning. The user already understands step progress, completed states, conditional inputs, automatic saving, and Back/Continue behavior.

The event wizard is deliberately separate from Business Defaults because reusable business assumptions and event-specific facts have different lifecycles. This separation makes scenario comparison possible and prevents changes to one event from silently altering future analyses.

## Revenue-method reasoning

Revenue can be estimated through average ticket multiplied by expected buyers or entered as custom total sales. The two methods are mutually exclusive, so the interface shows the selected method as a clear card choice and reveals only its relevant fields.

The selected example combines attendance, conversion rate, average ticket, and expected buyers. These fields support both direct entry and reasoned estimation. Helper text explains relationships without forcing automatic calculation where the user may want manual control.

## Scenario structure

A scenario name appears early because multiple scenarios can belong to the same event. Naming the scenario before calculation helps users understand that they are creating a version of assumptions, not overwriting the event itself.

The current scenario snapshot provides early feedback and confirms that defaults and event-specific inputs are working together.

## Action hierarchy

- **Continue** advances to the next input category.
- **Back** supports correction.
- **Save as draft** preserves incomplete scenario work.
- Automatic save communicates continuity.

## Visual hierarchy

1. Active event-input question
2. Revenue-method selection
3. Event and scenario fields
4. Step navigation
5. Scenario snapshot
6. Save status and secondary actions

## Responsive reasoning

On mobile, the form becomes a single column and the step labels condense. Method selection remains visible before fields, preserving the conditional logic. Continue remains the dominant action.

## Intended user effect

The user should feel that event setup is organized and flexible. The process should make detailed estimation feel manageable while preserving enough structure for reliable comparison later.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
