"""Tests for scripts/prit-*.sh. They use a temporary bare remote and a fake gh command.

Run me when: I change any scripts/prit-*.sh file or the prit skill.
"""
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

# A fake gh. State lives in files under $FAKE_GH_DIR:
#   open_<branch> and merged_<branch> hold a PR number; state_<n> holds the PR state;
#   checks_rc holds the exit code of "pr checks"; mstate holds mergeStateStatus.
FAKE_GH = textwrap.dedent(
    r"""
    #!/usr/bin/env bash
    d="$FAKE_GH_DIR"
    echo "$*" >>"$d/calls.log"
    get_head() { while [ $# -gt 0 ]; do [ "$1" = "--head" ] && { echo "${2//\//__}"; return; }; shift; done; }
    get_flag() { local f=$1; shift; while [ $# -gt 0 ]; do [ "$1" = "$f" ] && { echo "$2"; return; }; shift; done; }
    case "$1 $2" in
      "repo view") echo main ;;
      "pr list")
        b=$(get_head "$@"); st=$(get_flag --state "$@")
        [ -f "$d/${st}_$b" ] && cat "$d/${st}_$b" || true ;;
      "pr create")
        b=$(get_head "$@"); echo 7 >"$d/open_$b"; echo OPEN >"$d/state_7"
        echo "https://example.invalid/pr/7" ;;
      "pr checks") [ -f "$d/checks_out" ] && cat "$d/checks_out"; exit "$(cat "$d/checks_rc" 2>/dev/null || echo 0)" ;;
      "pr view")
        case "$*" in
          *url*) echo "https://example.invalid/pr/$3" ;;
          *mergeStateStatus*) echo "$(cat "$d/state_$3") $(cat "$d/mstate" 2>/dev/null || echo CLEAN)" ;;
          *) cat "$d/state_$3" ;;
        esac ;;
      "pr merge")
        for f in "$d"/open_*; do
          [ "$(cat "$f")" = "$3" ] && { b=${f##*/open_}; mv "$f" "$d/merged_$b"; }
        done
        echo MERGED >"$d/state_$3" ;;
      *) echo "fake gh: unsupported: $*" >&2; exit 9 ;;
    esac
    """
).lstrip()


def sh(args, cwd, env=None, check=True):
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=check)


class PritBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.fake = self.tmp / "gh_state"
        self.fake.mkdir()
        bindir = self.tmp / "bin"
        bindir.mkdir()
        gh = bindir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=f"{bindir}:{os.environ['PATH']}",
            FAKE_GH_DIR=str(self.fake),
            GIT_AUTHOR_NAME="t",
            GIT_AUTHOR_EMAIL="t@example.invalid",
            GIT_COMMITTER_NAME="t",
            GIT_COMMITTER_EMAIL="t@example.invalid",
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_SYSTEM="/dev/null",
        )
        self.remote = self.tmp / "remote.git"
        sh(["git", "init", "--bare", "-b", "main", str(self.remote)], self.tmp, self.env)
        seed = self.tmp / "seed"
        sh(["git", "clone", str(self.remote), str(seed)], self.tmp, self.env)
        (seed / "a.txt").write_text("a\n")
        sh(["git", "add", "."], seed, self.env)
        sh(["git", "commit", "-m", "init"], seed, self.env)
        sh(["git", "push", "origin", "HEAD:main"], seed, self.env)
        self.repo = self.tmp / "work"
        sh(["git", "clone", str(self.remote), str(self.repo)], self.tmp, self.env)
        sh(["git", "checkout", "-b", "feature/x"], self.repo, self.env)

    def git(self, *args, cwd=None):
        return sh(["git", *args], cwd or self.repo, self.env)

    def run_script(self, name, *args, cwd=None):
        return sh(["bash", str(SCRIPTS / name), *args], cwd or self.repo, self.env, check=False)

    def commit_file(self, name="b.txt"):
        (self.repo / name).write_text("b\n")
        self.git("add", name)
        self.git("commit", "-m", "add " + name)

    def calls(self):
        p = self.fake / "calls.log"
        return p.read_text() if p.exists() else ""


