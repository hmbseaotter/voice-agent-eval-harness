"""Drive `hooks/pre-commit` against throwaway repositories.

WHY THIS EXISTS
---------------
The build prompt's rule: *an unverified guard is worse than none, because it is
relied upon.* Both guards are machine-level controls that this repository ships
but cannot install for itself (D14, D29), so the only thing standing between a
reader and a guard they merely believe in is a test that actually runs it.

Eight cases, and the six that are not the headline refusals matter most --
three of them ALLOW cases:

  * the three ALLOW cases pin the scoping, so a later "safer" widening of either
    pattern fails here rather than silently training people to --no-verify;
  * the fresh-repo case pins that failing closed on a bad enumeration does not
    block a repository's FIRST commit, which is the obvious way to get that
    fix wrong;
  * the two fail-closed cases prove the guards block when they cannot decide,
    which is the property the specification actually requires and the one no
    amount of reading the shell can confirm.

BOTH FAIL-CLOSED CASES ARE DRIVEN BY A `git` SHIM, ON PURPOSE.
The obvious way to make the staged-path enumeration fail is to run the hook in
a directory that is not a repository. That does not work, and the way it fails
is quietly instructive: git walks UP from the working directory, so a scratch
directory is "outside a repository" only if no ancestor is one. On the machine
this was written on, the system temp tree sits inside the user's home
directory, which is itself a git repository -- so the first version of this
test handed git a directory it happily resolved, `git diff --cached`
succeeded, and the assertion under test was never reached. It was a test of
the wrong condition that looked exactly like a test of the right one.

A shim that fails one subcommand tests the branch directly and depends on
nothing about where the test happens to run.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK: Path = Path(__file__).resolve().parents[1] / "hooks" / "pre-commit"

#: A populated key line, shaped like the real thing it exists to stop.
#: Comfortably over the 20-byte threshold.
POPULATED_ENV: str = "API_KEY=sk-not-a-real-key-01234567\n"

#: Under the threshold, which is how a committed template behaves.
TEMPLATE_ENV: str = "API_KEY=\nPORT=\n"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A scratch repository with no commits and no hook installed."""
    _git(tmp_path, "init", "-q", ".")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    # Without this, git renormalizes CRLF to LF when staging on Windows and the
    # staged blob is a different size from the bytes written -- which would make
    # the size assertion below platform-dependent for no reason.
    _git(tmp_path, "config", "core.autocrlf", "false")
    return tmp_path


def _stage(repo: Path, relative: str, content: str) -> None:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    # newline="" suppresses Python's own translation, for the same reason as
    # core.autocrlf above: what is written is what is measured.
    target.write_text(content, encoding="utf-8", newline="")
    # -f, because the guards are the backstop for exactly the case where
    # .gitignore was bypassed. Testing them only on un-ignored paths would
    # test the easy half.
    _git(repo, "add", "-f", relative)


def _shim_failing(directory: Path, subcommand: str) -> Path:
    """A `git` that fails one subcommand and passes everything else through."""
    real_git = shutil.which("git")
    assert real_git is not None, "git must be on PATH to run these tests"
    directory.mkdir(parents=True, exist_ok=True)
    shim = directory / "git"
    shim.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "' + subcommand + '" ]; then exit 1; fi\n'
        'exec "' + Path(real_git).as_posix() + '" "$@"\n',
        encoding="utf-8",
        newline="",
    )
    shim.chmod(0o755)
    return directory


