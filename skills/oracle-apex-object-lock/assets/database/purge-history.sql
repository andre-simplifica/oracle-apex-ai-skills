set define on
set serveroutput on
set verify off
whenever sqlerror exit sql.sqlcode rollback
whenever oserror exit failure rollback

define keep_days = '&1'

select user as database_user,
       sys_context('USERENV', 'SERVICE_NAME') as service_name
  from dual;

select user,
       sys_context('USERENV', 'SERVICE_NAME') as service_name,
       count(*) as purge_candidates
  from dev_object_lock
 where lock_status in ('RELEASED', 'EXPIRED')
   and nvl(released_at, last_heartbeat_at) <
       systimestamp - numtodsinterval(to_number('&&keep_days'), 'DAY')
 group by user, sys_context('USERENV', 'SERVICE_NAME');

begin
    pk_dev_object_lock.proc_purgar_historico(
        p_keep_days => to_number('&&keep_days')
    );
end;
/

undefine keep_days
exit success