class Check(PritBase):
    def test_refuses_default_branch(self):
        self.git("checkout", "main")
        r = self.run_script("prit-01-check.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("default branch", r.stderr)

    def test_clean_tree_exit_0(self):
        self.commit_file()
        r = self.run_script("prit-01-check.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tree: clean", r.stdout)

    def test_dirty_tree_exit_3_with_groups(self):
        (self.repo / "a.txt").write_text("changed\n")  # unstaged
        (self.repo / "s.txt").write_text("s\n")
        self.git("add", "s.txt")  # staged
        (self.repo / "u.txt").write_text("u\n")  # untracked
        r = self.run_script("prit-01-check.sh")
        self.assertEqual(r.returncode, 3)
        out = r.stdout
        self.assertIn("A  s.txt", out.split("-- unstaged")[0])
        self.assertIn(" M a.txt", out.split("-- unstaged")[1].split("-- untracked")[0])
        self.assertIn("?? u.txt", out.split("-- untracked")[1])

    def test_plan_end_candidate(self):
        steps = self.repo / "plans" / "p1" / "steps"
        steps.mkdir(parents=True)
        (steps / "01.md").write_text("---\nstatus: done\n---\n")
        (self.repo / "plans" / "p2" / "steps").mkdir(parents=True)
        (self.repo / "plans" / "p2" / "steps" / "01.md").write_text("---\nstatus: pending\n---\n")
        r = self.run_script("prit-01-check.sh")
        self.assertIn("PLAN-END candidate: plans/p1", r.stdout)
        self.assertNotIn("plans/p2", r.stdout.split("tree:")[0])


class Push(PritBase):
    def test_refuses_dirty(self):
        (self.repo / "u.txt").write_text("u\n")
        self.assertEqual(self.run_script("prit-02-push.sh").returncode, 1)

    def test_pushes_then_is_idempotent(self):
        self.commit_file()
        r = self.run_script("prit-02-push.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        heads = sh(["git", "ls-remote", "--heads", str(self.remote)], self.tmp, self.env).stdout
        self.assertIn("refs/heads/feature/x", heads)
        r2 = self.run_script("prit-02-push.sh")
        self.assertEqual(r2.returncode, 0)
        self.assertIn("Nothing to push", r2.stdout)

    def test_never_forces_when_remote_has_extra_commits(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")
        other = self.tmp / "other"
        sh(["git", "clone", "-b", "feature/x", str(self.remote), str(other)], self.tmp, self.env)
        (other / "o.txt").write_text("o\n")
        sh(["git", "add", "."], other, self.env)
        sh(["git", "commit", "-m", "other"], other, self.env)
        sh(["git", "push"], other, self.env)
        self.commit_file("c.txt")
        r = self.run_script("prit-02-push.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("never forces", r.stderr)


class OpenPr(PritBase):
    def pushed(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")

    def body(self, text):
        p = self.tmp / "body.md"
        p.write_text(text)
        return str(p)

    def test_rejects_long_body(self):
        self.pushed()
        r = self.run_script("prit-03-open-pr.sh", "t", self.body("x" * 4001))
        self.assertEqual(r.returncode, 1)
        self.assertIn("limit is 4000", r.stderr)
        self.assertNotIn("pr create", self.calls())

    def test_requires_push_first(self):
        self.commit_file()
        r = self.run_script("prit-03-open-pr.sh", "t", self.body("ok"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("prit-02-push.sh", r.stderr)

    def test_creates_then_reuses(self):
        self.pushed()
        r = self.run_script("prit-03-open-pr.sh", "My title", self.body("ok"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pr create --base main --head feature/x --title My title", self.calls())
        r2 = self.run_script("prit-03-open-pr.sh", "My title", self.body("ok"))
        self.assertIn("already open", r2.stdout)
        self.assertEqual(self.calls().count("pr create"), 1)


class Merge(PritBase):
    def open_pr(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")
        (self.fake / "open_feature__x").write_text("7\n")
        (self.fake / "state_7").write_text("OPEN\n")

    def test_no_pr(self):
        self.commit_file()
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no open PR", r.stderr)

    def test_failing_checks_block_merge(self):
        self.open_pr()
        (self.fake / "checks_rc").write_text("1")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("pr merge", self.calls())

    def test_pending_checks_block_merge(self):
        self.open_pr()
        (self.fake / "checks_rc").write_text("8")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("pending", r.stderr)

    def test_conflicts_block_merge(self):
        self.open_pr()
        (self.fake / "mstate").write_text("DIRTY")
        self.assertEqual(self.run_script("prit-04-merge.sh").returncode, 1)
        self.assertNotIn("pr merge", self.calls())

    def test_squash_merge_without_admin_or_delete(self):
        self.open_pr()
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pr merge 7 --squash", self.calls())
        self.assertNotIn("--admin", self.calls())
        self.assertNotIn("--delete-branch", self.calls())


class Cleanup(PritBase):
    def merged(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")
        (self.fake / "merged_feature__x").write_text("7\n")

    def test_refuses_without_merged_pr(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")
        r = self.run_script("prit-05-cleanup.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no merged PR", r.stderr)
        self.assertIn("feature/x", self.git("branch").stdout)

    def test_deletes_after_squash_merge(self):
        self.merged()
        r = self.run_script("prit-05-cleanup.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("feature/x", self.git("branch").stdout)
        heads = sh(["git", "ls-remote", "--heads", str(self.remote)], self.tmp, self.env).stdout
        self.assertNotIn("feature/x", heads)
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD").stdout.strip(), "main")

    def test_linked_worktree_not_removed_without_flag(self):
        self.git("checkout", "main")
        wt = self.tmp / "wt"
        self.git("worktree", "add", "-b", "feature/y", str(wt))
        (wt / "y.txt").write_text("y\n")
        sh(["git", "add", "."], wt, self.env)
        sh(["git", "commit", "-m", "y"], wt, self.env)
        self.run_script("prit-02-push.sh", cwd=wt)
        (self.fake / "merged_feature__y").write_text("8\n")
        r = self.run_script("prit-05-cleanup.sh", cwd=wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LINKED WORK TREE", r.stdout)
        self.assertTrue(wt.exists())
        r2 = self.run_script("prit-05-cleanup.sh", "--remove-worktree", cwd=wt)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertFalse(wt.exists())
        self.assertNotIn("feature/y", self.git("branch").stdout)

    def test_also_refuses_unmerged_branch(self):
        self.merged()
        self.git("branch", "other", "main")
        r = self.run_script("prit-05-cleanup.sh", "--also", "other")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no merged PR", r.stderr)
        self.assertIn("other", self.git("branch").stdout)


if __name__ == "__main__":
    unittest.main()
