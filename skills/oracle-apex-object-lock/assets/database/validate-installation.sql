set define off
set serveroutput on
set verify off
whenever sqlerror exit sql.sqlcode rollback
whenever oserror exit failure rollback

declare
    l_missing number;
    l_invalid number;
    l_unusable_indexes number;
    l_errors  number;
    l_columns number;
    l_constraints number;
    l_version varchar2(20);
begin
    select count(*)
      into l_missing
      from (
            select 'DEV_OBJECT_LOCK' object_name, 'TABLE' object_type from dual
            union all select 'DEV_OBJECT_LOCK_UI1', 'INDEX' from dual
            union all select 'DEV_OBJECT_LOCK_I1', 'INDEX' from dual
            union all select 'VW_DEV_OBJECT_LOCK_ATIVO', 'VIEW' from dual
            union all select 'VW_DEV_OBJECT_LOCK_RECENTE', 'VIEW' from dual
            union all select 'PK_DEV_OBJECT_LOCK', 'PACKAGE' from dual
            union all select 'PK_DEV_OBJECT_LOCK', 'PACKAGE BODY' from dual
           ) expected
     where not exists (
               select 1
                 from user_objects actual
                where actual.object_name = expected.object_name
                  and actual.object_type = expected.object_type
           );

    select count(*)
      into l_invalid
      from user_objects
     where object_name in (
               'DEV_OBJECT_LOCK',
               'VW_DEV_OBJECT_LOCK_ATIVO',
               'VW_DEV_OBJECT_LOCK_RECENTE',
               'PK_DEV_OBJECT_LOCK'
           )
       and status <> 'VALID';

    select count(*)
      into l_unusable_indexes
      from user_indexes
     where index_name in ('DEV_OBJECT_LOCK_UI1', 'DEV_OBJECT_LOCK_I1')
       and status <> 'VALID';

    select count(*)
      into l_errors
      from user_errors
     where name = 'PK_DEV_OBJECT_LOCK';

    select count(*)
      into l_columns
      from user_tab_columns
     where table_name = 'DEV_OBJECT_LOCK'
       and column_name in (
               'AD_DEV_OBJECT_LOCK',
               'OBJECT_OWNER',
               'OBJECT_TYPE',
               'OBJECT_NAME',
               'LOCK_STATUS',
               'LOCKED_BY',
               'BRANCH_NAME',
               'TASK_REF',
               'LOCK_CONTEXT',
               'REPO_BASE_REF',
               'REPO_HEAD_REF',
               'REPO_START_SHA',
               'REPO_END_SHA',
               'LOCKED_AT',
               'LAST_HEARTBEAT_AT',
               'LOCK_EXPIRES_AT',
               'RELEASED_AT',
               'RELEASED_BY',
               'RELEASE_REASON'
           );

    select count(*)
      into l_constraints
      from user_constraints
     where table_name = 'DEV_OBJECT_LOCK'
       and constraint_name in (
               'DEV_OBJECT_LOCK_PK',
               'DEV_OBJECT_LOCK_STATUS_CK',
               'DEV_OBJECT_LOCK_TYPE_CK'
           )
       and status = 'ENABLED';

    begin
        execute immediate
            'select pk_dev_object_lock.func_runtime_version from dual'
            into l_version;
    exception
        when others then
            l_version := null;
    end;

    if l_missing > 0
       or l_invalid > 0
       or l_unusable_indexes > 0
       or l_errors > 0
       or l_columns <> 19
       or l_constraints <> 3
       or nvl(l_version, 'UNKNOWN') <> '1.0.0'
    then
        raise_application_error(
            -20092,
            'Object-lock runtime is not compatible: missing=' || l_missing ||
            ', invalid=' || l_invalid ||
            ', unusable_indexes=' || l_unusable_indexes ||
            ', errors=' || l_errors ||
            ', columns=' || l_columns || '/19' ||
            ', constraints=' || l_constraints || '/3' ||
            ', version=' || nvl(l_version, 'UNKNOWN')
        );
    end if;

    dbms_output.put_line(
        'ORACLE_APEX_OBJECT_LOCK_STATUS=INSTALLED;VERSION=' || l_version
    );
end;
/

exit success
