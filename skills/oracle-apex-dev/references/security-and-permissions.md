# Security and Permissions in APEX

Use this reference when work touches authentication, authorization, credentials, public pages, REST services, ACLs, grants, or sensitive data.

## APEX Security

- Check authentication scheme before changing login or session behavior.
- Check authorization schemes before exposing buttons, pages, regions, processes, or REST actions.
- Do not remove authorization conditions to "make it work".
- Treat public pages, public REST endpoints, and unauthenticated AJAX callbacks as high risk.
- Preserve Session State Protection unless there is a clear reason and explicit approval.

## Credentials

- Prefer APEX Web Credentials or the consuming project's secure credential mechanism.
- Do not store secrets in page items, application items, constants, Git, docs, screenshots, or issue comments.
- If a project currently has hardcoded secrets, do not copy that pattern into new code. Flag it as technical debt or a security risk.
- Redact secrets in logs, debug output, and examples.

## ORDS and REST Modules

- Confirm module, template, handler, privilege, and role mapping.
- Confirm whether the endpoint is public or private.
- Do not change CORS, OAuth, roles, or privileges without understanding consumers.
- Validate OpenAPI docs against the real handler when available.

## Database Permissions

- Use least privilege.
- Avoid broad system privileges.
- Prefer role or schema-specific grants documented in migrations.
- Do not grant access directly in production without explicit approval and a deployment trail.

## Sensitive Data

- Do not expose customer data, personal data, financial data, legal/medical/HR data, internal IDs, or raw payloads in public docs.
- User-facing messages should be business-safe and should not reveal internals.
- Admin/debug screens still need access control and careful wording.

## Review Questions

- Who can access this page/action/API before and after the change?
- Does the change expose data to a broader audience?
- Are secrets stored or logged anywhere?
- Is there a project-approved auth pattern?
- Is the change safe for DEV only, or does it affect PROD?
