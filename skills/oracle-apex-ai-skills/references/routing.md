# Routing Oracle APEX Work

Use the smallest set of skills that covers the request.

| Intent | Required route | Output |
| --- | --- | --- |
| Install or update the project skill kit | `oracle-apex-ai-skills` | Managed skills, manifest, upstream lock, preserved local profile |
| Page, process, region, validation, API, job, PL/SQL, or runtime work | `oracle-apex-dev` | Implemented and validated change |
| Edit or compile a shared DEV database object | `oracle-apex-object-lock` + `oracle-apex-dev` | Owned lock, asserted compilation, released lock |
| Read-only APEX metadata inspection | `oracle-apex-export` temporary mode | Disposable export outside official snapshot |
| First repository version | `oracle-apex-export` initial-baseline mode | Full APEX application + full application-schema structural DDL |
| Release publication | `oracle-apex-export` release mode | Full APEX application + changed DB objects + pending DDL |
| Branded report, help canvas, PDF, or spreadsheet output | Optional `build-apex-brand-reports` | Project-branded output |
| Apache ECharts region | Optional `oracle-apex-echarts` | Self-contained APEX chart region |

## Authorization Matrix

Treat each operation separately.

| Operation | Read-only inspection authorizes it? | Explicit authorization normally required? |
| --- | --- | --- |
| Read repository/profile | Yes | No |
| Run project installer `status`, `check`, or dry-run | Yes | No |
| Copy managed skills into the current project | No | User request to install/update is sufficient |
| Audit lock runtime with SELECT metadata | Yes | Connection access still must be in scope |
| Install or upgrade lock runtime | No | Yes |
| Compile PL/SQL in DEV | No | Yes or clearly included in implementation request |
| Import APEX application | No | Yes |
| Generate official source exports | No | Explicit publication/release request |
| Commit, push, or open PR | No | Explicit Git publication request or repository rule |
| Apply release in TEST/PROD | No | Separate explicit authorization |

Never let authorization for one row silently authorize another.
