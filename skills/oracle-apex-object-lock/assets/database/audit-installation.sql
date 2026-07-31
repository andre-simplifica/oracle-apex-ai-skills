set define off
set serveroutput on
set verify off
whenever sqlerror exit sql.sqlcode rollback
whenever oserror exit failure rollback

declare
    l_present          number := 0;
    l_invalid          number := 0;
    l_unusable_indexes number := 0;
    l_errors           number := 0;
    l_columns          number := 0;
    l_constraints      number := 0;
    l_version          varchar2(100);
    l_required_version constant varchar2(20) := '1.0.0';
    l_status           varchar2(30);
begin
    select count(*)
      into l_present
      from (
            select 'DEV_OBJECT_LOCK' object_name, 'TABLE' object_type from dual
            union all select 'DEV_OBJECT_LOCK_UI1', 'INDEX' from dual
            union all select 'DEV_OBJECT_LOCK_I1', 'INDEX' from dual
            union all select 'VW_DEV_OBJECT_LOCK_ATIVO', 'VIEW' from dual
            union all select 'VW_DEV_OBJECT_LOCK_RECENTE', 'VIEW' from dual
            union all select 'PK_DEV_OBJECT_LOCK', 'PACKAGE' from dual
            union all select 'PK_DEV_OBJECT_LOCK', 'PACKAGE BODY' from dual
           ) expected
     where exists (
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

    if l_present >= 6 then
        begin
            execute immediate
                'select pk_dev_object_lock.func_runtime_version from dual'
                into l_version;
        exception
            when others then
                l_version := null;
        end;
    end if;

    if l_present = 0 then
        l_status := 'ABSENT';
    elsif l_present < 7
          or l_invalid > 0
          or l_unusable_indexes > 0
          or l_errors > 0
          or l_columns <> 19
          or l_constraints <> 3
    then
        l_status := 'PARTIAL';
    elsif l_version is null or l_version <> l_required_version then
        l_status := 'INCOMPATIBLE';
    else
        l_status := 'INSTALLED';
    end if;

    dbms_output.put_line(
        'ORACLE_APEX_OBJECT_LOCK_STATUS=' || l_status ||
        ';VERSION=' || nvl(l_version, 'UNKNOWN') ||
        ';REQUIRED_VERSION=' || l_required_version ||
        ';OBJECTS_PRESENT=' || l_present || '/7' ||
        ';REQUIRED_COLUMNS=' || l_columns || '/19' ||
        ';REQUIRED_CONSTRAINTS=' || l_constraints || '/3' ||
        ';INVALID_OBJECTS=' || l_invalid ||
        ';UNUSABLE_INDEXES=' || l_unusable_indexes ||
        ';PACKAGE_ERRORS=' || l_errors
    );
end;
/

exit success
