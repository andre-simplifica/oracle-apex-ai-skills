# Internal APEX APIs

Use internal APEX APIs only when the change is large, repeatable, multi-page, or safer through a controlled script.

## When to Use

- Create multiple components with a repeatable pattern.
- Apply a change across multiple pages.
- Generate a new screen from a well-documented pattern.
- Fix metadata when Page Designer would be slow and error-prone.

Do not use this path for small adjustments when Page Designer is simpler.

## Rules

- Resolve workspace/schema dynamically.
- Set the correct security group.
- Use the app id from the project profile.
- Locate parent regions by `application_id`, `page_id`, and `static_id`.
- If there is no reliable `static_id`, stop and choose a safer route.
- Create existence guards for reruns.
- Abort on ID collision or ambiguous components.
- Query `all_arguments` when API signatures are uncertain.
- Apply changes in small units.
- Validate metadata and runtime behavior afterwards.

## Temporary Export

If using a temporary export as reference:

- Preserve `begin` / `end;` / `/` boundaries.
- Never nest anonymous blocks.
- Do not alter `component_begin` / `component_end` wrappers.
- Do not import without a plan and validation.
