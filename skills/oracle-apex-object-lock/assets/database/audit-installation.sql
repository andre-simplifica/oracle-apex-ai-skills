set define off
set serveroutput on
set verify off
whenever sqlerror exit sql.sqlcode rollback
whenever oserror exit failure rollback

select user as database_user,
       sys_context('USERENV', 'SERVICE_NAME') as service_name
  from dual;

declare
    l_present          number := 0;
    l_invalid          number := 0;
    l_unusable_indexes number := 0;
    l_errors           number := 0;
    l_columns          number := 0;
    l_column_contract  number := 0;
    l_constraints      number := 0;
    l_pk_columns       number := 0;
    l_index_contract   number := 0;
    l_index_columns    number := 0;
    l_index_expressions number := 0;
    l_view_columns     number := 0;
    l_view_expected_columns number := 0;
    l_api_count        number := 0;
    l_version          varchar2(100);
    l_required_version constant varchar2(20) := '1.1.0';
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
      into l_column_contract
      from user_tab_columns
     where table_name = 'DEV_OBJECT_LOCK'
       and (
              (column_name = 'AD_DEV_OBJECT_LOCK' and data_type = 'NUMBER' and nullable = 'N' and identity_column = 'YES')
           or (column_name = 'OBJECT_OWNER' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 128 and nullable = 'N')
           or (column_name = 'OBJECT_TYPE' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 30 and nullable = 'N')
           or (column_name = 'OBJECT_NAME' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 128 and nullable = 'N')
           or (column_name = 'LOCK_STATUS' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 20 and nullable = 'N')
           or (column_name = 'LOCKED_BY' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 255 and nullable = 'N')
           or (column_name = 'BRANCH_NAME' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 255 and nullable = 'Y')
           or (column_name = 'TASK_REF' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 500 and nullable = 'Y')
           or (column_name = 'LOCK_CONTEXT' and data_type = 'VARCHAR2' and char_used = 'B' and data_length = 4000 and nullable = 'Y')
           or (column_name = 'REPO_BASE_REF' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 255 and nullable = 'Y')
           or (column_name = 'REPO_HEAD_REF' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 255 and nullable = 'Y')
           or (column_name = 'REPO_START_SHA' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 64 and nullable = 'Y')
           or (column_name = 'REPO_END_SHA' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 64 and nullable = 'Y')
           or (column_name = 'LOCKED_AT' and data_type like 'TIMESTAMP%WITH TIME ZONE' and nullable = 'N')
           or (column_name = 'LAST_HEARTBEAT_AT' and data_type like 'TIMESTAMP%WITH TIME ZONE' and nullable = 'N')
           or (column_name = 'LOCK_EXPIRES_AT' and data_type like 'TIMESTAMP%WITH TIME ZONE' and nullable = 'N')
           or (column_name = 'RELEASED_AT' and data_type like 'TIMESTAMP%WITH TIME ZONE' and nullable = 'Y')
           or (column_name = 'RELEASED_BY' and data_type = 'VARCHAR2' and char_used = 'C' and char_length = 255 and nullable = 'Y')
           or (column_name = 'RELEASE_REASON' and data_type = 'VARCHAR2' and char_used = 'B' and data_length = 4000 and nullable = 'Y')
           );

    select count(*)
      into l_constraints
      from user_constraints
     where table_name = 'DEV_OBJECT_LOCK'
       and status = 'ENABLED'
       and validated = 'VALIDATED'
       and (
              (constraint_name = 'DEV_OBJECT_LOCK_PK' and constraint_type = 'P')
           or (constraint_name = 'DEV_OBJECT_LOCK_STATUS_CK' and constraint_type = 'C'
               and instr(upper(search_condition_vc), 'LOCK_STATUS') > 0
               and instr(upper(search_condition_vc), '''ACTIVE''') > 0
               and instr(upper(search_condition_vc), '''RELEASED''') > 0
               and instr(upper(search_condition_vc), '''EXPIRED''') > 0)
           or (constraint_name = 'DEV_OBJECT_LOCK_TYPE_CK' and constraint_type = 'C'
               and instr(upper(search_condition_vc), 'OBJECT_TYPE') > 0
               and instr(upper(search_condition_vc), '''PACKAGE''') > 0
               and instr(upper(search_condition_vc), '''VIEW''') > 0
               and instr(upper(search_condition_vc), '''TRIGGER''') > 0
               and instr(upper(search_condition_vc), '''PROCEDURE''') > 0
               and instr(upper(search_condition_vc), '''FUNCTION''') > 0
               and instr(upper(search_condition_vc), '''TYPE''') > 0
               and instr(upper(search_condition_vc), '''SYNONYM''') > 0)
           );

    select count(*)
      into l_pk_columns
      from user_cons_columns
     where table_name = 'DEV_OBJECT_LOCK'
       and constraint_name = 'DEV_OBJECT_LOCK_PK'
       and position = 1
       and column_name = 'AD_DEV_OBJECT_LOCK';

    select count(*)
      into l_index_contract
      from user_indexes
     where table_name = 'DEV_OBJECT_LOCK'
       and status = 'VALID'
       and (
              (index_name = 'DEV_OBJECT_LOCK_UI1' and uniqueness = 'UNIQUE' and index_type like 'FUNCTION-BASED%')
           or (index_name = 'DEV_OBJECT_LOCK_I1' and uniqueness = 'NONUNIQUE')
           );

    select count(*)
      into l_index_columns
      from user_ind_columns
     where index_name = 'DEV_OBJECT_LOCK_I1'
       and ((column_position = 1 and column_name = 'LOCK_STATUS')
         or (column_position = 2 and column_name = 'LOCK_EXPIRES_AT'));

    select count(*)
      into l_index_expressions
     from user_ind_expressions
     where index_name = 'DEV_OBJECT_LOCK_UI1'
       and column_position between 1 and 3;

    select count(*)
      into l_view_columns
      from user_tab_columns
     where table_name in ('VW_DEV_OBJECT_LOCK_ATIVO', 'VW_DEV_OBJECT_LOCK_RECENTE');

    select count(*)
      into l_view_expected_columns
      from user_tab_columns
     where (table_name = 'VW_DEV_OBJECT_LOCK_ATIVO'
            and column_name in (
                'AD_DEV_OBJECT_LOCK', 'OBJECT_OWNER', 'OBJECT_TYPE', 'OBJECT_NAME',
                'LOCKED_BY', 'BRANCH_NAME', 'TASK_REF', 'LOCK_CONTEXT',
                'REPO_BASE_REF', 'REPO_HEAD_REF', 'REPO_START_SHA', 'REPO_END_SHA',
                'LOCKED_AT', 'LAST_HEARTBEAT_AT', 'LOCK_EXPIRES_AT'
            ))
        or (table_name = 'VW_DEV_OBJECT_LOCK_RECENTE'
            and column_name in (
                'AD_DEV_OBJECT_LOCK', 'OBJECT_OWNER', 'OBJECT_TYPE', 'OBJECT_NAME',
                'LOCK_STATUS', 'LOCKED_BY', 'BRANCH_NAME', 'TASK_REF', 'LOCK_CONTEXT',
                'REPO_BASE_REF', 'REPO_HEAD_REF', 'REPO_START_SHA', 'REPO_END_SHA',
                'LOCKED_AT', 'LAST_HEARTBEAT_AT', 'LOCK_EXPIRES_AT', 'RELEASED_AT',
                'RELEASED_BY', 'RELEASE_REASON'
            ));

    select count(*)
      into l_api_count
      from user_procedures
     where object_name = 'PK_DEV_OBJECT_LOCK'
       and procedure_name in (
               'FUNC_RUNTIME_VERSION', 'PROC_EXPIRAR_LOCKS',
               'PROC_PURGAR_HISTORICO', 'PROC_ADQUIRIR_LOCK',
               'PROC_RENOVAR_LOCK', 'PROC_LIBERAR_LOCK',
               'PROC_ASSERT_LOCK_COMPILACAO', 'FUNC_STATUS_LOCK',
               'FUNC_STATUS_RECENTE'
           );

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
          or l_column_contract <> 19
          or l_pk_columns <> 1
          or l_index_contract <> 2
          or l_index_columns <> 2
          or l_index_expressions <> 3
          or l_view_columns <> 34
          or l_view_expected_columns <> 34
          or l_api_count <> 9
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
        ';COLUMN_CONTRACT=' || l_column_contract || '/19' ||
        ';PK_COLUMNS=' || l_pk_columns || '/1' ||
        ';INDEX_CONTRACT=' || l_index_contract || '/2' ||
        ';EXPIRY_INDEX_COLUMNS=' || l_index_columns || '/2' ||
        ';ACTIVE_INDEX_EXPRESSIONS=' || l_index_expressions || '/3' ||
        ';VIEW_COLUMNS=' || l_view_columns || '/34' ||
        ';EXPECTED_VIEW_COLUMNS=' || l_view_expected_columns || '/34' ||
        ';PACKAGE_APIS=' || l_api_count || '/9' ||
        ';INVALID_OBJECTS=' || l_invalid ||
        ';UNUSABLE_INDEXES=' || l_unusable_indexes ||
        ';PACKAGE_ERRORS=' || l_errors
    );
end;
/

exit success
