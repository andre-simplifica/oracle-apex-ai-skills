# Object Browser

Use Object Browser when SQLcl is unavailable, when the project requires Builder UI, or when a focused change is safer through the interface.

## Rules

- Confirm workspace, schema, and environment.
- Paste complete package specification/body when compiling a package.
- Check compilation success.
- Inspect errors if compilation fails.
- Do not create/drop objects without an explicit request.

## After Compiling

Even when compiling through Object Browser, validate runtime behavior if the package affects an APEX screen.
