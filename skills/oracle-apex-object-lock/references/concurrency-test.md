# Two-session Ownership Smoke Test

`Util/scripts/object_lock_smoke.py` exercises the installed cooperative runtime
`1.1.0` using two independent SQLcl processes kept open for the scenario. This is
a database mutation, separate from file installation or a read-only audit.

## Prerequisites

- Explicit authorization for a **disposable, isolated DEV schema** with the
  runtime already installed and audited. No other process may use that schema
  during the test. The harness does not install or compile anything.
- An initially empty `DEV_OBJECT_LOCK` table. Runtime acquire, assert and release
  can expire other active rows through autonomous transactions; a unique fixture
  name alone would not isolate their effects. The guard rejects any row outside
  its own generated fixture key. Use a fresh lab for a new run; do not purge real
  history to satisfy the guard.
- A confirmed saved SQLcl connection. The harness accepts a simple saved name,
  never credentials or a connection string. SQLcl must support `connect -name`
  and noninteractive stdin. Review local SQLcl startup scripts before execution.
- POSIX (Linux/macOS), Python 3.10+, SQLcl on PATH or an approved launcher, and
  database-only expectations from [target-preflight.md](../../oracle-apex-dev/references/target-preflight.md).
  The session user and current schema must be equal. No APEX session or APEXlang
  operation is needed for this database-runtime test.

## Plan, Then Execute in the Authorized Lab

```bash
python3 Util/scripts/object_lock_smoke.py \
  --expect /private/path/lab-target.json --connection DEV_SQLCL_CONNECTION
```

The default only validates the local inputs and reports the plan. After reviewing
the actual target and obtaining authorization for this test:

```bash
python3 Util/scripts/object_lock_smoke.py \
  --expect /private/path/lab-target.json --connection DEV_SQLCL_CONNECTION \
  --run --confirm ISOLATED_DEV_LOCK_TEST
```

Use `--sql /path/to/approved/sql` if necessary. The confirmation is an execution
interlock, not evidence that a target is DEV; the operator must establish that
from the project's environment record. All sessions independently check identity.

Expected sequence:

1. A acquires and asserts the synthetic `PACKAGE` key; no actual package is created.
2. B's acquisition must raise `-20083`, and B's assertion must raise `-20088`.
3. A releases; B then acquires, asserts and releases that same key.
4. A fresh cleanup session checks identity, releases any remaining fixture-owned
   active lock and verifies no active fixture residue. Released history remains.

Any unexpected outcome, lost session or timeout returns nonzero. The harness
suppresses raw database output and reports the failing stage/error code. It
terminates only its own SQLcl process groups. On failure it reports the generated
fixture key for inspection in the same authorized lab. Autonomous commits survive
client failure and rollback; if cleanup cannot connect, the fixture may remain
active until its normal TTL. Do not force another owner's lock or delete history.

## Validation Scope

This tests ownership exclusion across two live sessions. It does not stress a
simultaneous insert race, TTL expiry, quoted identifiers or administrative recovery.
The local suite uses fake processes/sessions to verify orchestration, failure,
cleanup and default no-connect behavior. It is **not** a live Oracle concurrency
result. Before relying on the runtime, record a real authorized lab run with its
database, SQLcl and runtime versions and sanitized stage results. Initial live
Oracle validation remains pending.
