# APEX Pattern Learning

Use this to understand how the application already works before creating or changing a screen.

## Principle

- Temporary exports and APEX metadata are read-only analysis tools.
- Versioned snapshots are functional reference.
- Screen implementation should happen through Page Designer or a controlled script, according to the project profile.
- Do not edit versioned exports as the default implementation path.

## Read-Only Inspection

When you need to understand a page:

1. Export to `/tmp` or another temporary folder outside the versioned snapshot.
2. Read regions, items, buttons, processes, Dynamic Actions, validations, conditions, SQL sources, `static_id`, and `Items to Submit`.
3. Summarize the current flow.
4. Do not execute `install.sql` or `install_component.sql`.
5. Do not stage temporary output.

Example:

```bash
printf 'apex export -applicationid 100 -split -dir /tmp/apex_readonly_p123 -expComponents "PAGE:123"\nexit\n' | sql -S -L -name DEV
```

Adjust `applicationid`, directory, and connection according to the project profile.

## Local Catalog

The consuming project can maintain:

```text
.oracle-apex-ai/app-patterns.md
.oracle-apex-ai/page-patterns/
```

Record:

- good pages to copy;
- legacy pages to avoid;
- region, page, label, and button templates;
- breadcrumb patterns;
- menu patterns;
- button patterns;
- dialog/modal/drawer patterns;
- common Dynamic Actions;
- messages and user-facing terms;
- called packages;
- SQL source examples.

## Classification

- **Read-only**: understand a page, compare patterns, locate components.
- **Small adjustment**: label, condition, short text, template option, simple button.
- **Repeatable change**: multiple pages/components with a clear pattern.
- **New/complex screen**: requires example pages, local profile, and phased validation.
- **Backend**: requires versioned package/script, compilation, and `user_errors`.

## Expected Result

To create a new page, the agent must:

1. identify sibling/example pages;
2. read the local profile;
3. copy real patterns instead of inventing generic layout;
4. apply changes incrementally;
5. validate runtime behavior.
