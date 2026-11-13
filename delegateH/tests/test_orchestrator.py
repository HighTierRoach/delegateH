"""Offline process and Git integration tests. The provider fixture uses no network."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/orchestrator.py"
MODEL = "gemini-4-hydrogen-medium"
FIXTURE = r"""
import json, os, pathlib, subprocess, sys, time
args = sys.argv[1:]
model = "gemini-4-hydrogen-medium"
cwd = pathlib.Path.cwd()
home = pathlib.Path.home()
if args[:1] == ["acp"]:
    assert "--sandbox" in args
    assert "GEMINI_API_KEY" not in os.environ and "AGY_ADC_AUTH" not in os.environ
    for line in sys.stdin:
        request = json.loads(line)
        method = request["method"]
        if method == "initialize":
            assert request["params"]["protocolVersion"] == 1
            result = {"protocolVersion": 1, "agentCapabilities": {
                "sessionCapabilities": {"close": {}, "resume": {}}, "loadSession": True}}
        elif method == "session/new":
            assert request["params"] == {"cwd": str(cwd.resolve()), "mcpServers": []}
            available = "gemini-3.8-flash-high" if (home / "missing-model").exists() else model
            result = {"sessionId": "test-session", "models": {
                "availableModels": [{"modelId": available}]}}
        elif method == "session/close":
            assert request["params"] == {"sessionId": "test-session"}
            (home / "acp-closed").touch()
            result = {}
        else:
            raise AssertionError(method)
        print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}), flush=True)
    sys.exit(0)
if args == ["--help"]:
    print("--settings --input-format --output-format --json-schema --model --mode --sandbox --disable-slash-commands --log-file", file=sys.stderr)
    sys.exit(0)
if args == ["--version"]:
    print("offline-fixture")
    sys.exit(0)
settings = json.loads(args[args.index("--settings") + 1])
assert settings["modelProvider"] == "" and settings["useG1Credits"] is False
assert "GEMINI_API_KEY" not in os.environ and "AGY_ADC_AUTH" not in os.environ
assert "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ
assert "command(*)" in settings["permissions"]["deny"]
if args[-1] == "models":
    if not (home / "missing-model").exists():
        print(model + "\tGemini 4 Hydrogen (Medium)")
    else:
        print("another-model\tAnother model")
    sys.exit(0)
assert args[args.index("--model") + 1] == model
assert args[args.index("--log-file") + 1] == os.devnull
assert "--sandbox" in args
prompt = json.loads(sys.stdin.readline())["message"]["content"]
objective = next(line.split(": ", 1)[1] for line in prompt.splitlines() if line.startswith("Objective: "))
action, _, target = objective.partition(" ")
if action == "fail":
    print(json.dumps({"event":"result", "result":{"status":"ERROR", "error":"429 quota"}}))
    sys.exit(1)
if action == "transient":
    marker = home / "retries"
    if not marker.exists():
        marker.touch()
        print(json.dumps({"event":"result", "result":{"status":"ERROR", "error":"503 service unavailable"}}))
        sys.exit(1)
if action == "hang":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(90)"])
    (home / "descendant").write_text(str(child.pid))
    time.sleep(90)
if action == "concurrent":
    marker = home / ("started-" + cwd.name)
    marker.touch()
    deadline = time.monotonic() + 5
    while len(list(home.glob("started-*"))) < 3:
        assert time.monotonic() < deadline
        time.sleep(0.025)
    assert not (cwd / "local-only.txt").exists()
    assert not (cwd / ".env").exists()
    assert not (cwd / "link").exists()
    assert not (cwd / "other.txt").exists()
    file = cwd / target
    assert file.read_text() == "VALUE = 1\n"
    file.write_text("VALUE = 2\n")
if action == "write-new":
    (cwd / target).write_text("VALUE = 2\n")
if action == "mutate":
    (cwd / "out-of-scope").write_text("reject")
if action == "denied":
    print("Tool requires user approval", file=sys.stderr)
reported = "wrong-model" if action == "wrong-model" else model
print(json.dumps({"event":"init","init":{"model":reported,"cwd":str(cwd),"permission_mode":"request-review"}}))
report = {"status":"blocked" if action == "blocked" else "completed",
          "summary":"Synthetic fixture result", "evidence":["Checked requested output"],
          "checks":["GEMINI_API_KEY=synthetic-secret"] if action == "redact" else []}
