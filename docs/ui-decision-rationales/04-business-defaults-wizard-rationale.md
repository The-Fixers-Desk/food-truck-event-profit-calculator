# Business Defaults Wizard — Design Rationale

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

The Business Defaults Wizard captures reusable assumptions that become the starting point for every event analysis.

## Dominant task

Complete the current default-setting step and continue.

## Why a wizard was chosen

Business assumptions span several categories and include conditional choices. Presenting everything on one page would create a dense form, increase error risk, and make progress difficult to judge. A guided five-step structure reduces cognitive load and lets each concept receive enough explanation.

The left-side step list provides both location and context. Completed steps remain visible, the active step is strongly emphasized, and upcoming steps preview the remaining work. This supports movement backward without making the process feel fragmented.

The active form occupies the larger right panel because data entry is the current task. The form uses conditional disclosure: only the input associated with the selected profit rule appears. This prevents irrelevant fields from creating ambiguity and matches the underlying storage model.

## Why defaults are separated from events

Defaults are reusable starting assumptions, not permanent rules. The interface repeatedly explains that they can be changed later and overridden per event. This distinction prevents users from feeling locked into an initial setup choice.

The “Current default snapshot” keeps previously entered values visible while the user completes later steps. This reinforces continuity and helps catch inconsistent assumptions before review.

## Action hierarchy

- **Continue** advances the guided path.
- **Back** supports correction without losing work.
- **Save and finish later** protects users who cannot complete setup in one session.
- Automatic-save messaging reduces fear of data loss.

## Visual hierarchy

1. Current wizard step and question
2. Selected choice and matching input
3. Step navigation
4. Current default snapshot
5. Reassurance and save status
6. Secondary wizard actions

## Responsive reasoning

Desktop uses simultaneous step navigation and form content. On mobile, the step index compresses and the active form becomes primary. Actions remain close to the current step, with Continue full width.

## Intended user effect

The user should feel guided rather than interrogated. Setup should appear structured, editable, and worth completing because it will make every future analysis faster and more consistent.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
