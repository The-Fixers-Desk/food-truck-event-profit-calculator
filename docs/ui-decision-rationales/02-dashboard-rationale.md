# Dashboard — Design Rationale

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

The Dashboard is the fastest path into meaningful work. It answers two questions immediately: “What should I do next?” and “Where did I leave off?”

## Dominant task

Start a new event analysis.

## Why this structure was chosen

The left side is a large, simple hero because the most valuable first action is creating a new analysis. The question “Is your next event worth it?” expresses the user’s real decision rather than describing software functionality. The primary button sits directly beneath that question so the path from intent to action is immediate.

The recent-events list occupies the right side because resuming work is important but secondary. This arrangement prevents saved work from overwhelming a first-time or task-focused user while still making continuity visible.

The page avoids a grid of generic dashboard cards. The product is not a monitoring console; it is a decision tool. A focused hero plus a short recent-work list better reflects how users return to the app.

## Visual hierarchy

1. Decision-oriented hero question
2. Analyze new event action
3. Continue where you left off
4. Individual recent events and scenario metadata
5. View all saved events

The large headline and generous negative space make the primary action unmistakable. Recent rows use lighter hierarchy and dividers rather than heavy cards so they remain easy to scan.

## Content decisions

Recent rows include event name, scenario, date, location, and scenario count because those details help users distinguish similar events without opening them. Only the three most recently updated events appear, keeping the dashboard concise.

The wording “Continue where you left off” emphasizes continuity rather than file management. “View all saved events” clearly routes users to the complete library.

## Responsive reasoning

On narrower screens, the hero stacks above recent events. This preserves the dominant-task order and avoids shrinking the headline into a narrow column. The primary action becomes full width on mobile because it is the screen’s main purpose.

## Intended user effect

The user should feel that the app is ready to help immediately. Whether beginning a new estimate or returning to an existing one, the next step should be obvious within seconds.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
