# Coordinated and Parallel Exports

Use this workflow when a project-approved official export contains independent
APEX formats, database snapshot materialization, or both. Concurrency reduces
elapsed time; it must not weaken source consistency, environment identity, or
publication safety.

## Preconditions

- The user authorized the official export and its Git publication scope.
- The project profile identifies the canonical exporter, application, database
  connection, destinations, and release mode.
- Every SQLcl session validates the expected user and service before extraction.
- The project defines a global SQLcl/session cap that the database can support.
- The worktree is clean for the target paths or an isolated worktree is used.
- The coordinator owns non-blocking locks for the official targets and Git
  publication scope.

## Recommended Dependency Graph

When the canonical exporter supports it:

1. Start the APEX application lane and database snapshot lane independently.
2. In the APEX lane, generate split SQL plus readable YAML in one private
   scratch root and the monolithic application file in another. These exports
   may run concurrently when the connection budget permits it.
3. Capture the database snapshot once. Internal metadata capture may remain
   serial; do not describe it as parallel unless the database implementation
   actually is.
4. After the snapshot is confirmed, materialize schema/reference files and
   release files concurrently from that same immutable snapshot ID or source
   boundary.
5. Join every required worker, validate the complete bundle, and only then
   promote official paths and publish Git changes once.

Parallel generation does not change installation order. Preserve deterministic
numeric or dependency ordering in the generated release artifacts.

## Consistency Gates

For every required APEX representation, reconcile the metadata available to the
project, including application identity, alias, parsing schema, build status,
Supporting Objects decision, page inventory, and component/page version
metadata. Do not combine files from different export windows. Treat a checksum
as diagnostic when the export operation itself can change it; use the complete
metadata and inventory contract defined by the project as the authoritative
gate.

For database artifacts:

- record the confirmed snapshot/source identifier before downstream work;
- reject null, empty, truncated, or error-prefixed DDL;
- reconcile object counts by type between the source inventory and every
  materialized output;
- never mix snapshot identifiers in one official bundle;
- use a project-defined full snapshot release only when the project profile
  explicitly requires it; otherwise keep normal release scope to changed
  objects and pending migrations.

## Failure and Retry

- A worker may finish and preserve diagnostic evidence after a sibling fails,
  but the coordinator must block partial promotion and publication.
- Preserve per-worker logs, a machine-readable manifest, promotion status, and
  rollback outcome.
- If a database snapshot was confirmed before a later failure, fix the cause
  and retry with that same snapshot instead of creating a duplicate.
- Use timeouts that account for sequential waves inside each lane, not only one
  SQLcl call.
- On interruption, terminate supervised child process groups and release locks.
- Before retrying after an unclean stop, inspect the manifest, candidate paths,
  promotion marker, locks, worktree, and Git index.
- Correct the observed cause before retrying; do not use an unbounded retry loop.

## Timing Evidence

For a timed run, record:

- external wall-clock start, finish, and total duration;
- APEX lane duration and, when available, split/readable and monolithic worker
  durations;
- database snapshot duration;
- schema/reference and release materialization durations;
- database critical-path duration from snapshot start through the slower
  downstream database worker;
- configured global worker/session cap.

Report overlapping durations as overlapping work. Do not add concurrent worker
times and present the sum as elapsed wall-clock time.
