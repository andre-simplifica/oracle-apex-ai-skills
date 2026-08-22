# Dynamic Content Regions and Package-Owned UI

Actively consider an APEX Dynamic Content region backed by a project-owned PL/SQL package when the screen needs a branded or non-standard layout, coordinated filters, clickable dashboard interactions, custom grouping, print/PDF behavior, or reusable HTML composition that native components would make unnecessarily rigid.

This is a preferred option, not a universal replacement for native APEX components. Use Interactive Report, Interactive Grid, Forms, Cards, Faceted Search, and other native components when they already meet the requirement with better accessibility and maintenance.

## Ownership

- Keep business queries, authorization, tenant scope, and HTML composition in the project-approved package.
- Prefer a package function returning `CLOB` for document/region rendering.
- Keep page processes thin and bind-driven.
- Escape user-controlled text and attributes with the appropriate APEX escape APIs.
- Enforce authorization and company/customer scope server-side; hidden markup is not access control.
- Store reusable CSS/JavaScript in project-owned assets or the approved runtime, not as repeated page fragments.

## Interactions

For filters, export actions, drilldowns, chart clicks, grouping, or region refresh:

- assign stable, documented region and control Static IDs;
- use page items and bind variables for state;
- declare every required `Items to Submit` value;
- prefer native Dynamic Actions for simple orchestration;
- use `apex.server.process` only with an authorized AJAX callback and a defined JSON contract;
- refresh only the affected region when possible;
- preserve keyboard access, focus, loading state, empty state, and error state;
- validate initial render and the real post-refresh interaction path.

When a chart is the main requirement, route to the optional `oracle-apex-echarts` repository if installed. When the requirement is a branded report/help/PDF document, route to the optional `build-apex-brand-reports` repository if installed.

## Pattern Learning

When the user declares a button, layout, naming, filter, dashboard action, or package convention to be a project standard:

1. inspect the real example page and runtime behavior;
2. distinguish a reusable rule from a one-page exception;
3. record the rule in `.oracle-apex-ai/app-patterns.md` and detailed evidence in `.oracle-apex-ai/page-patterns/`;
4. reference the canonical example page;
5. apply the recorded rule to later pages without silently rewriting existing exceptions.

Project updates must preserve these learned files byte-for-byte.
