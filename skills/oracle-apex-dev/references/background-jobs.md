# Background Jobs and Long-Running Work

Use this reference for APEX Automations, APEX background processes, `DBMS_SCHEDULER`, queues, retries, and long-running PL/SQL.

## Before Creating or Changing a Job

- Confirm environment: DEV, TEST, or PROD.
- Confirm whether the job already exists.
- Confirm owner schema and privileges.
- Confirm expected frequency, time zone, and business calendar.
- Confirm whether concurrent executions are allowed.
- Confirm retry, alerting, and manual recovery expectations.

Do not enable or modify production jobs without explicit authorization.

## Job Design

- Log start, end, status, duration, and key counters.
- Log sanitized error details.
- Use explicit commit/rollback according to the transaction design.
- Prevent duplicate concurrent execution when required.
- Use locks, queue state, or idempotent markers for work that must run once.
- Avoid very short intervals unless justified by the business requirement and proven safe.
- Do not hide exceptions with `when others then null`.
- Do not create endless retry loops without backoff or a retry limit.

## APEX Automations

- Check schedule, status, last run, next run, and failure history.
- Validate the parsing schema and application context.
- Confirm whether the automation runs as an APEX user or database context.
- Keep long work out of page submit paths when it can be safely queued.

## DBMS_SCHEDULER

- Use clear job names and comments.
- Confirm job class, credentials, destination, and enabled status.
- Keep `enabled => false` until the user authorizes activation in the target environment.
- Do not drop or disable existing jobs unless explicitly requested.
- Prefer changing schedule/action intentionally over recreating jobs by trial and error.

## Closeout

Report:

- job/automation changed;
- environment affected;
- enabled/disabled state;
- schedule;
- validation performed;
- any manual production action required.
