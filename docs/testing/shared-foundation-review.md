# Shared foundation acceptance review

## Application Shell

- PASS: approved charcoal/copper tokens, typography, spacing, radii, borders, controls, focus treatment, and reduced-motion behavior.
- PASS: 280 px desktop sidebar, 64 px top bar, 1280 px centered content, specified responsive padding, and no shell-level horizontal overflow.
- PASS: branding, active navigation, bottom workspace menu, breadcrumbs, search, notifications, help, page-header actions, and route-stable shell.
- PASS: below 1024 px the sidebar becomes a keyboard-managed drawer; Escape/backdrop close it and focus returns to the trigger.
- PASS: desktop, mobile, keyboard, interaction, visual-comparison, and regression evidence is recorded in `docs/testing/shared-foundation/`.

## System Pages

- PASS: Empty, Loading, Error, Not Found, and Offline use one shared state component with configurable icon, copy, actions, live behavior, and status label.
- PASS: approved customer-facing copy and recovery actions are used; no raw technical errors or account claims appear.
- PASS: loading is integrated with Event Inputs submission; Saved Events, 404, 500, and offline handling use the shared patterns.
- PASS: every state is available through the deterministic testing-only `/test-system-states` route and remains complete on mobile.

## Final gate

- PASS: implementation, automated tests, responsive checks, keyboard checks, interaction checks, and side-by-side visual QA.
- PENDING: product-owner approval must be recorded by the product owner after reviewing the supplied evidence.
