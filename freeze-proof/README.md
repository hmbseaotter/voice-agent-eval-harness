# The freeze proof

Four git objects and the frozen `src` tree, published so that a claim made in another repository can
be checked by recomputation rather than believed.

## What it is for

`voice-agent-eval-harness-holdout` holds labels that were authored **after** this project's rubric
was frozen, and that ordering is the whole of its central claim: the rubric cannot have been designed
against labels that did not exist. It secures that ordering the only way an ordering can be secured
without a trusted clock — its seal commit **cites the freeze commit by full SHA**, in
`labels/MANIFEST`:

```
# rubric-frozen-v1: 6d3a7101aaa1f15b440de43fe5142434f69c9dc9
```

That is a commitment. You cannot cite the hash of a commit that does not yet exist, so a citation
committed there on 2026-09-17 proves the thing it names already existed. **No date is used**: author and
committer dates in a git object are self-asserted and forgeable, a hash is not.

**Both ends of this chain are public.** The held-out repository was published on 2026-09-22, so a
reader with no special access can follow it end to end: that repository's seal commit `e8dcc27`
carries the trailer `Rubric-Frozen: 6d3a7101aaa1f15b440de43fe5142434f69c9dc9`, its `labels/MANIFEST`
cites the same commit, and `freeze-proof/freeze-commit.txt` here hashes to it. Commitment and
opening are both readable and name one commit, so property (a) is settled by recomputation rather
than by trust — which it was not until that day, and this paragraph said so.

The opening of that commitment is the freeze commit itself — and this project is published as a
**snapshot** rather than as rewritten history (`SNAPSHOT.md`, D208), so the freeze commit is not
reachable in the public repository's log. That left the citation checkable in principle and
unresolvable in practice. **This directory is the opening.**

A git commit object references its tree and its parents **by hash, not by content**, so these objects
can be published alone. The commits behind the freeze stay private, and nothing here needs them.

## The four core objects

| object | file | git object id (SHA-1) | SHA-256 of the bytes | size |
|---|---|---|---|---|
| commit | `freeze-commit.txt` | `6d3a7101aaa1f15b440de43fe5142434f69c9dc9` | `2158f0a9b7855ee448c4f9e3e92daa3145ea9f50dbcf8216269236622249e415` | 1,363 B |
| tag | `freeze-tag.txt` | `ae987da81a6c51725ff3a4a32267913926e2c74a` | `9dfe40296a808d778c427109c2dbe98f3296bcb1919efb5f78d7d95e509a9c11` | 180 B |
| tree (root) | `freeze-tree.b64` | `11319cedc6fdf66dc9f53dac12453ffb876861e9` | `064ae41c64cf1c5ec09c7a20b52060d2291e2ece50765259c5669273870a2195` | 896 B |
| tree (`prompts`) | `freeze-prompts-tree.b64` | `825ef49b436807f8e28a65f55130f6e03fe80d50` | `8004fc1c83de6ad00b84ec885f1447c2bd317c1d9d1b7bd63513a2b2aa9a3f92` | 49 B |

The commit and the tag are **raw object bytes**, readable as they are: open them and read the freeze
commit's message and the tagger line. Tree objects carry NUL bytes and raw 20-byte ids, and this
repository tracks no binary file, so the two trees are **base64** of their object bytes, wrapped at
76 columns. The SHA-256 column is of the decoded object bytes, and it is there for the reason given
under *What cannot be forged*.

## The chain

Every link is a hash recomputation, and no link is a date:

```
holdout seal commit e8dcc27 (public, 2026-09-17) cites 6d3a710
  └─ 6d3a710  the freeze commit  → names tree 11319ce
       ├─ 11319ce  the root tree  → rubric.yaml = blob 31520e09762db6d753e6937776f1ac6d54271eca
       │                          → prompts     = tree 825ef49
       │                          → src         = tree b4415262dd4c4e6547fc64408a18cb8a96069597
       └─ 825ef49  the prompts tree → judge-dimension.v1.md = blob 5e8c3e4f83457f7b8915f3e093d8c385f7a24297
```

and both blobs are the files this repository carries at HEAD — `rubric.yaml` (90,037 B) and
`prompts/judge-dimension.v1.md`. That is the property the held-out labels rest on: they were scored
against **this** rubric text and **this** prompt template.

The annotated tag object reads, in full:

```
object 6d3a7101aaa1f15b440de43fe5142434f69c9dc9
type commit
tag rubric-frozen-v1
tagger Saso Gale <hmbseaotter@gmail.com> 1789340091 -0700

Freeze the rubric at the end of phase 4
```

## The frozen `src` tree, and why the bytes were not enough

The chain above settles *which* rubric and template were frozen. It does not settle **what the frozen
code computed over them** — and the held-out gate asserts the stronger thing. It derives the
prompt-template hash by running the frozen harness's own `load_template` in a separate interpreter
over the frozen `src`, and it refuses a hash that came from any harness but that one. It also reads
the template's path out of the frozen `cli.py` rather than hard-coding it.

So `objects/` publishes **the whole `src` subtree at the freeze** — not a subset, not an import
closure: every tree and every blob under `b4415262dd4c4e6547fc64408a18cb8a96069597`, which
reconstructs the frozen `src/` directory exactly. **34 files, 30 unique blobs** (five empty files
share one blob) **and 6 tree objects.**

