# Security Policy

This repository is public. Treat every issue, pull request, screenshot, log, export, and profile example as publicly visible.

## Do Not Share Sensitive Data

Do not open issues or pull requests containing:

- passwords, API keys, OAuth secrets, bearer tokens, refresh tokens, private keys, wallets, or connection strings;
- private APEX, ORDS, database, OCI, VPN, intranet, or customer URLs;
- real workspace names, schema names, application aliases, hostnames, service names, IP addresses, or internal usernames when they identify a private environment;
- customer names, production data, dumps, exports, screenshots, invoices, contracts, medical, legal, HR, or financial data;
- browser screenshots that expose sessions, cookies, customer information, or private navigation;
- logs with request bodies, response bodies, headers, stack traces, or payloads that have not been sanitized.

Use placeholders instead:

```text
https://apex.example.com/ords/
APP_SCHEMA
WORKSPACE_NAME
DEV_SQLCL_CONNECTION
Bearer <redacted>
```

## Project Profiles

The template at `templates/project-profile.md` is meant to be copied into a consuming project.

If your project profile contains private URLs, real workspace names, schema names, customer references, environment details, SQLcl aliases, or operational rules that should not be public, keep it in a private repository.

Do not copy a filled project profile into this public repository.

## Reporting a Security Issue

If you find a security problem in these skills or helper scripts, do not disclose private details in a public issue.

Open a minimal issue that says a security concern exists, or contact the repository owner privately through the available GitHub profile or organization channel.

## Sanitizing Before Contribution

Before sharing examples, replace:

- real URLs with `https://apex.example.com/ords/`;
- real schemas with `APP_SCHEMA`;
- real workspaces with `WORKSPACE_NAME`;
- real application IDs with `100`;
- real credentials with `<redacted>`;
- real customers with `Example Customer`;
- real screenshots with sanitized mockups.

When in doubt, remove the detail.
