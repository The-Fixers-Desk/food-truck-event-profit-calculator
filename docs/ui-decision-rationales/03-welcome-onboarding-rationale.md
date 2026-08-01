# Welcome / Onboarding — Design Rationale

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

The Welcome screen introduces the product, reduces uncertainty, and guides first-time users into a short default-setup process before their first analysis.

## Dominant task

Begin business-default setup.

## Why this structure was chosen

First-time setup can feel like work before value is visible. The design therefore explains what will happen, how long it will take, why it matters, and how the user’s data is handled before asking for commitment.

The headline frames the product personally: “Welcome to your event profit calculator.” The supporting copy explains the payoff of defaults—future analyses begin with numbers that already reflect the user’s business.

The three-step indicator provides a finite journey: Setup, Defaults, Dashboard. This prevents onboarding from feeling open-ended. “What happens next” breaks the process into understandable outcomes rather than technical configuration categories.

The “Before you begin” panel addresses likely friction directly: time, editability, and local storage. The privacy banner reinforces the app’s offline-first model at the exact moment trust matters most.

## Action hierarchy

- **Start setup** is the clear primary path.
- **What you’ll set up** supports users who need more context before proceeding.
- **I’ll do this later** preserves autonomy without competing visually with the recommended path.

Allowing deferral prevents onboarding from feeling coercive, while the strong primary treatment still communicates the preferred sequence.

## Visual hierarchy

1. Welcome headline and Start setup
2. Setup progress
3. What happens next
4. Before you begin
5. Privacy reassurance
6. Secondary and defer actions

## Responsive reasoning

On mobile, the progress indicator remains near the top, actions stack, and explanation cards become a vertical sequence. This maintains the emotional order: understand the process, choose to begin, then review details.

## Intended user effect

The screen should make first use feel calm, finite, and trustworthy. Users should begin setup knowing what they are doing, why it helps, and that they remain in control.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