def _run_hook(repo: Path, extra_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    env: dict[str, str] | None = None
    if extra_path is not None:
        env = dict(os.environ)
        env["PATH"] = str(extra_path) + os.pathsep + env["PATH"]
    return subprocess.run(["sh", str(HOOK)], cwd=repo, capture_output=True, text=True, env=env)


# --------------------------------------------------------------------------
# The two headline refusals
# --------------------------------------------------------------------------


def test_populated_env_is_refused(repo: Path) -> None:
    _stage(repo, ".env", POPULATED_ENV)
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "SECRET-GUARD-BLOCKED" in result.stderr
    assert ".env" in result.stderr
    measured = str(len(POPULATED_ENV.encode("utf-8")))
    assert measured in result.stderr, "the refusal should name the size it measured"


def test_private_path_is_refused(repo: Path) -> None:
    _stage(repo, "private/notes.md", "publication undecided\n")
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "PRIVATE-GUARD-BLOCKED" in result.stderr
    assert "private/notes.md" in result.stderr, "the refusal should name the path"


# --------------------------------------------------------------------------
# The scoping, pinned so a later widening fails here rather than in the wild
# --------------------------------------------------------------------------


def test_template_env_under_the_threshold_is_allowed(repo: Path) -> None:
    _stage(repo, ".env", TEMPLATE_ENV)
    assert _run_hook(repo).returncode == 0


def test_env_example_is_allowed_at_any_size(repo: Path) -> None:
    _stage(repo, ".env.example", POPULATED_ENV * 20)
    assert _run_hook(repo).returncode == 0


def test_nested_private_is_allowed(repo: Path) -> None:
    """`src/private/` is an ordinary source directory, and blocking it would
    train people to --no-verify -- which disables the secret guard too."""
    _stage(repo, "src/private/helpers.py", "VALUE = 1\n")
    assert _run_hook(repo).returncode == 0


def test_a_repositorys_first_commit_is_not_blocked(repo: Path) -> None:
    """Failing closed on a bad enumeration must not fire when HEAD is absent.

    `git diff --cached` compares the index against the empty tree when there is
    no HEAD and exits 0. If that ever changes, every repository's first commit
    starts failing, and this is where it surfaces.
    """
    _stage(repo, "README.md", "# scratch\n")
    assert _run_hook(repo).returncode == 0


# --------------------------------------------------------------------------
# Fail-closed: the guards block when they cannot decide
# --------------------------------------------------------------------------


def test_indeterminate_blob_size_fails_closed(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """An unreadable staged blob is treated as oversized, not waved through.

    The shim fails only `cat-file`, so the enumeration still succeeds and the
    size lookup is the single thing that breaks.
    """
    shim = _shim_failing(tmp_path_factory.mktemp("shim-catfile"), "cat-file")
    _stage(repo, ".env", POPULATED_ENV)
    result = _run_hook(repo, extra_path=shim)
    assert result.returncode != 0
    assert "SECRET-GUARD-BLOCKED" in result.stderr
    assert "999999" in result.stderr, "an indeterminate size is treated as oversized"


def test_failed_enumeration_fails_closed(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """With no list of staged paths, neither guard can say the commit is safe,
    so the hook blocks rather than reading the empty result as 'nothing staged'.

    That misreading is the fail-open hole this guard was written to close.
    """
    shim = _shim_failing(tmp_path_factory.mktemp("shim-diff"), "diff")
    _stage(repo, "private/notes.md", "publication undecided\n")
    result = _run_hook(repo, extra_path=shim)
    assert result.returncode != 0
    assert "STAGED-ENUMERATION-FAILED" in result.stderr


# --------------------------------------------------------------------------
# The threshold itself
# --------------------------------------------------------------------------


def test_the_twenty_byte_threshold_is_exercised_at_its_boundary(repo: Path) -> None:
    """The two `.env` fixtures are 34 bytes and 15. **The threshold itself was
    never exercised.**

    A guard tested only well inside and well outside its boundary is a guard
    whose boundary is untested, and an off-by-one there is the difference
    between refusing a template and admitting a key. 20 bytes must pass and 21
    must not -- the hook's rule is *over* 20.
    """
    at_threshold = "A" * 19 + "\n"
    assert len(at_threshold.encode("utf-8")) == 20
    _stage(repo, ".env", at_threshold)
    assert _run_hook(repo).returncode == 0, "a 20-byte .env is at the threshold, not over it"


def test_one_byte_over_the_threshold_is_refused(repo: Path) -> None:
    over = "A" * 20 + "\n"
    assert len(over.encode("utf-8")) == 21
    _stage(repo, ".env", over)
    result = _run_hook(repo)
    assert result.returncode != 0, "a 21-byte .env is over the threshold"
    assert "SECRET-GUARD-BLOCKED" in result.stderr
    assert "21" in result.stderr, "the refusal should name the size it measured"


def test_a_nested_env_is_still_refused(repo: Path) -> None:
    r"""The pattern is `(^|/)\.env$`, so `config/.env` is blocked while
    `src/private/` is not. That asymmetry is deliberate -- a `.env` is a secret
    wherever it sits, and `private/` is a name an ordinary source directory can
    share -- and nothing pinned it."""
    _stage(repo, "config/.env", POPULATED_ENV)
    result = _run_hook(repo)
    assert result.returncode != 0
    assert "SECRET-GUARD-BLOCKED" in result.stderr


def test_a_commit_with_nothing_staged_is_allowed(repo: Path) -> None:
    """An empty staged set must not be mistaken for an unreadable one. The
    fail-closed paths block on an *indeterminate* enumeration; blocking on an
    empty one would refuse every `--amend` and get the hook removed."""
    assert _run_hook(repo).returncode == 0


def test_staging_both_a_secret_and_a_private_path_refuses(repo: Path) -> None:
    """The secret guard exits first, so the private refusal never prints. Worth
    pinning: a reader who fixes the `.env` and re-commits must then meet the
    second refusal rather than a silent pass."""
    _stage(repo, ".env", POPULATED_ENV)
    _stage(repo, "private/notes.md", "draft\n")
    first = _run_hook(repo)
    assert first.returncode != 0
    assert "SECRET-GUARD-BLOCKED" in first.stderr
