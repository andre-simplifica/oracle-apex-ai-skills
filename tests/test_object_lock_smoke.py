from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from object_lock_smoke import SqlclSession, TestFailure, run_test
from test_target_preflight import database_target


class LockSmokeTests(unittest.TestCase):
    def test_default_plan_and_confirmation_failure_do_not_launch_sqlcl(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target.json"
            target.write_text(json.dumps(database_target()))
            command = [sys.executable, str(REPO_ROOT / "scripts/object_lock_smoke.py"),
                       "--expect", str(target), "--connection", "DEV_SQLCL_CONNECTION",
                       "--sql", "/nonexistent/sqlcl"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("no database contacted", result.stdout)
            result = subprocess.run(command + ["--run"], capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--confirm", result.stderr)
            self.assertNotIn("Cannot start SQLcl", result.stderr)

    def test_two_independent_sessions_and_cleanup_after_failure(self):
        sessions = []
        events = []

        class FakeSession:
            def __init__(self, executable, connection):
                self.number = len(sessions)
                sessions.append(self)

            def execute(self, sql, stage):
                events.append((self.number, stage))
                if stage == "release_A":
                    raise TestFailure("injected session failure after autonomous acquire")

            def close(self):
                events.append((self.number, "closed"))

        with self.assertRaisesRegex(TestFailure, "injected"):
            run_test("unused", "unused", database_target(), factory=FakeSession)
        self.assertIn((0, "acquire_A"), events)
        self.assertIn((1, "reject_B_proc_adquirir_lock"), events)
        self.assertIn((1, "reject_B_proc_assert_lock_compilacao"), events)
        self.assertLess(events.index((0, "closed")), events.index((2, "cleanup")))
        self.assertLess(events.index((1, "closed")), events.index((2, "cleanup")))
        self.assertIn((2, "cleanup_identity"), events)
        self.assertIn((2, "closed"), events)

    def test_process_protocol_detects_database_error_and_timeout_without_leaking_output(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "fake-sqlcl"
            fake.write_text(f"""#!{sys.executable}
import sys, time
for line in sys.stdin:
    if line.startswith('exit '):
        break
    if line.startswith('break-test'):
        print('ORA-20072: private-example', flush=True)
    elif line.startswith('slow-test'):
        time.sleep(0.5)
    elif line.startswith('prompt '):
        print(line[7:].strip(), flush=True)
""")
            fake.chmod(0o700)
            session = SqlclSession(str(fake), "EXAMPLE_CONNECTION", timeout=1)
            try:
                session.execute("begin null; end;\n/", "success")
                with self.assertRaisesRegex(TestFailure, "ORA-20072") as error:
                    session.execute("break-test", "failure")
                self.assertNotIn("private-example", str(error.exception))
            finally:
                session.close()
            session = SqlclSession(str(fake), "EXAMPLE_CONNECTION", timeout=0.1)
            try:
                with self.assertRaisesRegex(TestFailure, "timeout"):
                    session.execute("slow-test", "timeout_case")
            finally:
                session.close()
            self.assertIsNotNone(session.process.poll())
