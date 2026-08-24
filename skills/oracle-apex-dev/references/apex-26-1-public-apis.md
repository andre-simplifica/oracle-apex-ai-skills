# Oracle APEX 26.1 Public API Catalog

Read this reference only after the compatibility validator confirms APEX 26.1 or later. This is a routing and discovery catalog, not permission to call every API and not a replacement for the live package specification.

## New Public Packages and Types

| API | 26.1 capability | Required caution |
| --- | --- | --- |
| `APEX_DB_DICTIONARY` | Database-object metadata, table summaries, primary-key discovery, JSON metadata, and formatted metadata | Confirm object visibility and supported object type with `IS_SUPPORTED` |
| `APEX_INSTANCE_DEBUG` | Instance activity, page-view, and debug-message inspection | Requires an APEX administrator role; a public synonym does not prove the caller can use it |
| `APEX_GENDEV.PROCESS_BLUEPRINT` | Processes a blueprint and returns a parsing log plus an APEXlang ZIP BLOB | Keep the signature and purpose in project knowledge, but do not use its output as an application source/import workflow in this kit |
| `APEX_T_JAVASCRIPT_OBJECT` | Builds JavaScript object notation with constructor, append/put, open/close, reset, and CLOB output helpers | Confirm the exact constructor and method overloads in the live release |

## Material Additions to Existing Packages

- `APEX_AI`: agent-oriented `CHAT` and `GENERATE` overloads, attachments, available-token inspection, and `SET_TOOL_RESULT`.
- `APEX_APPLICATION_INSTALL`: subscription mode/mapping, Data Reporter mappings, dataset import modes, and remote-server AI token limits.
- `APEX_AUTHORIZATION.HAS_ACCESS`: public authorization check replacing deprecated utility usage.
- `APEX_EXTENSION.GET_BUILDER_LINK`: Builder navigation link generation.
- `APEX_HUMAN_TASK.DELETE_TASKS`, `EXCLUDE_POTENTIAL_OWNER`, and `REFRESH_BUSINESS_ADMINS`: destructive cleanup, participant exclusion, and administrator recalculation. `DELETE_TASKS` requires explicit data-cleanup authorization and restrictive filters.
- `APEX_WORKFLOW.DELETE_WORKFLOWS` and `SET_ACTIVITY_DUE_DATE`: destructive workflow-instance cleanup and activity due-date updates. Treat deletion as production DML, not routine metadata maintenance.
- `APEX_LANG.EXPORT_TEXT_MESSAGES` and `IMPORT_TEXT_MESSAGES`: XLIFF/CSV text-message translation interchange. These are not APEXlang APIs and remain usable after the 26.1 gate.
- `APEX_PAGE.GET_CACHE_DATE` and `APEX_REGION.GET_CACHE_DATE`: cache-date inspection replacing deprecated utility calls.
- `APEX_PLUGIN.GET_INPUT_NAME_FOR_ITEM`: page-item-aware input naming; older page-item signatures and plug-in fields are deprecated.
- `APEX_PRINT.GENERATE_DOCUMENT`: additional OCI Object Storage template and password overloads.
- `APEX_SESSION_STATE`: Boolean getter/setter support where the database release supports Boolean SQL values.
- `APEX_IG` and `APEX_IR`: report Static ID overloads for add, clear, and reset operations.
- `APEX_APPLICATION_ADMIN.SET_BUILD_OPTION_STATUS`: revised overloads.
- `APEX_DATA_EXPORT.GET_PRINT_CONFIG`: function form.
- `APEX_EXPORT`: `GET_APPLICATION` accepts the new APEXlang export type, and export-file types can carry BLOB content. These members are cataloged, but this kit always requests SQL and rejects APEXlang output.
- `APEX_SHARED_COMPONENT`: theme-aware refresh and publish operations.
- `APEX_WEB_SERVICE`: OAuth `P_SCOPE` overloads, including credential-based authentication.
- `APEX_EXEC`: expanded types and OData DML support.

JavaScript additions include `interactiveReportRegion`, named-template utilities, map-layer visibility and ordering, `htmlBuilder`, plural grid range selection, action-purpose and Ctrl-or-Meta handling, and accessibility updates across menus, facets, trees, models, templates, and spinners.

This catalog covers the 26.1 API families and members material to APEX application development. It does not copy every overload from the API Reference. Before implementation, use Oracle's APEX Diff application or compare the live public package specification so the exact signature, privilege, database dependency, and patch-level availability are verified.

## Upgrade and Deprecation Checks

Before upgrading a project or generating a controlled metadata patch, scan for:

- old APEX AI overloads based on `P_CONFIG_STATIC_ID`;
- deprecated plug-in fields and public-view `ATTRIBUTE_01` through `ATTRIBUTE_25` access where 26.1 returns JSON attributes instead;
- deprecated `APEX_UTIL` authorization and cache methods;
- old `STATIC_ID` substitution strings and view columns when the intent is actually HTML DOM identity;
- JavaScript `invokeAfterPaint`/`cancelInvokeAfterPaint` and singular `getSelectedRange` usage;
- undocumented JavaScript fields such as `regionStaticId` or column `staticId`, which do not have the same compatibility promise as public APIs.

## Live Signature Gate

Confirm public package targets and overloads before use:

```sql
select s.synonym_name,
       s.table_owner,
       s.table_name,
       a.object_name,
       a.overload,
       a.sequence,
       a.argument_name,
       a.in_out,
       a.data_type,
       a.defaulted
  from all_synonyms s
  left join all_arguments a
    on a.owner = s.table_owner
   and a.package_name = s.table_name
 where s.owner = 'PUBLIC'
   and s.synonym_name = upper(:p_public_package)
 order by a.object_name, a.overload, a.sequence;
```

Stop when the package target or required overload is not visible. Availability can depend on APEX administrator roles, database version, installation options, and schema privileges.

Primary Oracle references:

- [APEX 26.1 new features and PL/SQL API updates](https://docs.oracle.com/en/database/oracle/apex/26.1/htmrn/new-features.html)
- [APEX 26.1 API Reference changes](https://docs.oracle.com/en/database/oracle/apex/26.1/aeapi/changes-in-this-release.html)
- [APEX_DB_DICTIONARY](https://docs.oracle.com/en/database/oracle/apex/26.1/aeapi/APEX_DB_DICTIONARY.html)
- [APEX_INSTANCE_DEBUG](https://docs.oracle.com/en/database/oracle/apex/26.1/aeapi/APEX_INSTANCE_DEBUG.html)
- [APEX_GENDEV.PROCESS_BLUEPRINT](https://docs.oracle.com/en/database/oracle/apex/26.1/aeapi/APEX_GENDEV.PROCESS_BLUEPRINT-Procedure.html)
