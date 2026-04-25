# REST Integrations in Oracle APEX

Use this reference when creating, reviewing, or debugging outbound REST/API integrations from Oracle APEX or PL/SQL.

## Preferred Approach

- Prefer `apex_web_service.make_rest_request` for CLOB responses.
- Use `apex_web_service.make_rest_request_b` only when the response is binary.
- Use `apex_web_service.t_multipart_parts`, `append_to_multipart`, and `generate_request_body` for multipart uploads.
- Prefer APEX Web Credentials or the consuming project's secure credential mechanism when available.
- If the project has OpenAPI files or API docs, read them before inventing endpoints, headers, payloads, or auth rules.

## Secrets and Credentials

- Never hardcode tokens, API keys, passwords, client secrets, wallets, or private keys.
- Never log raw `Authorization`, `access_token`, `api_key`, `x-api-key`, password, cookie, wallet, or refresh token values.
- When examples are needed, use placeholders such as `<redacted>`, `Bearer <token>`, or `https://api.example.com`.
- Keep auth behavior project-specific. The shared skill can say how to inspect it, not which private credential to use.

## Request Checklist

- Clear `apex_web_service.g_request_headers` before setting headers.
- Set explicit `Content-Type` when sending a body.
- Set explicit `Accept` when the provider supports it.
- Use a clear `User-Agent` when the project standard requires one.
- Normalize HTTP method casing.
- Build JSON through safe JSON APIs or carefully reviewed string construction.
- Use bind variables for values coming from APEX items or SQL.
- Confirm timeout and retry expectations. Do not add retries blindly.

## Response Checklist

- Capture `apex_web_service.g_status_code`.
- Treat 2xx, 4xx, and 5xx differently.
- Validate that the response body exists when the downstream flow depends on it.
- Parse JSON with `json_value`, `json_table`, `apex_json`, or the project standard.
- Do not expose raw provider errors to end users.
- Log sanitized metadata: operation, URL category, method, status, duration, attempt, and a redacted error summary.
- Preserve technical details in internal logs only when secrets and personal data are removed.

## Error Handling

- Do not use `when others then null`.
- Raise or return a structured error that the caller can handle.
- Separate user-facing messages from technical diagnostics.
- For OAuth flows, validate missing `access_token`, `refresh_token`, expiration, consent, and revoked credentials explicitly.
- For webhooks, validate signature/authentication before trusting payload content.

## Before Closing

- Confirm the endpoint and auth method from project docs, OpenAPI, package code, or user-provided context.
- Test a success case and a known failure case when the environment allows it.
- Confirm the integration does not leak secrets in logs, page output, APEX debug, or Git diffs.
