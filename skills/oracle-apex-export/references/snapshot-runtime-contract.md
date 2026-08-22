# Database Snapshot Runtime Contract

A project may use `PK_DDL_SNAPSHOT` or another reviewed implementation to capture immutable database source. The runtime is optional and project-owned; installing this skill kit never creates snapshot tables or packages.

## Required Capabilities

The project profile must name the canonical audit, install/upgrade, export, retention, and uninstall commands. A compatible runtime must provide evidence for:

- one confirmed current snapshot ID reused by every downstream worker;
- normalized object identity: owner, type, name, and optional subname;
- a stable normalized DDL hash, preferably SHA-256;
- full inventory and full extraction from a specific snapshot;
- partial comparison against one explicit base snapshot;
- new, changed, unchanged, and removed inventory status;
- deterministic rendering into the five-file release contract;
- stored-script and snapshot counts before cleanup;
- bounded cleanup APIs that keep the configured history;
- installation audit and uninstall behavior appropriate to its own objects.

The runtime must not turn a missing current object into an automatic `DROP`. Record it as a removal candidate and route the change through reviewed pending DDL.

## Adapter Boundary

Projects can keep their existing proven snapshot package. Record its commands and any API mapping in `.oracle-apex-ai/project-profile.md`; keep private schema names and connection details out of this reusable core.

The default retention policy recognizes a compatible package named `PK_DDL_SNAPSHOT` with `purge_old_scripts` and `purge_old_snapshots`. Change the package name in `.oracle-apex-ai/export-policy.json` only after verifying the real signature. The retention helper emits review SQL; it does not connect or execute cleanup.

If no snapshot runtime exists, the project may use another immutable source boundary, but it must still produce the same lineage, hashes, counts, full/partial semantics, and five-file validation evidence. Do not fabricate a snapshot ID.

## Upgrade Rule

Before changing a project snapshot runtime:

1. audit its current tables, package signature, stored snapshots, and purge behavior;
2. compare the proposed contract with the existing canonical exporter;
3. preserve snapshots required by active comparisons or retries;
4. run a dry extraction from one existing snapshot;
5. validate both a full and a partial five-file candidate;
6. authorize installation/upgrade, retention, and uninstall as separate database mutations.
