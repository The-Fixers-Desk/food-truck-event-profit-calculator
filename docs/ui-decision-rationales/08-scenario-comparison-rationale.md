# Scenario Comparison — Design Rationale

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

Scenario Comparison exposes the tradeoffs between multiple scenarios for the same event and helps the user choose the strongest option.

## Dominant task

Select the scenario that provides the best acceptable outcome.

## Why side-by-side comparison was chosen

Scenario differences are meaningful only in relation to one another. Three aligned cards allow users to compare revenue, cost, profit, margin, and break-even values without repeatedly switching views.

The strongest scenario receives a clear outline, badge, and recommendation summary. This emphasis is helpful but not absolute: the assumption table remains visible so users can judge whether the added profit requires unacceptable staffing, hours, or risk.

## Assumption transparency

The comparison table aligns the inputs that changed across scenarios. Mini bars and impact notes make direction and consequence scannable. The interface distinguishes “higher is better,” “lower is better,” and genuine tradeoffs such as more crew capacity at greater cost.

This prevents the comparison from becoming a beauty contest between profit numbers. Users can see why one result improved and what operational commitment produced it.

## Recommendation reasoning

The summary names the preferred scenario and explains it using profit, margin, and break-even. These are the core decision measures already established in the analysis workspace, preserving conceptual continuity.

“Keep selected scenario” is the primary action because comparison should end in a decision that returns to the chosen scenario rather than creating a separate permanent comparison object.

## Visual hierarchy

1. Selected/best scenario
2. Key result cards
3. Assumption differences
4. Recommendation summary
5. Add, select, and return actions

## Responsive reasoning

Desktop supports three side-by-side columns. Tablet compresses the comparison while retaining alignment. Mobile uses one scenario at a time with clear scenario switching and preserves a summarized recommendation, avoiding unreadably narrow columns.

## Intended user effect

The user should understand both the winner and the tradeoffs in seconds. The screen should create confidence that the selected option is not merely the highest number, but the best fit among operational alternatives.

## Relationship to implementation

This rationale records design intent. The approved mockup remains the visual source of truth, the engineering specification defines implementation details, and the acceptance checklist determines whether the finished screen passes. Changes that contradict this rationale should be treated as product-design changes and reviewed before implementation.
