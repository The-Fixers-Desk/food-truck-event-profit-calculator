# Application Shell — Design Rationale

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

The Application Shell establishes the persistent frame that makes every feature feel like part of one product. Its job is not to compete with page content; it provides orientation, navigation, identity, and stable access to global utilities.

## Dominant task

Help the user understand where they are and move confidently between the product’s major areas.

## Why this structure was chosen

The fixed desktop sidebar gives the product a serious operational-tool character and keeps the six primary destinations visible without hiding them behind a menu. Branding remains at the top because the product name is long and benefits from a stable, recognizable home. The user module is pinned to the bottom so account and workspace context remain available without interrupting task navigation.

The top bar separates global utilities from page-specific actions. Breadcrumbs on the left reinforce location and hierarchy, while search, notifications, and help remain predictably placed on the right. The page header beneath it holds the title, explanation, and actions so every major screen begins with the same mental model.

The content container uses a maximum width rather than stretching indefinitely. This protects readability, keeps complex financial interfaces scannable, and prevents large monitors from producing disconnected layouts.

## Visual hierarchy

1. Page title and primary action
2. Page description and secondary actions
3. Main page content
4. Persistent navigation and utilities
5. Supporting metadata

The active navigation state uses a copper edge and elevated charcoal fill. This is intentionally stronger than a color-only change so the selected destination remains obvious in peripheral vision.

## Responsive reasoning

Below desktop width, the sidebar becomes a drawer accessed from a compact top app bar. This preserves content width for forms, analysis, and comparison while retaining the same information architecture. Primary actions become wider and action groups stack before content becomes cramped.

## Key design decisions

- A 280 px sidebar accommodates the product name and readable navigation labels.
- A 64 px top bar creates a clear utility region without consuming excessive vertical space.
- Charcoal surfaces remain neutral so copper and semantic colors carry meaning.
- Page actions live consistently in the header rather than drifting into content.
- Overflow actions are separated from the primary path to keep each page focused.

## Intended user effect

The shell should make the product feel stable, trustworthy, and easy to learn. After visiting two or three screens, the user should know where navigation, actions, help, and account context will always be.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