print(json.dumps({"event":"result","result":{"status":"SUCCESS","structured_output":report,
                  "usage":{"total_tokens":42}}}))
"""


class LocalIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delegateH-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "home"
        binary = self.home / ".local/bin/agy"
        binary.parent.mkdir(parents=True)
        binary.write_text(f"#!{sys.executable}\n" + FIXTURE, encoding="utf-8")
        binary.chmod(0o700)
        self.env = dict(os.environ, HOME=str(self.home), GEMINI_API_KEY="synthetic-secret",
                        AGY_ADC_AUTH="true", GOOGLE_APPLICATION_CREDENTIALS="/synthetic")
        self.state = self.home / ".local/state/delegateH"

    def command(self, *args):
        return [sys.executable, "-B", str(SCRIPT), *map(str, args)]

    def cli(self, *args):
        return subprocess.run(self.command(*args), env=self.env, text=True, capture_output=True,
                              timeout=35, check=False)

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], env=self.env, text=True)

    def repository(self, name):
        repo = self.root / name
        repo.mkdir()
        self.git(repo, "init", "-q")
        for filename in ("a.py", "b.py", "c.py"):
            (repo / filename).write_text("VALUE = 1\n")
        (repo / "other.txt").write_text("untouched\n")
        (repo / ".env").write_text("private fixture\n")
        (repo / "link").symlink_to("other.txt")
        (repo / "test_values.py").write_text(
            "import unittest, a, b, c\n"
            "class Values(unittest.TestCase):\n"
            "    def test_values(self):\n"
            "        self.assertEqual((a.VALUE,b.VALUE,c.VALUE),(2,2,2))\n")
        self.git(repo, "add", ".")
        self.git(repo, "-c", "user.name=Test", "-c", "user.email=test@localhost",
                 "commit", "-qm", "baseline")
        return repo

    def manifest(self, actions, mode="TEST"):
        tasks = []
        for index, action in enumerate(actions):
            objective, _, target = action.partition(" ")
            share = []
            write = []
            if objective == "concurrent":
                share = [target, ".env", "link"]
                write = [target]
            if objective == "write-new":
                write = [target]
            tasks.append({"id": f"worker-{index}", "objective": action, "expected": "Fixture evidence",
                          "share": share, "write": write})
        path = self.root / "manifest.json"
        path.write_text(json.dumps({"mode": mode, "tasks": tasks}))
        return path

    def summary(self, result):
        self.assertTrue(result.stdout, result.stderr)
        event = json.loads(result.stdout.splitlines()[0])
        path = Path(event["path"])
        return path, json.loads((path / "summary.json").read_text())

    def test_three_concurrent_isolated_workers_and_reviewed_integration(self):
        repo = self.repository("first-project")
        (repo / "other.txt").write_text("staged\n")
        self.git(repo, "add", "other.txt")
        (repo / "other.txt").write_text("unstaged\n")
        (repo / "local-only.txt").write_text("untracked\n")
        status = self.git(repo, "status", "--porcelain")
        result = self.cli("run", self.manifest(["concurrent a.py", "concurrent b.py", "concurrent c.py"],
                                               "BUILD"), "--repo", repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        run, data = self.summary(result)
        self.assertEqual(data["state"], "review_required")
        self.assertEqual(self.git(repo, "status", "--porcelain"), status)
        self.assertEqual((repo / "other.txt").read_text(), "unstaged\n")
        self.assertEqual(self.git(repo, "show", ":other.txt"), "staged\n")
        self.assertEqual((repo / "local-only.txt").read_text(), "untracked\n")
        entries = list(data["workers"].values())
        self.assertEqual(len({entry["workspace"] for entry in entries}), 3)
        attempts = [entry["attempts"][0] for entry in entries]
        self.assertLess(max(a["started_at"] for a in attempts), min(a["ended_at"] for a in attempts))
        self.assertEqual(self.cli("cleanup", run.name).returncode, 2)
        for entry, filename in zip(entries, ("a.py", "b.py", "c.py")):
            self.assertEqual(entry["reported_model"], MODEL)
            self.assertEqual(entry["changed_files"], [filename])
            self.assertEqual(entry["excluded_files"], 2)
            self.assertEqual(entry["usage"], {"total_tokens": 42})
            patch = Path(entry["patch"])
            self.assertIn("+VALUE = 2\n", patch.read_text())
            self.git(repo, "apply", "--check", "--", str(patch))
            self.git(repo, "apply", "--", str(patch))
        subprocess.run([sys.executable, "-B", "-m", "unittest", "-q"], cwd=repo, check=True)
        self.assertEqual(self.git(repo, "show", ":other.txt"), "staged\n")
        self.assertEqual((repo / "other.txt").read_text(), "unstaged\n")
        self.assertEqual(self.cli("cleanup", run.name, "--discard").returncode, 0)
        self.assertFalse(run.exists())

    def test_second_project_and_new_file(self):
        repo = self.repository("second-project")
        result = self.cli("run", self.manifest(["write-new new.py"]), "--repo", repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        run, data = self.summary(result)
        patch = data["workers"]["worker-0"]["patch"]
        self.git(repo, "apply", "--check", "--", patch)
        self.assertFalse((repo / "new.py").exists())
        self.assertEqual(self.cli("cleanup", run.name, "--discard").returncode, 0)

    def test_failure_retry_scope_permission_and_report_validation(self):
        cases = {"fail": "quota", "blocked": "incomplete", "wrong-model": "unverified_session",
                 "mutate": "out_of_scope_changes", "denied": "permission",
                 "transient": "candidate", "redact": "candidate"}
        for action, status in cases.items():
            with self.subTest(action=action):
                result = self.cli("run", self.manifest([action], "AUDIT"))
                run, data = self.summary(result)
                worker = data["workers"]["worker-0"]
                self.assertEqual(worker["status"], status)
                self.assertEqual(result.returncode, 0 if status == "candidate" else 1)
                self.assertNotIn("synthetic-secret", (run / "summary.json").read_text())
                if action == "transient":
                    self.assertEqual([a["status"] for a in worker["attempts"]], ["transient", "candidate"])
                discard = ["--discard"] if action == "mutate" else []
                self.assertEqual(self.cli("cleanup", run.name, *discard).returncode, 0)

    def test_missing_model_creates_no_run(self):
        (self.home / "missing-model").touch()
        result = self.cli("healthcheck")
        self.assertEqual(json.loads(result.stdout)["status"], "model_unavailable")
        result = self.cli("run", self.manifest(["read"], "DEBUG"))
        self.assertEqual(result.returncode, 2)
        self.assertFalse(list(self.state.glob("run-*")))

    def test_acp_catalog_closes_session_without_prompting(self):
        listed = self.cli("healthcheck", "--acp")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertTrue((self.home / "acp-closed").is_file())
        self.assertEqual(json.loads(listed.stdout)["available_models"], [MODEL])
        self.assertTrue(json.loads(listed.stdout)["supports_resume"])
        (self.home / "missing-model").touch()
        missing = self.cli("healthcheck", "--acp")
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(json.loads(missing.stdout)["status"], "model_unavailable")

    def test_timeout_and_cancellation_terminate_process_groups(self):
        timed = self.cli("run", self.manifest(["hang"]), "--timeout", 1)
        run, data = self.summary(timed)
        self.assertEqual(data["workers"]["worker-0"]["status"], "timeout")
        self.assertEqual(self.cli("cleanup", run.name).returncode, 0)
        marker = self.home / "descendant"
        marker.unlink(missing_ok=True)
        with subprocess.Popen(self.command("run", self.manifest(["hang"])),
                              env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as proc:
            try:
                deadline = time.monotonic() + 10
                while not marker.exists() and time.monotonic() < deadline and proc.poll() is None:
                    time.sleep(0.025)
                self.assertTrue(marker.exists())
                proc.send_signal(signal.SIGTERM)
                out, err = proc.communicate(timeout=8)
            finally:
                if proc.poll() is None:
                    proc.kill()
        self.assertEqual(proc.returncode, 130, err)
        event = json.loads(out.splitlines()[0])
        run = Path(event["path"])
        data = json.loads((run / "summary.json").read_text())
        self.assertEqual(data["state"], "cancelled")
        self.assertEqual(data["workers"]["worker-0"]["status"], "cancelled")
        pid = int(marker.read_text())
        probe = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
        self.assertTrue(probe.returncode or probe.stdout.strip().startswith("Z"), probe.stdout)
        self.assertEqual(self.cli("cleanup", run.name).returncode, 2)
        self.assertEqual(self.cli("cleanup", run.name, "--discard").returncode, 0)


if __name__ == "__main__":
    unittest.main()
