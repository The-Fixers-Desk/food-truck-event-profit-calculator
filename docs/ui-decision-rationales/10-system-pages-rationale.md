# System Pages — Design Rationale

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

System Pages define reusable patterns for empty, loading, error, not-found, and offline states so the product remains understandable when normal content is unavailable.

## Dominant task

Understand the current state and take the next appropriate action.

## Why the states are designed together

Failure and absence states are often implemented inconsistently when handled screen by screen. Presenting them as one system ensures shared messaging hierarchy, icon treatment, action placement, and tone.

Each state uses the same sequence: recognizable icon, plain-language title, brief explanation, one primary recovery action, and an optional secondary path. This consistency reduces the cognitive cost of unexpected moments.

## Tone and messaging

Messages avoid technical jargon, blame, and vague phrases. “We couldn’t load this event” explains the situation more usefully than an error code. “This event no longer exists” distinguishes absence from temporary failure.

The loading state communicates active work and uses skeleton elements to preserve layout expectations. The offline state acknowledges the network condition while emphasizing that local data remains available.

## Empty-state reasoning

“No saved events yet” is not treated as an error. It provides a constructive first action and an optional explanation. This turns an empty library into an onboarding moment rather than a dead end.

## Recovery hierarchy

- Retry is primary for temporary failures.
- Return to saved events is primary when the requested record is gone.
- Start first analysis is primary when no content exists.
- Offline messaging prioritizes continued local access before reconnection.

## Visual hierarchy

1. State title and icon
2. Primary next action
3. Brief explanation
4. Secondary recovery path
5. Supporting reassurance

## Responsive reasoning

Desktop may show the pattern gallery for documentation and testing, while actual runtime states occupy the available content area. Mobile states remain centered, concise, and action-led, with full-width primary buttons where appropriate.

## Intended user effect

Unexpected states should feel calm and recoverable. Users should always know what happened, what remains safe, and what they can do next.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
