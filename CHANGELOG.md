# Changelog

All notable public changes to this repository should be recorded here.

This project uses a simple changelog format. Dates use `YYYY-MM-DD`.

## Unreleased

## 2026-08-24 - 1.2.2

- Restored redaction-aware Bearer-token scanning so masked documentation examples remain valid while unredacted token-shaped values are still rejected.

## 2026-08-24 - 1.2.1

- Hardened the generic five-file database release validator so business comments such as `Error code constants` are not mistaken for extraction failures.
- Restricted exported-object detection to top-level DDL lines, preventing comments and nested PL/SQL text from being counted as release objects.

## 2026-08-24 - 1.2.0

- Added a deterministic Oracle APEX version validator with a 24.2 kit minimum, an accurate 22.2 Dynamic Content product gate, a 26.1 public-API gate, and explicit requirement checks.
- Added managed compatibility helpers to every consuming project and integrated optional live-version checks into `doctor`.
- Defined version-specific official application exports: split SQL + readable YAML + monolithic SQL before 26.1, and split SQL + monolithic SQL from 26.1 onward.
- Disabled APEXlang generation, export, parsing, editing, validation, compilation, and import across every supported release; 26.1 product availability is informational only.
- Updated the APEX export validator to require the confirmed APEX version, reject APEXlang artifacts, block releases below 24.2, and accept quoted `p_version_scn` values from 26.1 SQL exports.
- Added an APEX 26.1 public API catalog, live-signature gates, Static ID/DOM migration guidance, and deprecation checks.
- Added backward-compatible installation updates for pre-1.1 manifests and schema-v1 project policies while introducing the schema-v2 project export contract.
- Updated public documentation, project-profile scaffolding, compatibility schemas, and release guidance for equivalent APEX 24.2 and 26.1+ operation without APEXlang.

## 2026-08-22 - 1.1.0

- Added `oracle-apex-ai-skills` as the main router and project installation/update contract.
- Added repository-scoped Codex installation under `.agents/skills` with dry-run, checksummed manifests, upstream commit tracking, drift detection, and project-owned-file preservation.
- Added `oracle-apex-object-lock` with the complete cooperative `PK_DEV_OBJECT_LOCK` runtime, read-only audit, strict validation, and shared-DEV workflow.
- Expanded `oracle-apex-export` with temporary inspection, initial full APEX/schema baseline, application snapshot, and normal release modes.
- Added coordinated parallel export guidance for split/YAML/monolithic APEX
  snapshots, single-boundary database materialization, atomic promotion,
  resumable failure handling, and wall-clock/per-lane timing evidence.
- Defined pending DDL/DML lifecycle and release packaging rules.
- Made Oracle APEX 24.2 the explicit verified target and documented other-version validation boundaries.
- Added optional routing to Brand Report Kit and Oracle APEX ECharts without making either a dependency.
- Added installer and repository contract tests.
- Added complete/partial database release contracts with the same five ordered files, explicit snapshot lineage, deterministic hashing rules, and a local bundle validator.
- Added atomic APEX split SQL/readable YAML/monolithic validation, including application/page/SCN consistency and basic secret checks.
- Replaced parallel migration fragments with one pending root containing exactly one DDL file and one DML file; APEX components and standalone object source are rejected there.
- Added project-owned export policy, report-first repository retention, guarded pruning, and review-only SQL generation for compatible snapshot-table cleanup.
- Added package-backed Dynamic Content guidance for branded and interactive layouts, plus continuous project-owned pattern learning that survives kit updates.
- Expanded APEX 24.2 internal API discovery and connection-identity, PL/SQL, production DML, constraint, character-semantics, and Oracle egress guardrails.
- Updated the cooperative object-lock runtime to 1.1.0 with bounded character semantics, safe text truncation, history purge, guarded uninstall, stricter metadata validation, and disabled unauthenticated force operations.
- Added `doctor`, kit-version metadata, managed export tools, missing-project-file initialization, and update preservation for profiles, patterns, export policy, and migrations.
- Changed personal Codex installation to the current `$HOME/.agents/skills` discovery location; replacement backs up old copies and removes this kit's legacy `.codex/skills` duplicates before symlinking.
- Documented Brand Report Kit/PDF and Oracle APEX ECharts as separately versioned optional repositories.

## 2026-04-25 - 1.0.0

- Created the initial public Oracle APEX AI skills repository.
- Added reusable `oracle-apex-dev` and `oracle-apex-export` skills.
- Added project-profile templates to separate reusable APEX guidance from project-specific standards.
- Added installation and update scripts for Codex and Claude Code.
- Added English README and Portuguese onboarding README.
- Added MIT license and public contribution guidance.
- Added project hero image and improved the README opening section.
- Added security policy, safe contribution guidance, GitHub templates, and advanced APEX development references.
- Added humorous review cards to the README opening section.
- Emphasized the recommended AI-first workflow and project-knowledge transfer mindset.
- Moved humorous review cards after the core comparison to improve the README opening flow.
- Clarified the local skill refresh section so it explains why and when to update.
- Polished README wording so the English reads more naturally.
