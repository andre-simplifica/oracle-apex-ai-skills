# APEX Debugging

Use this reference when diagnosing APEX runtime errors, broken Dynamic Actions, AJAX issues, upload flows, or "it works in Page Designer but not in runtime" situations.

## First Alignment

Confirm these surfaces point to the same application and environment:

- Page Designer;
- runtime application session;
- Session State;
- SQLcl/Object Browser;
- exported page files used as reference;
- current DEV/TEST/PROD environment.

Do not assume a package compilation or Page Designer save changed the runtime path until the runtime session proves it.

## Minimum Checks

- Correct application ID and page ID.
- Correct runtime session.
- Correct user, authorization scheme, and role.
- Correct request value and submit button.
- Required items exist in Session State.
- Dynamic Action `Items to Submit` includes every item used by server-side logic.
- Region Static ID matches refresh or AJAX code.
- Server-side condition is true when expected.
- Process point and sequence match the intended flow.

## Dynamic Actions and AJAX

- Check triggering event, selection type, affected elements, and client-side condition.
- Check true/false action order.
- Check `Wait for Result` when later actions depend on AJAX completion.
- Inspect AJAX callback/process code and return format.
- Validate JSON shape before changing UI code.
- If a Dynamic Content region depends on item values, submit the items and refresh the region explicitly.

## Upload, Import, Wizard, and Async Flows

For upload/import/wizard flows, test the real cycle:

- upload/select file;
- validate;
- review warnings/errors;
- import/confirm;
- inspect staging/history tables;
- test known failure;
- test rollback/reversal when the flow supports it.

If validation should persist staging/history and it does not, treat that as functional evidence. Do not keep adjusting UI blindly.

## APEX Debug

- Enable APEX debug only in an appropriate non-production context unless the user explicitly authorizes otherwise.
- Capture the relevant request, page, process, item, and error lines.
- Remove session IDs, URLs, user/customer data, and payloads before sharing externally.
- Use debug output to prove sequence and condition behavior, not just to collect stack traces.

## Generic Error Triage

When the screen shows a generic APEX error:

- capture exact user action and page request;
- inspect APEX debug/error details when available;
- check Session State values used by the failing process;
- query staging/history/log tables if the flow should persist data;
- inspect `user_errors` for recently changed PL/SQL;
- verify that runtime is using the expected code path.

Close the task only after the runtime behavior matches the business request or the blocker is clearly documented.
