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

# A fake gh that understands only "gh api" (the scripts use REST only). It ignores the jq text
# except to choose which value to print. State lives in files under $FAKE_GH_DIR:
#   open_<branch> and merged_<branch> hold a PR number (slashes in names become __);
#   state_<n> holds OPEN or MERGED; runs and status hold the CI words (default: none);
#   mstate holds mergeable_state (default: clean); fail_create makes the create call fail.
FAKE_GH = textwrap.dedent(
    r"""
    #!/usr/bin/env bash
    d="$FAKE_GH_DIR"
    echo "$*" >>"$d/calls.log"
    [ "$1" = "api" ] || { echo "fake gh: only api is supported: $*" >&2; exit 9; }
    path=$2; shift 2
    method=GET; jq=""; head=""
    while [ $# -gt 0 ]; do
      case "$1" in
        -X) method=$2; shift ;;
        --jq) jq=$2; shift ;;
        -f) case "$2" in head=*) head=${2#head=} ;; esac; shift ;;
        -F) shift ;;
      esac
      shift
    done
    br() { local x=${1#*head=*:}; x=${x%%&*}; echo "${x//\//__}"; }
    case "$method $path" in
      "GET repos/{owner}/{repo}") echo main ;;
      "GET repos/{owner}/{repo}/pulls?head="*)
        b=$(br "$path")
        case "$path" in *state=open*) k=open ;; *) k=merged ;; esac
        [ -f "$d/${k}_$b" ] && cat "$d/${k}_$b" || true ;;
      "POST repos/{owner}/{repo}/pulls")
        [ -f "$d/fail_create" ] && { echo "boom" >&2; exit 1; }
        echo 7 >"$d/open_${head//\//__}"; echo OPEN >"$d/state_7"
        echo "https://example.invalid/pr/7" ;;
      "GET repos/{owner}/{repo}/commits/"*"/check-runs"*) cat "$d/runs" 2>/dev/null || echo none ;;
      "GET repos/{owner}/{repo}/commits/"*"/status") cat "$d/status" 2>/dev/null || echo none ;;
      "GET repos/{owner}/{repo}/pulls/"*)
        n=${path##*/}
        case "$jq" in
          *html_url*) echo "https://example.invalid/pr/$n" ;;
          *head.sha*) cat "$d/head_sha" ;;
          *mergeable_state*) cat "$d/mstate" 2>/dev/null || echo clean ;;
          *merged*) [ "$(cat "$d/state_$n")" = MERGED ] && echo true || echo false ;;
        esac ;;
      "PUT repos/{owner}/{repo}/pulls/"*"/merge")
        n=${path%/merge}; n=${n##*/}
        [ -f "$d/merge_fail_nomerge" ] && { echo "Server Error (HTTP 502)" >&2; exit 1; }
        if [ -f "$d/merge_fail_late" ]; then
          for f in "$d"/open_*; do
            [ "$(cat "$f")" = "$n" ] && { b=${f##*/open_}; mv "$f" "$d/merged_$b"; }
          done
          echo MERGED >"$d/state_$n"; echo "Server Error (HTTP 502)" >&2; exit 1
        fi
        for f in "$d"/open_*; do
          [ "$(cat "$f")" = "$n" ] && { b=${f##*/open_}; mv "$f" "$d/merged_$b"; }
        done
        echo MERGED >"$d/state_$n"; echo "Pull Request successfully merged" ;;
      *) echo "fake gh: unsupported: $method $path" >&2; exit 9 ;;
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
            PRIT_CHECK_WAIT="0",
            PRIT_MERGE_WAIT="0",
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
        self.assertNotIn("-X POST", self.calls())

    def test_requires_push_first(self):
        self.commit_file()
        r = self.run_script("prit-03-open-pr.sh", "t", self.body("ok"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("prit-02-push.sh", r.stderr)

    def test_creates_then_reuses(self):
        self.pushed()
        r = self.run_script("prit-03-open-pr.sh", "My title", self.body("ok"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("api repos/{owner}/{repo}/pulls -X POST -f title=My title -f head=feature/x -f base=main", self.calls())
        r2 = self.run_script("prit-03-open-pr.sh", "My title", self.body("ok"))
        self.assertIn("already open", r2.stdout)
        self.assertEqual(self.calls().count("-X POST"), 1)


class Merge(PritBase):
    def open_pr(self):
        self.commit_file()
        self.run_script("prit-02-push.sh")
        (self.fake / "open_feature__x").write_text("7\n")
        (self.fake / "state_7").write_text("OPEN\n")
        (self.fake / "head_sha").write_text(self.git("rev-parse", "HEAD").stdout)

    def test_no_pr(self):
        self.commit_file()
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no open PR", r.stderr)

    def test_failing_checks_block_merge(self):
        self.open_pr()
        (self.fake / "runs").write_text("fail")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("-X PUT", self.calls())

    def test_pending_checks_block_merge(self):
        self.open_pr()
        (self.fake / "runs").write_text("pending")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("pending", r.stderr)

    def test_conflicts_block_merge(self):
        self.open_pr()
        (self.fake / "mstate").write_text("dirty")
        self.assertEqual(self.run_script("prit-04-merge.sh").returncode, 1)
        self.assertNotIn("-X PUT", self.calls())

    def test_failing_commit_status_blocks_merge(self):
        self.open_pr()
        (self.fake / "status").write_text("failure")
        self.assertEqual(self.run_script("prit-04-merge.sh").returncode, 1)
        self.assertNotIn("-X PUT", self.calls())

    def test_stale_pr_head_blocks_merge(self):
        self.open_pr()
        (self.fake / "head_sha").write_text("0" * 40 + "\n")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("differs", r.stderr)

    def test_error_reply_but_merge_finished_is_success(self):
        self.open_pr()
        (self.fake / "merge_fail_late").write_text("")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("MERGED", r.stdout)

    def test_error_reply_and_no_merge_fails(self):
        self.open_pr()
        (self.fake / "merge_fail_nomerge").write_text("")
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not merged", r.stderr)

    def test_uses_rest_only(self):
        self.open_pr()
        self.run_script("prit-04-merge.sh")
        self.assertNotIn("gh pr", self.calls())
        self.assertNotIn("graphql", self.calls())

    def test_squash_merge_without_admin_or_delete(self):
        self.open_pr()
        r = self.run_script("prit-04-merge.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pulls/7/merge -X PUT -f merge_method=squash", self.calls())
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


class Install(PritBase):
    def target(self):
        t = self.tmp / "target"
        sh(["git", "init", "-q", str(t)], self.tmp, self.env)
        return t

    def test_installs_and_is_idempotent(self):
        t = self.target()
        r = self.run_script("prit-install-into.sh", str(t))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((t / ".agents/skills/prit/SKILL.md").is_file())
        self.assertTrue((t / "scripts/prit-05-cleanup.sh").is_file())
        self.assertTrue((t / ".claude/skills/prit/SKILL.md").is_file())
        self.assertTrue((t / "plans/archive/.gitkeep").is_file())
        self.assertEqual(self.run_script("prit-install-into.sh", str(t)).returncode, 0)

    def test_refuses_to_overwrite_a_different_file(self):
        t = self.target()
        (t / "scripts").mkdir()
        (t / "scripts/prit-lib.sh").write_text("different\n")
        r = self.run_script("prit-install-into.sh", str(t))
        self.assertEqual(r.returncode, 1)
        self.assertIn("CONFLICT", r.stderr)
        self.assertFalse((t / ".agents").exists())

    def test_claude_copy_is_real_file_not_link(self):
        t = self.target()
        self.run_script("prit-install-into.sh", str(t))
        p = t / ".claude/skills/prit/SKILL.md"
        self.assertFalse(p.is_symlink())
        self.assertFalse((t / ".claude/skills").is_symlink())


class SkillCopies(unittest.TestCase):
    def test_agents_and_claude_copies_are_identical_real_files(self):
        root = SCRIPTS.parent
        a = root / ".agents/skills/prit/SKILL.md"
        c = root / ".claude/skills/prit/SKILL.md"
        self.assertTrue(a.is_file() and not a.is_symlink())
        self.assertTrue(c.is_file() and not c.is_symlink())
        self.assertEqual(a.read_bytes(), c.read_bytes(), "copy .agents/skills/prit/SKILL.md to .claude/skills/prit/SKILL.md")


if __name__ == "__main__":
    unittest.main()
