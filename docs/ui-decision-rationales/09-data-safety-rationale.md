# Data Safety — Design Rationale

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

Data Safety explains the app’s local-storage model and gives users direct control over backup, restoration, and deletion.

## Dominant task

Understand and manage locally stored business data.

## Why this screen is prominent

The product stores real business assumptions and event decisions. Trust cannot be left to hidden technical behavior. A dedicated navigation destination makes privacy and data control discoverable before a problem occurs.

The page leads with “Your data stays on this device” because this is the most important fact. The supporting privacy model turns technical architecture into plain-language guarantees: stored locally, no cloud sync, no account, and offline operation.

## Management actions

Export, import, and sample-format download are grouped together because they support user control and portability. Each action includes an explanation before the button so users understand the outcome rather than guessing from an icon.

The local data summary shows what exists on the device and when it was last exported. This makes the storage model tangible and encourages informed backup behavior.

## Destructive safeguards

Destructive actions are isolated in a danger zone and use restrained red styling. The goal is not to alarm users; it is to slow them down, explain scope, and recommend export before deletion.

Separate actions for deleting events, resetting defaults, and clearing everything allow users to choose the narrowest necessary intervention.

## Visual hierarchy

1. Local-storage promise
2. Privacy model
3. Export and import controls
4. Local data summary
5. Danger zone

Copper remains the primary action color for safe management actions. Red is reserved only for destructive consequences.

## Responsive reasoning

On mobile, privacy assurances and data summary appear before management actions. Destructive controls remain separated at the end of the page, preventing accidental taps among routine actions.

## Intended user effect

Users should feel that the app is private by design and that their data belongs to them. They should know exactly where it is stored, how to back it up, and how to remove it.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
