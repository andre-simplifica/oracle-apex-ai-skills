# Oracle APEX Version Compatibility

Use the confirmed live APEX version, not a repository label or database version, to select behavior.

Read it from the authorized target connection before applying a gate:

```sql
select version_no
  from apex_release;
```

Confirm `USER` and `SERVICE_NAME` in the same SQLcl session. A value copied from documentation, an export directory name, or another environment is not runtime evidence.

Run the managed gate before a version-specific operation:

```bash
python3 Util/scripts/validate_oracle_apex_compatibility.py \
  --apex-version <confirmed-version>
```

Use `--require apex-26.1-public-apis` before calling a public API introduced in 26.1. Use `--require readable-yaml-export` before requesting readable YAML. A request for `--require apexlang` always fails because APEXlang operations are outside this repository.

## Compatibility Matrix

| Confirmed APEX version | Kit status | Public APIs introduced in 26.1 | Official application export |
| --- | --- | --- | --- |
| Below 24.2 | Blocked | Blocked | Blocked |
| 24.2 through releases before 26.1 | Supported | Blocked | Split SQL + readable YAML + monolithic SQL |
| 26.1 or later | Supported | Available after signature and privilege checks | Split SQL + monolithic SQL |

The 24.2 minimum is the supported and tested project baseline. Dynamic Content returning CLOB exists in Oracle APEX 22.2 and later, but releases below 24.2 remain outside this kit's supported contract.

## APEXlang Boundary

Oracle APEX and SQLcl expose APEXlang beginning with release 26.1. This kit records that product capability only so it can avoid accidental use.

Never use this kit to:

- run APEXlang generate, export, validate, or import;
- request `READABLE_YAML` on APEX 26.1 or later, because Oracle produces APEXlang instead;
- parse, edit, compile, diff semantically, or publish `.apx` application source;
- invoke an API whose purpose is to produce or consume APEXlang as an application workflow.

Use standard SQL exports for application source and import. A future, separate repository may own APEXlang workflows.

## Capability Is Not Authorization

A version gate only says that a feature belongs to the product release. Before a public API call, verify its synonym, target object, visible signature in `ALL_ARGUMENTS`, required role, and intended runtime behavior. Before an internal API call, use a fresh SQL export from the exact target version and inspect the live implementation signature.

Primary Oracle references:

- [APEX 26.1 API changes](https://docs.oracle.com/en/database/oracle/apex/26.1/aeapi/changes-in-this-release.html)
- [APEXlang prerequisites](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/26.1/sqcug/prerequisites-apexlang.html)
- [Dynamic Content introduced in APEX 22.2](https://docs.oracle.com/en/database/oracle/apex/22.2/htmrn/new-features.html)
