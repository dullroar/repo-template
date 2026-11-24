"""Tests for the CI workflow file. They read the workflow as text.

Run me when: I change .github/workflows/context.yml.
"""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "context.yml"
SHA_USES = re.compile(r"^\s*-?\s*uses:\s*\S+@[0-9a-f]{40}(\s|$)")
USES = re.compile(r"^\s*-?\s*uses:")


def unpinned_uses(text):
    return [l for l in text.splitlines() if USES.match(l) and not SHA_USES.match(l)]


def has_read_only(text):
    return re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", text, re.M) is not None


def has_paths_filter(text):
    return re.search(r"^\s*paths(-ignore)?:", text, re.M) is not None


def has_continue_on_error(text):
    return re.search(r"continue-on-error", text) is not None


def job_name_is_context(text):
    return re.search(r"^  context:\n    name: context$", text, re.M) is not None


def has_guard_steps(text):
    return (
        "scripts/secret_guard.py --tracked" in text
        and "scripts/secret_guard.py --range" in text
        and "fetch-depth: 0" in text
    )


def has_ci_profile(text):
    return "--profile ci" in text and "--report" in text


class WorkflowRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = WORKFLOW.read_text(encoding="utf-8")

    def test_pinned_uses(self):
        bad = "steps:\n  - uses: actions/checkout@v4\n"
        self.assertEqual(len(unpinned_uses(bad)), 1)
        short = "  - uses: actions/checkout@abc123 # v4\n"
        self.assertEqual(len(unpinned_uses(short)), 1)
        self.assertEqual(unpinned_uses(self.real), [])
        self.assertIn("uses:", self.real)

    def test_read_only(self):
        self.assertFalse(has_read_only("name: x\njobs: {}\n"))
        self.assertFalse(has_read_only("permissions:\n  contents: write\n"))
        self.assertTrue(has_read_only(self.real))

    def test_no_paths_filter(self):
        self.assertTrue(has_paths_filter("on:\n  push:\n    paths:\n      - a\n"))
        self.assertFalse(has_paths_filter(self.real))

    def test_no_continue_on_error(self):
        self.assertTrue(has_continue_on_error("    continue-on-error: true\n"))
        self.assertFalse(has_continue_on_error(self.real))

    def test_job_name(self):
        self.assertFalse(job_name_is_context("jobs:\n  controls:\n    name: controls\n"))
        self.assertTrue(job_name_is_context(self.real))

    def test_guard_steps(self):
        self.assertFalse(has_guard_steps("steps:\n  - run: echo hi\n"))
        self.assertTrue(has_guard_steps(self.real))

    def test_ci_profile(self):
        self.assertFalse(has_ci_profile("run: python3 scripts/check_context.py\n"))
        self.assertTrue(has_ci_profile(self.real))

    def test_triggers(self):
        for trigger in ("pull_request:", "push:", "workflow_dispatch:"):
            self.assertIn(trigger, self.real)


if __name__ == "__main__":
    unittest.main()
