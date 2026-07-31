# Pull Request

## Summary

Describe what changed and why.

## Scope

- [ ] Generic APEX development guidance
- [ ] Project installation/update and routing
- [ ] Cooperative object-lock runtime/workflow
- [ ] Baseline/export/snapshot/release guidance
- [ ] Project-profile template
- [ ] Install/update scripts
- [ ] Documentation
- [ ] Security/safety guidance

## Safe Contribution Checklist

- [ ] This change does not include passwords, tokens, wallets, private keys, API keys, or connection strings.
- [ ] This change does not include private URLs, internal hostnames, real schema names, real workspace names, or real customer names.
- [ ] This change does not include production data, dumps, screenshots, payloads, or logs with sensitive content.
- [ ] Project-specific rules stayed in project-profile examples or docs and were not added as universal core rules.
- [ ] Any APEX version assumptions are explicit.
- [ ] File installation does not silently mutate Oracle.
- [ ] Project-owned profiles, patterns, and migrations remain preserved.
- [ ] Structural DDL uses the pending-migration workflow.
- [ ] I ran `bash scripts/validate_repo.sh`.

## Notes for Reviewers

Mention any compatibility, safety, or migration concern.
