# First-use, Defaults, and Dashboard acceptance review

## Welcome / Onboarding

- PASS: first-use routing, approved hero, three-stage progress, action hierarchy, setup preview, reassurance, privacy copy, desktop/mobile composition, and no database writes on entry or deferral.
- PASS: `Start setup` opens Defaults; `What you'll set up` moves to the preview; `I'll do this later` opens a limited Dashboard without exposing setup-dependent workflows.
- PASS: deferred state survives an application restart through the signed local session; completed setup is determined from persisted Defaults after restart.

## Business Defaults Wizard

- PASS: exactly five ordered sections: Revenue assumptions, Food cost method, Profit rule, Operating assumptions, and Review.
- PASS: completed/active/upcoming navigation, conditional food/profit inputs, step validation, invalid-value preservation, Back/Continue, review Edit actions, and full completion persistence.
- PASS: unfinished progress and active step save locally through browser storage; `Save and finish later` returns to Dashboard without creating a partial database record.
- PASS: the snapshot reads persisted values only; existing model validation, Decimal/scaled-integer storage, labor ordering, and optional-field behavior remain intact.
- PASS: mobile shows first-use progress, horizontal step navigation, `Step n of 5`, and a full-width primary action in the sticky action area.

## Dashboard and cross-screen flow

- PASS: approved decision hero, single dominant action, empty state, three real most-recent events, whole-row reopen links, scenario badges, and Saved Events link.
- PASS: Welcome -> Defaults -> Dashboard, deferral, later Defaults editing, setup safeguards, persistence after restart, and no fake recent work.

## Final gate

- PASS: automated, browser interaction, responsive, console, persistence, and side-by-side visual QA.
- PENDING: product-owner approval must be recorded by the product owner after reviewing the supplied evidence.
