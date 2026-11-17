#!/usr/bin/env python3
"""Opt-in, two-session Object Lock smoke test for an isolated disposable DEV schema."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import time
import uuid

from target_preflight import SQLCL_SETTINGS, load_expectations, render_preflight


class TestFailure(RuntimeError):
    pass


class SqlclSession:
    """Private supervised SQLcl process. Never forward raw database output."""

    def __init__(self, executable: str, connection: str, timeout: float = 30):
        self.timeout = timeout
        self.lines: queue.Queue = queue.Queue()
        self.process = subprocess.Popen(
            [executable, "-S", "-L", "/nolog"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace", start_new_session=True,
        )
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.execute(SQLCL_SETTINGS + f'connect -name "{connection}"\n', "connect")
        except BaseException:
            self.close()
            raise

    def _read(self) -> None:
        try:
            for line in self.process.stdout:
                self.lines.put(line)
        finally:
            self.lines.put(None)

    def execute(self, sql: str, stage: str) -> None:
        marker = "LOCK_TEST_" + uuid.uuid4().hex
        try:
            self.process.stdin.write(sql + "\nprompt " + marker + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise TestFailure(f"{stage}: SQLcl session unavailable") from exc
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                line = self.lines.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TestFailure(f"{stage}: SQLcl timeout") from exc
            if line is None:
                raise TestFailure(f"{stage}: SQLcl exited before completion")
            error = re.search(r"\b(?:ORA|PLS|SP2|SP1|SQLCL)-\d+", line)
            if error:
                raise TestFailure(f"{stage}: {error.group(0)} (raw output suppressed)")
            if line.strip() == marker:
                return

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                self.process.stdin.write("exit failure rollback\n")
                self.process.stdin.flush()
                self.process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                # Only the process group created by this instance is affected.
                try:
                    os.killpg(self.process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()


def call_lock(method: str, actor: str) -> str:
    return (f"pk_dev_object_lock.{method}(p_object_name => :test_key, "
            f"p_object_type => 'PACKAGE', p_lock_owner => '{actor}');")


def fixture_guard() -> str:
    # Runtime acquire/assert/release may expire ALL old active rows. Refuse a
    # table containing any other key instead of promising fixture-only effects.
    return """declare
  l_count number;
begin
  select count(*) into l_count from dev_object_lock
   where object_owner != user or object_name != :test_key or object_type != 'PACKAGE';
  if l_count != 0 then
    raise_application_error(-20072, 'LOCK_TEST requires a dedicated empty runtime');
  end if;
  if pk_dev_object_lock.func_runtime_version != '1.1.0' then
    raise_application_error(-20072, 'LOCK_TEST unsupported runtime');
  end if;
end;
/
"""


def assert_no_active() -> str:
    return """declare
  l_count number;
begin
  select count(*) into l_count from dev_object_lock
   where object_owner = user and object_name = :test_key and object_type = 'PACKAGE'
     and lock_status = 'ACTIVE';
  if l_count != 0 then
    raise_application_error(-20072, 'LOCK_TEST active fixture residue');
  end if;
end;
/
"""


def cleanup_sql() -> str:
    # No delete/purge or force operation. Released history remains as evidence.
    return fixture_guard() + """begin
  for r in (select locked_by from dev_object_lock
             where object_owner = user and object_name = :test_key
               and object_type = 'PACKAGE' and lock_status = 'ACTIVE'
               and locked_by in ('SMOKE_A', 'SMOKE_B')) loop
    pk_dev_object_lock.proc_liberar_lock(
      p_object_name => :test_key, p_object_type => 'PACKAGE', p_lock_owner => r.locked_by);
  end loop;