Each file is named by its own object id, so a file name is a checksum:

- `objects/<id>` — a **blob**, raw bytes, exactly as the frozen file was committed.
- `objects/<id>.b64` — a **tree**, base64, for the same reason the two trees above are.

Named by id rather than by path deliberately. These are 2026-09-13 versions of files whose current
versions sit beside them in this repository; a directory of stale `.py` files would invite being read
as live code, reformatted by a tool, or imported by accident. The paths are not lost — they are in the
tree objects, which is where the proof keeps them.

**What the frozen code computes**, for the template the frozen CLI names:

```
prompts/judge-dimension.v1.md → ce6ec2e5c5aa650abdfb1d4d1b31ad1dda171cbb0f18dba8e410d9ab54cc91be
```

That is also the `prompt_template_hash` recorded in the committed reference run log, and this
repository's suite holds the two to agreement.

**Why not simply compute it with the current code?** The template's bytes are unchanged — the
`prompts` tree is byte-identical at the freeze and at HEAD — but the computation over them is not
pinned. If `load_template`'s hashing ever moves, today's code yields a hash the frozen code never
computed, and a gate comparing them would fail a run that was honest. It would also mean deleting the
guard that makes the gate's answer mean anything. (As of 2026-09-21 the two do agree, which is worth
knowing and is not a guarantee.)

## Check it yourself

Git names an object by `sha1("<type> <size>\0" + bytes)`. Nothing else is needed — no clone, no
network, no history.

The four core objects:

```bash
{ printf 'commit 1363\0'; cat freeze-commit.txt; } | sha1sum
{ printf 'tag 180\0';      cat freeze-tag.txt;    } | sha1sum
{ printf 'tree 896\0';     base64 -d freeze-tree.b64;         } | sha1sum
{ printf 'tree 49\0';      base64 -d freeze-prompts-tree.b64; } | sha1sum
```

Each must print the id in the table above. Then the blob, which is the same rule with `blob`:

```bash
{ printf 'blob 90037\0'; cat ../rubric.yaml; } | sha1sum
```

must print `31520e09762db6d753e6937776f1ac6d54271eca`, the id the root tree names — so the rubric in
this repository is the frozen one, byte for byte. (On a checkout that put CRLF on disk, normalize to
LF first; the objects were committed as LF.)

Any object under `objects/` verifies the same way, against its own file name. That directory holds
the frozen `src` subtree and nothing else — the rubric's blob is the recipe above:

```bash
id=$(ls objects | grep -v '\.b64$' | head -1)   # any blob under objects/
{ printf "blob $(wc -c < objects/$id)\0"; cat objects/$id; } | sha1sum
```

All of it at once — the chain, both blobs, the reconstruction of the frozen `src/` and the frozen
code's own run over it:

```bash
uv run python -m tools.verify_freeze_proof
```

That command is also run by this repository's suite, and driven red by the control gate, so a
corrupted byte here fails a build rather than waiting for a reader.

## What cannot be forged

Substituting a different freeze commit after the fact would need a SHA-1 **second preimage** — some
other commit object hashing to `6d3a710…`. That is not broken. SHA-1's **collision** resistance is
broken, but a collision must be prepared *before* the hash is committed, and the holdout committed
this one on 2026-09-17. The SHA-256 digests above close even that footnote: they are of the very
bytes published here, so a reader who distrusts SHA-1 entirely can still pin these files.

## Why this repository carries no tag

`rubric-frozen-v1` is the name of the annotated tag object above, which points at the freeze. A
snapshot cannot carry a ref reaching that commit — git requires connectivity for a pushed ref, so
such a ref would drag the private history with it — and reusing the name for a tag on the snapshot's
own first commit made the freeze appear to *postdate* the seal it must precede (D209). Since D211 the
snapshot carries no tag at all and re-points nothing: the freeze pin names the freeze here exactly as
it does in the working repository, and this directory is where the tag is named. Two tests that ask
git for the freeze skip here, because a snapshot's log does not contain it; what they check, this
proof carries.

## How these files were produced

From the private working repository, once:

```bash
git cat-file commit 6d3a7101aaa1f15b440de43fe5142434f69c9dc9 > freeze-proof/freeze-commit.txt
git cat-file tag    ae987da81a6c51725ff3a4a32267913926e2c74a > freeze-proof/freeze-tag.txt
git cat-file tree   11319cedc6fdf66dc9f53dac12453ffb876861e9 | base64 -w 76 > freeze-proof/freeze-tree.b64
git cat-file tree   825ef49b436807f8e28a65f55130f6e03fe80d50 | base64 -w 76 > freeze-proof/freeze-prompts-tree.b64
```

and every object of the frozen `src` subtree, each written under its own id, blobs raw and trees
base64.

Nothing in them is private: every top-level name in the frozen tree is already published here, the
frozen `rubric.yaml` is the published one, the commit message is about the phase-4 audit, and every
frozen blob was scanned for the directory path the snapshot exists to leave behind — with the scan
first proved able to match a known instance, since a scan that cannot match reads exactly like a clean
result.
