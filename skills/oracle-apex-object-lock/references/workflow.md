# Cooperative Object-Lock Workflow

## 1. Identify the Actor and Objects

Choose a stable actor value such as `<developer>/<agent-or-session>`. List every supported object that may be compiled. Do not acquire speculative locks for unrelated objects.

For a package, lock the package name once with `p_object_type => 'PACKAGE'`; this covers specification and body.

## 2. Refresh Git Before Locking

Fetch the expected remote base and confirm that the working branch contains it:

```bash
git fetch origin
git merge-base --is-ancestor origin/main HEAD
```

Use the base branch defined by the project. If the check fails, update safely before editing. If local changes overlap the object, stop and resolve them rather than compiling stale source.

## 3. Inspect Active and Recent State

```sql
select object_type,
       object_name,
       locked_by,
       branch_name,
       task_ref,
       repo_start_sha,
       lock_expires_at
  from vw_dev_object_lock_ativo
 order by object_type, object_name;
```

For one object:

```sql
select pk_dev_object_lock.func_status_recente(
           p_object_name => '<OBJECT_NAME>',
           p_object_type => '<OBJECT_TYPE>',
           p_horas       => 48
       ) as status_recente
  from dual;
```

A recent released or expired lock means the Git source may have changed. Refresh again before acquiring.

## 4. Acquire

```sql
begin
    pk_dev_object_lock.proc_adquirir_lock(
          p_object_name    => '<OBJECT_NAME>'
        , p_object_type    => '<OBJECT_TYPE>'
        , p_lock_owner     => '<ACTOR>'
        , p_branch_name    => '<BRANCH>'
        , p_task_ref       => '<TASK>'
        , p_context        => '<SHORT_REASON>'
        , p_repo_base_ref  => '<BASE_REF>'
        , p_repo_head_ref  => '<HEAD_REF>'
        , p_repo_start_sha => '<START_SHA>'
        , p_ttl_minutos    => 240
    );
end;
/
```

If another actor owns the lock, do not compile. Local editing can continue only when it cannot create a stale or misleading result; report the blocked shared-DEV validation explicitly.

## 5. Assert Before Every Compilation

```sql
begin
    pk_dev_object_lock.proc_assert_lock_compilacao(
          p_object_name => '<OBJECT_NAME>'
        , p_object_type => '<OBJECT_TYPE>'
        , p_lock_owner  => '<ACTOR>'
    );
end;
/
```

Run this immediately before each `create or replace`, `alter ... compile`, or equivalent shared DEV operation. An earlier successful assertion is not a permanent authorization.

## 6. Renew

For work approaching its expiry:

```sql
begin
    pk_dev_object_lock.proc_renovar_lock(
          p_object_name => '<OBJECT_NAME>'
        , p_object_type => '<OBJECT_TYPE>'
        , p_lock_owner  => '<ACTOR>'
        , p_ttl_minutos => 240
    );
end;
/
```

TTL accepts 15 through 1440 minutes.

## 7. Release

After the task is published or intentionally abandoned:

```sql
begin
    pk_dev_object_lock.proc_liberar_lock(
          p_object_name    => '<OBJECT_NAME>'
        , p_object_type    => '<OBJECT_TYPE>'
        , p_lock_owner     => '<ACTOR>'
        , p_release_reason => '<RESULT_OR_ABANDONMENT_REASON>'
        , p_repo_end_sha   => '<FINAL_SHA>'
    );
end;
/
```

Release every lock acquired for the task. Query the active view afterward and report zero residue for the task actor, or list the intentional remaining locks.
