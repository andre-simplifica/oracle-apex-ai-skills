# Oracle APEX Internal Import APIs

Internal import APIs are useful for repeatable, multi-page, or generated changes, but they are not a stable public application-development API. Treat a fresh SQL export from the exact target APEX version and the live database signature as the source of truth. Never invent a parameter list from memory or reuse a component export from another APEX feature release.

## Route Selection

Use this route when:

- creating several components from one verified pattern;
- applying a deterministic change across multiple pages;
- generating a new screen from a real example page;
- repairing metadata when Page Designer would be slow and error-prone.

Use Page Designer for small focused changes. Use a full official application export for publication; a metadata patch is an implementation mechanism, not the official snapshot.

## Observed SQL Export Families

The following calls are commonly present in standard SQL application exports from supported APEX releases. This is a routing catalog, not a promise that every parameter remains compatible:

| Family | Common exported calls |
| --- | --- |
| Import envelope | `wwv_flow_imp.import_begin`, `component_begin`, `component_end`, `import_end` |
| Page lifecycle | `wwv_flow_imp_page.create_page`, `update_page`, `remove_page` |
| Regions and columns | `create_page_plug`, `create_region_column`, `create_report_region`, `create_report_columns` |
| Items and buttons | `create_page_item`, `create_page_button` |
| Submit flow | `create_page_process`, `create_page_validation`, `create_page_branch`, `create_page_computation` |
| Dynamic Actions | `create_page_da_event`, `create_page_da_action` |
| Reports and grids | `create_worksheet`, `create_worksheet_column`, `create_worksheet_rpt`, `create_interactive_grid`, `create_ig_report`, `create_ig_report_view`, `create_ig_report_column` |
| Cards, maps, actions | `create_card`, `create_card_action`, `create_map_region`, `create_map_region_layer`, `create_component_action` |
| Navigation | `wwv_flow_imp_shared.create_list`, `create_list_item`, `create_menu_option` |
| LOVs | `create_list_of_values`, `create_list_of_values_cols`, `create_static_lov_data` |
| Application logic | `create_flow_item`, `create_flow_process`, `create_flow_computation` |
| Security | `create_authentication`, `create_security_scheme` |
| Plug-ins and files | `create_plugin`, `create_plugin_attribute`, `create_plugin_attr_value`, `create_plugin_file`, `create_app_static_file`, `remove_app_static_file` |
| Automations and workflows | `create_automation`, `create_automation_action`, workflow/task-definition creation calls |

Before using a call, run the compatibility validator, locate the exact call in a fresh temporary SQL export from the target APEX version, and inspect its live signature. On APEX 26.1 or later, account for component wrappers such as `component_begin` and for quoted numeric metadata such as `p_version_scn`.

## APEX 26.1 Upgrade Break Assessment

Do not classify every Static ID change as an application-breaking change:

- Oracle keeps the legacy `STATIC_ID` public-view columns and substitutions for backward compatibility, although they are deprecated. Existing declarative applications are upgraded with generated permanent component Static IDs.
- The old Region/Button/IR/IG column Static ID meaning is now exposed as HTML DOM ID. Internal metadata scripts must use the exact 26.1 export parameter (`p_html_dom_id` or `p_dom_id` where present) instead of mechanically treating it as the new external component Static ID.
- Undocumented JavaScript properties are the confirmed immediate break risk: `regionStaticId` and column `staticId` must become `regionDomId` and `domId`.
- Public-view code that reads legacy `STATIC_ID`, substitutions such as `#REGION_STATIC_ID#`, and deprecated public APIs normally continue to run in 26.1, but must be migrated because Oracle can remove them later.
- A pre-26.1 internal import script is not a valid 26.1 candidate. Regenerate the page/component SQL on 26.1, preserve its wrapper calls and parameter names, and compare current metadata before applying the change.

Therefore, an APEX upgrade alone is not proof that prior internal-API updates broke. The required assessment is: scan custom JavaScript for the confirmed renamed undocumented fields, scan SQL/PLSQL/template code for deprecated DOM identifiers, regenerate controlled metadata patches on the target feature release, and runtime-test the exact affected pages.

## Required Discovery

Confirm the live owner and arguments instead of assuming them:

```sql
select owner,
       package_name,
       object_name,
       overload,
       sequence,
       position,
       argument_name,
       in_out,
       data_type,
       defaulted
  from all_arguments
 where package_name in ('WWV_FLOW_IMP', 'WWV_FLOW_IMP_PAGE', 'WWV_FLOW_IMP_SHARED')
   and object_name = upper(:p_method_name)
 order by owner, package_name, object_name, overload, sequence;
```

If the signature is unavailable, ambiguous, or differs from the same-version export, stop and use Page Designer or an official exported component script.

## Controlled Script Workflow

1. Confirm the configured SQLcl connection with `USER` and `SERVICE_NAME`.
2. Resolve workspace ID, application ID, page ID, parsing schema, and current page/component metadata from APEX views.
3. Export the real example page or component to a temporary directory.
4. Preserve the generated import envelope and `component_begin`/`component_end` boundaries.
5. Locate parents by application/page and the component identity appropriate to the target signature. On APEX 26.1 or later, distinguish the new stable component Static ID from the HTML DOM ID retained in compatibility columns; stop on zero or multiple matches.
6. Use IDs from the generated export or a project-approved deterministic allocation strategy. Abort on collision.
7. Add existence/current-state guards appropriate to the operation.
8. Apply one small component group at a time in the authorized environment.
9. Query metadata immediately, then validate the real runtime path.
10. Refresh the complete official application snapshot only when separately requested.

## Workspace Context

Resolve the workspace dynamically. When the approved script requires a security group context, use the public APEX utility available in the target version rather than hard-coding an internal workspace ID. Validate the application belongs to the resolved workspace before mutation.

## Safety Rules

- Never transplant a call from a different APEX version without signature and runtime validation.
- Never nest generated anonymous blocks or remove `/` delimiters.
- Do not alter generated component wrappers casually.
- Do not use names alone when duplicate labels are possible. Prefer stable component IDs, but verify whether a public view's legacy `STATIC_ID` column represents the browser DOM identity or the new external component identity in the target release.
- Do not mechanically replace `P_REGION_NAME`, `P_STATIC_ID`, or `P_BUTTON_STATIC_ID` with `P_HTML_DOM_ID`/`P_DOM_ID`; select the parameter exposed by the exact component overload.
- Regenerate page or component SQL on the target feature release. Do not import a pre-26.1 single-page/component export into 26.1 or later.
- Do not weaken authorization, Session State Protection, checksums, or tenant scope to make a script succeed.
- Treat an import/application metadata mutation as destructive: candidate, backup/rollback, explicit target, and runtime validation are required.
- Keep secrets and environment-specific substitutions out of generated scripts and Git.

## Validation

Validate at least:

- expected component count and parent relationship;
- unique IDs and Static IDs;
- authorization and conditions;
- Session State and `Items to Submit` for AJAX/Dynamic Actions;
- application/page runtime behavior;
- complete official export contract when publication was requested.

Primary Oracle 26.1 upgrade references:

- [Changed behavior](https://docs.oracle.com/en/database/oracle/apex/26.1/htmrn/changed-behavior.html)
- [Deprecated features](https://docs.oracle.com/en/database/oracle/apex/26.1/htmrn/deprecated-features.html)
- [Editing regions: HTML DOM ID and Static ID](https://docs.oracle.com/en/database/oracle/apex/26.1/htmdb/editing-regions.html)