end;
/
""" + assert_no_active()


def exercise(a, b) -> None:
    a.execute(fixture_guard(), "isolation")
    a.execute("begin " + call_lock("proc_adquirir_lock", "SMOKE_A") + " end;\n/", "acquire_A")
    a.execute("begin " + call_lock("proc_assert_lock_compilacao", "SMOKE_A") + " end;\n/", "assert_A")
    for method, expected in (("proc_adquirir_lock", -20083), ("proc_assert_lock_compilacao", -20088)):
        b.execute(f"""begin
  begin
    {call_lock(method, 'SMOKE_B')}
    raise_application_error(-20072, 'LOCK_TEST expected contention was not observed');
  exception when others then
    if sqlcode != {expected} then raise; end if;
  end;
end;
/
""", "reject_B_" + method)
    a.execute("begin " + call_lock("proc_liberar_lock", "SMOKE_A") + " end;\n/", "release_A")
    b.execute("begin\n" + "\n".join(call_lock(method, "SMOKE_B") for method in (
        "proc_adquirir_lock", "proc_assert_lock_compilacao", "proc_liberar_lock"
    )) + "\nend;\n/", "acquire_assert_release_B")
    b.execute(assert_no_active(), "postcondition")


def run_test(executable: str, connection: str, expectations: dict, factory=SqlclSession) -> None:
    sessions = []
    test_key = "AI_LOCK_TEST_" + uuid.uuid4().hex[:16].upper()
    initialization = render_preflight(expectations) + (
        "variable test_key varchar2(30)\nbegin :test_key := '" + test_key + "'; end;\n/\n"
    )
    try:
        for _ in range(2):
            session = factory(executable, connection)
            sessions.append(session)
            session.execute(initialization, "identity")
        original_failure = None
        try:
            exercise(*sessions)
        except TestFailure as exc:
            original_failure = exc
            raise
        finally:
            for session in sessions:
                session.close()
            sessions.clear()
            # Reconnect and recheck identity: a failed SQLcl session may already
            # have exited, and autonomous runtime commits survive that failure.
            try:
                recovery = factory(executable, connection)
                try:
                    recovery.execute(initialization, "cleanup_identity")
                    recovery.execute(cleanup_sql(), "cleanup")
                finally:
                    recovery.close()
            except (OSError, TestFailure) as cleanup_error:
                detail = str(cleanup_error) if isinstance(cleanup_error, TestFailure) else "SQLcl unavailable"
                if original_failure:
                    raise TestFailure(f"{original_failure}; cleanup also failed: {detail}") from cleanup_error
                raise TestFailure(f"cleanup failed: {detail}") from cleanup_error
    except (OSError, TestFailure) as exc:
        print(f"LOCK_TEST fixture={test_key}; inspect active residue in the authorized lab if cleanup failed",
              file=sys.stderr)
        if isinstance(exc, OSError):
            raise TestFailure("Cannot start SQLcl; database output and paths suppressed") from exc
        raise
    finally:
        for session in sessions:
            session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", type=Path, required=True)
    parser.add_argument("--connection", required=True, help="Existing saved SQLcl connection name only")
    parser.add_argument("--sql", default="sql", help="SQLcl on PATH or the approved launcher")
    parser.add_argument("--run", action="store_true", help="Execute the database mutation after separate authorization")
    parser.add_argument("--confirm", choices=["ISOLATED_DEV_LOCK_TEST"])
    args = parser.parse_args()
    try:
        expected = load_expectations(args.expect)
        if "apex" in expected or expected["session_user"] != expected["current_schema"]:
            raise ValueError("Use database-only expectations with session_user equal to current_schema")
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", args.connection):
            raise ValueError("Use a simple saved connection name, not a connection string")
        if not args.run:
            print("LOCK_TEST PLAN: two sessions; A owns, B rejected, A releases, B owns/releases; no database contacted")
            return 0
        if args.confirm != "ISOLATED_DEV_LOCK_TEST" or os.name != "posix":
            raise ValueError("Execution requires POSIX and --confirm ISOLATED_DEV_LOCK_TEST")
        run_test(args.sql, args.connection, expected)
    except (ValueError, TestFailure) as exc:
        print(f"LOCK_TEST FAIL: {exc}", file=sys.stderr)
        return 1
    print("LOCK_TEST PASS; two-session ownership checks passed; released fixture history retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
