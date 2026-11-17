# Backlog Implementation Decisions

Review date: 2026-11-17. This is the SQL-based kit with an APEX 24.2 baseline and
explicit later-version gates. APEX 26.2 **APEXlang** work belongs in the separate
[APEXlang repository](https://github.com/andre-simplifica/oracle-apex-ai-skills-apexlang).
A version number alone does not select that source workflow. No APEXlang
generation, import, export or validation is added here.

| Issue | Decision | Delivered scope or condition for resuming |
| --- | --- | --- |
| [#2 Target preflight](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/2) | Implement a small opt-in helper | Generate a bound, read-only SQLcl identity check from private explicit expectations. Same-session integration is project-owned. Live Oracle acceptance remains pending. |
| [#3 Lock concurrency test](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/3) | Implement an isolated-lab harness | Two persistent SQLcl sessions test ownership exclusion and handover. Because runtime calls expire rows globally, require a dedicated empty runtime. No runtime change or live execution is included. |
| [#4 Internal API recipes](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/4) | Defer executable recipes | Resume with a concrete APEX 24.2 task, a sanitized same-version export, verified signatures and an authorized DEV runtime result. A generic catalog already exists; frozen untested signatures would add risk. Do not borrow 26.2 APEXlang patterns. |
| [#5 Profile review](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/5) | Implement advisory lint and a reconciliation plan | Report version, route and unfilled/unrecognized guidance without printing private values or rewriting Markdown. A rigid new schema or automatic migration is unnecessary for project-owned profiles. |
| [#6 Parallel export runner](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/6) | Defer a generic runner | Existing guidance already specifies coordination. Resume when real SQL exporters demonstrate a common adapter interface, snapshot semantics, promotion and recovery behavior. A generic subprocess runner cannot guarantee those semantics. Do not copy an APEXlang coordinator here. |
| [#7 Continuous integration](https://github.com/andre-simplifica/oracle-apex-ai-skills/issues/7) | Implement | Run existing local validation on clean Linux checkouts with supported Python versions, no Oracle credentials or network database tests. |

Database-independent tests establish helper behavior, not live Oracle correctness.
File publication does not authorize a consumer installation, database test,
application import, full export or deployment.
