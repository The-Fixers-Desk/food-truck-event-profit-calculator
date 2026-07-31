# Senior product-design review

## Audit evidence and health

General health before recomposition: **functionally strong, visually noisy**.
The workflows were understandable, but global labels, repeated destination
cards, oversized management objects, and equal-weight actions obscured each
screen's main job.

1. [Welcome before](senior-design-audit/01-welcome.png) used four bordered
   instruction cards and read like documentation. [Welcome after](senior-design-audit/16-welcome-revised.png)
   leads with the decision the product supports, a three-step sequence, and one
   action.
2. [Dashboard before](senior-design-audit/02-dashboard.png) repeated four
   global destinations beneath its primary action. [Dashboard after](senior-design-audit/11-dashboard-revised.png)
   makes new analysis dominant and turns recent work into compact semantic links.
3. [Saved Events before](senior-design-audit/05-saved-events.png) exposed open,
   rename, and delete controls for every record. [Saved Events after](senior-design-audit/12-saved-events-revised.png)
   uses compact scenario rows, whole-row open links, and disclosed management.
4. [Analysis before](senior-design-audit/08-analysis.png) led with assumptions,
   showed six peer actions, and exposed raw Decimal strings. [Analysis after](senior-design-audit/13-analysis-revised.png)
   strengthens the decision column, consolidates secondary scenario actions,
   and formats every visible financial result.
5. [Dashboard narrow before](senior-design-audit/07-dashboard-narrow.png) stacked
   duplicate destination cards. [Dashboard narrow after](senior-design-audit/14-dashboard-narrow-revised.png)
   retains the primary task and compact recent row without duplicate navigation.
6. [Saved Events narrow after](senior-design-audit/15-saved-events-narrow-revised.png)
   preserves search, sort, selection, open, and management without page-wide
   overflow. The pre-change state is [available here](senior-design-audit/09-saved-events-narrow.png).

Static inspection and focused tests also covered Defaults, Event Inputs,
Comparison, Data Safety, dialogs, empty/no-results, recovery, and error states.
The screenshot review verifies visual hierarchy and overflow, but it is not a
screen-reader audit; semantic landmarks, names, current-page state, disclosure
controls, and focus-visible rules are covered by automated markup tests.

## Capability inventory (before recomposition)

| Capability | Preserved access |
| --- | --- |
| Dashboard | Primary navigation: Dashboard |
| New analysis / Event Inputs | Primary navigation: New analysis; Dashboard primary action |
| Business Defaults | Primary navigation: Business defaults |
| Event Analysis | Dashboard recent work; Saved Events event/scenario rows |
| Save / overwrite | Event Analysis scenario actions and save dialog |
| Save as new | Event Analysis scenario actions and save dialog |
| Reset | Event Analysis scenario actions |
| Rename Event / Scenario | Saved Events disclosed management actions |
| Delete Event / Scenario | Saved Events disclosed management actions, including final-Scenario protection |
| Saved Events | Primary navigation; restrained Dashboard link |
| Search / sort | Saved Events toolbar |
| Comparison selection | Saved Events Scenario rows |
| Comparison results | Compare selected action |
| Baseline selection | Scenario Comparison controls |
| Show differences only | Scenario Comparison controls |
| Data Safety | Primary navigation |
| Download backup | Data Safety primary task |
| Restore backup | Data Safety secondary task with confirmation |
| Recovery | Recovery-mode Data Safety route and restore workflow |
| Onboarding | Welcome and first Business Defaults setup |
| Error handling | Existing not-found and application-error routes |

## Manual review checklist

Inspect Welcome, Dashboard, Business Defaults, Event Inputs, Event Analysis,
Saved Events, Scenario selection, Scenario Comparison, Data Safety, dialogs,
empty/no-results/error/recovery states, narrow layouts, and long-content states.
For each state verify:

- one dominant task, focal point, and primary action;
- redundant navigation and repeated actions are absent;
- cards and borders identify real objects or decisions only;
- metadata is concise and subordinate;
- whitespace supports the task without hiding useful work;
- row interactivity is obvious and keyboard accessible;
- headings are not duplicated by generic shell context;
- low-priority content is progressively disclosed;
- source order, focus visibility, status announcements, and target sizes hold;
- narrow layouts retain identity and the primary task without page-wide overflow.

## Substantive removals and relocations

- Dashboard destination cards were removed; Saved Events, Business Defaults,
  Data Safety, and comparison selection remain in primary navigation or Saved
  Events.
- Generic shell context labels were removed; event/scenario context remains on
  Event Analysis where it is meaningful.
- Repeated Dashboard buttons were consolidated into semantic whole-row links.
- Event and Scenario management actions remain in compact disclosures rather
  than competing with the primary open action.
- Low-priority Event Analysis calculations remain available in disclosures;
  the decision summary leads the workspace.
