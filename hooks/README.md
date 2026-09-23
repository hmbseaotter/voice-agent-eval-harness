# Pre-commit guards — installation

`hooks/pre-commit` carries two fail-closed guards:

| Guard | Blocks | Threshold |
|---|---|---|
| Secret | a staged file named exactly `.env` | staged blob over 20 bytes |
| Private | a staged path under a **top-level** `private/` | any |

Both also block when they cannot determine the answer: an unreadable staged blob counts as
oversized, and a failed staged-path enumeration blocks rather than allows.

## Why this is not automatic

**A committed hook does not install itself, and on many machines it could not.** Git looks for hooks
in `.git/hooks/` — which is not part of the repository and is not populated by `git clone`. Worse,
if `core.hooksPath` is set machine-wide, `.git/hooks/pre-commit` **never fires at all**, so even
copying the file into place silently does nothing.

That makes these machine-level controls, not repository-level ones. Cloning this repository gets you
the `.gitignore` rules and **none of the enforcement** until you run one of the two steps below.
Stating this is not pedantry: a guard you believe you have is worse than one you know you lack.

## Install

First, find out which case you are in:

```bash
git config --global core.hooksPath
```

### Case 1 — the command printed nothing

No global hooks path is set, so a repo-local hook will fire. From the repository root:

```bash
ln -sf ../../hooks/pre-commit .git/hooks/pre-commit
```

On Windows without symlink permission, copy instead of linking — and re-copy after any change to
the source file:

```bash
cp hooks/pre-commit .git/hooks/pre-commit
```

### Case 2 — the command printed a path

That directory's `pre-commit` is the only one git will run, for **every** repository on the machine.
Append these guards to it rather than replacing it, so whatever else it does survives:

```bash
cat hooks/pre-commit >> "$(git config --global core.hooksPath)/pre-commit"
```

Then open that file and delete the second `#!/bin/sh` line — a shebang is only meaningful on line 1,
and leaving a stray one mid-file is confusing to the next reader. If your existing hook ends by
calling `exit 0` unconditionally, move that call to the bottom, or the appended guards never run.

Applying to every repository is the intended outcome, not a side effect: `private/` is a generally
useful convention, and a credential is worth blocking everywhere.

## Verify — do not skip this

An unverified guard is worse than none, because it is relied upon. **Which recipe verifies your
install depends on which case you followed**, and the earlier version of this section gave only the
Case 2 recipe to both audiences — so a Case 1 reader ran it, watched the commit succeed, and had no
way to tell whether that meant the hook was broken or the test was wrong. In a file whose whole
argument is that an unverified guard is worse than none, a verification that misleads half its
readers is the same defect one level up.

### Case 2 — a global `core.hooksPath`

The hook fires in every repository, so a scratch one is a fair test:

```bash
cd "$(mktemp -d)" && git init -q . && printf 'API_KEY=sk-not-a-real-key-0123456789\n' > .env && git add -f .env && git commit -m 'should be refused'
```

Expect a non-zero exit and `SECRET-GUARD-BLOCKED` on stderr.

```bash
mkdir -p private && echo 'draft' > private/notes.md && git add -f private/notes.md && git commit -m 'should be refused'
```

Expect a non-zero exit and `PRIVATE-GUARD-BLOCKED` on stderr.

### Case 1 — a repo-local hook

The hook lives in **this** repository's `.git/hooks/`, and git looks for hooks in the repository being
committed to. A scratch repo has none, so the recipe above **succeeds** there and proves nothing.
Verify inside the repository you installed into, on a throwaway branch:

```bash
git switch -c verify-hooks && printf 'API_KEY=sk-not-a-real-key-0123456789\n' > .env && git add -f .env && git commit -m 'should be refused'
```

Expect a non-zero exit and `SECRET-GUARD-BLOCKED`. Then clean up:

```bash
git restore --staged .env && rm -f .env && git switch - && git branch -D verify-hooks
```

### Either way, it is also checked for you

`tests/test_hooks.py` copies this repository's `hooks/pre-commit` into a throwaway repository and
drives it there, so both guards and both fail-closed paths are exercised on every test run
regardless of how — or whether — you installed it. That is the check that does not depend on a
reader remembering to run one.

## Bypass

```bash
git commit --no-verify
```

Deliberate, and visible in your shell history. That is the point: the guards make the unsafe commit
a decision rather than an accident.
