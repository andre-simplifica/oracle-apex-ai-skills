set define off
set serveroutput on
set verify off
whenever sqlerror exit sql.sqlcode rollback
whenever oserror exit failure rollback

select user as database_user,
       sys_context('USERENV', 'SERVICE_NAME') as service_name
  from dual;

prompt Uninstalling cooperative Oracle DEV object locks...

declare
    l_table_present number := 0;
    l_safety_columns number := 0;
    l_active number := 0;
begin
    select case
               when exists (
                        select 1
                          from user_tables
                         where table_name = 'DEV_OBJECT_LOCK'
                    )
               then 1
               else 0
           end
      into l_table_present
      from dual;

    if l_table_present = 1 then
        select count(*)
          into l_safety_columns
          from user_tab_columns
         where table_name = 'DEV_OBJECT_LOCK'
           and column_name in ('LOCK_STATUS', 'LOCK_EXPIRES_AT');

        if l_safety_columns <> 2 then
            raise_application_error(
                -20099,
                'Object-lock uninstall refused: the partial table cannot be checked safely for active locks.'
            );
        end if;

        execute immediate q'[
            select count(*)
              from dev_object_lock
             where lock_status = 'ACTIVE'
               and lock_expires_at >= systimestamp
        ]' into l_active;

        if l_active > 0 then
            raise_application_error(
                -20095,
                'Object-lock uninstall refused: ' || l_active || ' active lock(s) remain.'
            );
        end if;
    end if;
end;
/

declare
    procedure drop_if_present (
          p_object_name in varchar2
        , p_object_type in varchar2
        , p_statement   in varchar2
    )
    is
        l_count number;
    begin
        select count(*)
          into l_count
          from user_objects
         where object_name = upper(p_object_name)
           and object_type = upper(p_object_type);

        if l_count > 0 then
            execute immediate p_statement;
            dbms_output.put_line('Dropped ' || p_object_type || ' ' || p_object_name || '.');
        end if;
    end drop_if_present;
begin
    drop_if_present('PK_DEV_OBJECT_LOCK', 'PACKAGE', 'drop package pk_dev_object_lock');
    drop_if_present('VW_DEV_OBJECT_LOCK_ATIVO', 'VIEW', 'drop view vw_dev_object_lock_ativo');
    drop_if_present('VW_DEV_OBJECT_LOCK_RECENTE', 'VIEW', 'drop view vw_dev_object_lock_recente');
    drop_if_present('DEV_OBJECT_LOCK', 'TABLE', 'drop table dev_object_lock cascade constraints purge');
end;
/

declare
    l_remaining number;
begin
    select count(*)
      into l_remaining
      from user_objects
     where object_name in (
               'DEV_OBJECT_LOCK', 'DEV_OBJECT_LOCK_UI1', 'DEV_OBJECT_LOCK_I1',
               'VW_DEV_OBJECT_LOCK_ATIVO', 'VW_DEV_OBJECT_LOCK_RECENTE',
               'PK_DEV_OBJECT_LOCK'
           );

    if l_remaining <> 0 then
        raise_application_error(-20096, 'Object-lock uninstall incomplete: remaining=' || l_remaining);
    end if;

    dbms_output.put_line('ORACLE_APEX_OBJECT_LOCK_STATUS=ABSENT');
end;
/

prompt Cooperative Oracle DEV object locks uninstalled. History was permanently removed.
exit success
