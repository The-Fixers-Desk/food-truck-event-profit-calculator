# Event Analysis Workspace — Design Rationale

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

The Event Analysis Workspace turns entered assumptions into a transparent, decision-ready view of profitability.

## Dominant task

Decide whether the selected scenario is worth accepting, then revise or compare as needed.

## Why the workspace is dense

This is the product’s primary analytical screen. Users need revenue, costs, profit, margin, break-even, assumptions, recommendation, and sensitivity information together. The density is intentional, but hierarchy prevents it from becoming a wall of data.

The top metric strip answers the immediate numerical questions. The profitability summary then translates those numbers into a recommendation. Supporting panels explain the reasoning and show which assumptions matter most.

## Transparent decision logic

The design avoids presenting “Worth accepting” as a black-box verdict. The cost breakdown, input summary, target comparison, and driver analysis reveal how the recommendation was produced.

The recommendation references the user’s chosen profit target rather than applying a generic standard. This makes the outcome feel connected to the business defaults and helps users understand why two owners might make different decisions about the same event.

## Scenario controls

The scenario selector, duplicate action, and compare action appear near the page title because scenario exploration is a page-level activity. The scenario list in the left column keeps alternatives visible and communicates their recommendation states without requiring navigation away from the event.

Duplicating a scenario provides a safe way to test changes without destroying the original estimate.

## Visual hierarchy

1. Recommendation and estimated profit
2. Key metric strip
3. Cost breakdown
4. Scenario controls
5. Decision checks and sensitivity drivers
6. Input and event summaries

Green is used only for positive result states and profit emphasis. Copper remains the action and navigation color, preventing success status from being confused with interactivity.

## Responsive reasoning

On smaller screens, key metrics and the recommendation remain first. Supporting analysis follows in a vertical sequence. Compare scenarios becomes a prominent full-width action because side-by-side exploration is otherwise less visible on mobile.

## Intended user effect

The user should be able to answer “Is this event worth it?” quickly, then inspect the evidence and test alternatives without losing confidence in how the result was calculated.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
