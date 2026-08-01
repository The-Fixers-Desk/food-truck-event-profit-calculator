# Saved Events — Design Rationale

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

Saved Events is the product’s event library: the place users return to past estimates, reopen scenario work, and identify opportunities worth revisiting.

## Dominant task

Find and reopen the correct saved event.

## Why a table/list was chosen

Saved events are records with repeated comparable attributes: name, date, location, scenario count, update time, recommendation, and actions. A structured list provides faster scanning than a card grid and allows many events to remain visible at once.

The summary strip gives library-level context without becoming a generic analytics dashboard. Counts for events, scenarios, and recent updates help users understand the size and activity of their saved work.

## Findability

Status filters, sorting, search, and pagination support a growing library. Recommendation filters use both labels and semantic icons so users can quickly isolate promising or questionable events.

The default sort emphasizes recently updated work because continuity is the most common return behavior. The table also shows the last-updated timestamp to help distinguish similarly named events.

## Comparison entry points

Each event offers both Open and Compare actions. Open resumes the event’s analysis workspace, while Compare moves directly into scenario comparison when enough scenarios exist. Keeping both available reduces unnecessary navigation.

## Visual hierarchy

1. Saved event names
2. Recommendation states and quick actions
3. Date, location, and scenario count
4. Library filters and sorting
5. Summary totals and pagination

## Responsive reasoning

Desktop retains a semantic table. Tablet reduces column density, and mobile transforms each row into a labeled event card rather than forcing horizontal scrolling. The mobile card preserves event identity, recommendation, scenario count, and the primary continuation action.

## Intended user effect

Users should be able to re-enter past work immediately and feel that their analyses form an organized, persistent library rather than a collection of disconnected calculations.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
