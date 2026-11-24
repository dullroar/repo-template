"""Smoke tests: the pinned library on a fresh copy and on an old copy of the template.

Run me when: I change the shim, the pin, the plan checks or the old check scripts.

The tests need the network once, to fill the cache of the library.
If the library is not available, the tests skip with the message "library not available".
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIM = ROOT / "scripts" / "check_context.py"
BAD_PLAN = "plans/smoke-bad-plan"
STEP_NO_GATE = (
    "---\nid: s1\nstatus: pending\ndepends_on: []\ntouches:\n  - a.txt\nlane: none\n"
    'claimed_by: ""\nclaimed_at: ""\nevidence: ""\n---\n\n# A step without a gate\n'
)


def git(cwd, *args, check=True):
    return subprocess.run(
        ["git", "-c", "user.name=smoke", "-c", "user.email=smoke@example.invalid", *args],
        cwd=cwd, capture_output=True, text=True, check=check,
    )


def load_shim():
    spec = importlib.util.spec_from_file_location("shim_under_test", SHIM)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def library_python():
    """Return the Python of the cached library environment, or None."""
    try:
        shim = load_shim()
        spec, commit = shim.pinned()
        return shim.ensure_environment(spec, commit)
    except Exception:  # no network and no cache
        return None


def export_tree(commit, target):
    """Write the tracked files of a commit to target, as a new Git repository with one commit."""
    target.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", commit], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    git(target, "init", "-q", "-b", "main")
    git(target, "add", "-A")
    git(target, "commit", "-q", "-m", "copy")


def add_bad_plan(repo):
    plan = repo / BAD_PLAN
    (plan / "steps").mkdir(parents=True)
    for name in ("goal.md", "plan.md"):
        shutil.copy(repo / "plans" / "for-each-plan" / name, plan / name)
    (plan / "steps" / "s1.md").write_text(STEP_NO_GATE, encoding="utf-8")


def remove_bad_plan(repo):
    shutil.rmtree(repo / BAD_PLAN)


def run_check(repo, python=None):
    """Run the context check of a repository. Return (exit code, output)."""
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "check_context.py")],
        cwd=repo, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def library_rule_ids(python, repo):
    """Return the IDs of the library checks that failed."""
    proc = subprocess.run(
        [str(python), "-m", "deterministic_controls", "check", "--root", str(repo),
         "--profile", "ci", "--format", "json"],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, [
        c["check_id"] for c in json.loads(proc.stdout)["checks"] if c["status"] != "passed"
    ]


class SmokeBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = library_python()
        if cls.python is None:
            raise unittest.SkipTest("library not available")
        cls.tmp = Path(tempfile.mkdtemp(prefix="smoke-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, "tmp", ""), ignore_errors=True)


class FreshCopyTest(SmokeBase):
    def test_fresh_copy_passes_fails_and_passes_again(self):
        repo = self.tmp / "fresh"
        export_tree("HEAD", repo)
        code, out = run_check(repo)
        self.assertEqual(code, 0, out)
        add_bad_plan(repo)
        code, out = run_check(repo)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL check_plan.py", out)
        lib_code, _, failed = library_rule_ids(self.python, repo)
        self.assertEqual(lib_code, 1)
        self.assertIn("plans.schema", failed)
        remove_bad_plan(repo)
        code, out = run_check(repo)
        self.assertEqual(code, 0, out)


class OldCopyTest(SmokeBase):
    def old_commit(self):
        added = git(ROOT, "log", "--diff-filter=A", "--format=%H", "--", "plans/adopt-controls/goal.md").stdout.split()
        if not added:
            self.skipTest("history of the plan is not available")
        return added[-1] + "^"

    def test_old_copy_matches_after_adopt_apply(self):
        old = self.old_commit()
        if git(ROOT, "rev-parse", "--verify", "-q", old, check=False).returncode != 0:
            self.skipTest("history of the plan is not available")
        repo = self.tmp / "old"
        export_tree(old, repo)
        # Old scripts, before adoption.
        old_clean, _ = run_check(repo)
        add_bad_plan(repo)
        old_bad, old_bad_out = run_check(repo)
        remove_bad_plan(repo)
        self.assertEqual(old_clean, 0)
        self.assertEqual(old_bad, 1, old_bad_out)
        self.assertIn("check_plan.py", old_bad_out)
        # Adopt the pinned library. Then run the new shim.
        spec, commit = load_shim().pinned()
        proc = subprocess.run(
            [str(self.python), "-m", "deterministic_controls", "adopt", "apply",
             "--root", str(repo), "--commit", commit],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # Step m01 added a "Run me when" line to the pin by hand: the index builder needs it.
        pin = repo / "scripts" / "controls-requirements.txt"
        if pin.is_file() and "Run me when:" not in pin.read_text(encoding="utf-8"):
            pin.write_text(
                "# Run me when: I change the pinned version of the controls library.\n"
                + pin.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        # The shim changes the script index. Rebuild it, as the template rules say.
        built = subprocess.run([sys.executable, "scripts/build_indexes.py"], cwd=repo, capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "adopt", check=False)
        new_clean, new_clean_out = run_check(repo)
        add_bad_plan(repo)
        new_bad, new_bad_out = run_check(repo)
        _, _, failed = library_rule_ids(self.python, repo)
        self.assertEqual(new_clean, old_clean, new_clean_out)
        self.assertEqual(new_bad, old_bad, new_bad_out)
        self.assertIn("plans.schema", failed)


if __name__ == "__main__":
    unittest.main()
