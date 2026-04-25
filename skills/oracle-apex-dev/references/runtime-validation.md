# Runtime Validation

No visual or functional APEX screen change is ready without runtime validation, unless the user explicitly asked for analysis only.

## Minimum Checklist

- Page saved.
- PL/SQL objects compiled when applicable.
- Application run in the correct environment.
- Correct page, session, and context.
- Main flow tested.
- Known failure case tested when relevant.
- Text uses user-facing language.
- Layout has no broken sections, excessive empty space, poor scrolling, or truncated text.
- Error/success messages are understandable.

## Dynamic Actions and AJAX

- Check Session State.
- Check `Items to Submit`.
- Check affected region and `static_id`.
- Prefer native Dynamic Actions when available.
- Test real refresh, not only initial page load.
- Validate JSON/HTML response and error handling.

## Diagnosis

For generic errors, align:

- Page Designer;
- SQLcl/Object Browser;
- runtime;
- Session State;
- persisted staging/history data when relevant.
