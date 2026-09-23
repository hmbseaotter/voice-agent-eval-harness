# Voice-agent evaluation harness — Decision Record

- **Project:** voice-agent evaluation harness (LLM-as-a-judge reference project)
- **Identity:** A public, worked example of an LLM-as-a-judge evaluation harness for agentic voice-support calls — authored corpus, QA findings, design documentation, and a three-tier harness.
- **Spec:** `specs/voice-agent-eval-harness.md`
- **Status:** see *Document status* at the end of this file for the current high-water mark, which is the one place it is maintained. This line read "D1–D30 recorded" while the document held fifty-odd, and it is the first thing a reader sees. The history below is what this line is actually for. D1–D30 recorded as of the pre-build audit: D1–D18 from the /specify session of 2026-08-28; D19–D20 settled immediately after, when the repositories were created; **D21–D22 from verification passes rather than review** — D21's own *Consequences* notes it was found that way, which is the provenance this line exists to carry; **D23–D29 after a pre-build independent audit of 0.2.1**; **D30 on closing that audit's largest open question** by a session that had no part in the specification, which read the three documents, ran the scanner, and checked every concrete API assertion against current documentation. All six of the source handover's "Decisions owed" are settled.
- **Legend:** ✅ decided · 🔶 open / revisit · ⏭️ deferred to a later phase

<!-- rules-required-from: D19 -->

> **Rules are required from D19 onward.** Every decision recorded from the build phase on ends with
> a `**Rule** — …` line naming what enforces it: a test, a scan, or explicitly *judgment, not
> checkable*. D1-D18 predate this and are exempt. The reason is this project's own thesis applied to
> its own record: a rule kept as prose is applied by whoever remembers it, and memory does not
> survive a session boundary.

> **Numbering is allocate-once.** Never renumber and never reuse a retired number — the spec, the
> build prompt and later entries cite these by number. Supersede rather than rewrite.

> **Provenance of D1–D18.** These were resolved in conversation before this file existed, and were
> written down in one pass at the end of that session rather than incrementally. That is a
> deviation from the template's rule 2, and it is recorded here rather than hidden: the risk it
> creates is precisely the one the rule guards against — a rejected alternative quietly lost because
> the winner looked inevitable in hindsight. Every entry below was reconstructed from the options
> actually put on the table at the time, but entries from the build onward should be appended the
> moment each fork resolves.

---

## D1 — Where the artifacts land

**Fork:** Which repository root holds `specs/` and the built project?

**Options considered**
- **(A) A new repo in a directory tree containing no third-party confidential material** — clean isolation.
- **(B) A new repo elsewhere on disk** — same isolation, different parent.
- **(C) Inside the directory tree holding third-party confidential material** — everything cross-referenced in one place.

**Decision ✅** — **(A)** a dedicated repository root, isolated from any tree holding third-party confidential material. Its local path is recorded in `private/clean-room-sources.md`, not here.

**Why** — (C) was the convenient option and the dangerous one. That tree holds third-party confidential material, a prior reference implementation contaminated with its identifiers, and the earlier findings derived from it. A public repository initialized anywhere inside it is one `git add -A` away from a confidentiality breach, and the pre-publish checklist cannot catch what a stray path glob picks up. Isolation is a structural control; "remember not to stage the parent" is not.

**Consequences / caveats** — Cross-referencing the handover now means an absolute path rather than a relative one. Acceptable: the handover is explicitly an input, not a repo artifact.

---

## D2 — Repository topology and the held-out corpus

**Fork:** The findings document is both the rubric's traceability anchor and the judge's gold set. Publishing it publishes the answer key, and validating the judge against the same labels the rubric was authored from is circular. How is the corpus split, and what is the repo's visibility?

**Options considered**
- **(A) Public, design/held-out split evidenced by commit order, private-first, companion repo for the held-out set, freeze tag, hash commitment.**
- **(B) Public, one corpus, no split** — simplest, but judge agreement is measured on the labels the rubric was built from.
- **(C) Public, plus a permanently unpublished held-out set** — strongest anti-contamination posture, but no reader can verify any claim about it.
- **(D) Private until finished, then publish in one drop** — loses the commit-order evidence.

**Decision ✅** — **(A)**, in full: main repo built private and flipped public after a history scan; held-out corpus and labels in a separate public companion repo; a `rubric-frozen-v1` tag marking the freeze; a hash manifest of the held-out labels pinning them before publication.

> **Superseded in part by D21.** This entry placed the hash manifest *at the freeze tag*, which is incoherent with labels authored after that tag — there would be nothing to hash. D21 moves the manifest to between labeling and the first held-out judged run, which secures both properties instead of trading one against the other. Read this entry with that correction applied.

**Why** — The load-bearing insight is that **"held out" is a claim about the design process, not about secrecy**. Once that is seen, nothing needs to stay private, and the split becomes verifiable rather than asserted. Two further points decided the details. First, the separate companion repo is not about hiding the labels from readers — it is about **context contamination during development**: anything in the working tree can be globbed, grepped or incidentally read by an agent session, and once read it cannot be unread. Physical absence is the only mechanism that does not depend on obedience. Second, there are two distinct integrity claims and they are securable to very different degrees: *the rubric was authored without seeing the labels* rests on authoring order and cannot be proven; *the labels were not adjusted after seeing judge output* **is** cryptographically securable by publishing a hash before the plaintext. The second is the more common and more damaging failure, and it is the one that can actually be foreclosed.

**Consequences / caveats** — Three repositories to keep straight (see D12). Commit timestamps are trivially forgeable (`GIT_COMMITTER_DATE`), so commit-order evidence must be presented as evidence, not proof — the freeze tag makes it one checkable reference point rather than a diffuse appeal to history. **The private→public flip publishes history retroactively**, so private-first is a checkpoint, not a shield: the flip gate must scan *history*, not the working tree. This caveat bites again at D11.

---

## D3 — Serving the learner and the engineer

**Fork:** Two primary users were wanted — a reader learning the method, and an engineer adapting the harness to their own system. Can one project serve both without becoming a jack of all trades? The proposal on the table was a baseline repo plus an add-on repo, on a free-tier/unlock analogy.

**Options considered**
- **(A) One repo, layered by package and docs routing, with the seam proven in-repo by a second adapter.**
- **(B) One repo, same layering, second adapter deferred to a later phase.**
- **(C) Two repos: core (learner) + extensions (engineer)** — the original proposal.
- **(D) One repo, learner only; adaptability out of scope.**

**Decision ✅** — **(A)**. `core/` holds contracts, registry and engine; `corpus/` holds the worked example as the first adapter; a second adapter proves the seam. README routes the two audiences; adapter documentation stays out of the learner's path.

**Why** — The free-tier analogy does not transfer, because there is no gate: both repos would be public, so a split buys only a smaller core. Against that it charges three costs, and the second is decisive. **Version skew** — the extension repo depends on core internals, and one maintainer pays that tax forever. **The seam goes unproven** — "architected for adaptability" is credible only if something else actually uses the extension points, so moving the second adapter out of core makes the claim unfalsifiable, which is precisely the failure this whole project is about. **Discovery** — a reader landing on core sees one hardcoded corpus and concludes it does not adapt. The instinct underneath (a learner should not wade through adapter machinery) is sound, but it is a layout-and-routing problem, not a repository problem, and routing solves it without the coupling tax.

**Consequences / caveats** — The repo is larger and the README must route two audiences deliberately. The door is not closed on a later split: if the harness matures into something genuinely reusable, publishing `core` as a package with the worked example as a separate consumer is the natural evolution — an earned, later split rather than a v1 topology.

---

## D4 — Corpus size and repetition count

> **Superseded in part by D68.** The corpus is sixteen design transcripts, not twelve (D68, then D73, then D119). The
> held-out five are unchanged and so is the reasoning below; what changed is that a sweep of
> catalogd error types found classes the twelve could not carry. This banner names the
> change rather than editing the entry, per the record's own rule.

**Fork:** How many transcripts, and how many repetitions?

**Options considered**
- **(A) 12 design + 5 held-out, N=5.**
- **(B) 8 design + 4 held-out, N=5** — matches the reference's scale; thinner reachability signal.
- **(C) 20 design + 8 held-out, N=10** — real statistical power; corpus authoring swamps the harness work.
- **(D) Start at 6 and grow** — fastest to something running; defers the decision rather than making it.

**Decision ✅** — **(A) 12 design + 5 held-out**, with N subsequently corrected to 10 (see D17).

**Why** — At the reference's observed ~6 findings per call, 12 design transcripts yield ~70 findings, comfortably above the ~50 the severity bootstrap needs and with room for the comparison budget the bootstrap spends. *(Said "the pairwise sort" when written; that tool's D2 has since replaced the sort with a Bradley-Terry fit. The count is similar and the argument is unaffected.)* Twelve also supports several structurally-identical pairs for the cross-call consistency checks and makes a cross-corpus reachability statement meaningful. (C) was rejected because corpus authoring and hand-labeling would become the dominant cost of the project and crowd out the harness — the artifact people actually come to see.

**Consequences / caveats** — Corpus authoring and labeling is the single largest work item and must be staged across phases. **A clarification that changes what N means:** the handover's "N runs per scenario" is written for replaying scenarios against a live agent; this project has no live agent, so N can only be judge repetitions over a fixed transcript. That measures *evaluator* variance only, and any resulting rate describes judge stability and corpus difficulty — never a production failure rate. The report must say so inline.

---

## D5 — Raw transcript format

**Fork:** Given the architecture already runs raw source → frozen parsed artifact, what does the *source* format look like?

**Options considered**
- **(A) Realistic wrapped text as adapter 1, JSONL as adapter 2.**
- **(B) Realistic wrapped text only, one adapter.**
- **(C) Line-oriented text, one turn per line, wrapping forbidden** — designs out a bug class.
- **(D) Structured JSONL only** — extraction becomes schema validation.

**Decision ✅** — **(A)**.

**Why** — (C) and (D) both remove the extraction tier's reason to exist. The project would be teaching a lesson it had arranged not to need, and it would delete the failure mode the handover cites as its strongest evidence for building a real parser — a wrapped turn hiding the single most severe claim in a call. (A) beat (B) because it satisfies D3's seam requirement with a second *format* rather than a second corpus: far cheaper to author, and a stronger demonstration that the core is format-agnostic.

**Consequences / caveats** — A tight written format specification becomes a phase-1 deliverable, and wrapped-turn reassembly becomes the invariant the extraction tests must actually assert against the source file (the reference's W19 failure). Two adapters must be proven to emit byte-identical event streams.

---

## D6 — Clean-room origination of the corpus

**Fork:** Should the prior third-party material be read to inform the new format and corpus design? It was available.

**Options considered**
- **(A) Do not read them; design independently.**
- **(B) Do not read them, but have the user describe what is worth carrying across.**
- **(C) Read one for format shape only.**
- **(D) Read all eight.**

**Decision ✅** — **(A)**. Exposure is limited to the eight filenames, seen while auditing the handover, which established only that the source domain was retail order management.

**Why** — The user's own phrasing at D2 — *"no accidental reading that AI cannot unsee"* — is the argument. Commissioning a separate companion repo to keep held-out labels out of context, then voluntarily ingesting the proprietary corpus, would be incoherent. The asymmetry decides it: reading buys marginal format detail available elsewhere, and costs something irreversible. Not reading makes the new corpus's independence a **structural property of the process** rather than a claim about restraint — a distinction that survives review, where restraint does not. Two supporting points: the handover already specifies every element the format must carry, so marginal value is low; and format similarity is itself a family resemblance, the one thing a substitution policy cannot scrub because it is structural rather than lexical.

**Consequences / caveats** — The format is designed from stated requirements rather than observed practice, so it may miss a convention that would have been obvious. Accepted deliberately. If format knowledge does need carrying across, route (B) keeps exposure at zero.

---

## D7 — Judge-side prompt injection

**Fork:** How far should mitigation go, given caller speech is attacker-controllable and the corpus will contain adversarial calls by design?

**Options considered**
- **(A) Tagged populations + delimited untrusted block + instruction hierarchy + a seeded injection test.**
- **(B) All of (A) plus a deterministic injection detector filing hits as findings.**
- **(C) Tagging, delimiting and hierarchy — no seeded test.**
- **(D) Delimiting and tagging only.**

**Decision ✅** — **(A)**.

**Why** — There is an economy here that decided the shape: the W1 fix (the citable universe must match what the prompt renders) and injection defense want the *same* mechanism — tagging the two populations distinguishably, `[T<n>]` for transcript lines and `[F<n>]` for established facts. One change buys both. The seeded test is what separates (A) from (C), and it is the prize: it converts a security claim into something the repo can run. (C) would repeat the reference's exact mistake in a new place — citation validation there produced zero confirmed true positives precisely because it was never tested against a deliberately fabricated citation. (B) was set aside because pattern-matching for injection inherits the precision problems the handover documents for any phrase list.

**Consequences / caveats** — At least one corpus transcript must carry an injection attempt in caller speech, plus an equivalent transcript with it removed, so the acceptance criterion can compare verdicts.

**Amended during adjudication.** The criterion is satisfiable only while the injection finding stays outside the automated tiers, and nothing said so. CALL-06 carries F-27, which records the injection attempt itself and has no counterpart in CALL-07. F-27 is `human`, so nothing automated is ever asked about it and the two calls remain comparable. Re-classify it to `judge` or `assert` and a **correct** judge reports one more finding on the injected call than on the control — failing the criterion by being right. The classification read like an ordinary judgment call and was carrying a specification criterion. Now bound by `tests/test_corpus_hygiene.py::test_the_injection_pair_is_comparable_to_a_judge`, which compares the two calls' automated findings and ignores `human` rows, since differing there is what F-27 is for.

---

## D8 — Key-free running, reproducibility proof, and live usability

**Fork:** Can the repo run without an API key, prove its reproducibility claim, *and* be genuinely usable live with a reader's own key — coherently rather than as three bolted-on features?

**Options considered**
- **(A) Replay as a first-class mode with a committed reference run log, failing loudly on cache miss.**
- **(B) All of (A) plus a byte-identical golden-report regression test in CI.**
- **(C) Replay for tests only, no committed log.**
- **(D) No replay; document cost and require a key.**

**Decision ✅** — **(B) plus live usability**, unified as one seam. Defaults settled separately: replay is the default mode, live requires an explicit `--mode live` flag, and replay refuses to run against a stale log with `--allow-stale-replay` as the deliberate override.

**Why** — These are not three features but **one seam with a swappable transport**, which is what makes them combine cleanly. Recording is unconditional rather than a third mode, so any live run produces a new replayable log: the mechanism that makes the repo *teachable* is the same one that makes it *usable*, and an engineer pointing it at their own corpus gets a committable reference log as a by-product. The snapshot then splits in a way that proves the thesis rather than merely testing the code — **Tier A byte-identical in both modes** (it makes no model calls, so this is an unconditional reproducibility assertion) and **the full report byte-identical in replay only** (under live it is a sample, by design). Without that separation, someone runs live, sees a snapshot failure, regenerates it to make CI green, and silently destroys the regression signal. Replay was made the default so that behavior never depends on whether a credential happens to be present in the environment, and so money is never spent by accident.

**Consequences / caveats** — A committed run log goes stale the moment a prompt template or rubric entry changes, and would then report a fossil that quietly disagrees with live behavior. The log therefore records the rubric version and a prompt-template hash, and replay compares them. Regenerating the reference log becomes a routine cost of prompt iteration, which is one reason the cheaper judge model matters (D16).

---

## D9 — Licensing

**Fork:** One license or two, and which?

**Options considered**
- **(A) Apache-2.0 for code + CC BY 4.0 for corpus and docs.**
- **(B) MIT for code + CC BY 4.0 for corpus and docs.**
- **(C) MIT for everything.**
- **(D) Apache-2.0 for everything.**

**Decision ✅** — **(A)**.

**Why** — Two components with genuinely different natures. Apache-2.0's express patent grant and NOTICE mechanism are what make a testing tool adoptable inside a company without a legal review — a real signal to the engineer audience, and the one substantive difference from MIT. CC BY 4.0 fits the transcripts and policy documents better than any software license: they are creative works, and attribution is the term that actually matters for the part representing the most original labor. Applying a software license to a folder of transcripts (C, D) is a mild category error that says nothing useful about attribution.

**Consequences / caveats** — Two `LICENSE` files, and the README must state plainly which covers which tree.

---

## D10 — AI-assistance disclosure

**Fork:** Whether and how to disclose AI assistance in a public project about evaluating AI output.

**Options considered**
- **(A) README section + per-artifact provenance, with human-authored labels stated as a validity precondition.**
- **(B) All of (A) plus a dedicated build-log document.**
- **(C) A single line in the README.**
- **(D) No disclosure.**

**Decision ✅** — **(B)**, with publication of the build log itself left undecided (see D11).

**Why** — The reframing that decided it: **this is not primarily an ethics question, it is a validity claim.** The judge is validated by agreement with human labels, so if the findings document were model-generated, "human agreement" would measure nothing and the headline validation claim would collapse. Precision about which artifacts are human-judged is therefore load-bearing methodology, not a courtesy footnote. That yields the clean split the project wants: **model-assisted for the artifact under test** (transcripts, policy documents), **human for the ground truth** (findings rows, severities, the assert/judge/human classification).

**Consequences / caveats** — Constrains the build: the findings document and severity ordering must be human work, which no model setting changes and which sets the pace of phase 1. Also makes silence untenable — (C) leaves the gold-set provenance question unanswered, and that question is the repo's most important result.

---

## D11 — Where the build log lives while publication is undecided

**Fork:** The build log must exist and be publishable later, but whether to publish it is not yet decided. Where does it live meanwhile?

**Options considered**
- **(A) In the main repo's working tree but gitignored until the decision.**
- **(B) Outside the repo entirely, alongside the handover.**
- **(C) A small private third repo for undecided material.**
- **(D) Commit it now and decide at flip time.**

**Decision ✅** — **(A)**, subsequently completed by D14.

**Why** — (D) makes the decision by default and in the wrong direction: **the private→public flip publishes history retroactively** (D2's caveat), so a log committed during the private phase is public whatever you later conclude, and deleting the file does not help. (A) keeps the file where it belongs and where it will actually be maintained, while never entering history. (B) is safe but puts the log far from the work it documents, which is how build logs stop being updated.

**Consequences / caveats** — Gitignored means unversioned and outside git's recovery path, which D14 addresses with an external backup. "Publication deferred" needed a mechanism rather than an intention, and D11 supplies only the location — the enforcement half is D14.

---

## D12 — The comparative-judgment severity tool is a separate project

**Fork:** The severity tool is needed for scoring the corpus. Does it live in the harness repo?

**Options considered**
- **(A) Its own project/repo, referenced from the harness README.**
- **(B) Inside the harness repo, extracted later.**

**Decision ✅** — **(A)**. Its *method* is in scope for this project and applied here; its *code* is not.

**Why** — It is a standalone product with three jobs (severity scoring, gold-set labeling, judge-versus-human agreement measurement) and its own audience. Embedding it would interrupt the harness's narrative, and (B)'s "extract it later" is the kind of task that never happens.

**Consequences / caveats** — Three repositories total (with D2's companion). Creates a hard cross-project dependency on the critical path, resolved at D13. The harness README must link it prominently enough to be findable, since the method it implements is part of this project's documented approach.

---

## D13 — Sequencing around the severity dependency

**Fork:** Severity scoring sits upstream of the rubric, but the tool that produces it is a separate project. How is the sequence ordered so the harness is not blocked?

**Options considered**
- **(A) Author findings without severities, proceed to the rubric, backfill before any coverage claim.**
- **(B) Build the severity-tool MVP first, score, then start the harness.**
- **(C) Hand-score the design set once; build the tool for the held-out set.**
- **(D) Build it inside the harness repo and extract later.**

**Decision ✅** — **(B)**.

**Why** — Chosen over (A) despite (A) removing the serial delay. (B) gives the cleanest dependency order and a findings document that is complete before anything consumes it; the MVP is genuinely small — present two findings, record which is worse, persist, emit a total order, then three band cuts. (C) was rejected because hand-sorting ~70 findings is exactly the fatiguing absolute-versus-relative task the tool exists to make reliable, and a tired sort corrupts the gold set that everything else is measured against.

**Consequences / caveats** — A serial delay before any harness code exists, which runs against the handover's rule about having something running early. Partly offset at phase composition by pulling the extraction tier forward into phase 1. The tool is used **twice** — the design set now, the held-out set after the rubric freeze — which is itself an argument for real tooling over a one-off spreadsheet. Assumption recorded in the spec: the MVP is days, not weeks; if wrong, it becomes the project's critical path.

---

## D14 — Enforcing deferred publication

**Fork:** D11 fixed the build log's location but not its enforcement. What makes "publication deferred" a mechanism rather than an intention?

**Options considered**
- **(A) `private/` convention + global pre-commit guard + external backup + flip-time history scan.**
- **(B) `private/` convention + `.git/info/exclude`, no hook.**
- **(C) Keep the build log entirely outside the repo.**
- **(D) Global guard on a named path, no directory convention.**

**Decision ✅** — **(A)**.

**Why** — Three gaps in the bare gitignore approach. First, **`.gitignore` leaks the existence** — it is a committed file, so a public one listing `docs/build-log.md` tells every reader a build log exists and was withheld; a generic `private/` entry names nothing. Second, **`.gitignore` is advisory** and `git add -f` walks straight through it — and the natural fix has a trap the handover already documents: `core.hooksPath` is set globally, so a repo-local `.git/hooks/pre-commit` **never fires**. Enforcement must therefore live in the global hook or not exist. Third, unversioned means outside git's recovery path, which the external backup addresses. (B) is protection by intention again, which is the thing the question was asking to replace.

**Consequences / caveats** — Modifies a *global* hook, so the guard applies to every repository on the machine — desirable, since a `private/` convention is generally useful, but it is a machine-wide change made for one project. The guard must fail closed, matching the `.env` guard's posture. D2's flip gate scans history for the same path as the backstop.

---

## D15 — v1 exclusions

**Fork:** Which designed-but-unbuilt items are excluded from the v1 target?

**Options considered** — four candidates were offered for exclusion: judge-model comparison, per-instance severity, the cross-corpus check family, and the **source handover's** D6 log inspector. (Qualified deliberately: this record's own D6 is *Clean-room origination of the corpus*, and an unqualified number is exactly the ambiguity the header's numbering rule exists to prevent.)

**Decision ✅** — **Only the cross-corpus check family is excluded.** Judge-model comparison, per-instance severity and the log inspector all stay in the target at later phase tags. The LLM-as-parser stage stays in-target at the highest phase tag, on the instruction that it "will come at the very end."

**Why** — The cross-corpus family (taxonomy 12, 16, 25) needs a genuinely different check shape, its own result contract and its own report section — it is new machinery rather than another rubric entry, which is what distinguishes it from the others. The log inspector was kept because its input (the run log) is already a committed requirement and the handover argues nearly every reference defect would have been caught by exactly those invariants; excluding it would mean the harness cannot check itself.

**Consequences / caveats** — A useful side-effect: the corpus is still *sized and paired* to support the cross-corpus checks, so adding them later requires no re-authoring. Per-instance severity being in-target creates a design obligation — it must decompose into the boolean properties severity derives from and compute the level in code, never hand a model a four-level scale.

---

## D16 — Judge model tier

**Fork:** Which model runs the judged work?

**Options considered**
- **(A) Sonnet 5 for the seven dimensions, Opus 5 for synthesis.** *(Seven at the time. D42 later narrowed the judged tier to six; the routing decision is unaffected and the number is left as it was recorded, because a decision record that is edited to agree with later decisions stops being a record.)*
- **(B) Opus 5 throughout.**
- **(C) Sonnet 5 throughout.**
- **(D) Haiku 4.5 for dimensions, Sonnet 5 for synthesis.**

**Decision ✅** — **(A)**.

**Why** — It demonstrates the model-routing discipline rather than asserting it: the per-dimension judges do bounded calibration work against supplied facts, while synthesis reasons across every other dimension's result and is the part a human reads first. It also keeps the committed reference run log cheap to regenerate after a prompt change — which D8's staleness guard will correctly force. (B) is hard to argue is wrong and easy to argue is unexamined, which is the specific criticism this repo exists to pre-empt. (D) was attractive as a way of making the smaller-model hypothesis the default, but Haiku 4.5's 200K context is a real constraint once transcript, facts and schema share a prompt.

**Consequences / caveats** — The shipped reference run log is recorded from these models, so changing the default later means regenerating that artifact. Sets up the judge-model comparison (phase 6) as a real measurement rather than a defaulted preference.

---

## D17 — Judge repetition count

**Fork:** Raised at the assumptions gate: is N=5 enough to show a verdict distribution?

**Options considered**
- **(A) N=5** — as originally specified.
- **(B) N=10.**

**Decision ✅** — **(B) N=10**, superseding the N=5 recorded in D4.

**Why** — Five samples resolve only to 20% steps, so a genuinely low-frequency verdict flip may never surface at all — leaving the "a judged verdict is a sample, not a proof" claim unevidenced, which is one of the repo's headline points. N=10 halves the resolution step and raises the chance of observing a 10%-frequency flip from roughly even to about two in three.

**Consequences / caveats** — Doubles the reference run (~$12–16). Mitigated by prompt caching in phase 6: repeated calls for one dimension are byte-identical prompts, so the marginal cost of raising N further is well below linear. If the distribution still looks flat at N=10, raise N rather than re-architect.

---

## D18 — Corpus domain

**Fork:** Which domain does the new corpus live in? It needs genuine refund/cancellation policy, voice-support plausibility, and enough surface for the taxonomy's defect classes — while being chosen on its own merits rather than inherited from prior art.

**Options considered**
- **(A) Event ticketing.**
- **(B) Travel booking** — richest policy surface, but most complex to author convincingly.
- **(C) Subscription / telecom billing** — strong for arithmetic and instrumentation defects.

**Decision ✅** — **(A) Event ticketing.**

**Why** — It carries real policy with real edge cases (refunds, exchanges, transfers, name changes, tiered seating, delivery methods, hard event deadlines) and is a natural home for eligibility preconditions, irreversible writes and time-window rules. It is also **structurally unlike the commoner order-management shape** — no shipping, no inventory, no goods in transit — which keeps scenarios from being transferable from adjacent prior art. Names, dates and venues also give the heard-value reconciliation dimension something real to reconcile. (B) was rejected because its genuine intricacy competes for the reader's attention with the evaluation method the repo is actually about; (C) because its irreversible-action surface is thinner and billing disputes are well-trodden ground.

**Consequences / caveats** — Assumption recorded in the spec: event ticketing supports every seeded defect class. Mitigation is a required phase-1 deliverable — map all 35 taxonomy items to concrete ticketing scenarios *before* authoring begins, and record any class with no natural instance as a stated coverage gap rather than forcing it.

---

## D19 — Name of the held-out companion repository

**Fork:** What is the held-out repository called?

**Options considered**
- **(A) `voice-agent-eval-harness-holdout`** — exact prefix match.
- **(B) `voice-agent-eval-holdout`** — shorter, drops "harness".
- **(C) `voice-agent-eval-harness-goldset`** — emphasizes ground truth.

**Decision ✅** — **(A) `hmbseaotter/voice-agent-eval-harness-holdout`.**

**Why** — The exact prefix makes the two repositories sort adjacently in any listing, so the pairing needs no explanation to anyone landing on either. "Holdout" is the term practitioners already read as *do not design against this*, which is the signal the name should carry. (C) was rejected as actively misleading: the design set's labels are gold too, so naming only this one "goldset" implies the other 12 calls are unlabeled, and it discards the one word that explains why the split exists.

**Consequences / caveats** — The name is a **signal, not a mechanism**. D2's actual protection is physical absence from the main working tree; the name and the README's opening line only stop a human from casually browsing. The README must lead with why reading it before the freeze defeats the purpose.

**Rule** — The main repository contains no held-out transcript: a path check over the working tree asserting zero matches, already recorded as a phase-1 acceptance criterion. Enforced by test.

---

## D20 — Name of the comparative-judgment severity tool

**Fork:** What is the severity tool called, and is it prefixed with the harness project's name?

**Options considered**
- **(A) `comparative-judgment`** — the method's term of art.
- **(B) `pairwise-severity`** — names the primary problem.
- **(C) `pairwise-labeler`** — names all three jobs generically.
- **(D) `severity-sort`** — names the core loop.

**Decision ✅** — **(A) `hmbseaotter/comparative-judgment`**, deliberately unprefixed.

**Why** — Unprefixed because D12 scoped it as a standalone product doing three jobs — severity scoring, gold-set labeling, and judge-versus-human agreement measurement — none of which are voice-specific; prefixing would tie a general tool to one use and undersell it. Among the unprefixed candidates, the three jobs unify as *obtaining reliable human labels via pairwise comparison*, so any severity-centric name (B, D) is too narrow and would read oddly the first time it is used for something else. (A) is the established term from Thurstone's law of comparative judgment, familiar in educational assessment where the method reliably beats absolute rubric grading on inter-rater reliability — it is findable by anyone who knows the method and signals that the tool implements a known technique rather than an ad-hoc script.

**Consequences / caveats** — The name is bare, so the repository description carries the whole "what it does" load and must be written deliberately rather than left to default. The harness README must link it prominently, since the method it implements is part of this project's documented approach and a reader who cannot find the tool cannot reproduce the severity scoring.

**Rule** — The harness README links `hmbseaotter/comparative-judgment`: a docs check asserting the URL is present, run in CI alongside the other link checks. Enforced by test.

---

## D21 — When the held-out hash manifest is committed

**Fork:** D2 placed the hash manifest *at* the `rubric-frozen-v1` tag while the spec had the held-out labels authored *after* that tag — so the manifest would hash labels that did not yet exist. Which is right?

**Options considered**
- **(A) Move the hash to between labeling and the first held-out judged run.**
- **(B) Author labels before the freeze and hash them at the tag** — matches D2 as written.
- **(C) Drop the manifest; rely on commit order alone.**

**Decision ✅** — **(A).** The order is: freeze the rubric and tag it → author held-out labels, their commit citing the main repository's freeze commit SHA → commit a hash manifest of those labels → run the judge on the held-out set → publish plaintext labels and the agreement result.

**Why** — The contradiction existed because D2 conflated **two properties that are in tension**, and securing them at one moment forces a trade. *(a) The rubric was not designed against these labels* is strongest when the labels did not exist until after the freeze. *(b) The labels were not tuned once judge output was visible* requires a commitment made before any held-out judged run. Placing the manifest at the freeze forces the labels to pre-exist and weakens (a); authoring them after the freeze with no manifest loses (b). Separating the two moments obtains both, at no cost beyond stating the sequence explicitly. The added SHA citation strengthens (a) specifically: a commit SHA is a content hash, so citing it demonstrates the label commit was made with knowledge of a particular prior state — stronger than two independent, forgeable timestamps across two repositories, and it costs one line in a commit message. (C) was rejected because it discards the only claim here that is checkable by recomputation rather than merely evidenced, and post-hoc label tuning is both the more common failure and the more damaging one.

**Consequences / caveats** — Phase 5's ordering *is* the mechanism, so producing the right artifacts in the wrong order does not satisfy the phase. Property (a) remains evidence rather than proof; only (b) is checkable. The fix touches six passages across the spec plus this record — the kind of one-decision-many-places spread that the sweep checklist exists to catch, and it was found by a routine verification pass rather than by review.

**Rule** — The manifest's commit time precedes the earliest held-out judged run in the run log, and the manifest recomputes to match the published labels: both asserted as phase-5 acceptance criteria. Enforced by test.

---

## D22 — Findings document format, and where severity lives

**Fork:** This spec required a findings document but named no format for it, while the comparative-judgment spec — which has to *read* that document — had fixed one. Separately, this spec said severity was "backfilled" into the findings document, while the tool producing severity is forbidden to mutate it. Two questions: what format, and who owns severity?

**Options considered**
- **(A) YAML findings; severity in a separate file keyed by `id`.**
- **(B) YAML findings; severity written back into the findings document** — one file, nothing to join.
- **(C) Markdown table as the source of truth** — renders on GitHub with no generation step.
- **(D) CSV or JSON.**

**Decision ✅** — **(A).** Findings are YAML with a stable `id`, `observation`, `evidence` *as a list*, `consequence`, `detectable_by` and `tier`. A Markdown view is generated for reading. Severity lives in a separate file the comparative-judgment tool emits, keyed by `id` and carrying its run id, anchor-set version and log hash; the harness joins on `id`.

**Why** — The deciding constraint is the evidence field. It holds verbatim multi-line quotes, and the row schema requires fragments from different points in a call to remain visibly separate — so (C) is disqualified outright, because a Markdown table cell cannot hold a newline or an unescaped pipe and would force flattening exactly the distinction the schema exists to preserve. CSV quoting is fragile at the same job; JSON is machine-clean but poor for a human authoring multi-paragraph prose with no comments. A YAML list of evidence fragments carries the structure natively, stays diffable, and matches this project's existing pattern of data-as-YAML with readable output generated from it.

Severity went to a separate file because (B) requires the tool to write into a document it does not own — which that tool's own design forbids, so (B) was never actually available. Keeping severity separate also makes its provenance explicit: which scoring run, which anchor set, which comparison log produced this value, rather than an unattributed column edit.

**Consequences / caveats** — Two specs previously disagreed on a shared interface, in committed history, with neither decision record mentioning it. The gap was found by checking the detail while amending, not by review — and the second half (the "backfilled" contradiction) would have been *introduced* by a careless fix that only addressed the format. Any consumer of severity must join on `id` rather than expecting a field; the coverage report reads both files.

**Rule** — Three acceptance criteria, enforced by test: every findings entry carries all six required keys; a findings document containing a severity field is rejected by name; and the generated Markdown view regenerates identically from the YAML. A fourth check belongs with them and is *judgment, not checkable* today — that the two specs' descriptions of this interface stay in agreement, which no linter spans across repositories.

---

## D23 — A refusal is its own status, not an error

**Fork:** A pre-build audit observed that `stop_reason: "refusal"` is unhandled. It arrives as **HTTP 200** with a populated `stop_details` (`type`, `category` — an open set — and `explanation`), so it is not a transport error and the backoff path never sees it. The response carries no valid structured output, so it falls through to schema validation, consumes the informed retry on input that will refuse again, and resolves to `errored`.

**Options considered**
- **(A) A fifth status value, `refused`.**
- **(B) Keep four statuses; record `stop_reason` and `stop_details.category` so the two are separable after the fact.**
- **(C) Treat a refusal on a seeded-injection transcript as a finding about the *corpus*.**
- **(D) Six values — `refused` and `truncated` both.**

**Decision ✅** — **(A)**, with (B)'s logging adopted unconditionally rather than as an alternative. `status: refused`, `stop_details.category` and `explanation` recorded, no retry consumed, run continues. `refused` counts are reported alongside the other three and excluded from every rate denominator.

**Why** — This matters more here than it would in most projects, because D7 *requires* the corpus to carry deliberate prompt-injection attempts in caller speech, plus an otherwise-equivalent transcript without them. That is precisely the class of input a safety classifier may decline, so a refusal is an expected event on this corpus rather than an exotic one.

The consequence of (B) alone is not a crash but a **mislabeled failure mode**, in a harness whose entire thesis is that evaluation must distinguish them. `errored` would mean both "the judge could not produce a valid result" and "the model declined to engage". D7's own acceptance criterion — the injected transcript produces the same verdict as the clean one — would then pass with two `errored` results reading as agreement, or fail with one refusal and one verdict reading as a mitigation failure. Neither is what happened, and the harness would be unable to say so.

(D) was rejected as surface for a case that a correctly-set `max_tokens` (D24) should make rare; truncation stays inside `errored`, separable by the stop reason now recorded on every judged call. (C) is a genuinely interesting reading and is **not** an alternative — it is a reporting question that composes with (A), and it becomes available *because* (A) makes refusals countable.

**Consequences / caveats** — Amends the Result contract from a four-value to a five-value status channel, which is why this is settled now rather than during phase 3: the contract freezes at P2. Every rate computation and the escalation block move with it. Not consuming the retry budget on a refusal is deliberate — retrying identical input against a classifier that just declined it spends money to reach the same place.

**Adjacent, decided at the same time:** server-side refusal fallbacks are **not** enabled. Silently re-running a declined request on a different model would corrupt the very measurement this harness exists to take. Recorded rather than left to omission, because the default behavior of a convenience feature is exactly the kind of thing that gets switched on without a decision.

**Rule** — Acceptance criteria, enforced by test: a judged response with `stop_reason: "refusal"` produces `status: refused`, records `stop_details.category`, consumes no retry, and is distinguishable from a retry-exhaustion `errored` by log inspection alone.

---

## D24 — `max_tokens` is rubric data, and its absence is a refusal

**Fork:** `model & cost routing` pins the model, the effort level, adaptive thinking, the structured-output format and the supported-model set — and never pins `max_tokens`. The run log is required to record "the generation configuration" without saying what that contains.

**Decision ✅** — `max_tokens` is declared per rubric entry alongside `effort`, an entry lacking it is refused by name before any call is issued, and `stop_reason` is recorded on every judged call unconditionally.

**Why** — Sharper than it first looks: `max_tokens` is a **required** Messages API parameter. A missing value is therefore not a defaulting question but an unissuable request, and refusing by name beats discovering it as a 400 at the transport seam.

Left unspecified, a value gets chosen at the call site — which contradicts the existing rule that every check parameter is read from the rubric entry with no such value hardcoded in Python, and it is the parameter most deserving of per-entry control: these prompts carry a full transcript, the tagged fact population and a declared JSON schema, and the synthesis dimension additionally carries every other dimension's result.

A judged call that hits the cap returns `stop_reason: "max_tokens"` with truncated output. For a structured-output judge, truncation means an unparseable response, which presents as a schema or citation failure, burns the informed retry on identical input, and resolves to `errored` — the same conflation as D23, by a different route. Recording the stop reason separates them without a sixth status value.

**Rule** — Acceptance criteria, enforced by test: a rubric entry with no `max_tokens` is refused by name before any call; a response truncated at the cap is recorded with its stop reason and is distinguishable from a validation failure by log inspection alone; every judged run-log entry carries a `stop_reason`, and the count missing one is zero.

---

## D25 — The call ceiling moves to the phase that can spend

**Fork:** `--mode live` arrives at **P3**. The ceiling bounding it arrived at **P6**. Between them, P4 multiplies call volume roughly sevenfold and P5 runs the held-out judged set.

**Options considered**
- **(A) Move the ceiling requirement, the `--max-calls` flag and the criterion to P3.**
- **(B) Leave at P6 and record the exposure as deliberate.**

**Decision ✅** — **(A)**, plus a declared default ceiling when the flag is absent.

**Why** — At P3 the only protections were an estimate and a confirmation prompt, and both bound the *expected* call count. Nothing bounded the actual one — while P3 is exactly where the three mechanisms most capable of issuing more calls than intended arrive: the transport seam, the retry-with-backoff loop and the informed-retry path.

The `control surface` block says the stop conditions are "each specified as a requirement below". That sentence was true and misleading at once: a reader checking coverage would find the ceiling specified and not notice it was specified three phases after the capability it bounds. Phase composition had produced an exposure nobody chose.

Cost is not the argument against moving it. A counter and a comparison is cheaper than the estimate-and-confirm logic already tagged P3.

**Consequences / caveats** — Also fixes a smaller gap found in the same place: `--max-calls` was named only in the `model & cost routing` prose, so the CLI surface for the ceiling was unspecified in every requirement and criterion. The default matters as much as the flag — a ceiling that applies only when someone remembers to ask for it is not a ceiling.

**Rule** — Acceptance criterion at the same phase as `--mode live`: a live run reaching its ceiling halts without issuing a further call, asserted by a transport spy counting calls; a run with no `--max-calls` applies the declared default rather than running uncapped.

---

## D26 — Property (b)'s ordering is evidenced by a cited SHA, not by two timestamps

**Fork:** The spec claims property (b) — *the labels were not tuned once judge output was visible* — is "checkable by recomputation". It has two halves. The manifest recomputing to the labels is genuinely checkable by anyone. The second half, that the manifest's commit precedes the earliest held-out judged run, was asserted by comparing a git commit time against the run log's own timestamps.

**Decision ✅** — The **run log's header records the manifest's commit SHA**. The timestamp comparison stays as corroboration rather than as the mechanism.

**Why** — This is the project's strongest integrity claim, and the one D21 chose to build a mechanism for rather than settle for evidence. D21's own argument against timestamps — *"a commit SHA is a content hash, so citing it demonstrates the label commit was made with knowledge of a particular prior state — stronger than two independent, forgeable timestamps across two repositories"* — applies unchanged to this half of property (b), and was not applied there. One of the two timestamps is a `GIT_COMMITTER_DATE`, which D2 itself calls trivially forgeable; the other is written by the harness under audit.

The gap was narrow and the claim survived it — a manifest that recomputes still forecloses *editing the labels*, which is the damaging failure. But "checkable by recomputation" overstated what a reader can verify, in a document whose whole posture is not overstating. The fix costs one field and uses the device the project had already chosen.

**Rule** — Acceptance criterion, enforced by test: every held-out run-log header names a manifest commit SHA that resolves in the companion repository, and that manifest recomputes to the published labels.

---

## D27 — N repetitions become a requirement, not a number in a decision

**Fork:** `N=10` had an entire decision devoted to it (D17), with arithmetic about resolution steps and flip-detection probability — and no `SHALL` anywhere requiring the harness to *perform* N repetitions, no requirement to report a distribution, and no acceptance criterion asserting either. It appeared in prior decisions and in assumptions, nowhere else.

**Decision ✅** — A requirement at **P3** to perform N repetitions with N read from the rubric entry and one run-log entry per repetition; a requirement at **P4** to report the verdict distribution rather than a single verdict. Criteria at both.

**Why** — Three things already rested on machinery the requirements never asked for: the reproducibility carve-out (*"Tier B under live is a sample by design and SHALL NOT be asserted byte-identical"*, meaningful only if something takes multiple samples); the headline claim that *a judged verdict is a sample, not a proof*, which D17 names as one of the repo's headline points; and the in-scope P4 item *"an inline non-determinism caveat"*, which describes reporting a distribution the spec never required computing.

A builder working from requirements alone — which is what a build prompt asks them to do — would have produced a harness that judges each dimension once, and every one of those three claims would have quietly become false.

The phase split follows the shape of the work: repetition is transport-loop machinery (P3), distribution is reporting (P4). N lives in the rubric rather than in code, under the same rule as every other check parameter.

**Rule** — Acceptance criteria, enforced by test: a judged dimension run at N>1 writes N run-log entries; the report shows a distribution rather than a single verdict.

---

## D28 — CI is in the target, because two Rules already assumed it

**Fork:** `GitHub Actions` appeared once, in the stack list. `CI` appeared once more, in `triggers & scheduling`. There was no requirement, no criterion, no phase item and no workflow file — while D20's README link check said *"run in CI alongside the other link checks"* and D8 chose replay mode specifically so that *"a byte-identical golden-report regression test in CI"* would be possible.

**Options considered**
- **(A) Specify it: a phase item and criteria.**
- **(B) Declare CI out of the v1 target**, so the two Rules stop depending on it.

**Decision ✅** — **(A)**, at P2, running the type check, both linters, the test suite and `tools/check_spec_interface.py`; the golden-report regression joins it at P4.

**Why** — (B) is coherent but throws away the reason D8 exists. Its whole option-(B) argument was that replay makes a regression signal *possible*; without CI that signal is only ever observed when a human runs the suite, which is the condition every other guard in this project is written to stop relying on. The sister project reached the same conclusion from the other direction: its gates all passed every time they were run, which is a fact about those days rather than a property of the repository.

Including the interface scanner in the workflow is the point rather than a detail. It is the one check that can catch drift in a repository other than the one being committed to, and the build is when both repositories get edited most.

**Rule** — Acceptance criterion: the workflow runs the type check, both linters, the test suite and the interface scanner, and fails the build on any non-zero exit.

---

## D29 — The pre-commit guards ship installable, and are declared machine-level

**Fork:** Both guards are stated as system requirements (`IF [P1] … the pre-commit guard SHALL block the commit`) with phase-1 acceptance criteria. D14 correctly places them in the **global** hook, because a repo-local `.git/hooks/pre-commit` never fires once `core.hooksPath` is set machine-wide. What was never recorded is the publication consequence: this is a public reference project, and someone who clones it gets the `.gitignore` and no guards at all, while the specification presents both as properties of the system.

**Options considered**
- **(A) Ship the hook source under a documented path with a one-line setup step, and say in the spec that it is a machine-level control the repository provides but cannot install for you.**
- **(B) Scope the requirement explicitly to the authoring machine.**

**Decision ✅** — **(A).**

**Why** — D3 names two audiences, and the second is an engineer adapting this harness. Under (B) that reader is told plainly that the guards are not theirs, which is honest and cheap — but they are building the same thing with the same hazard, and the project has the hook already written. (A) costs a file and a README line and gives them the enforcement rather than the warning.

The generalization is the project's own: the build prompt says *"An unverified guard is worse than none, because it is relied upon."* A guard a reader **believes** they have, and does not, is that same hazard one step removed — and it is worse in this instance, because the `private/` guard is what keeps a build log out of a history that gets published retroactively.

**Consequences / caveats** — Adds a phase-1 deliverable. The installation step cannot be automated by the repository, since setting `core.hooksPath` is a machine-wide change no clone should make on someone's behalf — which is itself the reason the guards work this way, so the documentation says it rather than apologizing for it.

**Rule** — Acceptance criterion, enforced by test: the hook source is present in the repository under a documented path, and a test following that documented installation in a scratch clone reproduces both refusals. Checking the file merely exists would assert the weaker half — the failure being guarded against is a hook that is present and never fires.

---

## D30 — The taxonomy is mapped, and its gaps are recorded rather than closed

**Fork:** The pre-build audit named one open question larger than any of its findings: whether all 35 taxonomy items and W1–W35 are addressed or consciously deferred had been verified by *nobody*. The auditor's tooling blocked the reference document; the /specify session had read it, but selectively rather than item by item. The specification referenced three taxonomy numbers and one W-number, and nothing recorded what the other sixty-six were.

**Options considered**
- **(A) Read the reference, map every item, record dispositions — closing the gaps that are cheap and leaving the rest as recorded gaps for phase 1.**
- **(B) Read it and close every gap now**, adding dimensions and checks until nothing is unaddressed.
- **(C) Defer to phase 1**, when the corpus is authored and the taxonomy is in hand for the work itself.
- **(D) Leave it unverified**, on the grounds that the /specify session had the document in view.

**Decision ✅** — **(A).** `specs/taxonomy-coverage.md`, self-contained, every item carrying one of: seeded, checked, deferred with a reason, a harness constraint, or an open gap naming what would close it.

**Why** — (D) is what the *Not checked* entry already refused, and correctly: "had it in view" and "checked it item by item" are different claims, and only one of them is checkable.

(C) is the tempting one and it loses on timing. Every gap is a **corpus-authoring** decision, and phase 1 is where the corpus is authored — so deferring means discovering, mid-authoring, that a category needs a scenario the 12 transcripts do not have. Twelve transcripts is a small enough set that coverage has to be planned into it rather than noticed afterwards. Worse, four of the gaps imply a *judged dimension the spec does not have*; finding that after the corpus exists means either a dimension with no backing transcript, or re-authoring.

(B) overreaches in the other direction. Deciding all twelve gaps now would pre-empt phase 1 with choices made without the corpus in front of anyone — and two of them (an eighth judged dimension; a check family comparing two fact sources) are real design forks that deserve their own entries when there is something concrete to decide against.

**Consequences / caveats** — The map is a maintained artifact, not a one-off audit. Its tally is the number to keep honest: twelve gaps today (they now sit under *seeded, check gap remains* rather than under *neither seeded nor consciously deferred*, which reads zero), and a phase-1 corpus closing none of them should say so deliberately. A new acceptance criterion asserts every item carries a disposition — a gap is a recorded decision, a blank is an oversight, and only one of those is acceptable at a phase boundary.

**Written to be read without the source.** A builder should not need the reference document to author a transcript, and the two lists are the only part of it phase 1 needs. That matters more than usual here: the next session may be a fresh one that knows only what is in this folder.

**What the map found.** Of 35 categories: 15 seeded and checked, 5 deferred, 1 a harness constraint, **12 gaps**. Of W1–W35: 17 addressed, 4 deferred or not applicable, 4 partial, and **W2–W10 plus W19 unaddressed entirely** — nine measured correctness defects in a prior deterministic tier, seven of them producing a false pass or false failure on an absolute gate, against a specification that described that tier only as "every parameter read from the rubric entry". That is the same shape this project keeps finding: a guarantee stated at the level of *configuration* while the *correctness* it depends on goes unstated.

**Rule** — Acceptance criteria, enforced by test: every taxonomy item and every known weakness in `specs/taxonomy-coverage.md` carries a disposition, and the count of items without one is zero; each deterministic failure mode named in its Part 3 has a test that fails when the defect is present.

---

## D31 — Where the authored corpus lives, relative to the package

**Fork:** The specification says `core/` holds contracts and engine and `corpus/` holds the worked example as the first adapter. Does the authored corpus *data* — transcripts, policy documents, findings — live inside the Python source tree alongside that adapter, or outside it?

**Options considered**
- **(A) Data at repository-root `corpus/`; the adapter stays at `src/harness/corpus/`.**
- **(B) Everything under `src/harness/corpus/`,** data and adapter together, matching the spec's sentence literally.
- **(C) Data under `tests/fixtures/`,** treating the corpus as test data.

**Decision ✅** — **(A)**.

**Why** — D9 licenses code Apache-2.0 and corpus and documentation CC BY 4.0. Under (B) the two licenses interleave inside one package directory, and the README's "which license covers which tree" statement (a P6 deliverable) becomes unstatable without enumerating files. A license boundary that cannot be drawn as a path is one no reader can check and no packaging tool can respect. (C) is worse on a second axis: the corpus is the *subject* of this project, not scaffolding for its tests, and filing it under `tests/` would tell every reader the opposite.

The spec's sentence survives intact under (A), because what it actually assigns to `corpus/` is *the worked example's format binding* — the first adapter, which is the thing proving the core is format-agnostic when a second adapter lands at P6. The data the adapter reads is not the adapter.

**Consequences / caveats** — Two directories named `corpus` at different depths, which is a genuine readability cost and is why this entry exists. The package one holds code, the root one holds CC BY data. Paths stored in the frozen artifact are repository-relative and forward-slashed, so the artifact's content hash does not depend on which machine extracted it (W23).

---

## D32 — Retrieved policy text corresponds by normalized whitespace, not by bytes

**Fork:** A `POLICY` event quotes a clause from a policy document. What relation must hold between the quoted text and the document?

**Options considered**
- **(A) Equality after collapsing runs of whitespace to a single space.**
- **(B) Byte-identical equality.**
- **(C) Substring containment, unnormalized.**
- **(D) No stated relation; treat the quoted text as authoritative on its own.**

**Decision ✅** — **(A)**.

**Why** — Found by building, which is the part worth recording. The first pilot transcript's retrieved clause was copied from `refund.v1` and then **failed a byte comparison against the very document it was copied from** — because the markdown wraps at one column and the transcript wraps at another, so one contains a newline where the other contains a space. In a project whose premise is that a claim should be checkable against its source, the first check of exactly that kind failed on formatting.

(B) is the rule that produced the failure. Sustaining it would require two independently-wrapped documents to break lines at identical points forever — a rule nobody can maintain and everyone would eventually disable, which is worse than the weaker rule stated honestly. (D) removes the whole point of a logged retrieval: if the quoted text is authoritative, "the agent misstated a clause it retrieved" has no oracle. (C) is (A) minus the normalization and fails for the same reason (B) does.

**Consequences / caveats** — The P2 grounding check must normalize both sides before comparing, and *both* sides is the operative word: W6 records a normalization that was applied to the spoken value and never to the payload, so ordinary thousands separators produced false failures. A one-sided normalization here would reproduce that defect in a new place. The rule is stated in `specs/transcript-format.md` §4.3 and in each policy document's preamble, and is asserted by a test that re-reads the policy file.

---

## D33 — One timestamp per event: agent-side latency is deliberately not measurable

> **SUPERSEDED by D40.** The decision below rests on the premise that "start-stamped logs are what
> real systems overwhelmingly emit". That premise was never checked and is **false**: published
> platform schemas carry turn start *and* end, word-level timing, and separate STT/TTS windows.
> Format v2 carries start and end on every event. Taxonomy 33 remains seeded, by an honest instance
> — event boundaries make a gap computable but not attributable, because no audio layer sits behind
> this corpus. The entry is kept because the way it was wrong is the useful part: it reasoned from
> an assumption about the world where checking was cheap.


**Fork:** Taxonomy 33 observes that timestamps marking only the *start* of an utterance make agent-side latency impossible to compute, because the observable gap conflates speech duration, processing and caller think time. This project authors the instrumentation it then evaluates, so it can choose. Does the format carry one timestamp per event or two?

**Options considered**
- **(A) One timestamp, marking the start. Latency is not measurable, and the format says so.**
- **(B) Start and end timestamps. Latency becomes measurable.**
- **(C) One timestamp, and seed taxonomy 33 against some other unmeasurable property instead.**

**Decision ✅** — **(A)**.

**Why** — Three reasons, in order of weight. Start-stamped logs are what real systems overwhelmingly emit, so the corpus stays representative of the thing it teaches about. The category survives as a genuine seeded item rather than a contrived one — and under (B) taxonomy 33 would have to be manufactured, which (C) makes explicit and thereby exposes as the weaker option: an unmeasurability invented to fill a slot teaches nothing. Third and most important, the correct output for a property you intend to gate on but cannot measure is **a finding against the telemetry schema, not a guessed measurement** — and a corpus that carries the condition can *demonstrate* that rather than assert it.

There is a real cost, and it is not hypothetical: this is the project deliberately declining to fix a defect in its own instrumentation in order to keep the defect available as a teaching case. That is defensible only because the instrumentation is a corpus artifact rather than a production system, and the reasoning is written into the format specification where a reader meets it rather than left in this file.

**Consequences / caveats** — P7 (unmanaged latency and dead air) remains seedable: the gap between consecutive events is computable, its *attribution* is not, which is exactly the honest situation. Any later Tier A check reasoning about ordering uses the event index, never the timestamp — the timestamp stays an opaque string the harness never parses, per the specification's metadata block. If a future phase wants measured latency, the format version increments; it is not a field that can be quietly added, because the artifact's hash would change and every stamped result would stop reconciling.

---

## D34 — No untyped catch-all event kind

**Fork:** The event grammar needs a way to record system annotations that are neither speech, nor a tool call, nor an assignment, nor a retrieval. Does it get a general `NOTE` kind?

**Options considered**
- **(A) No catch-all. Seven typed kinds, and anything else is a parse failure.**
- **(B) A `NOTE` kind, non-citable and excluded from the facts block.**
- **(C) A `NOTE` kind, citable as an established fact.**

**Decision ✅** — **(A)**.

**Why** — W17 is the argument, and it is a measured defect rather than a worry: in the implementation this project diffs against, *any* system note containing an `=` was classified as a variable, so fabricated "facts" flowed into the grounding blob and into the judge's established-facts block. (C) is that defect restored deliberately. (B) fixes the classification but keeps the hazard's precondition — a kind whose contents are unconstrained, sitting one careless change away from being rendered.

The structural fix is not a better heuristic for what a note contains. It is that **every line declares its kind in a dedicated field, so nothing is inferred from punctuation**, and there is no unconstrained kind for a fabricated fact to occupy. `VAR` additionally uses `:=` rather than `=`, which is belt and braces: the kind column alone already settles it.

What would have gone in a `NOTE` has a typed home instead. Lifecycle instrumentation is `EVENT`; configured values are `CONFIG`; runtime values are `VAR`. Each is citable as an established fact because each *is* one.

**Consequences / caveats** — Authoring is stricter: a transcript cannot carry an aside, and a genuinely new category of system record requires a format-version increment rather than a free-text line. Accepted — the corpus is 17 calls authored by one person against a written grammar, and the cost of that strictness is paid once at authoring while the benefit is paid every time a judge prompt is rendered. The parser records an unknown kind as an unparsed line naming the token, so the refusal is legible rather than silent.

---

## D35 — Four seeded gaps stay unchecked, and the reasoning is recorded now rather than when someone decides

> **Superseded in part by D42.** Two of the four — taxonomy **17** and **31** — are in the judged
> tier D42 settled on, as its items 6 and 5, carrying those taxonomy numbers verbatim. **Two remain
> unchecked: 1 and 28.** The analysis below stands for all four and is what D42 drew on for two of
> them; read the table as "what each would need", not as "none of these exists". An independent audit
> found this entry, the scenario map and the coverage document all still saying four, in three
> different wordings, while the spec's own judged-dimension list contained two of them.

**Fork:** Taxonomy items 1, 17, 28 and 31 are seeded in the phase-1 corpus (D30's twelve gaps, all seeded per the scenario map). Each implies a **judged dimension this specification does not have**. What does phase 1 do about the four?

**Options considered**
- **(A) Seed them, build nothing, and record the deferral.**
- **(B) Seed them and draft the specification amendment now** — requirements, scale, gate — for acceptance or rejection.
- **(C) Do not seed what cannot be checked**, and reopen the four as gaps.

**Decision ✅** — **(A)**, *with the substance of (B)'s reasoning written down at the same time.*

**Why** — (C) is the option chosen against once already: seeding costs a few lines during authoring and adding a defect afterwards means re-authoring a transcript, re-extracting, and invalidating any findings already adjudicated against it. Seeding is not checking, and a corpus ready for a check that does not exist yet is strictly better than a corpus that is not.

(B) is out of scope, and the reason is specific rather than procedural: whether to add an eighth judged dimension is a **rubric** decision, and a rubric decision made without the rubric in front of it is a guess wearing a specification's clothes. P3 builds one dimension end to end precisely so the shape of a dimension is known before six more are added as data. Deciding the eighth now would pre-empt the phase designed to inform it.

**But the two halves of (B) are separable, and bundling them was the error this entry corrects.** *Deciding* early is the cost; *recording* early is free. The build prompt's own rule is that decision records are accumulated during the work rather than reconstructed afterwards, because reconstructed rationale gives the reason you would give now rather than the reason you had, and the rejected alternatives vanish silently. That rule does not have an exception for reasoning attached to a decision deferred to a later phase — if anything it applies more strongly there, since the gap between having the reasoning and needing it is longer.

So the four are written out below in enough detail that whoever takes the decision at P3 or P4 inherits the analysis rather than re-deriving it from a corpus and a taxonomy number.

**The four, and what each would need**

| # | The question the dimension asks | Why a deterministic check cannot | What the corpus already carries |
|---|---|---|---|
| 1 | *Given an explicit correction from the caller, does the agent re-read the payload, or manufacture a justification for its original answer?* | The justification is coherent, on-topic and plausibly phrased. Nothing in it is detectably wrong without evaluating whether it *follows from* the record — which is a judgment about reasoning, not a string comparison | CALL-10: caller corrects a date, agent restates the wrong one and explains it as "the date the booking was confirmed on our side" |
| 17 | *Does the agent's confidence exceed what its data sources can support?* | The agent's field says one thing; the caller reports a third party saying another. Both are internally consistent. What is wrong is the **posture** — asserting authority across a visibility boundary — which no assertion over the payload can see | CALL-10: agent contradicts the caller's account of Thornbury Building Society on the strength of a local `payment_instrument` value |
| 28 | *Could the stated next step have been performed in-channel?* | Requires knowing what the available tools could have done, and comparing that to what the agent told the caller to do elsewhere. The tool exists and was not called — a deterministic check sees an absence, not an avoidable one | CALL-04: caller is routed to a web form while `check_access_requirements` sits unused |
| 31 | *Is this claim plausible against the world, not only against the payload?* | **Nothing in the payload disagrees with anything else.** This is the defining property of the category and the clearest justification in the corpus for spending a model call at all | CALL-02: "back on the card within the hour", against card settlement that takes days (`corpus/entities.md`, class 5) |

**Consequences / caveats** — Three consequences worth stating.

The four are **check** gaps, not corpus gaps, and `specs/taxonomy-scenario-map.md` Part 4 says so in those words, so a later reader cannot mistake a seeded defect for a detected one. That distinction is the thing most likely to be lost.

Item 31 carries an authoring dependency that is already discharged and must stay discharged: its third party must remain a real-enough service class with invented specifics. If a later edit replaces Cardinal Pay with a wholly invented service carrying no stated properties, the category silently becomes unjudgeable and this entry's whole argument for spending a model call evaporates with nothing failing.

Whether these are one dimension or four is deliberately **not** decided here. Items 1 and 17 are both about posture under challenge and may collapse into one; 28 is about capability awareness; 31 is about external knowledge. That is exactly the judgment that wants the rubric in front of it, and it is the one thing (B) would have got wrong by deciding it early.

---

## D36 — The gold set does not exist until a human has made it

**Fork:** Phase 1 owes a findings document, and the rows are drafted by a model while D10 makes them the human's judgment. Where do the drafts live, and does `corpus/findings.yaml` exist before anyone has adjudicated them?

**Options considered**
- **(A) Drafts in `corpus/findings.candidates.yaml`; `corpus/findings.yaml` does not exist until adjudication produces it.**
- **(B) Drafts go straight into `corpus/findings.yaml`,** marked with a header saying every row is provisional.
- **(C) Drafts into `findings.yaml` with `detectable_by` and `tier` left blank,** filled in by the human.

**Decision ✅** — **(A)**.

**Why** — (B) is the option that looks identical to (A) and is not. A file at the gold set's path, in the gold set's schema, loadable by the gold set's loader, *is* the gold set to every tool and every reader downstream — a header comment is a claim about it, and claims are what this project keeps replacing with mechanisms. `cj load corpus/findings.yaml` would have worked, and nothing would have refused.

(C) fails for a different reason and is worth stating because it is the intuitive answer: an empty field cannot be reviewed. A reviewer handed a blank `detectable_by` has to derive the classification from scratch for all 47 rows, which is slower and produces *less* scrutiny, not more — there is nothing to disagree with. A proposal beside an unticked choice gets argued with; a blank gets filled in.

So the drafts carry proposals, and the gold set is secured by **not existing**. That is the same mechanism as the held-out set (D2, D19): a property secured by an absence is checkable, and a property secured by a promise is not. The absence is also self-announcing — anything that tries to read the gold set fails loudly rather than reading drafts.

**Consequences / caveats** — Phase 1 cannot close on this deliverable without a human, by construction, and that is the intended shape rather than a scheduling problem. Two things depend on it: the acceptance criteria for the findings schema run against the candidates and against fixtures, which establishes the *machinery*; and severity scoring must wait, because `cj` detects findings text that has moved under judgments already made, so scoring drafts and then rewording them appends a revision acceptance to the comparison log and changes the log hash the severity file names. Adjudicate first, score once.

---

## D37 — The held-out scan declares rather than excludes

**Fork:** `tools/check_holdout_absence.py` scans the working tree for transcripts and refuses any it does not recognize. Its first run failed on three test fixtures, which are genuine conforming transcripts. How is that resolved?

**Options considered**
- **(A) Declare them.** Every transcript in the tree must be named in `corpus/DESIGN_SET` or `tests/fixtures/FIXTURE_SET`.
- **(B) Skip `tests/fixtures/`.**
- **(C) Reserve a call-id range for fixtures** and allow anything in it.

**Decision ✅** — **(A)**.

**Why** — (B) is one line shorter and creates a hiding place, which is the single thing this check exists to deny. A directory the scan does not enter is exactly where a copy would end up — not maliciously, but because someone wanted to look at a held-out transcript "just for a moment" and needed somewhere to put it. The check would stay green throughout.

(C) is (B) with extra steps: a range nobody has to declare into is a range anything can be dropped into.

Under (A) nothing is excluded from scanning and every transcript is accounted for **by name**. Adding a fixture costs one line in a declaration file, which is the correct price for adding a file that the project's only held-out protection has to know about.

**Consequences / caveats** — Two declaration files rather than one, and the check asserts they do not overlap. The scan reads line 1 of every file in the tree rather than matching filenames, because a filename check is defeated by a rename — which is precisely what "just having a quick look" produces. Gitignored directories are scanned, `private/` included, since a stashed copy is still a copy. The false-positive half is tested too: a README mentioning a call id in prose must not be flagged, because a check that fired on ordinary files would be switched off within a week and would then protect nothing.

---

## D38 — The review worksheet pre-ticks nothing

**Fork:** The worksheet shows a model's proposed `detectable_by` and `tier` beside the alternatives. Is the proposal pre-selected?

**Options considered**
- **(A) Show the proposal in its own column; leave every choice box empty.**
- **(B) Pre-tick the proposal,** so a reviewer who agrees does nothing.
- **(C) Show no proposal at all.**

**Decision ✅** — **(A)**.

**Why** — (B) collects agreement rather than judgment, and the two are indistinguishable afterwards. A worksheet returned with every proposal still ticked is evidence of exactly nothing: it cannot be told apart from a worksheet nobody read, and both are indistinguishable from the model having assigned the labels itself — which is the failure D10 exists to prevent, arrived at through a convenience rather than a decision. (C) is D36's option (C) again and fails the same way: there is nothing to disagree with.

Under (A) a returned worksheet carries a mark that someone made. That is a low bar, and it is a bar.

**Consequences / caveats** — Ticking 47 × 2 boxes is more work than confirming defaults, deliberately. Recorded here mainly because the first implementation *did* pre-tick while the docstring immediately above it said it did not — a claim in prose the code did not honor, which is now the fifth instance of that shape in this project (a specification, a validator, a detector, a manifest, and this). The comment in the code says why rather than what, so the next person to "simplify" it has the argument in front of them.

---

## D39 — Public platform schema documentation is outside D6's boundary

**Fork:** D6 says no prior third-party material is read. Does that extend to published documentation on how production voice platforms log calls?

**Options considered**
- **(A) No. Schema documentation is a different category and is read.**
- **(B) Yes. Nothing external is read; the format is designed from stated requirements alone.**
- **(C) Read third-party transcript corpora as well.**

**Decision ✅** — **(A)**. Schema and field-level documentation, not transcript collections.

**Why** — D6 has two stated reasons: professional conduct about a company's exercise material, and avoiding design fixation on one prior implementation. **Neither covers general public knowledge of how voice platforms log calls.** Treating them as one boundary is how "do not copy this specific thing" became "reinvent telephony from first principles", and the cost of that was measured rather than hypothetical: the first human review of the corpus found a transcript with no recording disclosure, no identification, and no record of what the agent could see — three things anyone who had looked at a real call log would have included.

The distinction that holds is **schema, not corpus**. Documentation tells you what fields exist; a transcript collection tells you what scenarios look like, and scenario shape is exactly what the substitution policy protects. Reading the first does not touch the second.

There is a further argument specific to this project. An engineer adopting this harness already has logs in whatever shape their vendor emits. A canonical model designed without reference to what vendors emit will not receive what they send, and the harness is then a demonstration rather than a tool.

**Consequences / caveats** — The read-prohibited paths in `private/clean-room-sources.md` are untouched and remain so; this widens D6 in one direction only. What was read is cited in `specs/event-model.md` §4, so the boundary stays auditable rather than becoming a general license. The corpus's *content* is still originated independently — the reviewer's phrase was "a fusion of existing structure while the content gets regenerated", and that is the rule.

---

## D40 — Format v2: the model is the contract, the text format is one adapter

**Fork:** The transcript format was specified as the thing the harness reads. But every platform logs differently, and an engineer adopting the harness has their vendor's shape. What is the contract?

**Options considered**
- **(A) A canonical event model is the contract; every source format is an adapter onto it.**
- **(B) The text format is the contract; other formats are converted into it as text.**
- **(C) The harness reads vendor formats directly, with checks written per format.**

**Decision ✅** — **(A)**.

**Why** — (C) multiplies every check by every format and makes the rubric unportable. (B) is subtler and worse than it looks: converting a vendor log into a *text transcript* means round-tripping structured data through a wrapped-text serialization designed for human reading, losing anything the text grammar cannot express and gaining a parsing step nobody needs. The text format exists because a wrapped human-readable log is the harder parsing case and therefore the better test of the extraction tier — that is a reason for it to be **adapter 1**, not a reason for it to be the contract.

Under (A) nothing above the adapter line knows which platform a call came from, which is the property the second adapter exists to prove and the property an engineer writing a third adapter depends on.

**The model is a fusion of what platforms already emit, not an invention.** `specs/event-model.md` §4 maps each canonical element to its Retell, Vapi and Connect equivalent, which is both the evidence for that claim and the table someone writing an adapter reads.

**Consequences / caveats** — `specs/event-model.md` is new and `specs/transcript-format.md` now serializes it rather than defining it. The P6 "JSONL adapter" is retargeted: a JSONL format of this project's own invention would prove nothing, so adapter 2 should be shaped like a real vendor's call object. Adapters owe three things — ordering, vocabulary mapping, and honest gaps — and **anything a source cannot supply is recorded as unavailable, never defaulted**, because a defaulted value is indistinguishable from a real one and a check keyed to it would be asserting on a value nobody supplied.

---

## D41 — Invocation and result are separate events, and the chain is assertable

**Fork:** v1 had one event per tool call, carrying a status that mixed permission with outcome. A human review pointed out that a disposition label needs more than an attempt: eligibility is established, the action is performed, **a confirmation is published**, and only then may anything depending on it happen.

**Options considered**
- **(A) Split invocation and result into two events linked by id, with an explicit `successful` flag.**
- **(B) Keep one event, split the status vocabulary into eligibility and outcome channels.**
- **(C) Keep one event and derive success from the status.**

**Decision ✅** — **(A)**.

**Why** — It is what platforms do, and that was checked rather than assumed: Retell interleaves `tool_call_invocation` with `tool_call_result` linked by `tool_call_id`, the result carrying a `successful` boolean; Vapi splits `tool_calls` from `tool_call_result` with a `toolCallId`; call-logging practice records `toolResultStatus` with separate start and completion timestamps. (C) was v1 and made "the agent proceeded against state that already said it could not" inexpressible, because a single event has no *before* for the agent to have proceeded against.

**`successful` is carried separately from `status`, and the redundancy is deliberate.** Platforms carry both, and a result whose `successful` disagrees with its status is a real data-integrity defect the model must be able to represent. `ToolStatus.implies_success` is therefore a *check*, not a derivation.

**Eligibility is the content of a read, not the status of a write.** A write's result says whether the write happened; whether it was permitted is what a prior read reported. Keeping those separate is what makes the corpus able to seed an agent ignoring an eligibility answer it already had.

**A note on what this does and does not establish.** The tool-calling protocol guarantees the agent *has* a result before its next turn — the runtime appends each `tool_result` to the conversation and calls the model again, and errors are returned as results precisely so the model can recover. So "the agent announced success after receiving a failure" is an agent disregarding something in its own context, not a race or a missing signal. What no platform does automatically is **enforce** the chain: nothing blocks a write because a prior confirmation is absent. That gap is what the harness tests, and it is why a write executing against an unset gate is a *platform* finding rather than an agent one.

**Consequences / caveats** — The adapter checks pairing structurally: every result references an earlier invocation, every invocation has exactly one result, no id is reused. A dangling call or an orphan result aborts, because a log that cannot say whether an action completed makes every ordering assertion built on it meaningless.

---

## D42 — `detectable_by` is `assert` unless the judgment is genuinely conversational

**Fork:** Seventeen of forty-seven drafted findings were classified `judge`. A human review rejected several by name, with a rule: a judge must not be asked to evaluate an agent's response against the value of a system variable.

**Options considered**
- **(A) `assert` for anything derivable from context, tool calls, results, state and their order. `judge` only for non-deterministic conversational quality.**
- **(B) `judge` wherever a check would be intricate to write.**
- **(C) `judge` wherever the defect involves what the agent *said*.**

**Decision ✅** — **(A)**.

**Why** — (C) was roughly the operating rule and it is wrong: most defects involve speech, but the *oracle* is usually the event log, and comparing speech against the log is an assertion. (B) confuses cost with kind — an intricate check is still deterministic, and routing it to a model buys unreliability at a price.

Under (A) the judged tier's justification narrows and gets much stronger. What survives is what nothing else can do:

- **Were all of the caller's concerns addressed?**
- **Did the agent hold a coherent conversation, or repeat itself unnecessarily?** — and *unnecessarily* is the whole point. A repeat after a caller with an unfamiliar accent or limited proficiency is correct behavior; a repeat of a question already answered is a defect. No counter separates them.
- **Did the terms the agent stated in reply to this question actually align with policy?** — retrieval and quotation are assertable; whether the paraphrase conveyed the rule is not.
- **When the caller objected and a reversal or transfer followed, had the agent misunderstood them in the first place?**
- **Is a claim plausible against the world rather than only against the payload?** (taxonomy 31)
- **Does the agent's confidence exceed what its data sources can support?** (taxonomy 17)

**Consequences / caveats** — Rebuilt CALL-01 yields **zero** `judge` findings, which is a result rather than a gap. It also means the corpus must include calls **authored specifically** to exercise the dimensions above, including the legitimate-repeat case as a true negative — otherwise a check scores well by firing on every repeat, and the judged tier is justified by assumption rather than by anything in the corpus.

---

## D43 — Findings carry an owner

**Fork:** A drafted finding bundled "the platform recorded no verification state" with "the agent claimed verification it never attempted". A human review rejected it: those are different problems.

**Options considered**
- **(A) `owner` becomes a required field: `agent` | `platform` | `data`.**
- **(B) Keep it in the observation prose.**
- **(C) Split by report section at render time.**

**Decision ✅** — **(A)**.

**Why** — A row with two owners is actionable by nobody: different fix, different desk, different section of the report. (B) makes the distinction unreadable by machine and unenforceable, so rows would keep merging. (C) defers the judgment to rendering, which is where it would be *guessed* — the person who wrote the finding knows whose defect it is, and the renderer does not.

The specification already splits the report into an agent-behavior audience and a data/integration one at P4. This makes that split a property of the finding rather than an inference made later.

**Consequences / caveats** — A seventh required key. Verified by running rather than assumed: `comparative-judgment` accepts the findings file with the extra key, since its required set is the six and it tolerates additions. `data` is distinct from `platform`: a record holding two values for one field is a defect in the data whatever the orchestration does, and P9's "grounding has a ceiling set by the data" needs that category to exist.

---

## D44 — The corpus is set in the United States

**Fork:** The corpus was authored British — `en-GB`, `+44`, pounds, and venue names drawn from English places. A human review asked for US ZIP codes.

**Options considered**
- **(A) Move the whole canon to the US: locale, currency, numbering, ZIP codes, idiom, entity names.**
- **(B) Change only the ZIP format.**
- **(C) Leave it British.**

**Decision ✅** — **(A)**.

**Why** — (B) produces a call in a US number range at a venue named after a Yorkshire village, quoting pounds. Half-localized is worse than either end: a reader notices, and what they notice is that nobody was paying attention.

The move also improves something unrelated to nationality. California's two-party consent makes the recording disclosure a **legal requirement** rather than a nicety, so the `DISCLOSURE` event has a stated reason to exist and its absence in a call becomes a defect with a name.

**Consequences / caveats** — Every reserved range changes and each is chosen so it cannot correspond to a real person: NANP reserves `555-0100`–`555-0199` for fictional use, and ZIP codes are drawn from `00000`–`00499`, below USPS's lowest assigned code (`00501`). No street addresses appear at all — a ZIP is used for verification and nothing else. The corpus-hygiene tests assert all three ranges, so a drift back is a failing test rather than a reading.

---

## D45 — A finding names one owner, so F-10 became two findings

**Fork:** The second human review marked F-10 — "the agent said the refund would arrive within the
hour" — with **both** owners and **both** classifications, and asked which was at fault: "Was the
platform too slow, or did the agent jump the gun?" A finding cannot carry two owners under D43, so
something had to give.

**Options considered.** (A) Pick the more severe owner and drop the other. (B) Widen `owner` to a
list. (C) Split the row into one finding per owner.

**Decision: (C).** F-10 keeps the invented figure and stays `agent`. F-50 is new and `platform`: the
settlement timeline reached the agent at event 18, two turns *after* it answered the caller's
question at event 16, and no policy clause retrieved in the call states one either. F-51 is new and
`agent`: three turns remained with the caller on the line after `expected_days=5` arrived, and the
figure was never corrected.

**Why** — (A) discards the reviewer's actual observation, which was that both are true. (B) is the
one that looks reasonable and is not: D43 exists because a row bundling a platform defect with an
agent defect is actionable by nobody, and a list-valued owner recreates exactly that bundle with
extra syntax. A finding is a unit of work for one team. Three findings is the honest count because
there are three distinct things to fix: an agent that answers questions it has no grounding for, a
platform that supplies a timeline after the moment it was needed, and an agent that does not revise a
claim when the grounding arrives.

**Consequences / caveats** — the corpus now carries 51 findings, and F-50 is the first finding whose
subject is *when* a platform supplied a correct value rather than whether it did. It needs the
`[context]`/`TOOL_RESULT` ordering the v2 format introduced; under v1 it would have been unstateable.
F-50 is deliberately not an excuse for F-10, and says so.

---

## D46 — A document that claims to be machine-checked is a claim like any other

**Fork:** `corpus/seeding-manifest.md` states that its anchor table — the `(call, index, kind,
fragment)` rows restating every positional reference in the manifest — is asserted against the
extracted corpus by `tests/test_corpus_hygiene.py`. It was not. No test read the table. CALL-01 was
then rewritten, four of its five anchors moved, and the suite stayed green.

**Options considered.** (A) Write the test the manifest already claims exists. (B) Delete the claim
and keep the table as prose. (C) Delete the table.

**Decision: (A)**, plus a paragraph in the manifest recording that the claim was false until it was
checked.

**Why** — the table exists *because* the manifest's own text says positional references break
silently, and it was added after exactly that happened once already. A guard named in prose and never
written is worse than no guard: a reader who sees "asserted by" stops looking, which is the entire
value of the sentence and the entire cost of it being wrong. (B) and (C) both answer a drift problem
by removing the instrument that would detect it.

**Consequences / caveats** — the test parses the manifest's Markdown table, which couples a test to a
document's formatting; a reshaped table fails the row-count guard rather than silently matching
nothing. The same audit found three more claims of this shape and one true gap: the entity register
called itself the canonical list while ten context variables in use were absent from it (now
declared, now asserted); the held-out fixture claimed to be held-out-shaped while frozen at format v1
(now v2, and now parsed rather than asserted-by-eye); the type check claimed to cover "the whole
package" while excluding `tests/`, where most of what this project asserts lives (now included, which
required a PEP 561 `py.typed` marker the package had been shipping without). **The pattern is one
worth naming: every one of these was a sentence that described a check, and in each case the sentence
was the only thing doing the checking.**

---

## D47 — Two values for one field are only a contradiction when they describe the same thing

**Fork:** `test_a_record_contradicts_itself_only_where_it_is_seeded` compared every `door_time=` in a
tool result against the call's context and reported a mismatch as P9's seeded data-layer
contradiction. CALL-01's rewrite added a `find_performance` lookup, which returns a *different*
performance — legitimately with a different door time — and the check reported the corpus as
carrying an unseeded contradiction.

**Options considered.** (A) Add CALL-01 to the seeded set. (B) Drop `door_time` from the compared
fields. (C) Establish which event a result describes before comparing anything.

**Decision: (C).** The result's own `match=EV-#####`, then the invocation's `event=` argument; a
result naming neither is assumed to concern the booked event, which keeps the check looking rather
than letting silence exempt it.

**Why** — (A) is the tempting one and is a lie in a file whose whole purpose is to separate seeded
defects from accidents. (B) removes the only field the check actually covers. The real defect was in
the check: it could not tell "this record disagrees with itself" from "these are two different
events", so it reported the second as the first. A comparison without a subject is not a
contradiction test.

**Consequences / caveats** — the check now depends on results identifying their subject, which the
corpus's tool vocabulary happens to support. A future tool returning a door time for an unnamed event
would fall through to the conservative branch and be compared against the booked event, which is the
right default but is a default.

---

## D48 — Speech timing gets a plausibility floor, not a model

**Fork:** The review observed that CALL-01's eighty seconds of dialogue would take a person
considerably longer to say. Measurement confirmed it across the corpus: a median of 116 words per
minute against a conversational 130–160, with individual utterances at 42 and at 253. Timestamps were
recomputed. What, if anything, should stop them drifting back?

**Options considered.** (A) Nothing — it was a one-off authoring error. (B) Generate durations from
word counts at fix time and never hand-write them. (C) Assert a plausibility band, and pin the
corpus median as well as the per-utterance edges.

**Decision: (C).** 110–185 wpm per utterance, median 130–160, utterances under four words exempt.

**Why** — (A) is what was in place, and it is why the defect reached a human reviewer. (B) makes
durations a derived field, which sounds tidy and removes the ability to author a deliberately slow or
rushed turn — the corpus needs both, and CALL-12's seeded duration mismatch depends on being able to
write a wrong one. (C) keeps authoring free and catches drift. The band is deliberately wider than
real conversational speech because 130–160 is a population statistic and these are individual
utterances; the median test is what stops a uniformly-slow corpus passing inside a wide band.

**Consequences / caveats** — this asserts plausibility, not realism. There is no audio behind these
transcripts and no correct duration for an invented utterance. The test says so in its own docstring,
because a reader who mistakes it for a fidelity claim would trust the corpus further than it earns.

## D49 — F-50 was built on a premise that the corpus contradicts

**Fork:** F-50 was written to capture a human reviewer's observation that the platform supplied the
refund settlement timeline only after the agent had answered a question about it. The reviewer's
stated reasoning was "since the agent does not have the guidance on refund timeline from the policy,
it is not surprising that it would make up something". Auditing the corpus documents found that
`refund.v1 § 3.2` states five business days, and that CALL-02's agent had used `fetch_policy`
successfully two turns before it answered.

**Options considered.** (A) Keep it platform-owned and narrow it to "settlement timing should be
exposed on a read, not only on the write that produces it". (B) Delete it — F-10 already covers the
agent side. (C) Re-cut it as an agent finding: a policy claim made with no retrieval behind it.

**Decision: (C).** `owner` becomes `agent`. The observation is now that the agent answered a policy
question without fetching the clause that answers it, in a call where it had just demonstrated it
could.

**Why** — the platform withheld nothing. The clause existed, the tool worked, and the agent had used
it. (A) would be defensible in isolation but is not what happened here, and a finding that survives
by being narrowed until it is true of something else is not the same finding. (B) loses a genuinely
distinct and *cheaper* detection: F-10 needs knowledge of how card settlement works, whereas "a
policy term was spoken and no `POLICY` event supports it" is an assertion over the event stream. That
distinction is the argument for the `POLICY` event existing at all.

**Consequences / caveats** — this contradicts the premise the reviewer gave, and saying so is the
point rather than an awkwardness: the corpus is the authority on the corpus. D45 recorded F-10's
split into three findings and described F-50 as platform-owned; that description is superseded here,
and the split itself still stands. The platform half of D45 dissolves — of the reviewer's two
candidates, "the platform was too slow" and "the agent jumped the gun", only the second survives
contact with the policy documents.

---

## D50 — The audit that found it, and what it says about the rest

**Fork:** After correcting the seeding manifest, the same read-every-claim pass was run over the
remaining corpus documents. It found one substantive error (D49), four gaps, and a version number that had not moved. What is the general
rule, given that this is now the sixth such find in two sessions?

**Options considered.** (A) Fix the five, note the pattern in prose. (B) Fix them and write a
standing check per claim, wherever a claim is machine-checkable. (C) Stop asserting things in prose
that cannot be checked.

**Decision: (B)**, and all five are closed accordingly:

- The policy-correspondence check compared a quoted clause against **the whole document**, while all
  three policy documents' preambles promise correspondence with **the cited clause**. A `POLICY`
  event citing § 2.1 while quoting § 2.3 passed, and `refund.v1`'s three refund windows differ by a
  number and a word. Now clause-level, with a control asserting the three are distinguishable.
- `outcome` had no declared vocabulary anywhere while `disconnection_reason` had a validated one.
  Now closed, validated, declared, and asserted against the register.
- The entity register headed a section "Reason codes" for a field renamed `outcome_reason` — the
  canonical list naming a field that no longer exists.
- `corpus/findings.candidates.md` had a regeneration check; `corpus/findings.review-worksheet.md`,
  the document a human actually reviews, had none. A stale worksheet collects judgments and attaches
  every one of them to the wrong row. `tools/make_review_worksheet.py --check` now exists and a test
  runs it.
- `CORPUS_VERSION` read `0.1.0` through a format migration, two review rounds, a complete re-timing
  and 47 → 51 findings. Bumped to `0.2.0`.

**Why** — (C) is the tempting overcorrection and it is wrong: the claims worth making are frequently
the ones a test cannot express, and deleting them leaves a reader with less. The defensible rule is
narrower — **a document may assert whatever it can support, but a sentence that names a check is
itself a claim, and a claim about a check is exactly the kind that goes stale silently.** Every one
of the six was of that form.

**Consequences / caveats** — what checked out clean is worth recording too, because an audit that
only reports finds gives no sense of the base rate: all identifier shapes conform; per-ticket prices
and booking fees sit inside the register's stated ranges; every `outcome_reason` in use is declared;
every finding-to-finding cross-reference and every policy clause cited inside a finding resolves; the
three policy documents interlock without contradiction, including the pair that looks like one
(`refund.v1 § 4.1` requires a transfer to be reversed, `transfer.v1 § 1.1` says Verso cannot reverse
one — consistent, because the current holder can transfer it back). The corpus was in better shape
than the documents describing it, which is the pattern in all six finds.

## D51 — A tool that needs a derived input builds it rather than demanding it

**Fork:** `tools/make_review_worksheet.py` read `build/extraction-artifact.json` and exited with an
instruction when it was absent. `build/` is gitignored. The test added at `fcf8397` runs that tool
with `--check`, and CI runs the test suite *before* the extraction step — so the suite passed on
every machine that had run extraction at some point and failed on a fresh clone. An independent audit
reproduced it; so did I, before acting on the report.

**Options considered.** (A) Fall back to re-parsing `corpus/transcripts/` when the artifact is
absent. (B) Have the tool build the artifact itself. (C) Move the extraction step above the test step
in CI. (D) Commit the artifact.

**Decision: (B)**, with **(C)** as defense in depth.

**Why** — (A) is the obvious fix and it contradicts the loader's own docstring, which gives a real
reason to read the artifact: *"so the text a reviewer reads is the text the harness actually
extracted. If those ever diverge, the reviewer is adjudicating something the harness will never
see."* A fallback is a second way to produce the worksheet, and two paths can disagree exactly when
it matters. (D) is worse: the artifact carries a content hash over derived data, and committing it
invites the derived and the source to disagree with a merge conflict as the only signal. (C) alone
fixes CI and leaves `pytest` broken for a human who clones and runs it, which is the more common
case.

**Consequences / caveats** — the tool now has a side effect on a path nobody asked it to write, which
is why it says so on stderr. The general rule is worth stating: **a dependency satisfied only by
yesterday's command is not a dependency anyone can see.** The suite now passes with `build/` deleted
entirely, which is the condition that was never tested.

The same fork had a second half. `verify_phase1.py` read only the JUnit nodes its own `CRITERIA` list
names, so a failing test that no criterion mentions — exactly this one — left it printing *"All 21
phase-1 acceptance criteria pass"*. It now reads pytest's exit code as well and refuses to report a
pass when the suite is red. Verified in both directions with a deliberately failing probe: exit 1
with it, exit 0 without.

---

## D52 — The held-out scan reads a deny list, and looks past line 1

**Fork:** `tools/check_holdout_absence.py` is, by its own docstring and by D2, the only mechanism
protecting the held-out set. It promised a transcript is found *"pasted anywhere, under any name"*.
Two independent narrowings meant it was not: an allow list of six file suffixes, and a requirement
that the format marker sit on **line 1**.

**Options considered.** (A) Add the missing suffixes. (B) Invert the suffix list to a deny list of
binary formats. (C) Also look for the marker anywhere in the file, not only on line 1.

**Decision: (B) and (C) together.**

**Why** — (A) is what the audit report proposed and it closes only half the hole. The two narrowings
are independent, and the case the report itself calls *"the one that matters"* — a transcript pasted
into a scratch Python string — is defeated by the **line-1** rule, not by the suffix filter. Adding
`.py` to an allow list would have made the scan *look* fixed while that case stayed open. An allow
list is also the wrong polarity for a guard: it has to enumerate every extension a person might type,
which is not a finite set, whereas the set of binary formats is small and stable. Measured: the same
synthetic transcript written under nine names and locations went from **1 of 9 found to 9 of 9**.

**(C) needs a second condition** or the format specification and the scanner itself would report
themselves, since both quote the marker while documenting it. A marker found below line 1 counts only
when a `call_id` follows it; documentation does not carry one and a transcript always does. A marker
**on** line 1 still counts alone — that file is a transcript whatever else is true of it, and one
with its `call_id` stripped is reported as unreadable rather than waved through.

**`build/` comes off the skip list at the same time**, and the test that asserted a copy there is
*not* found is replaced by one asserting it is. The other skip entries are tool-generated trees
nobody authors into. `build/` is gitignored, writable, and the harness's own output directory — which
is D37's argument exactly: skipping a directory creates the hiding place the scan exists to deny.

**Consequences / caveats** — widening the scan made `tests/test_holdout_absence.py` itself a
held-out transcript in the working tree, and the scan said so. That is correct: the file carried a
verbatim conforming transcript in a string literal. The fixture now interpolates the scanner's own
`_FORMAT_MARKER` instead of copying it, which removes the transcript *and* a copy that could drift
from the constant it imitates.

Worth recording separately: **the audit's second-order claim here was wrong, and checking it changed
the fix.** It said widening the suffix list "will turn the scan red" because of that literal. It
would not have — the line-1 rule meant a `.py` file whose first line is a docstring was never
examined at all. The literal only becomes visible once (C) lands. Acting on the report without
reproducing it would have produced a fix that closed the smaller half of the hole and pinned a
mitigation for a problem that had not yet appeared.

---

## D53 — The judged tier is six dimensions, and two of D35's four gaps are inside it

**Fork:** D42 settled the judged tier at six dimensions and its list names taxonomy **31** and **17**
verbatim, with those numbers attached. Six other places said seven, and three documents still said
taxonomy 1, 17, 28 and 31 each imply *"a judged dimension the specification does not have"*. So the
specification's own judged-dimension list contained two items three of its documents described as
missing. An independent audit found it; the count also drives the cost model.

**Options considered.** (A) Six, with 17 and 31 inside — D42 is the later decision and its list is
explicit. (B) Seven, on the reading that a dimension was intended and dropped in drafting; restore it
to D42. (C) Leave both readings and mark the contradiction.

**Decision: (A).** Six. D35 is superseded in part: **1 and 28 remain unchecked; 17 and 31 do not.**

**Why** — (B) would need a seventh dimension somebody could name, and nothing in the record names
one; "seven" is simply older than D42 and survived in the places D42's author did not visit. (C) is
what the repository already had, and the cost model shows why it is not neutral: a stale count is not
inert, it propagates into a figure that gates a human confirmation prompt at P3. The run estimate was
960 judged calls at 12 x 7 x 10 plus synthesis; at six it is **840**.

**Consequences / caveats** — eleven sites changed across four documents. Two were left alone
deliberately. D16's option (A) still reads "seven dimensions" with a note saying why: it records what
was considered when it was considered, and a decision record edited to agree with later decisions
stops being a record. And D35's table still describes all four gaps, because the analysis it holds is
what D42 drew on for two of them — the banner says which two are closed rather than deleting the
rows.

Fixed in passing, because the sentence was being rewritten anyway: the coverage document's breakdown
of the twelve gaps named item 7 without classifying it, listing it after the count instead of in a
bucket. It is a cheap deterministic check, so the deterministic bucket is five, not four. (The audit
reported this as a breakdown "accounting for eleven" of twelve; that part is wrong — the passage does
enumerate all twelve, and its quotation stopped one sentence short of the one naming item 7. The
classification gap is real; the arithmetic error is not.)

---

## D54 — Six of the eight findings keys cross the repository boundary, and the split is now declared

**Fork:** `harness.core.findings.REQUIRED_KEYS` holds eight keys.
`tools/check_spec_interface.py` — the detector whose entire purpose is catching the two repositories
drifting apart about this interface — named six, and `tests/test_check_spec_interface.py` re-typed
the same six as a literal. An independent audit read this as *"the drift detector has itself drifted
two keys behind the code"* and reported it as a defect.

**It had not drifted.** The severity tool compares one finding against another to place it in an
order; which call a finding came from and whose defect it is change nothing about that comparison,
and the tool's specification names exactly the six — measured, not assumed. `owner` and `call_ref`
are harness-side. Requiring the tool's documents to name them would be requiring the tool to document
fields it has no use for, and the scanner demands each key appear on *both* sides.

**But there was a real defect underneath, and it was worse than the reported one.** `owner` — the
field D43 added and the loader enforces — appeared in the specification **only in two changelog
paragraphs**. Not in scope, not in a SHALL, not in an acceptance criterion; `call_ref` appeared once
as the words "the call reference" and never as a key. So a findings document built to the
specification was rejected by the code implementing it, and the acceptance criterion for the key set
enumerated six of the eight.

**Options considered.** (A) Add the two keys to the scanner, as the audit proposed. (B) Leave the
scanner and document the subset in a comment. (C) Derive the scanner's list from the loader's, minus
a **declared** harness-only set, and give the two keys a requirement and a criterion.

**Decision: (C).**

**Why** — (A) would turn the scanner red against a tool that correctly does not mention fields it
never reads, and the only way back to green would be adding fields to another repository's
specification to satisfy a check. (B) leaves the subset as prose, which is the shape this project
keeps finding in itself. Under (C) the subset is computed: `FINDINGS_KEYS = REQUIRED_KEYS -
HARNESS_ONLY_KEYS`, so adding a key to the loader forces the choice — shared, or harness-only —
rather than silently widening a difference. The test file imports both lists instead of re-typing
them, and three new tests bind the partition, the severity pair, and the specification's own SHALL
and criterion to `REQUIRED_KEYS`.

**Consequences / caveats** — the scanner now imports from `harness.core.findings`, so it needs the
package importable. It is run under `uv run` in CI and locally, and it is a harness-repo tool; a
future need to run it standalone would have to vendor the list, which would recreate the copy.

The general shape is worth naming, because the audit's misreading is the evidence for it: **a subset
that exists only as the difference between two hand-maintained lists is indistinguishable from a
stale copy.** A careful reader with the code in front of them concluded, reasonably, that the
narrower list was drift. The subset was correct and its *documentation* was the defect.

---

## D55 — The `[context]` continuation rule is positional, and the format specification now states it

**Fork:** `specs/transcript-format.md` §3 said only *"wrapping permitted"* for the `[context]` block.
The parser had a rule anyway — any line not matching `name :=` continues the previous value — and its
docstring called that *"the same continuation rule as the event stream"*, which it is not. §4.1's
rule is **positional**: an empty index field. The context rule was **content-based**, and the
difference corrupted without a sound:

| Written | Parsed as |
|---|---|
| a wrapped value whose continuation contains ` := ` | **two variables**, the second fabricated |
| a wrapped value whose continuation begins with `#` | **one variable with its tail deleted** |

No unparsed line, no error, no counter. An independent audit reproduced both; so did I.

**Options considered.** (A) Keep the content-based rule and document it. (B) Make the rule positional
— an indented line continues — and state it in §3.1. (C) Forbid wrapping in `[context]` entirely.

**Decision: (B).**

**Why** — (A) documents a hazard rather than removing one, and the hazard is severe out of proportion
to the block's size: the context record is what `event-model.md` §2 uses to decide whether a finding's
owner is the agent or the platform, so a fabricated variable there mislabels a defect rather than
merely mangling a string. (C) is the safest and is wrong for the same reason §4.1 permits wrapping in
the event stream — a format that forbade it would design out the bug class the extraction tier exists
to catch, and one context value in the current corpus already wraps across three lines.

The polarity is the argument. **A positional marker cannot collide with the content it delimits; a
content-based one collides with exactly the values most worth wrapping** — the long ones, which are
the ones likely to contain punctuation. That is W17's shape (a fabricated fact entering the record
from punctuation) and W16's (a fragment silently lost), both of which this project believed it had
closed at D34 and format v2. They were closed in the event stream and reopened in the block for which
no rule was written.

**Consequences / caveats** — an unindented line that is not an assignment now aborts naming itself,
where it used to be absorbed into the value above. Nothing in the corpus changes: the extraction
artifact's content hash is identical before and after, because every existing continuation is already
indented. Five tests pin the rule, including the false-positive half — a genuine second assignment
must still become a second variable, or the fix would be the same defect pointing the other way.

---

## D56 — A malformed line stays a counting problem all the way down

**Fork:** Two more parser defects from the same audit, both reproduced.

`_check_tool_pairing` runs over surviving events, so a `TOOL_RESULT` rejected into `unparsed` left
its `TOOL_CALL` looking dangling. Changing one arrow in a result body produced *"tool call(s) with no
result: t1"* — an abort that names the well-formed invocation and never mentions the malformed line.
That contradicts the adapter's first stated principle, that *"a line the grammar cannot read is a
counting problem"*, and the specification's requirement that an unparsable line increments a counter
rather than aborting.

Separately, `expected_index` advanced on every rejection path **except** the field-count one and the
non-integer-index one — and the field-count path is reachable with a perfectly readable index. The
project's own fixture shows the cost: the line after the damaged one is commented *"Another
well-formed line"*, is well formed, and was reported out of sequence. **One defect, two findings.**

**Options considered.** For the pairing check: (A) skip ids whose partner is unparsed; (B) run
pairing only over a stream with nothing unreadable in it. For the index: (C) advance by one on every
rejection; (D) also resync to a declared index when the line carries a readable one.

**Decision: (B) and (D).**

**Why** — (A) requires knowing which id an unreadable line *would* have referenced, which is the thing
that could not be parsed. Under (B) the run still fails, on the unparsed count, with a message naming
the actual line and its number; the pairing abort was adding a wrong explanation to a failure that
was already going to happen. A genuinely dangling call in a clean file still aborts, and a test pins
that, because a fix for a misleading message must not delete the check. (D) over (C) because a
rejected line that declares where it sits is telling the truth about its position even when its body
is unreadable, and resyncing is what the out-of-sequence branch already does.

**Consequences / caveats** — the fixture's unparsed count drops from six to five and it keeps four
events rather than three, which is the point rather than a regression. The test named for this
invariant asserted over surviving event indices, which the bug does not disturb — so it passed for as
long as the bug existed. It now asserts over the **unparsed line numbers**, and cross-checks that no
line the fixture itself calls "well-formed" appears among them.

---

## D57 — A test cited as evidence must check the thing it is cited for

**Fork:** Two tests asserted something weaker than their docstrings claimed, and both were load-bearing.

`test_the_corpus_carries_a_wrapped_state_event` asserted
`wrapped or any(len(v.split()) > 8 ...)`. The corpus contains **no** wrapped `STATE` event, so it
passed entirely on the second clause -- a **word count**, which is not a wrap. The long value does
wrap, but by luck rather than by anything the test looked at, and `tools/verify_phase1.py` names this
test as one of three pieces of evidence for the three-line-wrap acceptance criterion.

`test_the_two_calls_that_do_not_verify_are_the_ones_the_findings_name` carried the docstring *"this
proves the corpus matches the findings, so the three documents cannot drift apart in a pair while
agreeing with the third"* and asserted a hardcoded `{"CALL-01", "CALL-12"}`. It never opened the
findings document. Written in this session, one commit after the audit that found the same shape in
the seeding manifest.

**Options considered.** (A) Rename both to what they check. (B) Seed a wrapped `STATE` event in the
corpus so the first test's subject exists. (C) Retarget both at the claim.

**Decision: (C)**, and (B) is deliberately **not** done.

**Why** — (A) is honest and gives up the coverage; the criterion would then rest on two tests instead
of three and nobody would notice the loss. (B) means editing a transcript to make a test's subject
exist, which re-authors the corpus to suit the suite and would move findings evidence, manifest
anchors and the artifact hash for a test's convenience. The rule covers two wrap sites -- a `STATE`
event and a `[context]` assignment -- and the corpus exercises one of them; the assertion now says
so, measured as a **source-line span** at both sites, so a corpus that stopped wrapping anything
fails rather than passing on a proxy. A second test asserts every source fragment survives into the
parsed value, read from the file rather than from the parser's output, which is the W19 discipline.

For the second test, the findings side is now derived: a `platform`-owned finding naming
`identity_verified` is one asserting the platform never recorded verification, and the set of calls
carrying such a finding must equal the set of calls that do not verify. F-05 and F-46 own it.

**Consequences / caveats** — the wrap criterion in `verify_phase1.py` now names the two retargeted
tests instead of the one. The gap that remains is stated rather than closed: **no `STATE` event in the
corpus wraps.** If one is ever seeded, the assertion's second line is where to record it.

---

## D58 — A number quoted in prose is a claim, and a countable claim gets counted

**Fork:** Fourteen stale statements across four documents, from an independent audit. **Six of them
were numbers**: 308 events against 285, 47 candidate findings against 51, "eleven" for a ten-item
list in three places, a judged tier stated as 7 in six places against D42's 6 (D53), a decision header
reading D1–D30 against a document holding fifty-odd, and a maintenance note describing a tally row
that had since moved. Fixing fourteen sentences takes an hour. What stops the fifteenth?

**Options considered.** (A) Fix them and move on. (B) Fix them and add a `docs-drift` CI step over
the counts that keep going stale. (C) Stop quoting numbers in prose.

**Decision: (B).** `tests/test_document_counts.py`, nine assertions.

**Why** — (A) is what happened after the last two sweeps, and the count came back. (C) removes the
information: a sentence naming how many transcripts and how many events tells a reader the size of
the thing, and deleting it to avoid maintaining it is a worse document. (Written here without the
figures it is about, because the guard added by this very decision reads any sentence of that shape
as a live claim — and an example quoted inside an argument is not one.) (B) is available *because these particular
claims are countable* — the events exist, the findings exist, the decision headings exist, and a list
has a length. **That is the narrow condition, and it is worth stating:** the fix does not generalize
to prose, only to prose that names a number that something else determines.

It found one immediately. The sweep had corrected two of the three "eleven" sites by hand and missed
a third in the 0.4.0 changelog entry; the test failed on it before the commit.

**Consequences / caveats** — the assertions read Markdown with regular expressions, so a reshaped
heading or table makes them fail rather than silently match nothing; each carries a guard that fails
when its pattern finds no candidates at all, because a checker that stops finding anything is the
failure this whole class is about. The en dash the documents use for ranges is a named constant
rather than a literal, since an en dash and a hyphen are indistinguishable in most editors and a
pattern that quietly stopped matching would make these tests pass by finding nothing.

**Two numbers are deliberately not corrected in place.** D16's option (A) still reads "seven
dimensions" and the *Not checked* block keeps its historical entries struck through rather than
deleted: both are records of a state that was true when written, and a record edited to agree with
later decisions stops being a record. The 0.4.0 changelog's "eleven" **is** corrected in place, and
the distinction is the point — that number was never right, so there is no earlier state it was a
faithful record of.

**The rest of the sweep**, none of it interesting individually: the build prompt gains a supersede
banner and loses "eight substitution classes" (it is seven, corrected in the spec at 0.4.0 and never
here) and "eleven unaddressed known weaknesses"; the decision record's header points at *Document
status* instead of restating a number it cannot keep current; the *Not checked* block moves below the
last decision, since sitting between D44 and D45 guaranteed a reader met it before the thirteen
entries superseding parts of it; assumptions 2 and 3 are ticked with their measured outcomes
(assumption 2 was wrong in a way worth keeping — 51 findings, 4.25 per transcript, not ~70);
`severity.py` stops naming `corpus/findings.yaml`, whose *non-existence* is a mechanism (D36), as the
file its loader reads; the W16 and W17 residues record that both were closed at v2, reopened in the
`[context]` block, and closed again at D55; the specification's `private/` requirement and criterion
state the top-level scoping that lived only in a hook comment; `hooks/README.md` gives Case 1 readers
a recipe that works for them, where it had given both audiences the Case 2 one — in a file whose
argument is that an unverified guard is worse than none; and seven British spellings that survived
the conversion at `745d1a6` are converted, five of them in files the conversion missed because it
walked `git ls-files` and they are gitignored.

---

## D59 — Six mechanisms narrower than the claims made for them

**Fork:** An independent audit's §3, all six reproduced before being acted on. Each is a check that
runs, passes, and covers less than the sentence citing it says.

**M1 — the verifier counted its own list.** `tools/verify_phase1.py` printed *"All 21 phase-1
acceptance criteria pass"* using `len(CRITERIA)`. The specification carries **19** `[P1]` criteria;
`CRITERIA` has 21, because it splits the severity criterion in two and adds the interface scanner,
which is not an acceptance criterion in the specification at all. Nothing bound the two, so a
criterion added to the specification and never added to the tool was invisible — and every changelog
entry from 0.5.0 on repeated a number a reader would map onto the document. **Decision:** each entry
carries a `spec_anchor`, a distinctive substring of the criterion it verifies; three tests assert
every `[P1]` line is claimed, every anchor still resolves, and the one unanchored entry is the
declared extra. The closing line now reads *"All 21 checks pass — 20 of them the specification's own
[P1] acceptance criteria."*

**M2 — an assertion that degrades to a warning.** The specification says the severity field list *"is
asserted by `tools/check_spec_interface.py`"*, unconditionally and with a stated reason. In CI the
sibling repository is checked out with `continue-on-error` and a missing one emits a warning while
the build stays green. **Decision:** state the condition in the specification. The alternative is a
harness build that cannot pass without a second repository, which is worse — but the trade-off
belonged in the document making the claim, not only in a workflow comment.

**M3 — the anchor table was narrower than the paragraph above it.** Of Part 1's sixteen positional
references, **three** were anchored. The unanchored thirteen are the true negatives — the rows telling
a future check what it must *not* fire on, where drift is most expensive, because a check calibrated
against the wrong events fires on correct behavior and gets switched off. **Decision:** anchor all
sixteen, and assert *coverage* rather than rows, so a new true negative citing an index has to be
anchored.

**M4 — Part 2's findings ranges had no check.** `F-08…F-12, F-50, F-51` and eleven more rows, correct
today, asserted by nothing, and the notation already perturbed once when a finding split in three.
**Decision:** parse the ranges and compare them to the findings document.

**M5 — the tally was checked for shape, not content.** The disposition test's regex is
`^\|\s*(\d{1,2})\s*\|\s*\*\*.+?\|.+?\|\s*$` — and **whitespace satisfies `.+?`**, so a row
with a blank disposition counted as carrying one. Nothing asserted the tally's counts against its own
item lists, their disjointness, or that their union is exactly 1–35. **Decision:** all four, plus a
disposition vocabulary.

**M6 — a constant nothing read.** `FACT_KINDS` was declared `Final` and referenced nowhere;
`citation_population` derived `"F"` as *not in `SPEECH_KINDS`*, so a ninth event kind would have been
classified `"F"` whether or not anyone added it, and `FACT_KINDS` would have been quietly wrong while
looking authoritative. **Decision:** read both tuples, raise on a kind in neither, and assert the
partition — with a control that both populations are non-empty, since W1 is what happens when the
fact population is empty.

**Why these six together** — they are one shape at six sizes: *the mechanism is real and the sentence
citing it describes a larger one.* That is the same shape as D46 and D57, and the reason to record it
again is the range. It appears in a printed summary line, a CI fallback, a table's coverage, an
absent check, a regex quantifier, and an unused constant. **No single discipline catches all six**,
which is the argument against believing the last audit closed the class.

**Consequences / caveats** — `CRITERIA` now carries an anchor per entry that must be maintained
alongside the specification's wording; the tests fail loudly when one stops matching, which is the
intended cost. The M5 vocabulary is a list of tokens seen today, so a genuinely new disposition kind
will fail until it is added — deliberately, since a disposition nobody declared is the thing being
guarded against.

---

## D60 — The test gaps, and the one that could not be closed by adding a test

**Fork:** The audit's §5, eight items. Most are ordinary absences: a reachable branch with no case.
Two are not, and they are why this entry exists.

**What was added.** `owner`'s vocabulary — the field D43 added, the only closed vocabulary on a
finding with no refusal case, while `detectable_by` and `tier` were both parametrized; plus a test
that the parametrization covers every closed vocabulary the `Finding` type declares, so the list
cannot fall behind the schema again. Eight severity malformations, including a non-numeric `theta`,
which needed a code fix first: `float(row["theta"])` let a `ValueError` escape the `SeverityError`
contract every other branch honors, so a caller catching `SeverityError` caught everything except
the one field whose type decides the ordering. Ten extraction paths — unknown `DisclosureState`
(three of the four closed vocabularies were specified and unproven), duplicate `tool_call_id`,
missing section, duplicate `[call]` key, empty file, empty speech body, two per-kind body grammars,
an empty transcripts directory, and CRLF stripping. The hook's **20-byte threshold**, which had
fixtures at 34 and 15 bytes and no case at the boundary it exists to draw; a 20-byte file passes and
a 21-byte file is refused, and both are now asserted, along with a nested `config/.env` and a commit
staging nothing. `DISCLOSURE` speech is rate-checked, which it was not, though a disclosure is the
utterance where being spoken too fast matters most.

**The empty speech body was not a missing test.** It was a missing rejection: the parser accepted an
utterance with no words, which reaches the citation universe as an empty citable line — the W1 family.
Counted rather than raised, like every other unreadable body.

**The speech-rate control did not call the function it controls.** It compared three fabricated floats
against two module constants, which proves the band excludes 42 and 253 wpm and nothing about
`_rate_wpm`. A bug returning `None` for every utterance would have left the band tests green over an
empty list and the control green over its own literals. It builds events and measures them now.

**And one gap stayed open on purpose.** The self-contradiction check looped over the one-element tuple
`("door_time",)` under a docstring generalizing to "one record holding two values for one field".
Widening it to the nine fields a result *could* echo was the obvious fix, and **it compared nothing
new**: measured, `door_time` yields two comparisons across the corpus and the other eight yield zero,
because no tool result in this corpus echoes them in `field=value` form. Shipping the longer tuple as
though it were coverage would have been this project's own recurring defect, committed while fixing
it. So the tuple stays, the docstring says the reach is `door_time` twice, and a second test measures
the comparisons and fails when they stop happening.

**Consequences / caveats** — the leakage scan now reads the findings document, its generated view and
the review worksheet, which the acceptance criterion had described as repository-wide while they sat
outside it; the three exclusions carry stated reasons and a test refuses a corpus document in neither
list. The ZIP scan's `\b(\d{5})\b` is anchored against a preceding hyphen: `EV-88011` presents a
word boundary before its digits, so the pattern would have collected an identifier's tail and called
it a ZIP above 00501 — it passed because no identifier is spoken as bare digits, which is a property
of the corpus and not of the check. The interface scanner's quote-stripping is pinned as a fraction
(2.7% today) rather than fixed, because the rule also does real work.

---

## D61 — A statement about the held-out labels is a label, and prose routes around the guard that holds them

**Fork:** The companion repository's README carried a sentence asserting a property of the held-out set's defect composition, together with the validation-design reasoning behind it. Both are facts about labels that do not yet exist, sitting in the one file in that repository a harness-side session has a legitimate reason to open — it explains the pairing and is reachable from this repository's own links. It was present in `783109e`, the commit that populated the repository. Does it stay?

**Options considered**
- **(A) Remove it, and reproduce neither the claim nor its reasoning here.** Both publish with the labels at phase 5.
- **(B) Keep it.** The transcripts are public, so the composition is discoverable by anyone who reads them; the sentence only saves the reading.
- **(C) Remove it from that README and record it here** — this file being the project's usual home for design rationale.
- **(D) Extend `tools/check_holdout_absence.py` to flag prose asserting label facts.**

**Decision ✅** — **(A)**.

**Why** — (B) confuses secrecy with contamination, and this project was never about secrecy: D2 settled that the held-out set is public from the day it is written. What D2, D19 and D21 protect is a *process* property — that the rubric was not designed against these labels — and that property is damaged by the fact entering the design context, not by the fact being knowable. A reader with the transcripts in front of them forming their own view costs nothing. The repository *asserting* the view, in a file linked from the design side, delivers it to precisely the context the split exists to keep it out of.

(C) is the option that had to be rejected most deliberately, because it is this document's default and it is wrong here. Design rationale lives in this file; **this** rationale is made of the labels it reasons about. Moving the sentence here relocates the exposure from a file a harness session *might* open to the file it certainly opens. The same argument disqualifies restating the claim in weakened or generalized form: a principle recorded here as the reason a sentence was struck from *that* README carries the struck sentence by implicature. So this entry names the class of the claim and stops. What was removed, and why it was true, publish with the plaintext labels at phase 5 — where composition is public regardless and the reasoning becomes explanation rather than a hint.

(D) fails for the reason D37 already gives about its own false-positive half. That scan is *required* to leave alone prose that merely mentions the held-out set, because a check firing on ordinary README text would be switched off within a week and would then protect nothing. A check that must separate *"`CALL-13` exists"* from *"`CALL-13` has property P"* is a check that fires on ordinary prose. The cure is the disease.

**What this actually exposes** — D21 secures property (a) by the labels **not existing** before `rubric-frozen-v1`. That is a guarantee about files, and a good one. D37's scan reads line 1 of every file in this tree and deliberately tolerates prose. Both decisions are correct and **neither one covers a sentence**. The gap is not closable by tightening either check; it is a seam between two mechanisms that are each right about their own half. It also went unnoticed through the population of the companion repository and the audit that followed, which is the argument for recording it rather than quietly editing it.

**Rule** — No statement about the held-out set's labels — their distribution, their composition, or any property of them — appears in either repository before phase 5, in prose or in a file. **Not enforced by test, on purpose**, after considering it: see (D). Enforced by review at label authoring and at any edit to the companion README.

**Consequences / caveats** — The public claim about the held-out set is weaker by one sentence until phase 5, when the published labels replace assertion with evidence. That is a better trade than it first looks: the sentence asked a reader to take the author's word for something the labels will simply show. One related exposure is **not** closed here. `corpus/entities.md` records that a held-out transcript relies on the initial-and-surname rule — narrower, being about format rather than labels, and it shifts no defect prior, but it is a held-out content fact living on the design side and it arrived by the same route this one did. It stays, because the rule it documents is unstated elsewhere and a corpus author needs it. It is named here so the next audit meets it as recorded scope rather than a fresh finding.

---

## D62 — The eight the audit found and the last session did not fix

**Fork:** The independent audit's remaining items sat recorded-but-unfixed, deliberately, on the
grounds that a session four hours deep would do them worse than a fresh one. The user asked for them
closed before starting adjudication, which is the right ordering for a different reason: seven of the
eight are in the parser and the loader, and adjudication is the first activity that reads a large
volume of their output.

**Decision:** all eight, each reproduced again before being touched.

- **P3 — a repeated section marker.** `_sections` assigned `found[marker] = offset` across the whole
  file, so a second `[call]` overwrote the first and everything between them was never read.
  Reproduced: a doubled block parsed cleanly and reported the **second** `call_id`. That is the worst
  shape a silent failure takes — it does not lose a value, it substitutes one. Each marker must now
  appear exactly once, and the refusal names the lines.
- **P10 — the `[call]` timestamps.** All three were stored as raw strings while
  `transcript-format.md` §2 requires UTC ISO-8601 with millisecond precision and a `Z`, and
  `duration_ms` was checked for integrality but not for sign. Both validated; a call can no longer
  report having lasted a negative time. The consequence was not cosmetic:
  `test_header_duration_reconciles_with_the_event_log` calls `datetime.fromisoformat` on those
  strings, so a malformed stamp surfaced as a `ValueError` from inside a hygiene test rather than as
  a named parse failure where the file was read.
- **P5 — `extract()` took two parameters it never used**, and four call sites passed them. Removed,
  and `ARG` added to `[tool.ruff.lint] select` so the class is caught rather than the instance —
  which immediately found two unused imports the previous rule set had not.
- **P6 — `reassembled_body()` was a one-line identity function** whose docstring said it was
  "present so a test can name the invariant it asserts". No test referenced it. Deleted: the
  invariant is `event.body` and the tests assert on it directly, so the function was a docstring
  making a claim about a test that did not exist.
- **P7 — `_event_to_dict` claimed exhaustiveness it did not have.** `mypy --strict` reports match
  exhaustiveness only through `assert_never`, so a ninth `Event` member would have fallen through
  every case and serialized with the seven base fields and none of its own — silently, with the
  artifact hash changing and nothing to explain why.
- **P8 — a condition asking one question twice.** `DetectableBy` is a `StrEnum`, so membership in
  `__members__.values()` and in the value set are the same test; the adjacent `owner` and `tier`
  checks ask it once, which is what made the asymmetry visible.
- **P11 — an entry whose `id` is `""`** was reported as the empty string, which reads as a
  formatting bug rather than as the finding it is. Named by position now, and the message is the
  whole point of `SeverityFieldPresentError`.

**And the improvement that was not just a tidy-up.** `Call` gains `context_source_lines`, aligned
with `context` by position. Every event carries `source_lines`; the context record did not, which
made the `[context]` block **the one part of a transcript whose provenance the canonical model could
not express** — an inconsistency in `event-model.md` §2 rather than a missing convenience. The
practical cost was visible: two tests asserting that block's wrapping rule had re-implemented the
parser, twenty-odd lines of it, to work out how many lines a value spanned. That second
implementation is now deleted.

**Why the content check did not move with it.** `test_a_wrapped_context_value_keeps_every_source_fragment`
still opens the transcript. The *span* is a fact about the file and the model may state it; whether
every fragment survived reassembly is a fact about the parser, and asking the parser is the W19
mistake. A third test asserts the model's spans against the source, because **adding a field to the
model does not make its values true.**

**Consequences / caveats** — `extract()`'s signature changed, which is a breaking change to a public
function; phase 1 is the only caller and the four sites moved with it. The `[call]` timestamp
validation is a format tightening: a transcript with a second-precision stamp parsed before and
aborts now. Nothing in either corpus is affected — 297 tests, and the extraction artifact's content
hash is unchanged.

---

## D63 — Phase 1 closes twice, and the tags say so

**Fork:** `064fb15` closed phase 1 on 2026-08-28. Everything after it — format v2, two rounds of
human review of the corpus, an independent audit of both repositories, and D39–D62 — reopened the
format, the corpus, the findings, eleven mechanisms and the parser. The phase was closed and the
close was no longer true of anything. Nothing recorded that, and **no tag existed at all**, so a
reader had no way to ask where the phase stood except by reading sixty decisions.

**Options considered.** (A) Tag the current commit `phase-1-closed` and leave the first close in its
commit message. (B) Tag both: `phase-1-closed-v1` retroactively on `064fb15`, `phase-1-closed-v2`
here. (C) Avoid the word *closed*, since two human steps remain, and tag `phase-1-verified-v2`.

**Decision: (B)**, with the tag message stating what is outstanding.

**Why** — (A) hides the interesting fact. That a phase closed, reopened for a day, and closed again
is not an embarrassment to be tidied into prose; it is the strongest single piece of evidence that
the review and audit steps did something, and `git tag -l` is where someone looks first. (C)
understates it. The phase's own *Done when* is **"its tagged acceptance criteria pass, and every
design transcript parses with a zero unparsed-line count"** — both are true, verified by running
rather than by reading, so refusing the word *closed* would be inventing a stricter bar than the
specification sets.

**What the tag claims, and what it does not.** It claims the Done-when. It names two outstanding
items rather than implying they are done:

- **The 51 candidate findings are unadjudicated** and `corpus/findings.yaml` — the gold set — does
  not exist. D10 makes that the human's, and D36 makes its non-existence the mechanism: a
  model-generated gold set would make judge-versus-human agreement measure a model against itself.
  *(Fifty-one is what the tag claimed on 2026-08-29 and is left as it was. Both halves are now
  false — the corpus carries 86 and all of them are adjudicated — which is what the tag being a
  record of a moment means. A count-synchronizing edit rewrote this to 86 and a test enforced it,
  because the test scanned the whole document rather than its present tense; both are corrected.)*
- **The design-set findings have not been scored.** Phase 1 names this a *"prerequisite (outside
  this spec)"*, and it is **structurally circular**: scoring needs the corpus, and the corpus is
  phase 1's own first deliverable. That circularity is in the specification rather than in the work,
  and naming it in the tag is cheaper than a reader re-deriving it.

**Consequences / caveats** — a retroactive tag on `064fb15` asserts something about a commit made a
day earlier, which is exactly the shape D26 refuses for held-out ordering. It is acceptable here for
a reason that does not generalize: **this tag is navigational and secures no property.** Nothing
cites it, no claim depends on its ordering, and the commit it names says in its own message that it
closed the phase. `rubric-frozen-v1` is the opposite case — it is load-bearing for property (a), it
must be created at the moment it claims, and it must never be applied retroactively.

If phase 1 reopens again, the next tag is `-v3`. A phase that closes three times is worth being able
to see.

---

## D64 — Every value the agent passes to a tool must have a source in the call

**Fork:** While adjudicating CALL-02, a human review asked what set `clause="2.2"` in
`fetch_policy(document="refund.v1", clause="2.2")` — nothing in the transcript produces it — and
generalized the question: *"How many other instances are there in call transcripts where the data
just appears as if from thin air? There should be no such instances."*

Auditing all eighty tool-call arguments across the 12 design transcripts then in the corpus against every source
available at the moment of the call — context, call record, prior speech, prior event bodies,
arithmetic over context values — found **thirteen with no origin**. Twelve were `fetch_policy`
arguments (D65). The thirteenth was `check_availability(event="EV-44901")` in CALL-09, used again at
two later events: the exchange target the whole call turns on, with no `find_performance` and only
`EV-44803` in context.

**Options considered.** (A) Repair the transcripts so every value has a source, and enforce it.
(B) Add a finding for the unresolved identifier and leave the transcript as authored. (C) Record the
gap in the seeding manifest and leave both alone.

**Decision: (A).** CALL-09 gains a `find_performance` call keyed on the production, venue and the
date the caller asked for, whose result supplies `EV-44901` — the shape CALL-01 already models.

**Why** — (B) is the tempting one and it inverts the problem. A corpus where values appear when
convenient cannot support findings *about grounding*, because it is then modelling an agent with
knowledge no real agent would have; turning that into a finding would make the corpus's own defect
the thing under test. The reviewer's framing is the argument: *"else the call transcripts will look
like a convenient fairytale."*

(C) fails on this project's own standard. The seeding manifest described CALL-09 as **"every step
correct, the order wrong"** — a claim an unresolved identifier flatly contradicts. Two authored
documents disagreeing with nothing comparing them is the shape D46 and D50 keep finding.

**What the repair cost, and what caught it.** Inserting a call-and-result pair before the premature
announcement — before, so that "the June date" in the agent's speech also has a source — renumbered
every later event by two, shifted their timestamps by 2000 ms, renumbered four tool-call ids, and
moved `duration_ms` and `ended_at`. **Nothing was found by reading.** The manifest's anchor table
named six drifted rows, the findings-evidence check named thirteen, and the document-count check
caught 285 events against 287. Every one failed loudly. F-33's seeded defect is untouched: a read is
neither an exchange tool nor an availability check, so the announcement still precedes both.

**Consequences / caveats** — one exception is declared rather than skipped: `fetch_policy`'s
`document` argument. A document's *name* is part of the tool's contract the way the tool's own name
is, while a *clause number* presupposes having read the document — which is D65. The exception list
carries its reason and a second test fails if an exception stops being used, because an exception
nobody needs is an exception nobody rechecks.

**Rule** — `tests/test_corpus_hygiene.py::test_no_tool_call_argument_appears_from_nowhere`, with
`test_the_provenance_exceptions_are_all_still_used` binding the exception list. **Observed to bind,
not merely configured**: the pre-repair CALL-09 was planted and the guard named
`check_availability(event='EV-44901')` before passing on the repaired corpus — the standard D52 set
by planting nine copies rather than reading the diff.

---

## D65 — Policy retrieval returns a document; the POLICY event names the clause applied

**Fork:** `fetch_policy(document, clause)` required the agent to name the clause it wanted. A human
review put the objection plainly: *"before that tool call to fetch para 2.2, there should be a tool
call to fetch the entire refund policy and after the policy is read and analyzed, it is determined
that para 2.2 is the correct thing to use."* The signature can only be called correctly by an agent
that already holds the knowledge it is retrieving — knowing `refund.v1 § 3.2` is the settlement rule
presupposes having read `refund.v1` — so it cannot be used to discover a rule the caller does not
know exists. Twelve of D64's thirteen unsourced arguments were this tool's.

**Options considered.** (A) Whole document; the agent selects the clause and the `POLICY` event
records which one it applied. (B) Two-step search-then-fetch, the RAG shape. (C) Keep the
clause-addressed call and add a preceding index call so the clause number has a source. (D) Policy
carried in context from the start, with no retrieval call at all.

**Decision: (A).**

**Why** — the criterion that decided it is **what defects become expressible**, since carrying
defects is what the corpus is for. Clause-addressed retrieval can only express *nothing was
retrieved*, which cannot separate an agent that guessed correctly from one that guessed wrongly.
Whole-document retrieval expresses something strictly better: **a clause governing the question was
inside the returned document and the agent applied a different one, or none.** CALL-02 is the worked
example — `refund.v1 § 2.4` states the booking fee is non-refundable *"including where a full refund
of the ticket price is due"*, it is among the fourteen clauses returned at event 12, and the agent
promised the fee back anyway. Grounded and still wrong beats ungrounded.

(B) is the realistic answer for a large knowledge base and a fiction at three documents of forty-odd
lines; a retrieval index over `refund.v1`, `transfer.v1` and `exchange.v1` would be over-building in
the opposite direction from the defect it fixes. (C) is the smallest edit and leaves the tool's
signature stating that the caller knows where the answer lives. (D) is arguably the most realistic of
all — production agents often carry a small policy set in the system prompt — and it is the worst
here: every claim becomes nominally grounded, the `POLICY` event loses its purpose, and the corpus
loses the grounded-versus-ungrounded distinction entirely.

**Consequences / caveats** — two findings were re-cut because the change falsified their premise,
and both got sharper. F-09 moves from "no retrieval supported the fee claim" to "§ 2.4 was returned
and its negation was spoken". F-50 moves from "no clause was retrieved" to "the only POLICY event
cites § 2.2 while the question was about timing" — which **strengthens D49 rather than reversing
it**: its argument for keeping F-50 distinct from F-10 was that the defect is an assertion over the
event stream, and it still is, over the same stream, more sharply. The seeding manifest's CALL-02
true negative said *"F-50 is that the agent did not ask"*, which this falsifies; it now reads that
the agent did not apply the clause it had been handed.

Clause correspondence (D32, D50) is untouched. A `POLICY` event still cites exactly one clause and
quotes it, and the quotation must still equal that clause under whitespace normalization. Widening
retrieval did not widen what a quotation may say.

The change reaches the held-out set and nothing in this repository can see it. Recorded as O-2 in
`HOLDOUT-OBLIGATIONS.md`, which exists because of this decision.

**Rule** — `specs/event-model.md` § 3.5 states the convention and the three-event shape.
D64's provenance test enforces the absence of the clause argument, since a reinstated
`clause="2.2"` has no source and fails. The result line's clause count is checkable against
`corpus/policies/`; that check is **now written** —
`test_every_policy_retrieval_states_the_document_s_real_clause_count`. It was recorded here as
owed and stayed owed for one session, during which `specs/event-model.md` § 3.5 described it as
already existing. An independent sweep found the two documents disagreeing — D46's own shape,
caught one level up.

---

## D66 — Eight findings for error classes the taxonomy does not enumerate

**Fork:** Adjudication surfaced a question the corpus could not answer about itself: *"are there
error types whose nature our generated call transcripts do not cover, ever?"* Auditing the 12
design transcripts against a broader inventory of voice-agent failure modes found five classes with
no instance anywhere in the corpus, and none of them is among the twelve recorded taxonomy gaps —
they are outside the 35-item taxonomy altogether. What is seeded, and how is the taxonomy's silence
recorded?

**Options considered.** (A) Seed the classes and record that the taxonomy does not enumerate them.
(B) Extend the 35-item taxonomy to 40 and seed against the extension. (C) Record the five as known
absences and seed nothing.

**Decision: (A).** Eight findings across four calls, and the taxonomy is left at 35 with the gap
stated rather than closed.

**Why** — (B) is the tempting one and it changes what the taxonomy *is*. The 35 items are an
inherited analysis with a recorded provenance; renumbering them to 40 would make later readers
believe five items came from that analysis when they came from this corpus. An inventory whose
membership silently grows cannot be cited. (C) leaves the corpus unable to demonstrate classes it
has now been shown to lack, which is the opposite of what the audit was for.

**What was seeded, and what each demonstrates:**

- **Retry against a hard refusal (F-53, agent) and no deduplication on a timed-out write (F-54,
  platform, question).** CALL-05 already called `issue_refund` three times with identical
  arguments and no idempotency key; the corpus simply had no finding saying so. `timeout` means no
  response arrived, not that the write did not happen — so the one status that most needs a
  deduplication key is the one retried without it. **No transcript change was required**, which is
  the uncomfortable part: the defect had been sitting in an authored call through two review rounds
  and an audit.
- **Injection arriving in retrieved data (F-55, data).** CALL-06 and CALL-07 carry injection in
  *caller speech*, which an evaluator can be told to distrust wholesale. CALL-08's event record now
  carries a note addressed to an automated reviewer — the channel an evaluator must trust to
  establish what happened at all. The agent ignores it, which is a true negative rather than an
  absence of defect. **It has no clean control twin**, so it demonstrates the vector without
  supporting D7's same-verdict comparison; that limit is recorded rather than implied.
- **Authentication factor strength (F-56, platform, human, question).** Every call but CALL-18 selects
  its account on `matched_by := caller_ani` and challenges one caller-supplied ZIP. *(Corrected
  2026-09-02: this read "every call" and was wrong when written — the same sweep that added
  F-56 added CALL-18, which matches on a booking reference. An audit caught the sentence in the
  finding itself as G3 and did not catch this copy of it.)* On that basis
  CALL-03 performs a transfer `transfer.v1 § 1.1` says Verso cannot reverse. No finding had ever
  mentioned ANI, and the seeding manifest called those calls a true negative that "verify properly"
  — wording that would have scored a check reporting factor strength as *wrong*. The manifest now
  claims only that the flow was executed.
- **AI-status disclosure, configured and never delivered (F-57, platform) and not answered when
  asked (F-58, agent, judge).** The context carries `disclosure_ai_status`; no `ai_status` event
  exists. The caller asks outright at the point the repetition makes them wonder, and the agent
  answers a different question. Deflection rather than denial was chosen deliberately: a flat denial
  contradicts the call record and is assertable, where deflection is what deployed systems do and is
  why the judged tier exists.
- **Success at the API boundary (F-59, data, human, question) and the resend that ignores it
  (F-60, agent, judge).** CALL-12's caller was already ringing because a confirmation never
  arrived; the booking record now says one was sent. *(F-59 was later re-homed to CALL-11, the
  call where a confirmation actually sends and the record still cannot say whether it arrived —
  the row says so itself. Recorded here rather than silently rewritten.)* Nothing in the schema separates *accepted by
  the sending service* from *received*. F-59 is a question by construction — the caller's word is
  the only evidence against the record, and a corpus treating a caller assertion as an oracle would
  teach a detector to trust speech over the log.

**Consequences / caveats** — the corpus goes to 60 findings, 53 defects and 7 questions. Five of
the nine are `question` or `human`, which is a higher proportion than the corpus carried before and
is the honest consequence of seeding classes whose defects are architectural rather than behavioral.

**The taxonomy-coverage mapping for these five classes is owed, not done**, and is recorded that way
rather than claimed: `specs/taxonomy-coverage.md` still describes 35 items with 12 recorded gaps and
does not mention idempotency, retrieved-data injection, factor strength, AI-status disclosure or
delivery state. D46's rule applies to this entry as much as to any other — a document that says a
mapping exists is making a claim, and this one does not exist yet.

**Rule** — `tests/test_corpus_hygiene.py::test_no_tool_call_argument_appears_from_nowhere` covers
the transcript edits, and `test_every_judged_taxonomy_item_has_a_judge_finding` binds the judged
dimensions. Binding every finding to a taxonomy item is **not** enforced and would fail today by
construction, since five classes have no item to bind to. Stated here so the absence is deliberate.

---

## D67 — Four judged rows each carried an assertion, and the habit was in the drafting

**Fork:** Adjudicating CALL-04, CALL-05 and CALL-08 split four findings that had been drafted
`judge` while resting on a comparison D42 calls an assertion — F-19 against `resale_eligible`, F-20
against a declared-and-uncalled tool, F-23 against a remedy the platform returned in the refusal
itself, F-32 against a `malformed` result naming a conflict. Four in one pass is a habit rather than
four slips. Is the remedy per row, or is there something to record?

**Options considered.** (A) Record the pattern, name the rows, state the remedy. (B) Leave the
reasoning in the eight per-row adjudication notes, where it already sits. (C) Record it *and* amend
D42's wording so a future drafting round cannot repeat it.

**Decision: (A)**, with D42's wording left alone.

**Why** — the four share one shape. Each states a **conclusion** that needs judgment, resting on an
**observation** that does not, and classifies the whole row by the conclusion. That is D42's rule
read one level too coarsely: the rule sorts *claims*, and a row can carry two of them.

(B) leaves the pattern recoverable only by reading eight notes, and the pattern is the more useful
artifact — it tells a reader of the finished gold set why the asserted tier is larger than the drafts
implied, and it is the kind of thing that would otherwise be rediscovered by the next person to draft
findings for this corpus.

(C) is the tempting overcorrection. D42's rule is not wrong, and rewording it to say "split rows
carrying both" would turn a classification rule into a drafting instruction. What was missing was
never a rule; it was the habit of asking of every judged row **what part of it a check could already
do**.

**Consequences / caveats** — four rows became eight: F-19/F-61, F-20/F-62, F-23/F-63, F-32/F-64. The
corpus now classifies 41 `assert`, 18 `judge` and 5 `human` across 64 findings.

**The judged tier lost nothing.** Every split kept its judged half, and each surviving half sits on a
dimension D42 names: whether a reply answered what was asked (F-19, F-20), whether a conversation
addressed the caller's concern at all (F-23), whether the agent's confidence exceeded its data
sources (F-32). So the split raised the asserted tier's coverage **without** weakening the argument
for spending a model call, which is the outcome that makes it worth doing rather than merely tidy.

Worth stating plainly because the arithmetic invites the opposite reading: a corpus that moves rows
from `judge` to `assert` looks like a corpus discovering it needs a model less. What happened is
narrower — it needed a model for fewer *claims*, and the claims it still needs one for are sharper
than they were when they arrived bundled with something checkable.

**Five more splits followed this entry and are recorded here rather than left to a reader to
reconstruct.** D67 was written after four; applying its test to the remaining calls produced
F-35/F-65, F-38/F-66, F-39/F-67, F-42/F-68, F-43/F-69 and F-44/F-70. Nine splits in total, and
the two that were argued hardest are worth naming: F-66, because its assertion is a shape
nothing else in the corpus carries — a value that *was* spoken and could not support what was
asked of it — and F-39/F-67, which was leaned against and then split for consistency, on the
grounds that a reader finding four rows split and two comparable ones whole has to reconstruct
why. An independent sweep found F-65, F-67, F-68, F-69 and F-70 named in no specification
document at all; this paragraph is that omission closed.

**Rule** — **judgment, not checkable.** No test can decide whether a row's conclusion requires a
model; that is the classification D10 reserves for a human and the reason this project exists. What
*is* checked is narrower and already exists: `test_every_judged_taxonomy_item_has_a_judge_finding`
binds the judged dimensions the specification names by number to the findings that instantiate them,
so a split that emptied one would fail rather than pass quietly — which is exactly how the taxonomy
31 gap was found.

---

## D68 — The corpus grows to 14 design calls, and stopping gets a rule

**Fork:** D4 fixed the corpus at 12 design transcripts and 5 held out. A systematic sweep of 141
catalogd voice-agent error types against all 70 findings found roughly 45 already expressed, about
25 structurally inapplicable, and **~40 the corpus could not express** — several of them in clusters
that could not be crowded into existing calls without making those calls implausible. Density had
already risen from 0.18 findings per event to 0.24, with CALL-12 at 0.50. Does the corpus grow, and
if it does, what stops it?

**Options considered.** (A) Hold at twelve and record the uncovered classes as gaps. (B) Grow, and
state a stopping rule. (C) Grow without one.

**Decision: (B).** Two calls added — **CALL-18** (a caller who is not the account holder, helped too
much) and **CALL-19** (a rescheduled event, a date read out of the wrong day) — with a rule for when
the corpus stops.

**Why** — (A) was the working position until the sweep put a number on what it cost. Five types in
the security family are inexpressible in this corpus *at all*: no call carries a caller who is not
the account holder, and without one, payment data volunteered, an internal field read aloud, and an
agent narrating its own bypass have nowhere to happen. Crowding them into an existing call means a
caller who is simultaneously verified and not, which is not a defect a corpus can seed — it is a
corpus that contradicts itself.

(C) is how a corpus becomes a catalog, and density is the measurement that decides it. At 0.18 the
calls read as calls. CALL-12 at 0.50 reads as a list of things that went wrong, and a transcript
whose every other event is a defect has stopped being the artifact the corpus exists to provide.

**The stopping rule.** A class earns a seeding only if **all three** hold:

1. the corpus cannot currently express it;
2. it contributes a **detection shape the corpus lacks**, rather than a further instance of one it
   already has;
3. it fits a call at or below **0.35 findings per event**, or justifies a new call on its own.

Test 2 is the one that does the work, and it came out of the split analysis rather than from
principle: five splits produced only two shapes between them, and the sixth was worth making solely
because F-66 asserted something nothing else did. Without that test, "consistency" argues for
splitting every judged row and the corpus grows without covering more ground.

**Consequences / caveats** — the design set is `CALL-01`…`CALL-12`, `CALL-18`, `CALL-19`. The
held-out range 13–17 is **skipped rather than reused**, so the two sets never collide and the gap in
the numbering points at the companion repository. Five sites hard-coded twelve: two tests now key on
`corpus/DESIGN_SET`, one on the transcripts directory, the manifest-rows check on the declaration,
and the phase-1 verifier's prose was corrected.

Totals move to **14 design calls, 335 events, 86 findings**, from 12 / 285 / 51 at the start of the
adjudication session.

**The ratio D4 chose changes and the held-out set does not grow.** Fourteen design to five held out,
rather than twelve to five, and the five carry none of the classes added since. That is recorded as
O-3 in `HOLDOUT-OBLIGATIONS.md` rather than resolved here: whether the held-out set should carry the
new classes is a decision that needs a session which can read it, and this one deliberately cannot.

**Rule** — `tests/test_document_counts.py::test_the_transcript_count_is_the_declared_design_set`
binds the declaration to the directory, and
`tests/test_corpus_hygiene.py::test_the_manifest_findings_ranges_match_the_findings_document` binds
the manifest's per-call rows to `DESIGN_SET`, so adding a transcript without declaring and
describing it fails. The stopping rule itself is **judgment, not checkable**: no test decides whether
a class contributes a new detection shape, and the density figure is a guideline a reader can
recompute rather than a gate.

---

## D69 — An independent sweep reads the gold set, and three of its items do not survive contact

**Fork:** The gold set was generated, the suite was green, and D38's argument predicts exactly that —
a process that collects agreement will report agreement. A separate session with no history in this
one was given the repository and asked to sweep the gold-set work. It returned **24 items** across
five severity labels. Fixing what a sweep reports is not the same as being right about it, and a
sweep is a model too.

**Options considered.** (A) Fix everything reported, in the order reported. (B) Reproduce each item
first, fix what survives, record what does not. (C) Triage by the severity labels the report
assigned.

**Decision: (B) then (A)** — every item reproduced before anything was changed, the assessment put
to the user, and the confirmed set then fixed in the report's own order rather than in severity
order.

**Why** — the report's order groups items by the file they touch, which is the order that minimizes
half-finished states between fixes. Severity order (C) would have interleaved edits to the same
files. And (A) alone was not available: **three of the twenty-four did not survive reproduction as
stated.**

- **M2** was reported as a structurally unreachable branch. It is reachable. What is true is
  narrower: no change *to the corpus* reaches it. The branch stays, and so does the narrower claim.
  *(**That narrowing is itself wrong**, found by the sweep of 2026-09-02. Declaring
  `internal_note` in a second call's context **is** a change to the corpus and does reach the
  branch — the probe set is built from context fields. The accurate statement is that no change
  to **speech alone** reaches it; the context declaration has to move too. Nothing downstream
  depends on it, and the sentence is left standing with its correction attached rather than
  rewritten, because D69's own argument is that reproducing before fixing is what keeps the
  record honest — and a record that quietly becomes right is not one.)*
- **G4** hedged itself, and was right to.
- **B3** was reported as two defects and is one. The `KeyError` is real; the split-test failure
  traveling with it is ordinary prose staleness — a different defect with a different fix, and
  merging the two would have buried the second under the first.

**The three that mattered most were not the ones labeled most severe.**

**G3 — a false sentence inside the gold set.** F-56 said every call in the corpus selects its account
the same way. CALL-18 does not; it matches on a booking reference. **This session wrote CALL-18,
noticed the collision while designing it, and dropped the thread.** Nothing caught it afterwards
because every evidence check binds a finding to its own transcript, and this claim is about the
corpus. A cross-call citation form now exists and is read.

**G5 was larger than the report knew.** It measured *evidence fragments*, and found none carrying an
internal newline — which is true. The live case was one field across: **38 consequences** carried
paragraph breaks that `_fold` flattened on every generation, silently, and the gold set had been
generated that way from the first run.

**The `reject` path had never been executed.** Zero of 86 rulings reject — which D38 predicts, and
which the open-questions list already records. The sweep simulated one, and it broke two tests.

**Consequences / caveats** — the sweep read this repository and not the held-out set, so its
coverage claims stop at the design corpus. It is one session's reading and not a second person's:
D10's separation is untouched, and **the gold set still has one author and no independent human
reader.** Two of the twenty-four were about documents claiming to be machine-checked, which is D46
arriving for the third time in this project and the second time in this session.

**Rule** — the items that were about checkable properties each left a test behind; the two that
carried decisions are recorded in D70, and the remainder are struck through in
`specs/error-type-sweep.md`'s owed list as they close. **Reproducing before fixing is judgment, not
checkable** — nothing decides whether a reported defect is real except doing the work.

---

## D70 — CALL-12 gets longer rather than an exemption, and the density figure becomes a gate

**Fork:** D68 capped a call at 0.35 findings per event. CALL-12 sat at **0.500** — and CALL-12 is
the call whose density produced the rule in the first place. A rule whose only failing case is also
its only exception is not a rule.

**Options considered.** (A) Exempt CALL-12 and record why. (B) Move or drop findings until it fits.
(C) Lengthen the call.

**Decision: (C)** — twelve events, six declared true negatives, **0.500 → 0.342**, and no finding
changes home.

**Why** — (A) was rejected on the user's instruction that consistency is the goal and an exemption
works against it. (B) was measured rather than assumed: **eleven of the thirteen findings are
scenario-bound**, about this call's particular defects with nowhere else to be, so (B) means
deleting coverage to satisfy an arithmetic.

(C) had a second reason, and it is the better one. The added turns are not padding — **each is the
correct counterpart of a defect the corpus seeds elsewhere**, so the edit that fixes the density also
closes part of the thin true-negative balance both the sweep and the adjudication flagged. The
corpus's worst call now demonstrates six things done right, which is where true negatives belong:
scattered, rather than collected in the good calls.

| added | what is correct about it | the defect it constrains |
|---|---|---|
| events 7–8 | a reference from speech, read back before it is used | F-13 |
| events 16–17 | a recorded charge stated as the record has it | F-08 |
| events 18–19 | says what it is about to do, and waits | F-15 |
| events 26–27 | a degrading line answered with a route that keeps the caller | F-23 |
| events 30–31 | a figure it does not have, declined rather than invented | F-10, F-85 |
| events 35–36 | a repeat the caller asked for, given without friction | F-44, F-70 |

**Placement was constrained, and that is the part worth recording.** F-69 asserts a booking reference
was supplied and consumed with nothing in between that lost it. F-70 asserts *no event of any kind*
separates a confirmation from its repeat. Both are assertions about **absence** — and an absence is
the one thing a lengthening can destroy without contradicting a single quoted line. Every insertion
point was chosen against those two spans before any text was written.

**Consequences / caveats** — twelve events renumber twenty of CALL-12's, moving **55 event citations**
across the drafts and the ledger, **five anchor rows**, **four prose references** inside the manifest's
own Part 1 rows, and **one citation from another call**. That last was found by the cross-call check
written for G3 the same day, on its first real use: the shift script keyed on each finding's own
`call_ref` and so never looked at the CALL-18 row that cites CALL-12. Twelve new anchor rows were
added, six of which existed only because Part 1 ranges are anchored at **both** ends.

**F-48's final-event figure moved a third time**, and the ledger note claiming it was machine-checked
was wrong: the span form is read, that fragment is not a span, and "the call-record and span forms
are read" was doing work the word "and" cannot do. `_FINAL_EVENT` now reads it. The wrong claim is
left standing in the note rather than edited, per D53 — a note that quietly becomes true is not a
record of anything.

**D68's density figure stops being a guideline.** That entry recorded the stopping rule as judgment
throughout, and called the figure "a guideline a reader can recompute rather than a gate". Tests 1
and 2 of that rule are judgment and stay so. Test 3 is a ratio over two counts, which is exactly
D63's narrow condition for a number that gets checked — and the corpus spent an entire adjudication
session at 0.500 with nothing to say so. **That clause is superseded here rather than rewritten
there.**

Totals move to **14 design calls, 347 events, 86 findings**. The held-out set is unchanged and O-3
in `HOLDOUT-OBLIGATIONS.md` grows by twelve events it cannot see.

**Rule** — `tests/test_corpus_hygiene.py::test_no_call_carries_more_findings_than_its_length_allows`
reads the gold set against the transcripts and names any call over the ceiling with its arithmetic;
it was planted at 0.30, observed to name four calls, and restored. The `_FINAL_EVENT` branch in
`tests/test_findings_evidence.py` holds F-48's figure and was observed to fire on the stale one.
`test_every_part_one_reference_is_anchored` binds each new true negative to its events at both ends,
and caught six missing anchors here. **Which turns count as correct behavior is judgment, not
checkable**: no test decides that events 30–31 are a model answer rather than an evasion.

---

## D71 — A sweep the version bump would otherwise have claimed, and what reading found that running did not

**Fork:** Adding a changelog entry for D69–D70 moved the spec version, and
`test_the_spec_version_and_the_last_sweep_agree_with_the_changelog` binds `Last swept` to it. So a
version bump *claims a documentation sweep*, and two decisions is well short of the trigger the
marker itself states (~8–10 accrued decisions, before publishing, or at phase completion). Either
the claim goes in unearned, or the entry does not go in, or the sweep actually happens.

**Options considered.** (A) Bump both and inherit the precedent — 0.19.0 was corpus work and moved
the marker the same way. (B) Leave the spec at 0.19.0 so D69–D70 live only in the decision record.
(C) Sweep, then bump.

**Decision: (C)**, on the user's instruction, with the added requirement that the sweep verify the
checks themselves rather than only the prose.

**Why** — (A) is what the previous round did, and reading it back is what exposed the problem: the
marker had moved to `0.19.0 @ D68` while the decision record's own copy said `0.22.0 @ D68`, a
version this project has never been at. `git log -S` finds it in no commit. It was a typo made while
moving the other two markers, and it survived a full suite, a phase-1 verifier run and an
independent sweep, because **nothing read the third marker**. That is (A)'s failure mode in one
artifact: a marker moved by hand each round, checked by nobody.

(B) keeps the trigger rule intact and costs the changelog a round. It was the safe option and the
wrong one, because the round it would have omitted is the round that found the typo.

### What the sweep found by reading

**Nine live statements still said the design set was 12 calls.** D68 moved every count that had
a test behind it and left every count that did not — the outcome statement, the in-scope bullet, the
*prior decisions* line, a performance requirement, an acceptance criterion, the phase-1 floor, a
derived judged-call total (840, from 12 × 6 × 10 plus synthesis — now **980**), and two in the
scenario map.

**A count that had already been "corrected" twice was still wrong in a third place.** The
substitution classes are seven. The acceptance criterion said eight and was fixed at 0.4.0; the
build prompt said eight and was fixed at D58, whose own text records it as "corrected in the spec at
0.4.0". *Prior decisions* said **"eight entity classes"** the whole time. Two sweeps each fixed the
site in front of them and each recorded the fix as done.

**Assumption 2's discharge had gone stale in the direction that flatters it.** It read: 51 findings
across 12 calls, 4.25 per transcript against an assumed ~6, budget ~255. The corpus is now 86
across fourteen — **6.14 per transcript**, and a budget of ~430. The original estimate was closer
than the discharge that corrected it. Appended rather than rewritten, so all three counts stand.

**Two taxonomy documents describe a design set that has since grown, and neither said so.** Neither
mentions CALL-18 or CALL-19 anywhere. They are **scoped rather than remapped**, for D66's reason:
the 35-item taxonomy does not enumerate the classes those calls carry, and renumbering it to absorb
them would misrepresent where they came from.

### What the sweep found by running

**No test in the suite is vacuous, and eleven needed checking to know it.** A static pass found zero
tests with no assertion and zero tautologies, and eleven whose every assertion sits inside a `for` —
which passes when the iterable is empty. Each was counted at runtime through a trace hook rather
than reasoned about, because reasoning about exactly this is what produced a green-and-blind guard
earlier in the same session. All eleven run; the smallest fires once and the largest 694 times.

**A planted mutation renaming the ticketing platform in one transcript was caught by nothing.** The
register check reads context variables, tool names, disclosure names, outcomes and reason codes —
substitution **Class 6**, the machine tokens, which reach the parser as fields. **Class 1** —
company, brand, venue and production names — lives in free speech, where an undeclared name looks
like every other capitalized word, and no check had ever looked at it. This is the register's own
asymmetry note (a name declared and never used versus a name used and never declared) turning out to
apply to a whole class rather than to individual entries.

**Consequences / caveats** — the marker is now earned rather than asserted, and `Last swept` reads
`0.20.0 @ D71`. The design-set size and the substitution-class count join the judged-dimension count
as prose numbers with a guard behind them, and both guards scan **number words** while historical
counts stay digits — the convention the dimension guard states in its own docstring, which is also
why four historical uses of "twelve" were rewritten as "12" rather than exempted.

**Class 1 is only half-closed, and the half that is closed is stated as such.** The platform is named
in every call and that is now asserted; every production and venue reaching a record through
an `event="X at Y"` field is asserted declared. What is **not** asserted is that no undeclared brand
appears in speech, which is not enumerable from a transcript. A guard narrower than its rule is the
failure this project keeps finding, so the narrowness is written into the test rather than left for a
reader to discover.

**Rule** — `test_every_worded_design_set_size_agrees_with_the_declaration` reads `corpus/DESIGN_SET`
and names any document stating a different size;
`test_the_substitution_class_count_agrees_across_every_document` counts the enumeration in
`constraints` and names any document disagreeing;
`test_the_not_checked_marker_agrees_with_the_spec_version` binds the third version marker to the
other two; `test_every_call_names_the_declared_platform` and
`test_every_production_and_venue_in_a_record_is_declared` close the Class 1 half that is enumerable.
Each was planted against and observed to fire before being kept. **Whether a sweep was thorough is
judgment, not checkable**: no test decides that a document was read rather than skimmed, and this
entry is a claim about that, like any other.

---

## D72 — Three owed debts closed, and one of them by narrowing the claim rather than satisfying it

**Fork:** `specs/error-type-sweep.md` carried three debts, each recorded with the words *owed, not
done*. Two were work. The third asked for **a corpus row that uses the multi-line evidence format
D22 chose YAML to carry**, and there is no natural one: every quotable source in this corpus — event
bodies, context values, policy clauses — is prose that wraps, so a line break in a quote of any of
them is presentation rather than content, and `>-` is the correct marker for it. A search of all
three policy documents found no clause with internal structure at all.

**Options considered.** (A) Author a finding whose evidence needs the format. (B) Put structure into
a policy document so a quote of it would need the format. (C) Narrow D22's justification to the
parts that are exercised, and say which part is not.

**Decision: (C).** And the two that were work: `specs/taxonomy-coverage.md` gains **Part 2b**, and
the unused vocabulary tokens are **classified rather than exempted**.

**Why (A) and (B) are both worse than an unexercised format.** (A) means inventing a finding, and
findings are adjudicated by a human — D10 is the whole reason this project's gold set is worth
anything, and a row authored to make a sentence in a specification true is the exact inversion of it.
(B) is worse still: it would edit the corpus's *ground truth* to suit a format decision.

**What D22 actually claimed, and how the three parts have aged.** The justification had three legs:

1. **`evidence` is a list**, so fragments from different points in a call stay visibly separate.
   Exercised by every row in the gold set.
2. **Block scalars carry text whose line breaks are content.** Exercised by **dozens of `consequence`
   fields** — and it took an independent sweep to find that `make_gold_set._fold()` had been
   flattening every one of them on every generation since the first. That sweep looked in `evidence`,
   found nothing, and was one field away from the live case.
3. **`evidence` holds verbatim multi-line quotes.** **Nothing carries this, and probably nothing
   will.** It is also the leg quoted in the spec's own in-scope bullet.

Legs 1 and 2 carry the format on their own. Saying so is more useful than a row authored to make leg
3 true, and it leaves the next author a real question rather than a satisfied checkbox.

**Part 2b, and why it is not ten more rows.** The sweep's ten classes are `S1`–`S10`, with their own
tally. Renumbering the inherited 35-item taxonomy to absorb them would quietly change what "taxonomy
17" means in five other files. Every class is seeded and **none has a check** — which is not peculiar
to them: phase 1 builds no Tier A checks at all, so the disposition column records what a check would
have to be. Adding the section immediately broke the Part 2 tally test, which had been reading `S1,
S6, S7, S8` as taxonomy items 1, 6, 7 and 8 and reporting them double-counted; the parser is now
scoped to the tally it is about, and the new tally has a guard of its own.

**Classified, not exempted.** "State the exemption" had produced a sentence saying the exemption was
stated, which is not the same thing. Of the ten unused vocabulary tokens, **two are structurally
inapplicable** for reasons already on record — `asr_error` has no audio layer behind it (D40), and
`voicemail_reached` cannot occur in a corpus where every call is inbound. The rest are **candidates
with a named value**, and the sharpest is `DisclosureState.skipped`: it is the value a correct
platform would have recorded in the very call where F-57 reports the opposite, so seeding it would
give that finding its true negative. `DisconnectionReason.transferred` with `Outcome.transferred` is
the strongest single candidate, because escalation to a human is a failure surface the corpus does
not touch at all. **None is seeded here**, because seeding one means authoring findings.

**Consequences / caveats** — the held-out repair also gained a document rather than a repair:
`HOLDOUT-REPAIR-BRIEF.md` states the conforming shapes for O-1 and O-2, the verified clause counts,
the renumbering hazard and the re-check list, and is explicit that it was written by a session that
may not read the five and therefore names rules rather than defects. **All three obligations remain
undischarged**; the brief is what a permitted session needs, not a discharge.

**And the demonstration found a live defect in the gold set.** Asked to show what a multi-line
evidence row would look like, the first thing read was F-70 — which carried **"no event of any kind
falls between events 23 and 18"**. Its own observation says 23 and 24, and the two are adjacent. The
M6 renumbering had remapped `events N to M` and not `events N and M`, so the first index moved and
the second did not, and the fragment reached the drafts, the ledger, the gold set and every generated
view. Nothing read it because it is **prose about an absence** — the one branch of the evidence
checker that returns without checking anything. It is now the branch that checks the most: a claim
that no event falls between two indices asserts they are adjacent, and a claim that no event *of a
named kind* falls between them is a filter over the events that do. Both are computable, and F-86
carried the second shape unchecked as well.

**Rule** — `test_the_findings_format_uses_the_block_scalar_it_was_chosen_for` asserts that leg 2 is
still carried, and that the emitter and the parser agree about which text is multi-line;
`test_the_part_2b_tally_counts_match_its_own_class_lists` binds the new tally to its own class list
and to the classes the section defines. `_GAP_CLAIM` in `tests/test_findings_evidence.py` reads gap claims against the event stream, and was planted against three ways: the original stale index, a genuine gap, and a kind-filtered claim widened past an event of that kind. All were planted against and observed to fire. **Whether leg
3 will ever be exercised is judgment, not checkable** — and deliberately, no test forbids a
multi-line evidence fragment, because the point is that the format is available and unused rather
than unavailable.

---

## D73 — The corpus transfers a call, and a reviewer's model of a handoff corrected the design twice

**Fork:** D72 recorded a transfer-to-human call as the strongest single corpus candidate left and
deliberately did not build it, because seeding a class means authoring findings and findings are
adjudicated by a human (D10). The human said build it. What should it be?

**Options considered.** (A) Leave it recorded. (B) Build the call as drafted. (C) Build it against a
stated model of what a handoff owes, and let the model settle the design.

**Decision: (C).** The model was the reviewer's, and it changed the call twice.

### What the first draft got wrong

**A queue acknowledgement is not a handoff.** The draft ended on `position=2` followed by
`call.ended(reason="transferred")` — the agent stopped participating while the caller was second in a
queue, and the record already said the transfer had succeeded. The reviewer's rule: *a transfer is an
action like any other and is not complete until its result comes back — success or error.* **The
corpus had already said the same thing and this session had not noticed**: 50 tool results across 8
statuses, including `timeout` and `error`. Every action in the corpus waits for its result. Making
transfer the one exception would have broken the corpus's own grammar, not merely a design
preference.

**And the defect that ending on a queue position would have seeded was not new.** It was claimed here
as the sharpest escalation finding available. It is not: *"a provider accepting a message is not a
recipient receiving it"* is class **S5**, already seeded in CALL-11 and CALL-12 (F-59, F-60). Same
shape, one tool over. Under D68's test 2 it earns no second seeding, and the claim was withdrawn
rather than carried.

**`Outcome.transferred` should probably never be used, which unpicks half the reason for the call.**
This call was justified partly as exercising two unused vocabulary tokens. But `disconnection_reason`
records *how a call ended* and `outcome` records *whether the caller's need was met* — different
axes. On the reviewer's rule a successful handoff is `resolved` and a failed one `unresolved`, which
leaves `Outcome.transferred` straddling both and duplicating the other field. So the token is less a
gap to fill than a schema smell, and the call earns its place on the other ground: **escalation is a
failure surface the design set did not touch at the time.**

### What the call now is

`disconnection_reason: transferred` · `outcome: resolved` · `outcome_reason: escalated` — three
fields answering three different questions, and **declared as a true negative** in the seeding
manifest rather than left to be inferred.

**The reason set was genuinely short, and gained a value rather than keeping the gap as an exhibit.**
Nothing in `exchange_completed`, `refund_issued`, `transfer_completed`, `name_changed`,
`information_provided`, `unresolved`, `caller_abandoned` says *handed to a human*, so a correctly
escalated call could only be filed `unresolved` — making the metric that would show escalation
working the metric that reports it failing. `escalated` is now declared. `transfer_completed` does
not fill the gap: it names a **booking** moving between holders, which is a different event that
reads alike, and both names are now spelled out together in the register for that reason.

**Three findings, and the one the call exists for is F-88.** The reviewer's model has the specialist
pulling the caller's profile themselves — phone, name, ZIP, recent bookings — so the payload's job is
not volume of context. What a specialist cannot reconstruct is *why the call is arriving* (F-87,
`summary=""`) and *which record this conversation was* (F-88). `dispute_reference` is declared as a
state variable and written in no transcript in the corpus; this is the call that needed it. **Fifteen
calls are about what an agent said and did inside a call; F-88 is the only finding about whether the
call can be found again from outside it.**

### The failure paths are recorded rather than seeded, and the gap has a floor

A transfer can fail three ways, and the reviewer separated them: **(a)** the agent believes it
initiated a transfer and did not, so nothing comes back; **(b)** it was initiated and failed
technically, so an error comes back; **(c)** no human answered, so a timeout comes back. (b) and (c)
are mutually exclusive, so showing both needs two calls.

What an agent should *do* next is left open, because it is a question for a human to answer
comprehensively. **But open is not unbounded, and the floor is stated so the gap cannot be read as
permission**: whatever the policy, a failed transfer must leave the caller somewhere to go — telling
them there is a technical problem and asking them to call back in ten minutes is the simplest thing
that clears it. Silence, a dropped call, or an assurance that the transfer succeeded do not.

**Consequences / caveats** — the register gains two names, `transfer_to_specialist` and `escalated`,
each with the reason it exists written beside it. Totals: **15 design calls, 375 events, 89
findings**; CALL-20's density is 0.107. `cj load` reads 82 admitted and 7 question-tier excluded.
Two draft rows were written and dropped before adjudication — a verification-does-not-travel finding,
which the reviewer's model made weak because a specialist re-verifies anyway, and the vocabulary-gap
finding, which the register change replaced.

**Building it found four defects in the harness rather than in the corpus**, which is the part worth
recording: `outcome` is a substring of `outcome_reason`, so the evidence checker compared record
citations against the wrong field; the verify check inferred *never verified* from owner plus
variable name, which the dropped F-88 broke by naming `identity_verified` because verification **did**
happen; `int(total_seconds() * 1000)` truncates, so a header that reconciled exactly read as an
unseeded taxonomy 32 defect; and `queue="venue disputes"` collided with CALL-18's internal-note
vocabulary, against a register rule of one canonical name per entity. **A fifteenth call was enough
to find four things fourteen had not.**

**Rule** — the register additions are bound by
`test_every_name_the_corpus_uses_is_in_the_register` and by
`test_the_corpus_demonstrates_the_vocabulary_it_claims_to`; the corrected record is a Part 1 true
negative with anchors, so a check that read a transferred call as a failed one would fire on it; the
three harness fixes were each planted against and observed to fire, in both directions where the
check has two. **Whether escalation deserved a call at all is judgment, not checkable** — D68's three
tests are applied by a reader, and this class passed them on the reading that no other call is about
what the next actor receives.

---

## D74 — A guard built to stop this drift was scoped to the cheaper half, and the counts it missed are rewritten rather than re-pinned

**Fork:** A second independent sweep, 2026-09-02, reported eleven items. **All eleven reproduce** —
against the previous sweep's twenty-one of twenty-four — and it opened by correcting a miss of its
own: its quantifier regex had not covered the *N of the M calls* shape, so **F-71 was already wrong
when it swept and it did not flag it.**

Its sharpest item is about a guard this project built two days earlier.
`test_every_worded_design_set_size_agrees_with_the_declaration` exists to stop exactly this drift and
was scoped to five specification documents. The sweep ran **the test's own regex** over the four it
did not scan and found **six wrong statements** — three of them inside `corpus/findings.yaml`, the
artifact judge-versus-human agreement runs against, and the one file where a stale sentence is a
stale label.

**Options considered.** (A) Correct the six. (B) Correct them and widen the guard. (C) Widen the
guard, and rewrite the statements so they cannot decay at all.

**Decision: (C).**

**Why** — (A) is what produced the six: every one was correct when written and went stale by
addition. (B) leaves six sentences needing correction on every corpus growth, which is a maintenance
burden disguised as a fix. The sweep's own phrasing is the argument for (C): *quantifying a claim
makes it checkable **and** makes it decay.* A row that read *thirteen of the 14 calls select their account this
way* now reads **every call in the corpus selects its account this way except CALL-18** — as
informative, and it cannot go stale by addition. Six statements were rewritten that way; the guard
now scans nine documents including the gold set, the drafts, the manifest and the register.

**Per-document minimums, not one total.** The sweep also found `specs/error-type-sweep.md` sitting in
the guard's loop and contributing **zero** matches — a document that has quietly stopped matching,
hidden inside an aggregate floor. Only the two documents that certainly state the size now carry a
non-zero minimum; the rest may legitimately never mention it. **A declared zero and an unnoticed zero
look identical until one of them is written down.**

**Two more numbers gained a test rather than a correction.** The *Not checked* block's ruling tally
(86 / 60 / 26 against a ledger holding 89 / 62 / 27) is now read from the ledger, and the judged-call
estimate — which stood at 980 in one document and 1,050 in another, for one quantity, with nothing
binding either — is now computed from the design-set size, the judged-dimension count and N, every
one of which was already pinned elsewhere in the same file.

**The injection pair's defining property was asserted in prose and checked by nothing.** D7's
acceptance criterion rests on CALL-07 being CALL-06 with one sentence removed. `INJECTION_PAIR` was
read by a single test, which compares *findings classifications*. The sweep diffed the transcripts by
hand and the property holds; it is now mechanized — same events, same kinds, same context, exactly
one differing utterance, and the control's version a **prefix** of the injected one.

**Class 1's hole went one noun further than D71 reached.** D71's mutation battery found that renaming
the ticketing platform in a single transcript was caught by nothing, and bound the platform name. The
agent's own persona sits in the same sentence of the same turn, is invented under the same
substitution policy, appears in **every** call — and thirteen of them were declared nowhere at all.
Now declared, bound, and with the reason variety is deliberate written down: a single persona across
the whole design set reads as one operator working every shift, and F-58 depends on the introduction
sounding like a person introducing themselves.

### One item is pushed back on

F4's second half reports `Last swept: 2026-09-01 @ 0.20.0 @ D71` as *"behind the work it is supposed
to cover"*. **It is not supposed to cover the work.** It records when a sweep last happened, and none
has happened since D71. Two decisions accruing against a stated trigger of eight to ten is that
trigger counting down, not a marker going stale — and D71's whole argument is that the marker must
never claim a sweep that did not occur. Making it assert equality with the highest decision, as the
sweep suggests considering, would force a sweep claim per decision, which is the failure it was
written to prevent. **F4's first half was real and is fixed**: the changelog entry's own scope line
said D69–D71 while the entry went on to narrate D72 and D73.

**D69's narrowing of M2 was wrong**, as reported. Declaring `internal_note` in a second call's
context *is* a change to the corpus and does reach the branch, because the probe set is built from
context fields; the accurate statement is that no change to **speech alone** reaches it. Corrected in
place with the correction attached rather than the sentence rewritten — the same treatment F-48's
ledger note got, and for the same reason: a record that quietly becomes right is not one.

**Consequences / caveats** — 348 tests. Four guards added or widened, each planted against and
observed to fire, and the two with a second failure mode planted against both. Nothing here was a
corpus defect: the transcripts, the parse, the density and CALL-20 were all clean on the sweep's own
measurement. **Every item was documentation or a check, which is what a corpus that is finished and
a harness that is not should look like.**

**Rule** — the widened guard reads nine documents with per-document minimums;
`test_the_zero_rejection_tally_matches_the_ledger` and
`test_the_judged_call_estimate_follows_from_the_design_set` compute two figures that were being
maintained by hand; `test_the_injection_pair_differs_only_by_the_injection` mechanizes D7's
precondition; `test_every_agent_persona_is_declared` closes Class 1's second half and asserts both
that every call yields a persona and that every persona is declared, because either alone would be
green and blind. **Whether a rewritten claim is still the claim that was adjudicated is judgment, not
checkable** — six sentences changed shape here without changing what they assert, and no test can say
that the meaning survived.

---

## D75 — The worksheet answered "is anything left to rule on?" wrongly, in the document that exists to answer it

**Fork:** Asked whether anything in `corpus/` still needed adjudicating, the cross-check was clean —
89 drafts, 89 rulings, 89 gold rows, no gaps in either direction, no placeholder notes. Then the
worksheet itself said, in its second paragraph: *"Every row is **drafted and unadjudicated**."*

Two sentences beside it had gone the same way. *"When you are done, the decisions become
`corpus/findings.yaml` … It does not exist until then, deliberately"* — it exists. *"**Do not run
`cj` before this is finished**"* — it is finished, and scoring is now the next step, so a live
instruction had become one that blocks the correct action.

**Options considered.** (A) Correct the three sentences. (B) Correct them and add a guard. (C) Make
the generator compute them, so the state cannot be asserted at all.

**Decision: (C).**

**Why** — (A) is what put them there: each was true when written and became false when the state
moved, which is this project's most-repeated finding, now with the twist that **the document
answering "what is left?" answered it backwards.** (B) would catch the next drift and still leave
three literals to maintain. Under (C) the preamble reads the ledger and the gold set's existence and
says what is true: with rows outstanding it names them and how many, and with none it says so and
points at the ledger as the place to change a ruling.

**What is not automated, deliberately.** The *content* of the preamble — that a finding cannot be
judged against a fragment, that D10 makes the classifications the human's, that Part 1's true
negatives are worth reading first — stays a literal. Only the three sentences that assert a
**position** are computed. A generator that wrote its own rationale would be the thing this document
exists to prevent.

**Consequences / caveats** — the worksheet is now described as a reading view rather than a
to-do list, which is what it has been since the last ruling landed. Nothing about the corpus, the
drafts, the ledger or the gold set changed; this was one generated file telling a reader the
opposite of the truth for two days, through a full sweep that did not open it.

**Rule** — `test_the_worksheet_renders_and_states_the_position_it_is_actually_in` binds the
rendered claim to the ledger and to the gold set's existence, not merely the generator's logic,
because a generator that computes the right sentence is no use if the file on disk was never
regenerated. Planted against and observed to fire. **Which sentences are position and which are
rationale is judgment, not checkable** — three were moved and the rest were left, and no test
decides that the line was drawn in the right place.

---

## D76 — The worksheet is rendered rather than committed, and "sweep everything again" becomes an inventory

**Fork:** Two questions arrived together after D75. Does the review worksheet need to exist at all,
given that adjudication happened in dialogue and landed in the ledger? And since D75's defect was
found *by accident* — while checking something else — does the project need a sweep of every
statement it contains?

### The worksheet

**Options considered.** (A) Keep it as it is, now that it is honest about its own state. (B) Keep the
generator, drop the committed output. (C) Delete both.

**Decision: (B).**

**Why** — its stated purpose is *scaffolding for the one phase-1 step a model must not do*, and that
step is done. It was never used for it: the rulings were made in conversation and written to
`corpus/findings.adjudication.yaml`, and the worksheet collected nothing. What remained was 221KB of
derived text — the largest file in the repository — that the specification names nowhere, while it
does name `findings.candidates.md` (*"a Markdown view is generated from it for reading"*). And it had
just proved itself a staleness surface in the most direct way available.

(C) was rejected on the one argument that survives: **a second human reader is the project's
first owed item**, and this is the only view that lays each call out in full *with its findings in
place*. `--out` answers that without a committed file — the reader renders it when they arrive.

### The sweep

**Options considered.** (A) A fifth reading pass. (B) A statement inventory: enumerate the classes
where a statement names something that either resolves or does not, and check those mechanically.

**Decision: (B).** Four reading sweeps preceded this, and **each found what it looked at** — two of
them never opened the worksheet at all. The argument for (B) is what happened when it was tried: one
class-check, *every `test_*` named in prose must exist*, found a wrong name in **D73's own Rule
line** in about two minutes, after a full suite and two sweeps had passed over it.

**The quantifier pass, run first.** Fifty-two statements quantify over the corpus. Two were false:

- **F-47's evidence counted 11 other design calls emitting `call.ended`** — 14 do. In the
  gold set, stale through two corpus growths.
- **D66's summary of F-56 said "Every call selects its account on `matched_by := caller_ani`"** — a
  **third copy** of the sentence an audit caught as G3, and, like the others, *wrong when written*:
  the same sweep that added F-56 added CALL-18, which matches on a booking reference. G3 fixed the
  finding and neither audit looked for the sentence anywhere else.

**And the guard that should have caught the first one was one adjective away.**
`_DESIGN_SET_SIZE` required `design` to follow the number, so *"eleven **other** design calls"*
slipped through. It now captures `other` rather than merely allowing it, **because the word changes
the arithmetic**: N *other* calls must equal the design set minus the one being discussed.

**The inventory, run second**, over seven classes: repository paths, finding ids, call ids, decision
references, policy documents, policy clauses, taxonomy item numbers. Its first run reported thirty
items, of which **twenty-seven were its own false positives** — the clause extractor read `##`
headings while the policies number clauses in bold, so it reported every clause citation in the
project as unresolved. Recorded because it is the sharper failure: *a checker whose extraction is
wrong does not report nothing, it reports everything*, and a reader who acts on that list does
damage a silent check never would.

One real defect survived: two documents named the worksheet after it was deleted. One is the
decision record naming a file that existed when the entry was written, which is what a record does
and is left alone.

**What it deliberately does not do**, stated because an inventory's honest output includes its own
boundary: it does not read prose for truth. Roughly **200 existence claims** in these documents are
of the kind no script settles, and they stay a reader's job.

**Consequences / caveats** — `tools/statement_inventory.py` is re-runnable and defaults to skipping
the decision record's historical paths, per D53; `--all` shows them. The corpus, the drafts, the
ledger and the gold set were unchanged by any of this except F-47's one evidence fragment.

**Rule** — `test_every_test_named_in_a_rule_line_exists` binds the class that started it;
`test_every_worded_design_set_size_agrees_with_the_declaration` now scans nine documents, adjusts for
`other`, and was planted against with the exact wording that hid;
`test_the_worksheet_renders_and_states_the_position_it_is_actually_in` runs the generator, because a
generator with no committed output can rot unnoticed; and
`test_every_identifier_named_in_prose_resolves` runs the inventory. **Which statements are
mechanically checkable at all is judgment, not checkable** — seven classes were chosen and the rest
left to readers, and no test decides that the line was drawn in the right place.

---

## D77 — The readable findings document was the drafts, and it called itself the findings

**Fork:** A human review of `corpus/findings.candidates.md` turned up four prose defects the suite
could not reach — a claim contradicting its own evidence fragment, a citation of the wrong half of
D42, an idiom that read as a contradiction of another finding in the same call, and an off-by-one
position. Chasing the third of those exposed something larger: **the document being reviewed was not
the corpus.**

`findings.candidates.md` is generated from `findings.candidates.yaml`. **Twenty-three rows carry
ledger text**, so for those the gold set reads the ruling and the view shows the proposal. Measured:

| | the view being read | the gold set |
|---|---|---|
| title | *"Findings — design set"*, with nothing saying "drafts" | — |
| stated split | **81 defects, 8 questions** | **82 defects, 7 questions** |
| tiers | 60 assert / 23 judge / 6 human | **61 assert / 22 judge / 6 human** |
| rows differing in text | — | **21 of 89** |
| rows differing in **evidence** | — | **14** |

And the spec's own P1 criterion reads: *"The generated Markdown view of **the findings document**
matches the YAML it was generated from."* **The findings document had no view at all.** The one that
existed was of the candidates and was standing in for it, under a title that invited exactly that
reading.

**Options considered.** (A) Retitle the candidates view so it announces what it is. (B) Generate a
gold-set view as well, and retitle the other. (C) One view, of the gold set; the drafts stay YAML.

**Decision: (C).** `corpus/findings.md`, generated from `corpus/findings.yaml`, and the candidates
view is deleted.

**Why** — (A) leaves the criterion unmet and a reader one honest sentence away from the same mistake.
(B) is defensible: a readable form of what was *proposed* is the human-readable half of an
`accept-with-edits`, and a reader comparing the two can see what the adjudication changed. It was
rejected because two documents differing in a quarter of their rows, one of which is authoritative,
is the situation that just cost a review pass — and the diff it offers is available from the two YAML
files, which is where a diff belongs.

**Where this sits among the session's findings.** The corpus was repaired, the gold set generated,
four sweeps run, and roughly twenty guards written — and through all of it **the document a human
would actually open was the wrong one**. Two independent sweeps ran `findings_view --check` and
reported it current; it was current, against the drafts. No check was wrong. The thing nothing
checked was *which document the criterion was about*.

**Consequences / caveats** — the drafts remain as `corpus/findings.candidates.yaml`, which is what
`make_gold_set.py` reads and what the ledger is a diff against. `findings_view` now defaults to the
gold set, so the bare command produces the right document; the regeneration test follows it. The four
prose defects the review found are fixed in the file that governs each: F-67 and F-63 in the drafts,
F-23 and F-14 in the ledger, **because a draft edit to a row the ledger overrides is dead text** —
which happened once here and was caught only by checking.

**Rule** — `test_the_markdown_view_regenerates_identically` now renders `corpus/findings.yaml` and
compares against `corpus/findings.md`, so the view cannot drift from the gold set or be generated
from the wrong source without failing;
`test_every_identifier_named_in_prose_resolves` caught the deleted path in the handover within one
run of this change. **Which document a specification means by "the findings document" is judgment,
not checkable** — a criterion naming an artifact is only as good as the reader who maps it to a
filename, and for two days that mapping was wrong while every check was green.

---

## D78 — The spec's metadata named the intended end state as the current one

**Fork:** Immediately after the phase-1 push, this session told the repository's owner that the gold
set was now public, and drew a consequence from it: that the benchmark-contamination assumption had
become load-bearing. The owner corrected it — all three repositories are private and flip when the
project is minimally functional.

The claim did not come from nowhere. The specification's metadata header reads, as its fourth line:

> `- Visibility: public — built private, flipped after a history scan (D2)`

D2 *decided* the flip. It has not happened. `gh api` confirms
`voice-agent-eval-harness`, `voice-agent-eval-harness-holdout` and `comparative-judgment` are all
private. A second live claim sat in the in-scope section — *"a clone of **this public repository**
gets the `.gitignore` and none of the enforcement"* — asserting the same thing as an established
fact.

**Options considered.** (A) Leave it; the line becomes true at the flip. (B) Correct both to state
the current position. (C) Correct them and add a check comparing the stated visibility against the
GitHub API.

**Decision: (B).**

**Why** — (A) is the cheapest and was refused on evidence: the header had *already* misled a reader,
and the reader was the session that had spent two days finding exactly this class of defect
everywhere else. A document that misleads its own author is not waiting for a better example.

(C) is the reflex this project has earned, and it is wrong here. Comparing the stated visibility
against `gh api repos/…` needs network access and an authenticated CLI, fails on a fork or offline,
and checks a fact about **GitHub** rather than about anything in the repository. It would be the
first check in the suite whose subject is not the tree it lives in.

**What replaces it is wording rather than machinery.** The line now states the position *and the
trigger*: private today, public when the project is minimally functional. A statement of intent with
its condition attached cannot go stale the way a bare `public` can, and the flip — when it happens —
edits that line as part of the act rather than leaving it to be noticed.

**Consequences / caveats** — this is the third entry in three days about a document asserting a state
it is not in: D75 (the worksheet's preamble), D77 (the readable findings document being the drafts),
and now the specification's own front matter. The shape is consistent enough to name: **the claims
that go stale are the ones describing the project rather than the corpus.** Every count about the
corpus is now bound to the corpus. Nothing binds a sentence about where the project *is* — its
visibility, its phase, what has been reviewed — because those refer to facts that live outside the
tree, and a check that reaches outside the tree buys its coverage with a dependency the suite does
not otherwise have.

**Rule** — none, deliberately, and the reason is the entry's substance rather than an omission:
`tools/statement_inventory.py` covers identifiers that resolve inside the repository, and this is a
claim about GitHub. **Whether a project-state sentence is current is judgment, not checkable** — the
mitigation is that such sentences now carry their trigger, so a reader can tell what would make them
true rather than having to know whether they already are.

---

## D79 — The calibration note matched three findings that sit below the line

**Fork:** The `critical_high` cut ships with a note recording what the boundary was calibrated
against — the one absolute judgment a pairwise method needs, because an interval scale has no origin.
Tested after it was written, the shipped note is true of all four critical rows and also of three
below the line: **F-75** (rank 10), **F-46** (18) and **F-14** (19). Either the ordering is wrong and
those three belong above the cut, or the note is too broad and needs narrowing until its extension is
exactly the four.

**Options considered.** (A) Raise F-75, F-46 and F-14 to critical, so the band matches its stated
criterion. (B) Sharpen the note until it excludes them. (C) Neither: ship the note as the reason for
the cut, and treat the mismatch as a reading of the ordering rather than a fault in it.

**Decision: (C).**

**Why** — the bands come from 410 comparisons, not from the note. The note anchors the scale; it does
not place the rows. If it placed them, the comparisons would be decoration and this would be a rubric
— which is the instrument comparative judgment is chosen *instead of*.

(A) edits an ordering to agree with a sentence written after it. That is D53's shape, and here it is
not an analogy: `comparison_log_hash` is folded into `run_id` precisely so an ordering cannot be
quietly re-cut to suit a later conclusion. Re-scoring is allowed; re-scoring without saying so is not.

(B) fits prose to an outcome. A note whose extension is exactly the four rows above the line is true
by construction and tells a reader nothing they could not get by listing the four. The note is
supposed to be the *reason*, and a reason is falsifiable — which is the whole value of discovering it
over-includes.

**What the note had to survive, and what it killed.** Three candidates were tested against the four
critical rows and the three immediately below:

- *"Critical means harm that reaches beyond this caller and this call"* — the shipped-through-scoring
  placeholder, and **this session's phrasing, not the owner's**, which is the D10 line at its thinnest
  point: one absolute judgment in an otherwise pairwise method.
- *"whatever can put operational control of the account into non-owner's hands"* — **failed F-78.**
  CALL-18 carries `account_zip := 00284` and `billing_zip := 00461`. They are different values, so
  disclosing the billing ZIP hands over nothing touching account control; F-78's own consequence says
  the harm "is not to this booking but to the card, somewhere else, later."
- The shipped note adds **"and/or associated payment instruments"**, which names that asset, and is
  the first candidate true of all four.

A note that fails a row *inside* its own band is the defect. A note that stretches to the weakest rows
of the adjacent band is not.

**Consequences / caveats** — the over-inclusion is a standing signal, recorded here rather than
resolved:

- **F-75** at rank 10 — "makes the account readable by anyone who has ever been sent the booking" —
  was already logged as an ordering tension before the note existed, and every exposure-flavored
  wording has passed it. It is the strongest candidate for a genuine mis-ranking.
- **F-46** and **F-14** are the bottom two rows of the high band and the same family as F-04, a
  critical row: all three are verification bypasses. The feature separating them is **not named in the
  note** — in all four criticals something crossed to the caller (data in F-45 and F-78, a false
  assurance of verified status in F-04, the bypass rule itself in F-76), whereas in F-46 and F-14 the
  gate fails internally and nothing leaves. That the note does not carry this is the honest reading:
  one sentence carries fewer features than 410 comparisons.

**Rule** — none mechanical, and deliberately. Whether a rank is right is the judgment the method
exists to elicit; a check that enforced agreement between the note and the ordering would enforce
exactly the edit (A) was refused for. **The resolution is a second rater** — already the standing gap
on the gold set, and now on the ordering too. If a second person's comparisons put F-75 at rank 10
again, the ordering is stable and the note is simply narrower than the judgment that produced it. If
F-75 moves up, the note found a real defect, which is the argument for writing calibration notes at
all.

---

## D80 — A cross-call citation went stale in prose, where no check reads

**Fork:** F-68's consequence said *"CALL-12 event 9 is the true negative — the same readback done by
naming the holder and the address in full."* Event 9 is `t1 lookup_booking(...)`. The readback is
event **11**, which is what the seeding manifest declares. The citation was correct at `8cd8aaa` and
`9f1c49c`; the adjudication commit rebuilt CALL-12's degraded-line exchange, the readback moved, and
the finding did not. It survived a full suite, four independent sweeps and a human read, and was
found three days later while answering a question about commit ordering.

`test_every_quoted_fragment_appears_in_the_event_it_cites` exists for exactly this class and did not
fire, because it reads `finding.evidence`. This citation lives in a sentence.

**Options considered.** (A) Fix the citation; the class is rare enough that a guard is
over-engineering. (B) Add an existence check over prose citations. (C) Add the existence check *and* a
check comparing any true negative named in prose against the seeding manifest.

**Decision: (C).**

**Why** — (B) alone does not catch this defect, and finding that out is the entry's substance. **Event
9 exists.** An index that drifts onto a different real event passes an existence check silently, which
is the same failure as the guard already in place: green, and blind to the thing it was written for.
What makes the claim checkable is that the manifest is the *authority* on true negatives, so the
coordinates can be compared against something rather than merely resolved.

(A) was refused on the cause rather than the instance. Transcript rebuilds shifting indices have now
produced three defects — F-80's cross-call citation, F-70's gap claim, and this one — and a person
found each of them after a suite had passed.

**Consequences / caveats** — the two guards have honestly different populations, stated here rather
than left for a reader to measure. The existence check binds **39** prose citations across the gold
set. The manifest check binds **one**: F-68's is the only finding naming a true negative's coordinates
in prose. That is thin, and it is the row the guard was written for. The population is small because
naming a location in prose is rare, not because the check is narrow — but a guard with one subject is
one a single rewrite can leave with none, and nothing warns when that happens.

The ledger's ruling for F-68 still says event 9. It was true when written, and a note edited to agree
with what came after it stops being a record (D53). A correction is appended beneath it, following
F-48's precedent.

**Rule** — `test_every_event_cited_in_findings_prose_exists` and
`test_a_true_negative_named_in_prose_agrees_with_the_seeding_manifest`, both in
`tests/test_findings_evidence.py`. The second was watched failing on the real defect before the gold
set was regenerated, rather than on a planted one.

---

## D81 — A declared true negative was the tolerable form, not the correct one

**Fork:** Part 1 declares *"CALL-12 event 11, its form only"* a true negative and said the readback's
**form is correct** — the agent states the event, the date, the holder and the destination address in
full. F-68 and F-42 report the opposite behavior in CALL-11, where the same readback is done by
description. Reading F-45 while placing the severity bands produced a third position: the agent should
never state the address on file at all. The caller spells the address they claim, and the agent
verifies it against the record. That gets what F-42 wants — the caller can tell the address is wrong,
and consent to a specific destination is evidenced — without F-45's disclosure, and it holds whether
or not verification has happened.

The stakes are why this was not left. A booking reference is *"printed on every confirmation email and
forwarded whenever tickets are shared"* (F-75), so F-45 turns a widely circulated token into the
holder's name and email. With a ZIP that F-56 records as spoofable, that is the material for
operational control of an account. F-45 sits at rank 2 of 82.

**Options considered.** (A) Leave it; the row is a true negative for the comparison it actually makes.
(B) Narrow: correct the manifest's claim about the *form*, and the one sentence in F-68 that endorses
it. (C) Wide: also re-frame F-68's defect around *"the caller was given nothing to check"* rather than
*"the address does not reach the caller"*.

**Decision: (B).**

**Why** — (C) is truer and it breaks the finding. Under spell-back-and-verify the address still never
reaches the caller, so F-68's observation would be satisfied by the better behavior too, which is a
real argument for re-framing. But *"nothing to check"* is a judgment and *"no agent turn contains the
address"* is a fact, and F-68 is `detectable_by: assert`. D42 says assert what is assertable; taking
(C) would push F-68 off its detection mode or force a second split of a finding already split once.

**Reading the rows narrowed the change further than the obligation that raised it.** The handover said
*"probably the framing of F-68 and F-42"*. **F-42 needed nothing** — its text already reads *"They were
given no way to tell which address that is"*, which is the spell-back framing, not the name-it-in-full
one. What was wrong was the manifest's claim and one sentence of F-68's, and nothing else. An
obligation written at the moment of noticing is a guess about scope, and this one was wider than the
defect.

**Consequences / caveats** — the row still bounds F-68 and F-42, because it is the better of the two
behaviors *those* findings compare. It is no longer described as what the corpus would recommend, and
it now says why: a check calibrated to demand it would be demanding a disclosure. That distinction is
one a true negative can carry and a finding cannot, which is an argument for the manifest existing at
all.

**Rule** — none. Which of two acceptable behaviors is better is a judgment, and the manifest is where
this project records the judgments that constrain checks.

---

## D82 — The severity file attests to the comparison log, not to what was compared

**Fork:** `corpus/findings.severity.json` carries `comparison_log_hash` and `run_id`, and both describe
the *judgments*. Neither describes the **rows those judgments were made about**. Editing a finding's
observation, evidence or consequence after an export leaves the file describing text that no longer
exists, and every severity test in this suite joins on `id` — so nothing here notices. Found while
fixing D80's citation, which changed F-68's text after the export.

**Options considered.** (A) Add a check here that recomputes each finding's content hash and compares
it. (B) Extend the severity schema in `comparative-judgment` to record what it scored, and add a
`cj verify`. (C) Document what the provenance does and does not attest to, and name the tool that
already detects the drift.

**Decision: (C).**

**Why** — (A) requires the hash function, which is `content_hash` in
`comparative_judgment.core.models`. This package deliberately does not depend on that one:
`harness.core.severity` reads *"a file this project does not write"*, and that separation is what makes
the two sides independently checkable. Closing the gap here means a second definition of one hash in
two repositories, and two definitions drift faster than the gap they would close.

(B) is the correct long-term shape and is not this session's work. It is a schema change, a new command
and a version bump in another repository, to close a gap that a documented step closes today.

(C) works because **`cj load` already is the detector.** Run without `--accept-revisions` it refuses,
names every changed finding, and reports how many comparisons were made against the old text. Nothing
said so anywhere. `src/harness/core/severity.py` described the provenance fields without saying what
they do not cover, which is how a reader ends up trusting a file for something it never claimed.

**Consequences / caveats** — this is D78's rule applied a second time: a check whose subject lives
outside this tree buys its coverage with a dependency the suite does not otherwise have. The mitigation
is the same one — the sentence carries its own trigger, so a reader knows what to run rather than
having to know whether it was run.

The gap is real and stays open. A severity file can still be committed alongside findings it no longer
describes, and only a person running `cj load` will find out. (B) is the entry that would close it.

**What this session's own use recorded.** F-68's revision was accepted rather than re-compared — 10
prior comparisons carried over, rater `Saso Gale`, with `observation` and `evidence` byte-identical and
only the consequence's closing cross-reference changed. `comparison_log_hash` moved from `9d2d1838…` to
`9771a324…` and `run_id` from `2dcd6d9e74cf29b7` to `053f9e69d7a79cc0`. The acceptance is visible rather
than silent, which is the property the log hash exists to provide.

**Rule** — none mechanical, deliberately, and the reason is the entry itself: the only place the check
can live without duplicating a hash is the tool that owns it.

---

## D83 — The held-out obligations, discharged by the first session that could read the five

**Fork:** `HOLDOUT-OBLIGATIONS.md` carried three entries that no check in this repository can reach,
and `HOLDOUT-REPAIR-BRIEF.md` stated the conforming shapes without being able to say whether any
defect was present — it was written by a session that could not read `CALL-13`…`CALL-17`. A cleared
session read them on 2026-09-06. What it found is below in counts; what it decided is O-3.

**Options considered.** (A) Repair O-1 and O-2, and settle O-3 by stating in the published result
which classes the held-out measurement does not reach. (B) Repair O-1 and O-2, and seed the absent
classes into the held-out set. (C) Repair, and seed only escalation — the one class the five could not
have expressed at all. (D) Repair, and leave O-3 open.

**Decision: (A) for the repairs and the reach statement, (C) for escalation**, with the seeding done
under named controls by a different model in a session given a curated input packet.

**Why** — the repairs were not a judgment call. Twenty-six non-excepted tool-call arguments across the
five, four unsourced across four transcripts: three were `fetch_policy`'s retired `clause` argument and
left with the O-2 repair, and the fourth was a bare integer on a write, re-keyed onto the booking
already in its context. **No exception was added and no event was inserted**, so nothing renumbered —
event counts and every timestamp are unchanged and all five still parse with a zero unparsed-line
count. Three of the five carried the retired two-argument `fetch_policy`; the other two make no policy
retrieval. Clause counts were re-derived from `corpus/policies/` rather than taken from the brief and
agree with it at 14, 10, 10.

O-3 was the only real fork. Seeding's cost is **twins**: a held-out escalation call written by the same
author, in the same week, from the same error-type sweep as CALL-20 will resemble it, and the judge is
built against a rubric designed on CALL-20. Agreement measured on a near-twin is inflated — not by
cheating, but because the test case resembles the material the judge was shaped on. Against that, the
reach statement's cost is a measurement narrower than the judge it measures.

(C) survives because the twin risk is **remediable and the remedy is checkable**, which is this
project's usual escape from a trade-off. The resemblance has three channels and they respond
differently: the author's habits (a different model varies these), the shared source material (closed
by withholding CALL-20 and everything that describes it), and the targeting itself (irreducible — a
seeded instance is always a cleaner specimen than a natural one, which is true of the design set too).
The second channel is the load-bearing one and it is the one a curated input packet closes. The
sweep's own note that **CALL-20 seeds the successful transfer path only** fixes the assignment: the
held-out call takes that same path, so the judge is measured on a class it was built for, and the
*scenario* is invented by the authoring session rather than supplied.

**Consequences / caveats** — four, and the first two are weaknesses rather than notes.

**The ported provenance rule is a copy, not an import.** The held-out repository's own
`test_holdout_conventions.py` duplicates `_sourced_by` from `tests/test_corpus_hygiene.py`, because it is a
private helper in a test tree and a test module is not an importable interface. Two copies of a rule
are two things that can disagree; if this one changes and that one does not, the held-out suite goes
green against a stale convention — which is `HOLDOUT-OBLIGATIONS.md`'s own failure mode, one layer
down. Moving `_sourced_by` into the `harness` package would close it. Not done here.

**A limit of the provenance check, applying to this repository too.** No bare integer of one or two
characters can pass it: the speech and prior-event paths require three characters, and the arithmetic
path sums context values rather than subtracting them. So a small-integer argument has no honest
repair available — only a coincidental match against an unrelated context number, which is the false
source the length floor exists to prevent. The repair is to change what the argument *is*, and that is
what was done. Worth knowing before someone widens the check to make a failure go away.

**The clause-count check alone would not have caught what it was ported for.** The retired
`fetch_policy` shape returns a detail stating no count, so there is no number for that check to find
wrong; it would have passed on all five while three carried the defect. A companion that fails on the
signature itself was added. This is D79's shape again — a guard satisfied without touching its subject
is green and blind.

**O-3's own wording was wrong, not merely unverified**, and the brief predicted it might be.
`HOLDOUT-OBLIGATIONS.md` said the five "exercise none of the 35 findings". Checked rather than
inherited: of the eight classes named, five are absent, one is absent in part (no zone arithmetic
anywhere; date arithmetic present in two calls), one exists only as a uniform convention across all
five so nothing isolates it, and **one is genuinely present**. Escalation's absence is confirmed
mechanically — no `transferred`, no `escalated`, no `transfer_to_specialist`, all five `resolved` —
and so is the absence of the four context fields added at D68.

**The seeding control is a packet, not a rule.** The first version of this decision was going to hand
the authoring session an allow-list — "read these, not those" — which is the shape this project
rejects everywhere else, because it depends on obedience the way a `holdout/` directory would have.
The owner's correction was to hand over **modified documents instead of instructions about
documents**. `holdout-authoring-packet/` therefore holds the format spec, the event model, the entity
canon and the five held-out transcripts, with every design-call reference removed — one passage in the
event model, five in the entity canon — and a leak scan over the result. **Redactions are visible
markers, never silent rewrites**, so a reader can tell that something was removed rather than
believing they have the whole document. The packet sits outside both repositories and outside any git
working tree, so it cannot be committed by accident. No scenario is supplied, deliberately: whoever
assembles the packet knows CALL-20's, and suggesting one would reintroduce the resemblance the packet
exists to prevent.

**One consequence for the held-out repository when the call lands.** Its workflow asserts the set is
*exactly* `CALL-13`…`CALL-17`, and adding a sixth must update that step rather than suppress it. The
new call's identifier is deliberately not named here: `tools/statement_inventory.py` checks every call
id in this tree against `corpus/DESIGN_SET` and the held-out range, and naming one that does not exist
yet is asserting a future state — which is what D53 forbids, arriving from the other direction.

**Noticed while building the packet:** `corpus/entities.md` enumerates the design set as
`CALL-01`…`CALL-12`, `CALL-18` and `CALL-19`, while `corpus/DESIGN_SET` declares fifteen including
`CALL-20`. The register is one call stale in the document whose job is to be the canonical list — the
same shape D82 records at line 237 about a renamed field. ~~Left for a session that may do
design-corpus work, which this one may not.~~ **Corrected on the owner's instruction, 2026-09-06, by
this session.**

**The crossing is recorded rather than made quietly**, because the bar on design-corpus work is
categorical by design and reasoning past it is the failure it exists to prevent. What makes this one
safe is narrow and worth stating: the corrected line is a *transcription of `corpus/DESIGN_SET`*, so
the fix is mechanical and no held-out knowledge could inform it. Anything requiring a judgment about
design-set content — the `EV-88011` dates at D85, widening the title check — stayed undone for that
reason.

**And the correction has no check behind it**, which is the state this session spent its length
arguing against. `corpus/DESIGN_SET` is the declaration and that line is prose about it; nothing
compares them, which is why the prose stayed wrong through D73. A check asserting the two agree is a
few lines and would have caught it — not written here, because it belongs with the session that
handles the rest of the design corpus.

**Rule** — **none mechanical in this repository, and the entry's own subject is why.** The first draft
of this line claimed the port as its mechanism and named the module. Two checks here rejected it, both
correctly: a Rule line may only name a test that exists in this tree, and prose may only name a path
that resolves in it. The port is real and it runs — in the *other* repository's workflow, where
nothing here can run it or notice it breaking. Claiming it as this record's mechanism would have been
the exact move `HOLDOUT-OBLIGATIONS.md` was written to catch, made in the entry discharging it.

So what is enforced here is unchanged, and the three things this decision rests on are all
procedural: the copy-drift is recorded rather than closed, because closing it means moving code
between two repositories to remove a risk a stated sentence covers today; the packet is a mechanism
only for as long as someone hands over the packet rather than the repository; and the check that makes
the packet worth anything is the resemblance comparison run afterwards by someone who can see both
sides. Naming that honestly is the most this side can do.

---

## D84 — A workflow that checked out a private repository, failed, and reported success

**Fork:** `HOLDOUT-REPAIR-BRIEF.md` requires re-checking that the held-out repository's CI still
passes after any edit. It passed. Reading *why* it passed is what found this: the workflow's second
`actions/checkout` targets the harness — a **private** repository — using the held-out repository's
default `GITHUB_TOKEN`, which is scoped to that repository alone and cannot read another. The step
carried `continue-on-error: true`, so the failure was swallowed; every step conditional on the
harness being present then skipped, and the job reported success having verified that five files
existed and that none was named like a label set. Nothing about their contents. **Every run from
2026-08-30, when that workflow was added, to 2026-09-06.**

The workflow announced it each time, in a warning. Nobody read the warning, which is the entire
mechanism by which this failure survived a week inside the repository built to make such failures
impossible.

**And it is not one repository's defect.** This repository's own workflow has the identical shape:
*Interface agreement across both repositories* checks out `hmbseaotter/comparative-judgment`, also
private, also `continue-on-error: true`, also warning-and-skipping. Verified skipping on the run of
the commit that fixed D83's checks. That check has therefore never compared the two interfaces it
exists to compare.

**Options considered.** (A) A fine-grained read-only token as a repository secret, then convert the
warning into a build failure. (B) Wait for the public flip, since D2 and D78 record all three
repositories going public when the project is minimally functional, at which point the default token
suffices. (C) Convert to a failure only, and let the build stay red until a token exists. (D) Record
it and change nothing.

**Decision: (A) for the held-out repository, in that order, and done.** `HARNESS_READ_TOKEN` carries
`Contents: read` on this repository and nothing else, with `secrets.HARNESS_READ_TOKEN ||
github.token` so behavior is unchanged when the secret is absent and no second change is needed at
the public flip. The conditional steps then ran for the first time: five transcripts parsed with a
zero unparsed-line count, and the four ported checks passed in CI rather than only on a machine. The
warning is now an error with a non-zero exit.

**The same fix is owed in this repository and is not applied here.** It needs a second token, for
`comparative-judgment`, and that is a credential decision rather than an edit.

**Why not (B)** — because "it resolves at the public flip" is a prediction about a date nobody has
set, protecting a check that is currently asserting nothing. The interval is the whole problem: a
week of green builds already went by. **Why not (C)** — a red build with no path to green teaches
people to ignore the build, which is how the warning came to be ignored in the first place. **Why not
(D)** — D46's shape exactly: a documented mechanism that does not run is a claim about a mechanism
that does not exist.

**Consequences / caveats** — three.

**A token expires, and the failure mode returns silently.** That is the argument for the ordering:
the fatal step is not decoration on top of the token, it is what converts the token's eventual expiry
from an invisible reversion into a red build. Without it, this entry describes a fix with a
self-destruct.

**`continue-on-error` was kept, deliberately.** Removing it would fail the run at the checkout with a
raw API error; keeping it lets the guard report the consequence in the workflow's own words — which
checks did not run, and what to look at. The distinction is between failing and saying why.

**This is the third instance of one shape in a single session.** The clause-count check that could
not fail on the defect it was ported for, because the retired form states no number to be wrong; the
Rule line in D83 claiming a mechanism that lives where this tree cannot run it; and this. D79 named
the pattern as a guard satisfied by a neighbor. The generalization is worth stating plainly: **a
check's subject and a check's trigger are different things, and a green result only means the trigger
was satisfied.**

**Rule** — mechanical in the held-out repository, where the guard now exits non-zero when the harness
is absent. ~~**Not** mechanical here, and that is the open half of this entry: nothing in this tree
fails when its own interface check skips, and until a `comparative-judgment` read token exists,
nothing can.~~ **Closed the same day, and the closure found a fourth instance.**

`CJ_READ_TOKEN` landed and the interface check ran for the first time: six findings keys and seven
severity fields agreeing across both repositories, no stale cross-claims. Its warning branch is now an
error with a non-zero exit, matching the held-out repository.

**The fourth instance was underneath it.** `TestTheRealDocuments` looked for the sibling only at
`../comparative-judgment` — a working copy's layout, not CI's, where the workflow checks it out
*inside* the workspace. So that test ran on one machine and skipped every CI run since it was written,
while the workflow step above cited it by name as the reason a failed checkout was safe to tolerate:
*"the scanner's own test skips when the checkout is absent rather than failing. That skip is visible
in the test output."* Visible, unconditional, and therefore empty. Both layouts are accepted now, and
the run that followed reported **354 passed and nothing skipped** — the first in this repository's
history in which every check it declares actually executed.

Recorded as a strike-through rather than a rewrite, per D53: what this entry believed when it was
written is part of what it records. The distance between *recorded* and *closed* was four hours, and
naming that is worth more than a tidy entry claiming it was never open.

---

## D85 — One event id, two door times, and a check that compared the wrong field

**Fork:** while discharging O-1 and O-2 a cleared session noticed a contradiction the obligations did
not cover: two held-out calls name the same `event_id` and the same `event_title`, and disagree about
`door_time` — one of them placing the show four days *before* the call that was arranging to attend
it. No obligation named it, no check reaches it, and whether it was seeded was unknowable from
either repository, since the held-out labels do not exist. The owner confirmed from the seeding notes
that it was **not** deliberate.

**The first proposed fix was aimed at the wrong call, and a granted lookup caught it.** Aligning the
two held-out calls to each other looked obvious while only those two were in view. But the design
corpus fixes that event id's door time at the *earlier* value, in two calls both placed comfortably
before it — so the held-out call that appeared broken was the one agreeing with the canon. The real
problem was larger than one field: **both held-out calls are dated after that door time**, so under
the canon both concern a show that had already happened. A contradiction inside one set was a
collision between two.

**Options considered.** (A) Align the two held-out calls to each other. (B) Treat the design set's
value as canonical and move the held-out call records earlier. (C) Give the two held-out calls their
own event id, leaving the design set untouched. (D) Leave the reconciliation to a session cleared for
both corpora.

**Decision: (C)**, with the widened check below.

**Why** — (A) was the first proposal and it is wrong: it makes the held-out set self-consistent by
putting *two* of its calls in conflict with the design set instead of one, and records nothing about
why. (B) is the most faithful and the most invasive — three timestamps in each of two call records,
plus a spoken line that pins one call to the day before the show. (D) stayed tenable throughout, but
the fix turned out to be contained.

(C) works because **the corpus already does this.** One title maps to several event ids throughout the
design set: "The Halloway Ensemble at Ridgeline Pavilion" carries three, and the production at issue
here already carries two. A run of performances sharing a name is the established convention, so a
third id for the later performance invents no entity — it names one the canon's own shape already
allows. Both held-out calls now identify that performance, their titles are untouched, every timestamp
is untouched, and the two tool-call arguments referencing the old id moved with the context so
provenance still resolves.

**The harness has a cross-call check already, and it would have passed.**
`test_one_event_title_per_event_id_except_where_drift_is_seeded` asserts one canonical name per event
id — and these two calls agree about the name. They disagree about the door time, which that check
does not look at. Ported as-is it would have run, compared, and reported nothing, on the exact pair
of transcripts carrying the contradiction. So the port widened it: every field scoped to the *event*
rather than the booking is compared, deliberately excluding fields like `ticket_count` and
`booking_reference` that two callers buying seats to one show are expected to differ on.

`door_time` is the field that most needed including. Every deadline in the policy set is measured
against it — a transfer window closes twenty-four hours before it — so an agent reasoning about a
window against the wrong date reasons correctly to a wrong answer, and the transcript reads as
though the agent erred.

**Consequences / caveats** — three, and the first is the one that matters.

**The design set carries the same contradiction, and it is not seeded.** `EV-88011` holds three
different door times across the three calls that name it — two of them on the same date half an hour
apart, one of them a week later. `corpus/seeding-manifest.md` never mentions that event id, and the
seeded defects in those three calls are about verification, refund band, settlement time and
over-disclosure. The two declared reschedules are elsewhere. So this is undeclared drift in the design
corpus, of exactly the class just repaired in the held-out one, and **the check in this repository
cannot see it** — all three calls agree about the title, which is the only field it compares.

**This repository's check is therefore unchanged and now known to be insufficient**, not merely
suspected. Widening it means running it against the design corpus and then reconciling three dates,
which is corpus work the discharging session may not do. Recorded here for a session that may. The
widened version in the held-out repository is the shape to copy.

**The ported version carries no seeded-drift exemption**, unlike its counterpart here. That is
deliberate: naming drift is a design-set defect class, and a held-out transcript needing an exemption
should get one added explicitly with its reason rather than inheriting a hole sized for another
corpus. If the held-out set later seeds a deliberate contradiction, this check fails and the fix is to
declare it, not to widen the hole.

**Rule** — mechanical in the held-out repository, where the ported check compares every event-scoped
field and was verified to fail on the pre-repair value before being trusted. Not mechanical here:
`test_one_event_title_per_event_id_except_where_drift_is_seeded` is unchanged and still compares one
field, which is the open half above.

---

## D86 — The seeded escalation call, and whether the controls that produced it worked

**Fork:** D83 decided to seed one escalation instance in the held-out set under named controls — a
different model, a curated input packet, and a resemblance check afterwards. The call now exists. The
fork this entry settles is whether to **accept it**, and that turns on a question the controls were
built to make answerable rather than arguable: is it a near-twin of the design set's escalation call?

**Options considered.** (A) Accept, merge, and record what the comparison found. (B) Return it for
revision by the authoring session. (C) Reject the seeding and fall back to stating the reach.

**Decision: (A), with a single field returned under (B).** The call stands; one enum value was sent
back to the authoring session for correction, for the reason in the first consequence below.

**Why** — the comparison found difference on every axis that was free to vary and agreement only on
the two fields the assignment fixed. Twenty-three events against twenty-eight. Tool sequences sharing
exactly one entry, `transfer_to_specialist`, which the assignment required; the rest of one call's
tools appear nowhere in the other's. One call carries a `POLICY` event and the other none. Sixteen
context fields against twelve. The kind sequences diverge from the seventh event onward.
`disconnection_reason` and `outcome_reason` match, and they had to: they are the escalation
vocabulary, and a call that did not use them would not be an instance of the class.

That is what a working control looks like from the outside, and it is worth naming *why* it worked,
because the reasoning generalizes. The load-bearing element was never the model swap. It was that the
authoring session was handed **modified documents rather than instructions about documents** — the
format spec, the event model, the entity canon and the existing transcripts, with every reference to
the design set's escalation call removed behind a visible marker and a leak scan over the result. A
session told "do not read X" can still be influenced by knowing X exists and roughly what it says. A
session that never receives X cannot. The owner's correction turned an allow-list into a mechanism,
and this entry is the evidence it was the right correction.

**The comparison was run structurally, and deliberately so.** Event counts, kind sequences, tool
sequences, dispositions and context keys — no prose from the design transcript was read by the session
running it, which had already read the packet's brief and could not have judged phrasing without
becoming the thing it was checking for. Structure is the axis a twin would betray itself on anyway.

**Consequences / caveats** — three, and the first runs to five paragraphs because it turned out to be
this entry's real subject.

**The control had a cost, it landed, and it is the most useful thing this entry records.** The call
was authored with `outcome: transferred` where the design set records `outcome: resolved` for the same
situation. Both values are in the closed vocabulary and `transferred` is a reasonable reading of it —
but `corpus/seeding-manifest.md` declares the design set's call record a **true negative**, with the
reasoning spelled out: getting the caller to someone who can settle the matter *is* the resolution
available, so `outcome: resolved` sits beside `disconnection_reason: transferred` and
`outcome_reason: escalated`. That is a corpus-wide convention.

**And it lives only where the held-out side can never read it.** The manifest is a design-set artifact.
`corpus/entities.md` lists the `outcome` vocabulary and never says which value an escalation takes;
its escalation passage concerns `outcome_reason` alone. The packet redacted every reference to the
design set's escalation call — correctly, that was the whole control — and in doing so withheld a
convention the author needed and had no other route to. The author did not err; the register did not
say.

**So the mechanism that prevents a twin also prevents the author learning conventions documented only
on the design side.** That is the general cost of a curated packet and it is worth stating plainly,
because the instinct on discovering it is to loosen the packet, and that is the wrong repair. The
right one is to move such conventions out of the seeding manifest and into the register, where they
travel with the entity canon rather than with the labels — tasked, not done here, since it is
design-corpus work. The field itself was returned to the authoring session with the rule and not its
source, so the packet's control survived the correction.

**Had this gone unnoticed it would have been the failure `HOLDOUT-OBLIGATIONS.md` exists to prevent**,
arriving through the door that file does not watch: not a convention changed after the held-out set
was written, but one never written down where the held-out side could see it. A judge taught by the
design set would have flagged the outcome, and the labels would have called the call clean, and the
disagreement would have measured convention drift while reading as judge error.

**And the packet was never the session's only input**, which qualifies every claim above about the
control. The authoring session ran rooted at a directory whose project memory loads automatically, so
a "packet-only" session was not packet-only. Nothing leaked — checked, not assumed: neither the memory
index nor the project entry named the design set's escalation call before that session edited them.
But the channel was open, unrecorded, and outside the packet's reach, and the session then wrote the
outcome convention *into* memory so a future packet-based session would inherit it. That is a sensible
stopgap and the wrong resting place: memory is per-machine, lives outside both repositories, is
invisible to anyone cloning them, and no reviewer ever sees it. The convention belongs in the register.
**A curated packet bounds what a session is handed, not what it can see** — worth knowing before the
next one is built, because the packet's guarantee was stated more strongly than it was true.

**Speech plausibility was checked and is not marginal**: ten measurable turns between 138 and 152
words per minute, median 145, against a band of 110–185 and a target median of 130–160. Worth stating
because a generated transcript passing a plausibility band by a hair is a different artifact from one
sitting in the middle of it.

**The ratio is now fifteen-to-six, and O-3's other half is still owed.** Seeding closed the escalation
gap alone. Every other class D85 and the obligations file enumerate as absent is still absent, and the
published result must still say which classes the held-out measurement does not reach. Adding one call
did not retire that sentence.

**Rule** — mechanical in the held-out repository, whose workflow now asserts the set is exactly the
six and runs every ported check against all of them. Not mechanical here, and one thing genuinely is
not checkable anywhere: **that the authoring session received the packet rather than the repository.**
That was true because a person arranged it, and no artifact records it. A future seeding should say so
in its own commit message, which is the closest thing to evidence available.

---

## D87 — One event id held three door times in the design set, and repairing it beat declaring it

**Fork:** D85 recorded the design set's half of the event collision and could not act on it. Reproduced
before acting rather than inherited: `EV-88011` carries `2027-03-19T19:00:00Z` in CALL-01,
`2027-03-26T19:30:00Z` in CALL-02 and `2027-03-19T19:30:00Z` in CALL-18, and all three agree about the
title — which is the only field
`test_one_event_title_per_event_id_except_where_drift_is_seeded` compares, so it ran over the three
transcripts holding the contradiction and reported nothing. Is this a defect to repair, or drift to
declare and seed?

**Options considered.** (A) Repair — read the three as what they are, two performances of a touring
production and two records of one evening, and reconcile them. (B) Declare it in the seeding manifest
as deliberate cross-call drift and author a finding for it. (C) Give all three their own event id,
changing no door time. (D) Leave it, and state the reach.

**Decision: (A).**

**Why** — (B) fails three ways and the first alone settles it. **It would be false.** D85 established
this class was not deliberate, and the manifest's opening sentence is that it exists "so a later reader
can tell a seeded defect from an accident" — the difference being that somebody wrote the seeded one
down *first*. Writing it down afterwards, to make a check green, converts the manifest from a record of
intent into a record of what the checks currently tolerate. Second, a seeded defect earns a finding
(D10), findings are adjudicated by a human, and the gold set is scored: `corpus/findings.severity.json`
pins a comparison-log hash, an 82/7 split and an empty `unplaced`, so a ninetieth finding would break
that join on the day it was written. Third, **cross-call consistency is out of scope for v1** by the
specification's own exclusion (taxonomy 12, 16, 25), so the seeded defect would have no check to detect
it and no report section to carry it. A defect nothing can report is worse than an accident, because
the accident does not also claim to be measured.

(C) is D85's own choice for the held-out set and it does not transfer. It worked there because the two
calls concerned one performance the canon fixed elsewhere. Here it would leave CALL-01 and CALL-18 as
two performances of a chamber ensemble at a 1,100-seat venue **thirty minutes apart on one Friday
evening** — taxonomy 31, external-world plausibility, seeded by accident in the act of repairing an
accident. (D) leaves the corpus contradicting itself in the one repository that can see it.

### The repair is two context values, and nothing else moves

- **CALL-18** `door_time` `2027-03-19T19:30:00Z` → `19:00:00Z`. Both calls concern the same
  Friday-evening performance and CALL-18 never speaks a time — "the show's tonight", at 16:12Z — so
  nothing in speech, in a tool argument or in a tool result moves with it.
- **CALL-02** `event_id` `EV-88011` → `EV-88214`. Its door time is a week later and its caller asks
  about "the 26th": a different performance. One title mapping to several event ids is the corpus's
  established shape rather than an invention — "The Halloway Ensemble at Ridgeline Pavilion" already
  carried five.

**Which value is canonical was not a free choice.** `EV-88011` keeps `2027-03-19T19:00:00Z` because
CALL-01 pins it arithmetically twice — `exchange_window_closes_at := 2027-03-17T19:00:00Z` in context
and `closed_at=2027-03-17T19:00:00Z` in the eligibility result, both exactly the 48 hours
`exchange.v1` § 2.1 states — and because **D85's held-out repair was reconciled against that value.**
Moving it would silently invalidate a repair made in a repository this one cannot check.

**And the gold set had already settled it, which a review pass found and the first draft of this entry
did not.** `2027-03-17T19:00:00Z` is quoted verbatim in five places: twice in `corpus/findings.yaml`,
twice in the drafts, once in the adjudication ledger and once in the generated view. Making `EV-88011`
canonical at `19:30:00Z` would have moved that derived value and taken five pieces of adjudicated
evidence with it, two of them in the artifact judge-versus-human agreement is measured against. So the
choice was never between two defensible values. It is recorded this way round because the weaker
argument — an inference about a sentence in D85, written by a session that could see the other corpus —
was the one reached for first, and the checkable one was sitting in this tree the whole time.

**Consequences / caveats** — seven, and the last two are the ones that outlive this entry.

**No line was inserted or removed in either transcript**, so no event index moved and every positional
anchor in `corpus/seeding-manifest.md` still points where it did. That is the hazard the anchors
section was written for, and it was checked rather than assumed: 15 calls, 375 events, 0 unparsed lines,
every anchor row still resolving.

**Nothing cited either line.** Neither `EV-88011` nor `19:30:00Z` nor the string `event_id` appears in
the gold set, the drafts, the adjudication ledger, the generated view or the manifest, so findings
evidence, manifest anchors and the 89-row gold set are untouched. What moves is the extraction
artifact's content hash, which is what a corpus edit is supposed to move. `CORPUS_VERSION` goes to
**0.5.1** — a repair rather than new content.

**The spec version deliberately does not move.**
`test_the_spec_version_and_the_last_sweep_agree_with_the_changelog` binds the header's version to its
`Last swept` marker, so bumping one here would claim a sweep that did not happen — the failure D71
recorded and D74 refused to make mechanical. A corpus repair is recorded in `CORPUS_VERSION` and here,
which is what those two markers are for.

**The port is a sibling, not a widening, and the reason is a record's.** D85's Rule line names
`test_one_event_title_per_event_id_except_where_drift_is_seeded`; a record may not be left citing a
test that has been renamed or re-scoped underneath it. So `test_one_event_id_means_one_event` lands
beside it, comparing every field in `_EVENT_SCOPED_FIELDS` — `event_title` and `door_time` — with **no
seeded-drift exemption**, for the reason D85 gave when the held-out port declined one: an exemption
sized for naming drift is a hole in a door-time check. The comparison floor is **per field**, because
an aggregate floor would let `door_time` fall to zero behind `event_title`'s nine. Today it makes nine
title comparisons and eight door-time comparisons — measured by running it, after the first draft of
this sentence guessed seven and was wrong, which is the whole argument for the floor being a
measurement rather than a remembered number.

**The control was planted, and its second half is the point.** With the pre-repair values restored,
`test_one_event_id_means_one_event` names all three disagreeing pairs while
`test_one_event_title_per_event_id_except_where_drift_is_seeded` **passes on the same three
transcripts** — which is D85's finding, reproduced in this repository rather than inferred from the
other one. That demonstration is committed rather than left in this paragraph: the control plants
CALL-18's old value on a copy and asserts both halves.

**Event ids are now a shared namespace with nothing watching it.** D85 allocated a new id in the
held-out set whose value this repository does not know; this entry allocates `EV-88214`, whose value
that repository does not know. Two corpora drawing from one `EV-#####` space with no check on either
side is `HOLDOUT-OBLIGATIONS.md`'s own shape exactly, so it is recorded there rather than here.

**Found while checking this repair's neighborhood, and deliberately not acted on: CALL-01 asks for a
Saturday and is given a Sunday.** The caller says *"the Saturday performance"*, event 8 calls
`find_performance(..., when="saturday")`, and event 9 returns `EV-88120` with
`door_time=2027-03-21T19:00:00Z` — **2027-03-21 is a Sunday**, and no timezone reading rescues it
(19:00Z is noon PDT the same day). The agent then names the Saturday performance again at event 16, and
two findings quote that phrase as the target. `corpus/seeding-manifest.md` declares CALL-01 as seeding
taxonomy 11, 15 and 34; a date read out of the wrong day is CALL-19's class, declared for CALL-19 only.
So it is undeclared, and it is *not* the same defect this entry repairs — it is a claim about a day
name rather than a disagreement between calls, and no check in this repository looks at either. Two
readings are open and neither is settled here: an undeclared defect in CALL-01's platform data, or a
corpus-wide looseness about writing evening door times as `19:00Z` that only CALL-19 ever makes
load-bearing. **Recorded rather than repaired**, because deciding which reading holds is corpus work
with a wider blast radius than this entry's, and because the honest output of a check is partly what it
found and did not fix.

**Rule** — `test_one_event_id_means_one_event` compares every event-scoped field across calls sharing
an id and asserts a per-field comparison floor;
`test_the_event_scoped_check_fires_on_a_door_time_its_titles_agree_with` is its control, planting the
pre-repair value and asserting that the title comparison stays green on it. **Whether two calls a week
apart are two performances or one mis-stated date is judgment, not checkable** — a check can say the
corpus disagrees with itself, never which side of the disagreement is right.

---

## D88 — The escalation convention moves into the canon, and the token D73 left open gets its answer

**Fork:** three things landed on "a design-corpus session" and are settled together because they are one
subject. D86 asked that the escalation convention move out of `corpus/seeding-manifest.md` and into
`corpus/entities.md`, having found it unreachable from a curated authoring packet. H-16 asked for a
decision on `Outcome.transferred`, which D73 called a schema smell without saying whether it should go.
And D83 left a check owed: the register's `Design set:` line is prose about `corpus/DESIGN_SET` and
nothing compared the two.

**Options considered**, for the token, since the other two were tasks rather than forks. (A) Remove
`transferred` from `Outcome`. (B) Keep it, and write into the register that this corpus never uses it
and why. (C) Keep it and say nothing, which is the state H-16 objects to.

**Decision: (B)**, with the convention and the explanation written as one register passage and both
halves bound by tests.

**Why not (A)** — removal is the tempting reading of "schema smell" and it contradicts D39. The closed
vocabularies are deliberately wider than any corpus needs, so that an adapter receives what vendors
send; a platform emitting `outcome: transferred` is one this harness is meant to be able to read, and a
parser refusing it would fail on real data in order to forbid a token no transcript writes. That is the
worse failure of the two. **What was missing was never the token.** It was that nothing said when the
value is correct, so a reader met a declared member of a closed vocabulary with no guidance beside it
and reasonably picked it — which is precisely what happened. (C) is that state, restated.

**What the register now carries**, in three paragraphs: the three fields an escalation sets and what
each one answers, with D73's failed-handoff variant (`outcome: unresolved`, the other two unchanged);
why `Outcome.transferred` is not among them and why it stays declared regardless; and why the passage
belongs in the register rather than the manifest.

**It names no transcript, and that is the load-bearing detail rather than a stylistic one.** D86's
finding is that the convention could not reach a curated authoring packet: the manifest is a design-set
artifact the packet does not carry, and the register's existing escalation paragraph *is* carried but
redacted, because it names a design call. A convention stated with a call id attached would be redacted
the same way and would not arrive. Stated without one, it passes the packet's leak scan intact. **The
mechanism that prevents a twin no longer also prevents the author learning the rule**, which is what
D86 said the right repair would achieve — and it is achieved by how the sentence is written, not by
loosening the packet, which D86 named as the wrong instinct.

**Consequences / caveats** — six.

**Four checks, and the division between them is the point.**
`test_an_escalated_call_records_the_escalation_convention` holds the corpus to the rule and asserts a
floor, because a corpus that stopped escalating anything would satisfy the rule by having nothing to
check. `test_no_call_files_its_outcome_as_transferred` holds the other direction, and also asserts the
register still *declares* the token — so "declared and deliberately unused" cannot quietly become
"undeclared", which is a different and worse state wearing the same green tick.
`test_the_register_states_which_outcome_an_escalation_takes` holds the **canon** rather than the corpus:
a test asserting that the corpus follows a convention teaches the convention to nobody, and the whole
defect was that the rule was unreadable where it was needed. And
`test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` plants D86's actual defect
on a copy — one substitution, both values in the closed vocabulary, the parser accepting either.

**One assertion was written and then deleted for being unfalsifiable.** The first draft of the token
check opened with `Outcome.TRANSFERRED in set(Outcome)`, which cannot fail: removing the member breaks
the test module's import instead, so the assertion decorates a failure that happens somewhere else. It
was replaced with one that can fail — that the register's `**Outcomes.**` paragraph still declares the
token. Recorded because the suite is full of tests written to catch exactly this and it was still the
first thing typed.

**The register check requires all three pairs in one paragraph**, not three anywhere in the file, and
its control deletes the paragraph it found and asserts that nothing else states the rule. One
convention stated in three places is three things that can disagree, which is the condition this entry
exists to end; a check indifferent to that would tolerate the state it was written against.

**D83's owed check is written, and it covers the held-out enumeration too.** The register's `Design
set:` line and its `Held-out set:` line are both prose about a declaration this repository holds, both
written as a range plus stragglers, and both have gone stale by addition within the last week — the
first when `CALL-20` was added, the second when `CALL-21` was. One helper reads either line, expands
the range, and compares. Writing only the design half, in the entry whose subject is a guard narrower
than its rule, would have been that defect committed twice.

**The size guard would not have caught either, and did not.**
`test_every_worded_design_set_size_agrees_with_the_declaration` reads number *words* followed by a
countable noun; neither line states a number. They enumerate. **A list and a count decay identically
and are caught by different checks**, so the size guard's green tick was never evidence about the
enumeration, and for as long as only one existed a reader could not tell which had been checked.

**The controls plant what actually happened rather than something invented.** Dropping `CALL-20` from
the design line reproduces what D83 found in the register; dropping `CALL-21` from the held-out line
reproduces what was found in three documents on 2026-09-06. Both were observed to fail before the
checks were trusted.

**Rule** — `test_an_escalated_call_records_the_escalation_convention` and
`test_no_call_files_its_outcome_as_transferred` bind the corpus to the convention in both directions;
`test_the_register_states_which_outcome_an_escalation_takes` and
`test_the_register_says_why_the_transferred_outcome_is_unused` bind the canon to it;
`test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` is the plant;
`test_the_registers_design_set_enumeration_agrees_with_the_declaration`,
`test_the_registers_held_out_enumeration_agrees_with_the_declaration` and
`test_the_enumeration_check_fires_on_the_call_that_actually_went_missing` close D83's owed check and its
control. **Whether the held-out set follows the convention is not checkable here** — it is recorded as
an obligation, because the only repository that can run that check is the one this cannot see into.

---

## D89 — Three counts wrong against the corpus, and the guard that should have seen one of them is case-blind

**Fork:** an audit reported three quantified statements in the corpus documents as wrong. Each was
verified against the corpus before being touched, per the rule that produced this project's better
fixes; all three reproduce, and one of them is wrong in a way the audit did not name. The fork is what
to write in their place, and what to do about the guard that was built for exactly this and did not
fire.

**Options considered.** (A) Correct each number. (B) Correct them and widen the guard that missed one.
(C) Rewrite them so they cannot decay at all, and treat the guard separately.

**Decision: (C)**, which is D74's own decision arrived at again, on statements D74's pass did not reach.

**What was verified, and what it turned out to be.**

`corpus/entities.md` said *"Thirteen design calls carry `caller_ani`; CALL-18 carries
`booking_reference`."* Measured: **every** design call carries `caller_ani` and **every** design call
carries `booking_reference`. So the sentence is wrong three times over, and only the first was
reported. The count is stale by addition. The count is also of the wrong thing — the sentence reads as
though the two populations differ, and they are the same population. And what actually distinguishes
the call it names is the *value of `matched_by`*, which is the variable the paragraph exists to
explain. Rewritten to state the distinction rather than count either population.

`corpus/seeding-manifest.md` said *"Without the **eleven**"* beside a list of **twelve**, and *"the
**fourteenth** uses something weaker still"* in a set that had grown past both numbers. Both verified: the list is twelve
and it equals what `test_the_verification_true_negatives_are_the_calls_that_verify` derives from the
corpus, so the list was right and the word beside it was wrong; and the ordinal is a leftover from a
shorter corpus, referring redundantly to a call the same sentence had already named. Rewritten to
"the calls listed here", and to the wording the finding itself already uses — F-56 was rewritten to
D74's shape and the manifest's paraphrase of it was not, which is how a de-quantified claim and its
quantified summary ended up in the same repository.

**Consequences / caveats** — six.

**The guard that should have caught the register's count is case-sensitive, and that is why it did
not.** `test_every_worded_design_set_size_agrees_with_the_declaration` scans nine documents including
that one, and its pattern matches a number word followed by the noun -- in lower case only. The
register's sentence opened with the number, so a capital letter was the whole of the miss. Its sibling
`_HELDOUT_SET_SIZE`, written four days later for the same class of defect, carries `re.IGNORECASE`.
**Verified rather than reasoned about:** running the pattern with the flag added reports the register's
sentence and nothing else in the live documents, plus one historical count in this record.

**This entry could not quote the sentence it is about, which is a constraint the repair has to carry.**
The paragraph above first spelled out the lower-case collocation as an illustration, and the guard read
the illustration as a claim and failed the build. So a document explaining a checker cannot contain the
checker's trigger, and a record quoting a corrected sentence verbatim is a record the checker will
eventually reject. The recall net needs an exemption class for quoted historical text or it will make
this record unwritable -- noted here rather than discovered there.

**And it is deliberately not patched here.** Adding the flag treats this instance; the class is that a
pattern-matching guard **fails open**, so a number it cannot parse is a number nothing checks and
silence is indistinguishable from success. Every count defect found in this project has that shape:
capitalization here, a number not adjacent to its noun in the manifest, an ordinal beside it, an
endpoint range for the held-out set, and a measured figure sitting behind a `>=` floor in the test
suite. The repair is a **recall net** — a deliberately over-broad pattern that finds *sites* rather
than values, with every site it finds required to be either parsed by a strict checker or exempted
with a reason. That is agreed work and follows this entry; patching the flag first would remove the
only live example it can be planted against.

**A count was written into this repair and the guard caught it, red, within the minute.** The
manifest's correction note first described the shorter corpus by writing its size as a word beside the
noun `call`, which is precisely the collocation `_DESIGN_SET_SIZE` matches -- and it failed, against a
design set that is no longer that size. The escape hatch the file
declares is to write historical counts as digits; it was not taken, because a de-quantified sentence
needs no escape hatch. Recorded because it is the cheapest available evidence that the guard works
where it can see, which is the other half of the paragraph above.

**The register's claim now has a check, and the check is narrower than the claim.** Said plainly rather
than left to be assumed: `test_the_register_names_every_call_matched_on_something_other_than_the_number`
compares **call ids**, so it binds the repaired sentence and would have *passed* on the sentence that
prompted it — which named the right call and the wrong number. Of the three failures in that one
sentence, the check closes one, the size guard would have closed the second had it not been case-blind,
and the third — counting which calls *carry* a variable when the claim is about which value `matched_by`
takes — needed a reader and still does.

**One correction is invisible from here and is recorded rather than made.** The held-out authoring
packet redacts the register's `caller_ani` sentence by exact string, so that pattern is now stale.
The leak scan is what guards it and it fails closed, which is the correct behavior — but the redacted
text it was replacing was, as it happens, **the accurate claim**: "Most design calls carry `caller_ani`;
at least one carries `booking_reference` instead." The de-quantified version written for the packet was
right about the corpus for as long as the register's own version was wrong. Filed as an obligation.

**Rule** — `test_the_register_names_every_call_matched_on_something_other_than_the_number` binds the
register's `matched_by` claim to the corpus and
`test_the_matched_by_check_fires_when_the_register_names_the_wrong_call` is its control;
`test_every_design_call_carries_both_a_calling_number_and_a_booking_reference` binds the half the old
sentence got wrong; `test_the_verification_true_negatives_are_the_calls_that_verify` already bound the
manifest's list and continues to, which is why only the words beside it were wrong. **That the
rewritten claims still mean what was adjudicated is judgment, not checkable** — D74's own caveat,
applying again to three more sentences.

---

## D90 — The count checkers fail open, so a net finds sites and an inventory has to account for them

**Fork:** five count defects reached commits in three days, and a guard built for that exact class
missed each one for a different reason — a capital letter, a number not adjacent to its noun, an
ordinal, an endpoint range, digits where the pattern reads only words. Patch the patterns as the
instances arrive, or change the direction the checking runs in?

**Options considered.** (A) Correct each pattern when an instance is found. (B) Add `re.IGNORECASE`,
ordinals and digits to the existing guards in one pass. (C) Keep the strict checkers for *values*, and
add a deliberately over-broad net that finds **sites**, with every site required to be accounted for.

**Decision: (C).**

**Why** — (A) is what has been happening. (B) is (A) done in advance and it does not change the
property that matters: **a strict checker verifies a value and says nothing at all about a site it
could not parse.** It fails open, so a number outside its pattern is a number nothing checks, and
silence is indistinguishable from success. Every one of the five is that, and the sixth would be a
shape nobody has thought of yet. (C) inverts it: the net cannot verify anything, and does not try —
its only job is to refuse to be quiet. A number in live prose that no checker parses and no entry
declares fails the build with its own text quoted.

**Keyed on `(document, number, noun)`**, not on the sentence. Rewording passes; changing a number
fails. That is exactly the behavior wanted, since the edit that moves a count is the edit that needs
looking at, and a key that failed on every rewording is a check somebody switches off inside a week.

**The inventory has three kinds of entry and the third is the useful one.** *VERIFIED* names the
checker that compares the value. *HISTORICAL* means the sentence is dated or explicitly past-tense in
a live document, so it is a record and correct. *UNCHECKED* means neither — a live count nothing
computes. That last list is this project's inventory of claims it carries on trust; it is short, it is
now visible, and it should shrink.

**Consequences / caveats** — seven, and the first is what the mechanism is worth.

**It found a stale live count on its first run, in the file whose entire purpose is preventing them.**
`HOLDOUT-OBLIGATIONS.md` read *"the same rule, in all five transcripts"* as a present-tense
requirement while the held-out set holds six. De-quantified rather than re-pinned (D74). The reason
nothing caught it: `_HELDOUT_SET_SIZE` scans the specification and the phase-1 verifier, and that file
is not among them — the audit that prescribed the guard named the briefs and the handover too, and the
implementation reached two of the six locations.

**And a second scope gap beside it.** `_HELDOUT_SET_SIZE` requires the literal `held-out` after the
number, so *"the six transcripts it declares"* in `tools/verify_phase1.py` — a held-out count, correct
today — is outside it. Declared UNCHECKED with the gap named as the guard's rather than the sentence's.

**Two false-positive classes, both worth having found.** `sum(1 for criterion in CRITERIA)` is Python,
not prose: the verifier is scanned because its criterion *text* is read by a human, and its code is
not. And `Sonnet 5 for dimensions, Opus 5 for synthesis` is a **model name** — the digit is a version
and moves when a vendor ships, not when this corpus grows.

**The net's own gap is asserted, not merely admitted.** `Without the eleven` puts no noun beside its
number; it stands in for a list named earlier, so no noun-anchored net reaches it. Extending to bare
number words was **measured rather than argued about**: 152 sites, almost all of them `the two
together`, `the one place`, `the twenty-two dollars`. A net at that signal-to-noise is a net somebody
turns off. So the shape is asserted as a *non-match*, which stops the gap being forgotten into a claim
of coverage the way this entry's own first draft did.

**Two of this entry's claims were falsified by the tests written to hold them, on the commit that
introduced them.** The section comment and a docstring both claimed the net reproduced all five
instances; it reproduces four, and the assertion listing them said so. And the inventory's first draft
generated the product of six documents and two nouns, declaring seven shapes that do not exist —
rejected by `test_no_declared_count_has_quietly_stopped_existing`, which exists because a declaration
matching nothing will silently absolve whatever takes its shape next. A mechanism catching its author
twice in an hour is the cheapest evidence available that it binds.

**The numeral-form question was raised and settled the other way.** Expressing every count in digits
was considered and rejected: this tree already uses numeral form to carry meaning — **words are a live
claim and get checked, digits mark a historical one and are exempt** — and *17 of the 50 declared
shapes are historical statements inside live documents*, ten of them already digits because the
convention is being followed. Flipping it would strand every one of those in a per-site exemption
list, edit records for presentation, and put the scored gold set's text at risk for a formatting gain.
What the instinct was actually reaching for is that the marker is **implicit**: it lives in one comment
in one test file and is invisible at the site. That is what tagging fixes, and it is the next entry's
subject rather than a reason to invert a working convention.

**What none of this catches**, said here because an inventory's honest output is partly the list of
what it cannot check: a number that is right and describes the wrong thing — which is what
`corpus/entities.md` was doing when it counted the calls *carrying* `caller_ani` rather than the calls
*matched on* it (D89). The net sees a count. Whether it is a count of the right population is a
reader's judgment and stays one.

**Rule** — `test_every_countable_claim_in_live_prose_is_checked_or_declared` requires every site to be
verified, historical or declared unchecked; `test_no_declared_count_has_quietly_stopped_existing` binds
the other direction so a stale classification cannot absolve a later site;
`test_the_recall_net_fires_on_a_count_nobody_declared` is the plant; and
`test_the_net_would_have_seen_every_count_defect_this_project_has_found` holds the net to the instances
it was written after **and to the one it does not reach**. **Whether a declared HISTORICAL entry really
is historical is judgment, not checkable** — the net can see that a sentence states a number, never
that the sentence is about the past.

---

## D91 — A floor and an equality answer different questions, and a stated measurement gets the equality

**Fork:** `test_the_contradiction_check_is_comparing_something` carried a comment reading *"`door_time`
yields two comparisons across the corpus and the other eight yield zero"* and an assertion reading
`total >= 2`. Measured on the committed corpus: four comparisons, across three fields. The sentence had
been wrong for an unknown span and the check had been green throughout, because **four satisfies a
floor of two exactly as well as two does.** How should a number stated in prose be held?

**Options considered.** (A) Correct the sentence. (B) Correct it and assert equality on that one check.
(C) Make it a rule, and make stated measurements findable so the rule can be enforced rather than
remembered.

**Decision: (C).**

**Why** — (A) is what produced the defect: the sentence was right when written. (B) fixes one site and
leaves every other stated measurement in the suite in the same position. The distinction worth naming
is between two different things a number in a test can be. **A floor answers *is this guard blind?*.
A measurement answers *how much does it reach?*.** A floor is correct for the first and structurally
incapable of holding the second, and this suite had been using one for both. Both are kept: the floor
keeps its message about blindness, and an equality against `MEASURED` holds the number the prose
states.

**`Measured:` becomes a marker rather than a word**, capitalized and closed by a colon. A scan over
comments and string literals — tokenized, so identifiers like `measured = 0` are not mistaken for
claims — reports every site, and each must be **dated** ("Measured when this was written") or **bound**
to an equality, with the disposition declared.

**Consequences / caveats** — six, and four of them are the check catching its author.

**The first draft matched the bare English word and was unusable.** Ten sites, of which one was real:
`measured against it`, `measured as a span` and `what is written is what is measured` are the verb in
another sense, and **four of the ten were this check's own prose about measurement.** That is D89's
constraint — a document explaining a checker cannot contain the checker's trigger — arriving one file
over and in the checker itself. Requiring the colon is what made the signal usable.

**The control's plant is assembled at runtime**, because a literal would sit in a file the scan reads
and the test would fail on its own control. The comment beside it says so, since the next reader will
otherwise tidy it back into a string and turn the suite red.

**The disposition keys had to stop containing the marker.** A key is a string literal in a scanned
file, so a key beginning `Measured:` became its own second site — the check reporting the register that
classifies it. Fixed by requiring the number through a **lookahead** rather than consuming it, so the
excerpt is a fixed window and a key can be a distinctive tail instead.

**What it found outside itself.** `tools/make_gold_set.py` read *"No row in the corpus needs one today
— an independent sweep measured zero across all 86"*, supporting a present-tense claim with a count
taken when the corpus held 86 rows and now holds 89. De-quantified, and the residue stated: rows added
since have not been re-checked. **It sits outside the marker** (lower case, no colon), which is the
convention's honest cost — a convention works where it is used, and this check cannot find what does
not use it.

**One thing measured and deliberately not reported as a defect.** Checking that sentence turned up
that 41 of the 89 gold-set rows carry a newline inside a value. That does *not* falsify it: "needs a
literal scalar" is a different predicate from "contains a newline", and a folded scalar preserves
paragraph breaks. The predicate is not operationalized, so the claim cannot be bound — recorded as
unresolved rather than written up as a finding, because reporting an unfalsified claim as false is the
mirror of the defect this entry is about.

**Rule** — `MEASURED` holds the two distributions this suite states, asserted by equality in
`test_the_contradiction_check_is_comparing_something` and `test_one_event_id_means_one_event`;
`test_every_stated_measurement_is_dated_or_bound` requires every marked site to be one or the other;
`test_no_stated_measurement_declaration_has_gone_stale` binds the other direction; and
`test_the_measurement_scan_fires_on_an_undated_unbound_number` is the plant. **Whether a site declared
DATED really is dated is judgment, not checkable** — the scan reads that a sentence carries a
qualifier, never that the qualifier is true.

---

## D92 — A count that says which quantity it is, because inferring that from the surrounding words has a ceiling

**Fork:** the strict guards infer *which* quantity a number states from the words beside it — a number
word followed by `design calls` is taken to be the design-set size. D90 measured that approach's
ceiling: a number with **no noun beside it** is outside every noun-anchored pattern, and widening a net
to bare number words returns 152 sites of which almost none are counts. `Without the eleven` is that
shape and it is why D89's repair had to be a rewording rather than a check. What holds a count that no
pattern can identify?

**Options considered.** (A) Accept the ceiling and rely on rewording — de-quantify anything a pattern
cannot reach. (B) Keep widening patterns as new phrasings appear. (C) Let the **site** say which
quantity it states, and check by identity.

**Decision: (C)**, scoped to the three documents a reader takes as current.

**Why** — (A) is what D74 and D89 both did and it works, but it is a rule applied by whoever remembers
it, and de-quantifying is not always available: some claims need the number. (B) is D90's rejected
option arriving again. (C) removes the inference entirely: `sixteen design calls<!-- #design_set_size
-->` is checked against `len(corpus/DESIGN_SET)` because the tag says so, not because a pattern guessed
right. And it is the **only** mechanism that reaches the un-nettable shape — a future sentence phrased
with no noun beside its number can still be tagged.

**An HTML comment**, because it is invisible when the Markdown renders, greppable, and needs no tooling
this repository does not already have. Placed after the noun phrase rather than after the number, so
the existing strict guards still match the number and its noun and nothing already working is
disturbed.

**Consequences / caveats** — five.

**Nine sites, and the registry has three entries.** `design_set_size` (seven sites), `judged_dimensions`
and `taxonomy_items`. Both directions are asserted: a tag naming no declared quantity fails, and **a
declared quantity nothing tags fails too** — a registry entry no document uses is not coverage, and a
reader meeting the registry would take it for exactly that.

**`heldout_set_size` is deliberately not in the registry.** Nothing in the tagged documents states it as
a number: the register states it as an *enumeration*, which
`test_the_registers_held_out_enumeration_agrees_with_the_declaration` binds, and the specification was
de-quantified when the set grew. Adding it would have been a registry entry computing something no
document claims, which is the shape the paragraph above refuses.

**`corpus/seeding-manifest.md` is in scope and carries no tag, and that is a result rather than an
omission.** De-quantifying its two wrong counts (D89) left it stating no derived quantity at all. The
document is listed as tagged-with-nothing rather than dropped from the list, because a document quietly
outside a convention and a document deliberately empty of it look identical until one is written down —
which is D74's per-document-minimums argument, arriving a third time.

**The control was written unfalsifiable and rewritten.** Its first draft compared two integers it had
just computed, which cannot fail; it now changes the number in front of a real tag in the real
document, re-runs the real extraction, and asserts the real comparison rejects it. That is the third
time in this run of entries that the first thing typed was an assertion incapable of failing — D88
deleted one, D91 deleted one, and this is the third. Worth recording as a pattern rather than three
coincidences: **the natural way to write a test for a thing you have just made true is to restate that
it is true.**

**What this does not do.** It checks that a tagged number equals what computes it. It cannot know that
an *untagged* number should have been tagged — that is the recall net's job, and the two are
complementary rather than overlapping: the net finds sites and forces a disposition, and a tag is the
strongest disposition available. Nothing yet requires a site the net classifies as VERIFIED to carry a
tag, and doing so is the obvious next tightening.

**Rule** — `test_every_tagged_quantity_states_the_number_it_names` checks each tag by identity against
`_quantities()`; `test_no_declared_quantity_is_unused_and_no_tag_is_undeclared` binds both directions
so neither the registry nor the tag set can grow a member the other does not know about; and
`test_the_tag_check_fires_on_a_number_that_disagrees_with_its_tag` plants a wrong number under a right
tag in the real document. **Whether a claim deserves a tag is judgment, not checkable** — the mechanism
can hold a tagged number and can say nothing about a sentence nobody tagged.

---

## D93 — The scenario map missed two migrations, and superseding it was not available

**Fork:** an audit found `specs/taxonomy-scenario-map.md` claiming currency while describing format v1
and the pre-D44 canon, and offered two ways out: banner it SUPERSEDED like the build prompt, or bring
it current and add a check over its vocabulary. Every line it cited was reproduced first. **All eight
hold**, two of them differently from how the report put them.

**Options considered.** (A) Banner it SUPERSEDED. (B) Bring it current — migrate the stale tokens, fix
the banner, add the vocabulary check. (C) Bring it current *and* re-derive all 35 rows against the
sixteen-call design set.

**Decision: (B).**

**Why (A) is not available**, which is the part that settled this before the merits were reached.
The map is load-bearing in three ways right now. `specs/taxonomy-coverage.md` calls it **"the
authoritative allocation"** in a live sentence. `test_the_scenario_map_allocates_every_taxonomy_item`
is a phase-1 acceptance check requiring a row per taxonomy item.
And `test_every_judged_taxonomy_item_has_a_judge_finding` reads its rows to bind each judged
dimension to the finding that instantiates it — the guard added after re-classifying F-10 silently
emptied taxonomy 31. Superseding the map would retire the only mapping from taxonomy item to scenario
to finding, which is the binding that stops a judged dimension emptying unnoticed. A document three
live things depend on cannot be marked do-not-trust; it has to be made trustworthy.

**And the staleness is not superseded planning, which is what a SUPERSEDED banner would imply.** It is
**two missed migrations**. D40 took the format to v2 and the map kept `CONFIG`, `call_ended`,
`duration_seconds`, `UNAVAILABLE` and a tool result "returning `OK`" — none of them a token in any
vocabulary this project has ever declared. D44 moved the corpus from British to American, *including
entity names*, and the map kept **`Thornbury Building Society`** — a building society, which is a
British institution, in a corpus set in California. D44's own argument applies to its own residue:
half-localized is worse than either end, because what a reader notices is that nobody was paying
attention. A document that missed a migration gets migrated.

**(C) is refused for D66's reason and because the debt is already paid.** Extending the map means
either renumbering the 35-item taxonomy — which would silently change what "taxonomy 17" means in five
other files — or bolting on a second numbering. The second numbering already exists: `S1`–`S11` in
`specs/taxonomy-coverage.md` Part 2b.

**Consequences / caveats** — six.

**Two of the audit's eight claims were imprecise and reproducing changed the fix.** It reported
`payment_instrument` at row 17 as though the corpus did not carry it; CALL-10 carries **both**
`payment_instrument` and `charge_count`, and the defect is narrower — the agent's line is *"there's only
one charge against this booking"*, which is `charge_count`, so the map named the field that does not
support the behavior it describes. And it said `specs/error-type-sweep.md` "does not map" CALL-20;
that file *mentions* CALL-20, in an open question about transfer failure paths, and simply has no
scenario row for it. Both fixes stand, arrived at differently. **That is three of the last two audits'
claims needing correction on reproduction, which is the argument for the rule rather than against
commissioning audits.**

**The banner said extending the map was owed; it had been paid into three documents.** `CALL-18` and
`CALL-19` carry scenario rows with finding ids in the error-type sweep, `CALL-20`'s class is `S11` in
the coverage map, and all three have rows in `corpus/seeding-manifest.md` Part 2 — the one document
that allocates every design call. The banner enumerated two of the three and had not noticed the debt
was discharged elsewhere. Rewritten to point at where each lives.

**The guard rejected the correction's own wording, in the right direction.** The new banner first
wrote the scope as a number **word** beside the noun `calls`, and both count guards failed it against a
design set of fifteen. The convention the tree already declares is that a **historical count is written as a
digit**, which is what the document's two existing historical counts do. Rewritten to "the 12 calls".
Recorded because it is the clearest evidence available that the words/digits distinction is doing work:
it was examined this same day and deliberately kept rather than flipped, and an hour later it caught a
sentence that would otherwise have read as a claim the design set had shrunk. **And this paragraph
could not quote the wording it is about**, for the third time in five entries — D89 recorded the
constraint, D91 hit it inside the checker itself, and here it reaches a record describing a rejected
draft. The tax is real and small; naming it each time is what stops someone paying it by loosening a
guard instead.

**The vocabulary check found a gap in itself before it found one in the document.** Its first draft
assembled the declared set from the register, the event model, the enums, the policies and the parsed
corpus — and reported `call.ended` as undeclared, a name every call in the corpus emits, because
SYSTEM event bodies were the one source not collected. **A vocabulary assembled from four sources is
wrong in whichever direction the fifth would have corrected**, and the only way to find out is to run
it against a document that uses the language properly.

**And a measurement taken the wrong way invented a defect.** Comparing the map's proper nouns against
raw transcript **bytes** reported `Brightwater Live` as undeclared — the seeded naming drift in
CALL-08, which wraps across two source lines. The parser reassembles it; a byte scan does not. So a raw
comparison manufactures a finding in the one place the corpus deliberately carries one, which is W16
and W17's shape arriving in a check rather than in the parser. The check compares against the parsed
corpus.

**Rule** — `test_every_token_the_scenario_map_names_is_declared_somewhere` requires every backticked
identifier in the map to be a name the register, the event model, a closed vocabulary, the policy set,
the findings keys or the parsed corpus declares, with a floor so it cannot pass by reading nothing;
`test_the_scenario_map_names_no_undeclared_entity` requires every multi-word proper noun to be a
declared entity or one the corpus uses; and
`test_the_scenario_map_checks_fire_on_a_token_and_an_entity_nothing_declares` is the control, planting
`CONFIG` and `Thornbury Building Society` — the two migrations that actually happened, rather than
invented defects. Both were observed to fail on the pre-repair document before being trusted.
**Whether a scenario still describes the call it is allocated to is judgment, not checkable** — the
checks read vocabulary, never whether the sentence is a fair account of the transcript.

**Corrected 2026-09-07, in place and with the correction attached.** This entry named the guard
`test_every_judged_dimension_has_an_instance_in_the_corpus`, which has never existed; the guard is
`test_every_judged_taxonomy_item_has_a_judge_finding`. **The error is this entry's own subject** — it
argues the map is load-bearing because a named test reads it, and it named the test wrongly. D73's
Rule line did the same thing and `test_every_test_named_in_a_rule_line_exists` was written to catch
it, which it did not: the miscitation sat in consequence prose rather than in a Rule line, and in a
comment in the test file besides. D94 widens the guard to both places.

---

## D94 — Three documents named things that were not there, and the guard for that class read one file

**Fork:** an audit's H-9 reported two documents still calling the drafts "the findings document" and
an adjudication ledger header naming a test that no longer exists. Correct the sentences, or treat the
class?

**Options considered.** (A) Correct the three sentences. (B) Correct them and widen
`test_every_test_named_in_a_rule_line_exists`, whose own scope the audit named as the reason nothing
caught the ledger.

**Decision: (B).**

**Why** — (A) is what left them there. The Rule-line guard exists because D73's Rule line named a
guard that did not exist under that name, and it was scoped to Rule lines in this record because that
is where the defect had been found. **A name in prose is the same claim as a name in a Rule line** —
it says a mechanism exists and can be looked at — and every other document naming one was unchecked.

**What reproducing found that the report did not.**

The manifest's two pointers are as reported: D77 made `corpus/findings.yaml` the findings document and
the drafts the drafts, and the manifest kept naming the drafts. Corrected, with the substitution
named, because D77's own subject is a generated view of the drafts standing in for a gold set that
differed from it in 21 rows of 89.

**The ledger header carried a second defect nobody had cited.** Beside the retired test name it said
`corpus/findings.yaml` *"is the gold set and does not exist until adjudication is complete"* — present
tense, while that file has existed since 2026-09-01. **That is the same sentence the audit found in
`src/harness/core/severity.py`**, which was corrected on 2026-09-06; the correction did not reach here,
because nothing compares a claim that a path is absent against the path. Both sentences in this header
are now corrected in place with the correction attached, which is D74's treatment: a record that
quietly becomes right is not one.

**And the third instance was this session's own, from the hour before.** D93 and a comment in the test
suite both named `test_every_judged_dimension_has_an_instance_in_the_corpus`, a guard that **has never
existed under any name** — the real one is `test_every_judged_taxonomy_item_has_a_judge_finding`. The
error sits in the entry arguing that the scenario map is load-bearing *because a named test reads its
rows*, so the sentence claiming a mechanism is the sentence that got the mechanism's name wrong. It
passed every check: the Rule-line guard reads Rule lines and this was consequence prose, and
`tools/statement_inventory.py` resolves paths, findings, call ids and decision numbers but not test
names outside that one context.

**Consequences / caveats** — five.

**The decision record keeps the narrower guard, deliberately.** The widened check reads the corpus
documents, the specifications other than this record, the obligations register and the suite's own
comments and docstrings. This file is excluded for the reason the Rule-line check's docstring already
gives: the record names tests *as they were then*, and D57 discusses two by their pre-rename names
while describing what they did wrong. Reading every name here would demand rewriting history to
satisfy a checker, which is D53 arriving from the other direction.

**Names wrap, and a scan that does not rejoin them invents defects.** Two real tests are cited in the
suite as `..._only_where_` / `it_is_seeded` and `..._agrees_with_` / `the_declaration`, broken across
a line by the wrap. The first draft reported both as missing — two manufactured defects against one
real one. **This is the third time in this session** that a measurement taken without rejoining
wrapped text produced a false finding: the same shape found `Brightwater Live` undeclared in D93, and
W16 and W17 are where the parser learned it.

**The controls had to be assembled at runtime, for the fifth time.** A literal plant would sit in a
file this check reads, so the check would report its own control. Splitting the prefix is the whole
trick, and the comment says so, because the next reader will otherwise tidy it back into one string.
Five instances in one session is no longer a coincidence worth noting once: **a checker that reads
prose cannot describe itself in prose**, and every one of these mechanisms pays that tax. Naming it
each time is what stops someone paying it by loosening the guard instead.

**The exemptions were global by name, and a plant proved that blind.** The first draft keyed on the
name alone, so `test_the_review_worksheet_on_disk_is_current` — legitimately quoted by the ledger
correcting itself — could have been written into *any* document with the guard staying quiet. It was
found by planting the retired name in the manifest and watching the suite stay green. **The committed
control had passed throughout**, because it exercised the extraction and not the exemption: a check
narrower than the claim made for it, written in the commit closing three of exactly that. Exemptions
are now scoped to the document that may name them, and a second assertion rejects an exemption whose
document has stopped naming it.

**Three exemptions, each with a reason, and a check that they stay true.** One name is quoted *as
gone* by the ledger correcting itself; two are checks that live in the held-out repository and are
named in the obligations register, which is that file's whole purpose. `test_no_exempted_test_name_
has_quietly_come_back` binds the other direction, because an exemption for a name that later exists
absolves whatever takes its place.

**Rule** — `test_every_test_name_in_prose_exists` requires every `test_*` name in the corpus
documents, the non-record specifications, the obligations register and the suite's own prose to be a
test that exists here or a declared exemption, with a floor so it cannot pass by reading nothing;
`test_no_exempted_test_name_has_quietly_come_back` holds the exemption list;
`test_the_name_check_fires_on_an_invented_test_and_rejoins_a_wrapped_one` plants both failure modes —
the invented name this entry is about, and a real name broken across a line.
`test_every_test_named_in_a_rule_line_exists` is unchanged and still owns this record. **Whether a
test that exists is the test the sentence means is judgment, not checkable** — a name can resolve and
still be the wrong mechanism to cite, which is a stronger version of the same error and one no scan
reaches.

---

## D95 — The specification described a workflow it no longer has, and a term it had recorded retiring

**Fork:** H-10 reported the specification contradicting the CI workflow and contradicting itself.
Three sentences, all reproduced, and one of them wrong in a way the report's phrasing would have led a
careless fix to overcorrect.

**Options considered.** (A) Correct the three sentences. (B) Correct them and add guards, since both
defects are shapes rather than instances: a document describing a workflow it has changed, and a
document using a term it has written down as retired.

**Decision: (B).**

**What reproducing established.**

**The CI sentence was half true, and the true half matters.** It said the workflow "checks the sibling
repository out with `continue-on-error`" — still exactly right, and deliberate: the checkout is allowed
to fail so that its own error does not mask the guard's message. What was false is everything after
it. The step now prints what was not compared and **exits non-zero**, so a private sibling or an
expired token turns the build red rather than green. And the paragraph's *argument* had inverted: it
called "a harness build that cannot pass without a second repository" the worse alternative, which is
precisely the alternative D84 chose after the companion workflow spent a week reporting success while
verifying nothing about transcript contents.

**The JSONL adapter appears in four live places and only two are wrong.** Lines describing the
**run log** are correct — the run log genuinely is JSONL — and a fix driven from the report's wording
rather than from the file would have changed them too. The two real sites are a `WHERE [P6]`
requirement and phase 6's `Includes:` list, and the second sits **two lines above its own `Done when:`
line, which already read "the second adapter"**. The document disagreed with itself inside three
lines, with the correction written above both.

**Consequences / caveats** — four.

**The retired-term guard reads the specification's own marker.** The document already records what it
has stopped saying — `Retargeted from "JSONL adapter"` — so the check needs no list of its own: for
every such marker, the quoted term may appear **only** in the marker's own quotation. That makes the
mechanism grow by itself, because the next retarget writes its own marker.

**Its first draft allowed a window, and its own control rejected it.** The check originally treated
any occurrence within 200 characters of the marker as part of the marker's sentence. The control
plants a reuse on the very next line, which fell inside that window and went undetected. **The real
specification would have passed either way** — its two live uses were far from the marker — which is
exactly what a window buys: correct today, blind to the case that arrives next. Tightened to the
captured span, where the allowance is one occurrence and not a region.

**The CI guard is narrow and says so in its own docstring.** Comparing prose about a workflow against
the workflow is not something a check can do in general. This pairs two specific retired sentences
with the `exit 1` that falsified them, and fails if either the sentences return or the workflow stops
failing closed. A third way of describing the same behavior wrongly is outside it, and that is
written down rather than implied.

**Both were planted against the real pre-fix text.** The retired term was put back into the `WHERE`
requirement and the pre-D84 wording back into the CI paragraph; each check failed, and both passed
again on restore. Neither was trusted on a green run alone.

**Rule** — `test_no_term_the_spec_says_it_retired_is_still_used_as_a_live_claim` holds every term the
specification records retiring, excluding the changelog because an entry recording a retirement has to
name it; `test_the_spec_does_not_describe_a_fail_closed_workflow_as_a_warning` pairs the two retired CI
sentences with the workflow's `exit 1`; and
`test_the_retired_term_check_fires_on_a_term_the_spec_retired` is the control that rejected the loose
first draft. **Whether a sentence describing CI is otherwise accurate is judgment, not checkable** —
these hold two known-wrong phrasings and the retired vocabulary, and nothing reads the workflow to
confirm the rest of the paragraph is true of it.

---

## D96 — A verifier that read a report it had not written, and called a write failure a test failure

**Fork:** `tools/verify_phase1.py` printed *"every criterion passed, but pytest exited 1. A test that
no criterion names still failed."* **No test had failed.** Every one of the 392 passed; pytest exited
non-zero from inside its own reporting hook, because the JUnit path was momentarily unwritable. The
sentence sent a reader looking for a failure that did not exist.

**And reproducing it found the worse defect underneath.** The tool runs pytest with
`--junit-xml`, then parses that file. It did not delete it first — so **a report the run did not write
is parsed as though it had been.** Every per-criterion verdict printed that day came from the previous
run's XML. They were right, which is the worst version available: a stale report is undetectable
exactly when it agrees with the current one, and the only reason this surfaced at all is that the
non-zero exit tripped a different branch.

**Options considered.** (A) Correct the message. (B) Correct the message, stop the staleness, and make
the branch testable.

**Decision: (B).**

**Why** — (A) treats the sentence and leaves the tool able to certify twenty-one criteria against a
run that did not happen. The staleness is the finding; the message is how it was noticed.

**Consequences / caveats** — four.

**The report is deleted before the run rather than overwritten by it.** One line, and it converts "the
file is probably current" into "the file exists only if this run wrote it". A test asserts the unlink
is there **and that it precedes the subprocess call**, because doing it afterwards would delete the
evidence instead of the staleness.

**The message now distinguishes three things it had collapsed into one.** A failing test, named. A run
that produced no report at all, with the path and the pytest output. And a report in which nothing
failed, which means the non-zero exit came from pytest's own machinery — a reporting hook that cannot
write, a collection error, a usage error — with its output printed rather than a cause invented.

**`diagnose_suite_exit` is public and separated from `main` so a control can drive it.** The message is
the entire product of that branch, and a message nothing exercises is the shape this repository keeps
finding in itself. Three cases, three assertions, and each also asserts the *absence* of the wrong
sentence: a report with no failures must not say a test failed.

**D94's guard caught this entry's own work twice, on the commit after it landed.** The control's
fixture node ids looked like test names, so the prose guard reported a file citing tests that do not
exist; and the comment written to explain that fix quoted the very ids it was explaining, so the guard
fired again on the explanation. **Seventh instance in this session of a checker reading its own text.**
The tax is small and the alternative is loosening a guard that is working, so it is paid and named
each time.

**Rule** — `test_the_verifier_tells_a_failing_test_from_a_pytest_that_could_not_report` drives
`diagnose_suite_exit` through all three cases and asserts the wrong sentence is absent from each;
`test_the_verifier_deletes_its_report_before_running` asserts the unlink exists and precedes the run.
**Whether the pytest output printed after a non-diagnosable exit is intelligible is judgment, not
checkable** — the tool now declines to name a cause it has not established, which is the most a check
can arrange.

---

## D97 — Two branches the parser could not reach, and an encoding artifact it refused a corpus for

**Fork:** an audit's H-13 reported two unreachable branches in the text adapter and H-14 reported that
no test covers a byte-order-marked transcript. Both reproduce, and the second turns out to be a
decision rather than a missing test: does the reader **accept** a BOM or **refuse** it?

**Options considered**, for the BOM. (A) Strip it, as the reader already strips a trailing CR.
(B) Refuse it, and name it in the message so a reader knows what they are looking at. (C) Leave the
behavior and add the test the audit asks for.

**Decision: (A)**, with the transcript format specification saying so.

**Why** — the specification already answers this one noun over. It reads *"UTF-8, LF line endings (a
trailing CR is stripped rather than rejected)"*, and `_read_lines` explains the reason: a Windows
checkout can introduce CRLF through git's own normalization, and **failing a corpus for its line
endings would be a refusal with no defect behind it.** A byte-order mark is the same argument and the
same class of artifact: invisible in every editor that writes one, carrying nothing about the call,
and exactly what `Out-File -Encoding utf8` produces — which this project has already been bitten by
once, in a commit subject that still carries one. (B) is defensible and loses on that consistency: a
reader who may not be refused for CRLF should not be refused for a BOM.

**What it did before.** The mark reached the header comparison as part of the first line, so a
perfectly good transcript was refused with a message quoting `'﻿#format: ...'`. That reads as a
corrupt file rather than as an encoding artifact, which is the difference between a reader fixing it
in seconds and a reader opening a hex editor.

**Consequences / caveats** — four.

**The empty-file message could not be produced, and its replacement is not a rewrite of the check.**
`parse_call` chose between "first line must be …" and "file is empty" on `not lines` — and
`"".split("\n")` is `[""]`, never `[]`, so `lines` was truthy for every input. An empty file reported
that its first line must be the header, `found ''`: true, and the least useful available way to say a
file has nothing in it. Emptiness is now tested on content rather than on the list's length, so the
message exists and can be reached, and a non-empty file with a wrong header still gets the header
message — asserted, so the new branch cannot swallow the old one.

**The dead speech check is removed rather than made reachable.** `_build_event` rejects an empty body
for every kind and then checked again inside the CALLER/AGENT branch. There is no input that reaches
the second check. It read as defense in depth and was dead code, and **a reader trusting it would
believe speech is validated twice.**

**That removal is asserted by shape, and the docstring says why.** Both versions raise the same
exception for the same input, so the behavior is unobservable — which is exactly how the dead branch
survived. The test counts the occurrences in `_build_event` and also asserts that the *surviving*
check is the one that names the kind, so a future edit cannot satisfy it by deleting the live guard
and keeping the dead one.

**The artifact hash is unchanged**, which is the point worth checking rather than assuming: no
transcript in the corpus carries a BOM or is empty, so none of this moves the corpus. What moves is
what the reader accepts from someone else's tree.

**Rule** — `test_a_byte_order_mark_does_not_refuse_a_transcript` parses a marked copy of a real
transcript and asserts its event stream equals the plain one's, so the mark is stripped at the edge
rather than tolerated in content; `test_an_empty_file_is_reported_as_empty` covers an empty file, a
whitespace-only file, and the header case that must not be swallowed;
`test_no_speech_event_reaches_a_second_emptiness_check` holds the removal. **Whether any other branch
in this adapter is unreachable is judgment, not checkable here** — these two were found by reading,
and nothing in the suite measures reachability.

---

## D98 — The sweep the trigger demanded, and the one live section of a historical document

**Fork:** `test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence` turned the suite red at
eleven accrued decisions (D86 → D97). That guard was added when H-1 was closed, and this is the first
time it has fired — on the session that accrued them. Sweep, or restate the trigger?

**Options considered.** (A) Perform the sweep and bump. (B) Widen the stated interval so the guard
passes. (C) Stop recording decisions until someone else sweeps.

**Decision: (A).** (B) is the move D74 already pushed back on when a sweep proposed weakening this
same marker, and widening a trigger to avoid the work it demands is the failure it exists to catch.

**What the sweep found**, in the block whose job is to prevent exactly this.

The *Not checked* block still read **"Scoring is now the next step and has not been taken"** — two days
after it was taken, at D82. And it still called the held-out set **five transcripts**, a day after
`CALL-21` joined it at D86. Both corrected, with the correction attached.

**Both sit inside a statement class an audit reported closed.** H-2's table named these two lines
explicitly and the audit's own banner lists H-2 among the closed findings. The guard that closure
added, `_HELDOUT_SET_SIZE`, cannot see them.

**Consequences / caveats** — three.

**The reason it cannot see them is the interesting half.** That guard excludes the decision record
wholesale, on D53's argument that a record edited to agree with later decisions stops being a record.
The argument is right and the scope was one section too wide: **the *Not checked* block is not a
record.** It is written in the present tense, it is re-dated at every sweep, and its own preamble says
it exists "so the next session does not rediscover these as fresh defects". Excluding the whole file
excluded the one part of it that makes live claims. The guard now reads that block and nothing else in
the file, which is the narrowest scope that covers the defect.

**A rewrite deleted a sentence a test was binding, and the test said so within the minute.** The
scoring entry carried the only live statement of `cj load`'s 82/7 split, and
`test_the_cj_load_split_is_derived_from_the_gold_set` asserts that some document states it. Restored
in the replacement text rather than the test relaxed — and the first restoration was worded with the
numbers before the verbs, which the pattern does not match, so the guard rejected it twice for two
different reasons before the sentence was right.

**The marker moves to 0.22.0 @ D97 and the changelog carries the entry.** Bumping the version claims a
sweep, which is D71's rule, so this entry exists to make the claim true rather than asserted. What the
sweep read: the specification's metadata and every live statement in it, the *Not checked* block entry
by entry, and the corpus documents by way of the eleven decisions that had just rewritten them.

**Rule** — `test_the_sweep_trigger_is_a_mechanism_and_not_only_a_sentence` is what forced this and is
unchanged; `test_every_worded_heldout_set_size_agrees_with_the_declaration` now reads the *Not checked*
block alongside the specification and the phase-1 verifier. **Whether a sweep read everything is
judgment, not checkable** — the trigger can only say that one is due, never that one happened, which
is why D71 made the marker a claim a human has to be willing to sign.

---

## D99 — A refusal that could not say what it had found, and four sentences the corpus outgrew

**Fork:** the audit's last two Low findings. H-15: `tools/check_holdout_absence.py` never reads
`HELDOUT_SET`, so a genuine held-out transcript in this tree is reported as an id declared nowhere.
H-17: four wording defects. Both reproduce.

**Decision:** close both, and treat H-15 as a message defect rather than a missing lookup, because
that is what it is.

**Why H-15 matters more than its severity suggests.** The two cases this check can find are not
variants of one event. **A file carrying an id nobody declared** means somebody forgot a declaration.
**A file carrying a held-out id** means delete it, and treat every session that opened it as having
read held-out content. The check reported both in the same sentence — *"declared neither in
`corpus/DESIGN_SET` nor in `tests/fixtures/FIXTURE_SET`"* — which is true of a held-out transcript
and buries what it is. This tool exists for the second case, and it was the case it could not name.

Reading `HELDOUT_SET` is safe and is the whole point of that file: **identifiers are metadata and the
transcripts are content**, which is the distinction that lets this repository hold the list at all.

**And the test planted a literal.** `test_a_held_out_transcript_in_the_tree_is_found` wrote `CALL-13`
by hand — the first member of a set that has already grown once. A literal would keep passing if the
held-out set were renumbered entirely, proving that *some* transcript is found, which is not what the
test claims. It now takes its id from the declaration the tool reads.

**Consequences / caveats** — three.

**Both branches are asserted, not just the new one.** A message that fires on everything tells a
reader nothing, which is why the undeclared case still exists and still has its own words. The test
plants one id from `HELDOUT_SET` and one that is in no declaration, and asserts each is classified as
what it is — including that the second is genuinely absent from `HELDOUT_SET`, so the two plants
cannot silently take the same path.

**H-17's four are corrected in place with the corrections attached.** A count of the sweep's classes
that `S11` outgrew, de-quantified rather than re-pinned (D74). A test docstring still describing the
corpus by a size it outgrew — named that way rather than quoted, because the guard for exactly this
class reads the collocation and would fire on the sentence recording its repair. Two paragraphs in the register opening with the same three bold words, where
a reader met the phrase twice and had to work out that the second was not a restatement — merged. And
a dangling reference: *"That combination is the thing to watch"* had drifted two paragraphs below the
pairing it names, so it pointed at a held-out transcript relying on a speech rule. **Moved back to the
sentence about names and reserved-range contact details**, which is the combination it is about.

**None of the four was reachable by any guard here**, and that is worth stating rather than treating
as a gap to close. Three are prose that is *misplaced* or *duplicated* rather than false, and the
fourth is a count inside a docstring — which the recall net does not read, because it scans documents
and the measurement scan reads only marked measurements. A sentence in the wrong place is not a
countable claim, and building a checker for it would be building a reader.

**Rule** — `test_a_held_out_transcript_in_the_tree_is_found` plants from `HELDOUT_SET` rather than
from a literal, and `test_a_held_out_id_is_reported_as_held_out_and_not_merely_undeclared` asserts
both branches classify what they find. **H-17 carries no mechanism, deliberately**: misplaced and
duplicated prose is judgment, and the four are recorded here so a later reader can tell a correction
from a rewrite.

---

## D100 — The conversion this repository made at 745d1a6 was held by nothing

**Fork:** `745d1a6` converted this repository to US spelling, on the argument that a corpus declaring `en-US` while its own agent speaks otherwise *"invites the reader to wonder what else was declared rather than done"*. It added no check of any kind. The severity tool later made the same conversion, met the same problem, and recorded the answer as its D29: a word list is only ever as wide as the sweep that built it. Port that guard here, or let this conversion go on holding by itself?

**Options considered**
- **(A) Port the guard**, converting whatever it turns up.
- **(B) Port it over code and prose only**, leaving `corpus/` out as authored content.
- **(C) Leave it.** The conversion happened, and nothing has undone it.

**Decision ✅** — **(A)**, with `corpus/` in scope and `.txt` among the file suffixes, which the severity tool's version does not carry.

**Why** — (C) is what has been true since `745d1a6`, and the sweep is the argument against it: **51 spellings survived that conversion**, across 17 files including this record, the specification, six test modules and the corpus. A boundary-anchored replacement cannot reach inside a compound, so a prefixed form and a spelling sitting inside a test's own name were both invisible to it.

(B) is the tempting scope and it is wrong here, for a reason particular to this project. The corpus is the *subject* rather than scaffolding; `corpus/entities.md` carries the `en-US` argument itself, and seven of the fifty-one were in the findings. Excluding the corpus would have exempted the files the original argument was about.

**The corpus edits went upstream, which is not a detail.** `corpus/findings.yaml` is generated — `tools/make_gold_set.py --check` compares it against its inputs — so the sites were changed in `corpus/findings.adjudication.yaml` and `corpus/findings.candidates.yaml`, and the gold set and its view regenerated afterwards. That ledger's own header says *"nothing in it is drafted by a model"*. Re-spelling a human's recorded judgment is a different act from re-spelling a docstring, and it was asked before it was done rather than after.

**Consequences / caveats** — **quoted spellings are exempted rather than converted.** The audit quotes three of them as examples of the variety this project does not use, and quotes a commit title from the severity tool's history word for word; `corpus/entities.md` quotes one as the evidence for its own claim. Correcting a quotation turns it into a misquotation. The exemption table is keyed on fragments that carry no forbidden spelling, so the table is not found by the scan it belongs to — the same self-reference the severity tool met three times.

**One word joined the ported allowlist**: `exercisable`, from `corpus/policies/transfer.v1.md`. That file is compared byte for byte against the clauses transcripts quote out of it, so a false positive there would have meant editing two artifacts to satisfy a guard that was wrong.

**The first attempt at the conversion was itself wrong, and a census caught it.** Replacing a stem that is shared with `mechanism` rewrote **103 of them** across the corpus, the specification and this record. Every family whose prefix is shared with an ordinary word is now enumerated by inflection instead, and the conversion counts the words that must *not* move — `mechanism`, `synthesis`, `analysis`, `basis` — before and after, refusing to write anything if one of them has.

**Rule** — `tests/test_document_counts.py::test_no_other_variety_spelling_returns`, planted by `test_the_spelling_guard_finds_a_planted_word` against a spelling in prose *and* one inside an identifier, and by `test_every_quoted_spelling_exemption_is_still_quoted` against an exemption that names nothing.

---

## D101 — The register's rule covers every kind of name, because a carve-out is what a later reader extends

**Fork:** A targeted sweep chased one class across the project: the register's own rule, *used
implies declared*. For every kind of name the corpus uses, it asked whether a canonical declaration
exists and whether anything enforces it. Twelve kinds; the rule was enforced over **six** and the
corpus names **nine**.

The three outside it were `SYSTEM` event names, tool arguments and tool-result detail keys. One
mattered immediately: `call.answered` and `call.ended` are declared in `corpus/entities.md`,
`specs/event-model.md` and `specs/transcript-format.md` — checked in all three — **nowhere at all**,
and the only thing holding either was two string literals inside one assertion in
`test_every_call_opens_and_closes_its_lifecycle`. `call.ended`'s absence is CALL-12's seeded taxonomy
32 omission, so the name is load-bearing in a seeded defect. `assume_verified` is CALL-12's
verification bypass and `difference_due` is cited by findings; both were names the canon had never
seen.

**Options considered.** (A) Declare the `SYSTEM` names and **state the exception** for arguments and
detail keys, with the reason each is covered by a different property — arguments by a sourcing check
that traces every value, detail keys by the specific comparisons that read them. (B) Declare all
three kinds and let the rule hold without exception. (C) Leave it and record the limit.

**Decision: (B).**

**Why** — (A) was the drafted answer and the owner rejected the shape rather than the content:
*"exceptions lead to more inconsistencies; therefore, when possible, exceptions should be avoided."*
That is right here for a specific reason. The exception would have been **true** — the sourcing check
is a stronger property than name declaration, and it is what stops a fabricated argument *value*. But
it does not stop a fabricated argument *name*, and the carve-out would have been the thing a later
reader extended: the next kind of name arrives, the register already says it does not enumerate
everything, and the rule erodes one honest paragraph at a time. Nine kinds with no exemptions is
shorter to state and harder to weaken, and it costs almost nothing — these are names the corpus
already fixed, and enumerating them means a new one must be declared deliberately rather than
arriving unnoticed.

**A second defect, found while closing the first, and worse than it.** `_declared_names` — the
extractor the whole rule runs through — carried a docstring reading *"up to the next
blank-line-separated paragraph that starts a new bolded section"* and code reading
`rest.find("\n## ")`. **The bound the docstring described was never implemented.** Every category's
declared set therefore contained every category below it: a name declared under *Outcome reasons*
satisfied *Context variables*. Six categories had been passing against a region of one file rather
than against their own list, and no test asked whether a category's set was its own.

Bounding it correctly is not "the next bold paragraph" either — the register uses bold for headings
*and* for prose, so that cut *Context variables* in half and reported twenty-six declared variables
as undeclared. The boundary is **the next category**, and the categories are now an enumerated tuple
the extractor asserts its argument against. The identifier pattern also gained a dot, because
`call.answered` is a name and `[a-z_]+` does not fail on it — it returns a smaller set, and a
membership test against a smaller set still reads as green.

**Consequences / caveats** — the register grew by fifty-nine names in three lists, which is the cost
of the rule having no exceptions. The sweep's other rows were **not** gaps and are not recorded as
such: tool arguments are covered by sourcing, `matched_by` values by a paragraph-versus-corpus check
with a planted control, and detail keys by the comparisons that read them. Reporting those as
uncovered would have been the same error this project keeps finding, pointed the other way — calling
something unguarded because one chosen check does not reach it while a better one does.

**One limit found and left open.** The countable-claim guard flagged "three findings" in the new
prose and did **not** flag "twenty-nine times" beside it: it reads a number followed by a noun it
tracks, and *times* is not one. Both counts were removed rather than checked, per D74, so nothing
here depends on it — but the guard's reach is narrower than its name suggests, and that is recorded
rather than widened, because widening it to bare quantities would fire on ordinary prose.

---

## D102 — Phase 1 closes a third time

**Fork:** `phase-1-closed-v2` sits at `0254592` (2026-08-29). **Forty-five commits landed after it**,
including the corpus repair that moved transcript content and the extraction artifact's hash, the
format work, a sixth held-out call, an independent audit of all three repositories and D87–D101. The
phase was tagged closed and the close had stopped being true of anything, again — and a session in
this conversation asserted "phase 1 is closed and tagged" while writing about tags, which is the
staleness it was auditing.

**Decision:** tag `phase-1-closed-v3`, on D63's own instruction: *"If phase 1 reopens again, the next
tag is `-v3`. A phase that closes three times is worth being able to see."*

**Why** — the alternative was to retract the claim rather than re-earn it, and the phase's *Done
when* is met: the acceptance criteria pass by running, and every design transcript parses with a zero
unparsed-line count. Nothing about the standard changed; the artifacts under it did.

**Consequences / caveats** — the tag claims the *Done when* and nothing more, and names what is
outstanding, as v2 did. The two items v2 named are now **both discharged** — the findings were
adjudicated on 2026-09-01 and scored on 2026-09-05 — so v3 is the first close where the phase's
stated prerequisite is actually met, which is worth saying in the tag rather than leaving a reader to
diff two messages.

---

## D103 — Order is a property of a list, and "no gaps" is true of a shuffled one

**Fork:** D100 was appended **after** the `Not checked` block, so the decision record read D99, D101,
D102, the block, then D100. Both halves matter and only one is about numbering: a reader working
forward met a decision *after* the section summarizing what is unresolved, which is the arrangement
D58 moved that block to the end to prevent, and the number sequence ran backwards with nothing
noticing.

Nothing noticed because `test_the_decisions_are_numbered_without_gaps` checks gaps and duplicates.
**Both hold for a shuffled list.** The guard was not weak at what it did; it did a different thing
than its neighbors assumed, which is this project's most common shape.

**Options considered.** (A) Fix the placement and rely on review. (B) Add an order assertion.
(C) Add an order assertion and a placement assertion, and plant both.

**Decision: (C).** The owner asked for a mechanism rather than a repair, which is the right
instinct: this is the second time the block's position has drifted, D58 being the first.

**Why plant them** — the comparisons are now functions taking text, so a control lifts D100 out of
the record and reinserts it after the block, reproducing the exact arrangement that occurred, and
asserts both checks report it. Neither mutation touches a file. The control also asserts the live
record is clean under both, because a plant proves the check fires and says nothing about the
document it is aimed at.

**Consequences / caveats** — the order assertion forbids appending out of sequence, which is the
point, and it forbids nothing else: superseding, striking through and banner-ing all leave a
heading where it was. The placement assertion is the narrower of the two and the more likely to be
tripped honestly, since appending to the end of a file is the natural motion and the block sits
there.

---

## D104 — The P2 criteria buy one half of five requirements, and the halves they miss are the contract

**Fork:** Phase 2 was about to be built against sixteen `[P2]` acceptance criteria and what the build
prompt called "5 SHALL [P2] requirements", with nobody having checked whether the two cover each
other. Two things fell out of checking.

The count was wrong first. `SHALL [P2]` as a literal string matches only the five *ubiquitous*
bullets. Seven more requirements carry the phase tag before the verb — `WHEN [P2] … SHALL`,
`IF [P2] … SHALL`, `WHERE [P2] … SHALL` — so the P2 contract is **twelve** requirement statements,
not five. Checking sixteen criteria against five would have left the entire rubric-validation family
and the tier selector outside the comparison.

Against all twelve: seven are fully covered. **Five are covered in half**, and in each case the
unasserted half is the half the requirement names:

| Requirement | Asserted | Not asserted |
|---|---|---|
| `status`/`verdict` (ubiquitous) | `verdict is None` when status is not `applicable` | the converse, and that the status set is closed at five |
| ground truth (ubiquitous) | a claim resolves against tool details, variables and clauses | that agent speech is **excluded** |
| no hardcoded parameters (ubiquitous) | *a* threshold or signal list moves a verdict | that **every** declared parameter is read |
| `unevaluable` (IF) | the status, and exclusion from the denominator | that the missing ground-truth reference is recorded |
| `--tier assert` (WHERE) | zero model calls | that only deterministic entries execute |

**Options considered.** (A) Amend the criteria, closing each half. (B) Record the gaps and build to
the requirement text, leaving the criteria list alone. (C) Amend only the two the build prompt flags
as highest-risk.

**Decision: (A).** Six criteria added — six rather than five, because the status/verdict requirement
is an "if and only if" and has two unasserted halves, not one.

**Why** — (B) is the shape this repository keeps finding in itself. The criteria are what a phase
verifier walks and what a later reader treats as the definition of done; leaving a half unasserted
means a green tick over a property nothing checked, which is D59's whole subject. Two of the five are
worse than the average instance:

* The status channel **freezes at P2**. A harness returning `applicable` with no verdict satisfies
  every criterion as they stood, and every later phase reads that channel.
* A grounding blob that concatenates agent speech *alongside* the three ground-truth sources
  satisfies the grounding criterion, because that criterion's fixture puts the supporting value in a
  retrieved clause and it resolves either way. The criterion cannot distinguish the design from its
  inversion, and inversion is the failure the requirement was written to forbid.

(C) would have closed those two and left three named holes, which is a carve-out and therefore what a
later reader extends.

**Consequences / caveats** — the P2 criteria go from 16 to 22. Three criteria remain backed by no
requirement at all, and that is now recorded rather than left to be read as an oversight: `ruff`
(backed by `constraints`), the W2–W10/W19 test list (orphaned **deliberately** —
`specs/taxonomy-coverage.md` says in as many words that the specification "says nothing about the
failure modes those checks must avoid"), and CI (backed by scope and D28). Two criteria depend on a
later phase and are annotated rather than moved: the `unevaluable` denominator clause rests on a P4
`WHILE` requirement, and the negative-pole guard names a judged scale, of which P2 has none.

The version is deliberately **not** bumped. `Last swept` is bound by test to equal the header
version, so a bump claims a sweep; five accrued decisions is inside the header's own ~8–10 trigger,
and the sweep belongs at phase completion where the trigger already puts it.

**Rule** — enforced by test: the count of `[P2]` requirement statements and of `[P2]` acceptance
criteria is pinned, and the pin reads requirements by phase tag rather than by the string
`SHALL [P2]` — which is the miscount this decision started from.

---

## D105 — A corpus seeded with defects exits non-zero, and the phase gate is agreement

**Fork:** Phase 2's *Done when* read "`--tier assert` runs the design set green", and a criterion
requires an absolute-gate negative verdict to fail the call and the run **on the process exit code**.
The design set is seeded with defects by construction. Both cannot hold: either Tier A declares
nothing an absolute gate, or the run over this corpus exits non-zero and is not "green".

**Options considered.** (A) Non-zero is correct; the phase gate is agreement with the gold set.
(B) No Tier A entry declares `gate: absolute`; the exit-code criterion is proven on a fixture rubric
only. (C) A flag that inverts the exit code over the design set.

**Decision: (A).** `harness run` exits non-zero when an absolute gate returns its negative pole, over
the real corpus as over a fixture. Phase 2 is done when the produced verdicts **agree with the gold
set**, asserted by the phase verifier.

**Why** — (B) makes the sentence true by removing the thing it was about. A harness that runs a
deliberately defective corpus green is W11 restated: the fail-open default, chosen on purpose this
time. The tier that can fail a whole run has to be able to fail this run, or the demonstration
demonstrates nothing. (C) buys the same green with a second exit-code semantics, and a carve-out is
what a later reader extends.

What (A) costs is that "green" has to be redefined where it appears, which is one sentence in the
phase block, now amended to say that agreement is the gate and that a zero exit over this corpus
would be the defect.

**Consequences / caveats** — the phase-2 verifier cannot use the run's exit code as its own pass
signal; it compares verdicts against the gold set and reports the exit code separately. That is a
stricter gate than the exit code, not a looser one: an exit code says a gate fired, agreement says
the *right* gates fired on the *right* calls.

**Rule** — enforced by test: `harness run --tier assert` over the design set exits non-zero with at
least one absolute-gate negative, and the verdict set it produces equals the gold set's expectation
for every traced finding.

---

## D106 — A check parameter lives in the rubric entry, not behind a path the entry names

**Fork:** Several Tier A checks need inventories the corpus already declares in `corpus/entities.md`
— the tool list, the internal-only field set, the disclosure names. The entry could carry the list
inline, or carry a pointer to the register and have the loader resolve it.

**Options considered.** (A) Inline in the entry. (B) A pointer the loader resolves. (C) Inline, with
a test asserting the inlined list agrees with the register.

**Decision: (C).** Inline, and bound to the register by test.

**Why** — the criterion that makes "no parameter is hardcoded" checkable is a test that **mutates the
rubric** and observes a different verdict. Under (B) the real value lives in a file the mutation
never touches, so the criterion passes while the property it stands for is unproven — which is W20
with an extra indirection. (A) alone lets the rubric and the register drift into disagreeing about
what the corpus declares, and the register is the document that makes "the capability existed and was
not used" a checkable claim at all. (C) costs one test and keeps both properties.

**Consequences / caveats** — rubric entries are verbose, and deliberately so: reading an entry tells
you everything the check will do. The binding test asserts the inlined inventories are **subsets** of
the register's declarations rather than equal to them — an entry may legitimately name three of
eighteen tools, but a name the register does not declare is the register's own *used implies
declared* rule broken from a new direction.

**Rule** — enforced by test: every inventory inlined in a rubric entry is a subset of the
corresponding declaration in `corpus/entities.md`, and a name in an entry that the register does not
declare fails by name.

---

## D107 — Every rubric entry names its negative instance, or declares that it has none

**Fork:** Tier A covers all 61 `detectable_by: assert` findings. Every check that keys on a signal
list adds false-positive surface across all sixteen design calls, and W4 and W9 are exactly that
failure measured: a claim detector that matched "are you all set?", and a paraphrase detector whose
validation measured the true positive and never the false-positive rate in the same call.

**Options considered.** (A) Ship fewer checks, to bound the surface. (B) Ship all of them and measure
precision in aggregate. (C) Ship all of them, and require every entry to name a call where the check
must **not** fire.

**Decision: (C).** Each entry carries a negative instance by call id. An entry with no negative
instance available in the design set declares that, by name, in the entry itself.

**Why** — (A) trades coverage for a property that a mechanism buys more cheaply, and the owner's
objection to it is the right one: absent checks become assumptions, and assumptions are where the
undetected mismatches live. (B) reports one number over the tier, which is exactly where a single
check firing on every call hides. (C) makes the per-check claim: this check fires here and is silent
there, both asserted. It is the discipline of planting a guard, applied to the guard's other half.

The declared-absence branch matters as much as the assertion. A check with no negative instance is
not forbidden — some properties genuinely hold in every design call — but it has been proven against
nothing, and D81 is this project's record of a declared true negative being the tolerable form rather
than the correct one. Declaring it puts the gap in the artifact instead of in a reader's inference
from silence.

**Consequences / caveats** — the coverage note phase 2 emits lists every entry lacking a negative
instance. That list is expected to be non-empty and is not a defect; a list that were empty by
construction, because the field defaulted, would be.

**Rule** — enforced by test: every rubric entry carries either a negative instance naming a call in
the design set, or an explicit declaration that none exists; the check is asserted silent on the
named call, and the count of entries carrying neither is zero.

---

## D108 — The judged tier is declared in fixtures at P2, not in the shipped rubric

**Fork:** Three P2 criteria talk about judged entries — a judged entry with an absolute gate is
rejected, the evidence-on-negative-pole guard is asserted "for a judged scale", and `--tier assert`
must skip judged entries. The shipped rubric could declare the six judged dimensions now as data, or
carry only deterministic entries and leave judged entries to fixtures.

**Options considered.** (A) Declare the six judged dimensions in the shipped rubric now.
(B) Deterministic entries only; judged entries exist in test fixtures. (C) One placeholder judged
entry in the shipped rubric.

**Decision: (B).**

**Why** — (A) and (C) both author P3 and P4 data inside P2, and the specification allocates
"remaining judged dimensions added as rubric data only" to P4 for a reason: those entries carry
prompts, scales, `requires_facts`, `max_tokens` and an effort level, none of which P2 can validate by
running.

What (B) costs is stated rather than hidden: over the shipped rubric, "issues zero model calls" is
**trivially** true, because no entry could have issued one. The transport spy there asserts silence
from a tier with nothing in it. That is why the tier-selector criterion added at D104 is asserted on
*which entries produced a result*, over a fixture rubric holding both tiers — the fixture is where
the teeth are, and the shipped run is a demonstration rather than the proof.

**Consequences / caveats** — revisit at P3, when one judged dimension exists for real: the fixture
assertion stays, and the shipped run stops being trivial on its own.

**Rule** — enforced by test: the shipped rubric declares no entry with `tier: judge`, and the
tier-selector assertion runs over a fixture rubric that declares both tiers.

---

## D109 — An unread parameter fails the entry, so "no value is hardcoded" is a run property

> **Amended 2026-09-08. The guard sees reads, and "read" is not "used".**
>
> An independent audit of phase 2 found that `ParamView` records **top-level** keys, and that is
> true: 159 of the 213 leaf parameter paths in the shipped rubric are nested — `topics.*.claim_signals`,
> `sources.*.match`, `capabilities.*.trigger_speech_signals`, `bands.*.fraction` — and a nested key is
> reached with ordinary `dict` access on a value the view already handed over. So the guard covers the
> level at which almost nothing is stored.
>
> **A recursive view would not close it, and that is the more useful half.** The blind spot is
> dataflow, not depth. `available_value_never_spoken` builds its lexicon with
> `_mapping(params, "number_words").items()`, so every key and value is read; `_compose` then resolves
> a scale word through `number_scales` and discards the lexicon value it was handed. A tracker at any
> depth records `number_words.hundred` as read. Only a mutation test distinguishes read from used —
> and a mutation test over a fixed corpus reports every parameter the corpus does not exercise as
> unread, which is why option (A) was not taken. Each instrument is blind to what the other sees.
>
> **Measured, and it is wider than the audit said.** Mutating one entry at a time against all fifteen
> design calls, **five** parameters of `A-available-value-never-spoken` move no verdict: `number_words`
> (every value multiplied, and the thirty-word lexicon cut to one word), `number_scales` (values),
> `digit_pattern` (replaced by a pattern matching nothing), `number_joiners` and `strip_characters`.
> Changing that entry's `sources.exchange_difference.match` from `numeric` to `literal` moves nothing
> either. The instrument works: changing the source `key` moves CALL-09, and changing the email
> source's `requires_speech_signals` moves CALL-11 and CALL-12.
>
> The cause is corpus coverage, not a broken check. Only CALL-09 reaches the numeric source, and its
> verdict is `withheld` — reached by finding no figure, which is what a wholly broken matcher would
> also produce. `tests/test_values.py` covers `figures_in` well, in 32 tests against a **fixture**
> lexicon; nothing binds the rubric's own tables to a verdict. That is W20's shape one turn on: not
> parameters nobody reads, but parameters proven by a fixture that is not those parameters.
>
> Closing it means a design-set call in which an agent speaks a payload figure in words, which is
> corpus authoring and is owed to a session cleared for it.
> `test_the_numeric_matching_parameters_that_move_no_verdict_are_the_recorded_five` holds the list, so
> the gap is tracked rather than invisible, and fails when it is fixed without being recorded.
>
> **Closed 2026-09-08 by D119.** CALL-22 states a `difference_due` of `1,250.00` and the agent says
> "one thousand two hundred and fifty dollars" out loud. Every parameter above now moves a verdict,
> and so does the `numeric` → `literal` mutation this amendment also recorded. The test that held the
> list is deleted rather than emptied: a list of parameters nothing exercises has no rows left, and a
> test asserting that an empty list is empty would keep the shape of a finding after the finding was
> gone.

**Fork:** The requirement is that every check parameter, threshold and signal list is read from the
rubric entry with no such value hardcoded in Python, and the criteria buy it with a mutation test:
change a threshold in the rubric, observe a different verdict. D104 already recorded that this proves
the property for whichever parameter the test chose. Building the loader raised the sharper question:
what enforces it for the other parameters, and for the ones added next month?

**Options considered.**

- **(A) Mutation tests only** — one per entry, or one per parameter, generated over the rubric.
- **(B) Each check declares the parameter names it reads**, and the loader compares that declaration
  against the entry's `params`.
- **(C) The parameter accessor records which keys were read**, and the engine refuses an entry whose
  check left a declared parameter unread.

**Decision: (C).** `ParamView` is a `Mapping` that records every key asked for; the engine calls
`validate_params_consumed` after each check returns and raises `UnreadParameterError` naming the
entry and the unread keys.

**Why** — (A) is what the specification asks for and it is a *sample*. It answers "can this parameter
move a verdict?" for the parameters somebody wrote a case for, and W20 is a tier where `params` were
decorative for every entry except the one anybody looked at. A sampling guard against a defect whose
defining property is that nobody looked is the wrong shape.

(B) is a second list. A check reading `window_ms` and declaring `["window_ms", "signals"]` is exactly
the drift the whole no-hardcoding rule exists to prevent, moved one file over — and D101's rule
applies: a declaration nothing derives from the thing it describes goes stale silently.

(C) needs no second list and no per-parameter test, because reading *is* the evidence. It also
inverts the burden in the useful direction: under (A), a check that quietly stopped consulting a
threshold passes until someone writes the case; under (C) it fails the entry on the next run, naming
the parameter.

**What it costs, stated.** `ParamView` is not a frozen dataclass, and it is the one type in the
contract package that is not. It has to accumulate observations while the check runs, and the
observations are its product. The exemption is narrow and the frozen-dataclass scan is unaffected —
it reads `@dataclass` decorators, and this is a plain `Mapping` subclass — but the reason is recorded
here rather than left for a reader to infer from its absence. Two views of one entry do not share
read state, asserted, because one call's read history satisfying another call's requirement would
make the guard pass on the second call of any run.

**What it does not do.** It cannot see a value hardcoded in Python that the rubric never declared —
a check with a constant nobody put in `params` reads nothing and leaves nothing unread. That half
stays with the mutation criterion and with review of each check, and saying so is the point: this
closes the direction "declared and ignored", not the direction "never declared".

Nor, as the amendment above records, the direction "declared, read, and then discarded". Reading is
the evidence, and a check can read a value and use none of it.

**Rule** — enforced by test and by the engine: an entry declaring a parameter its check does not read
raises `UnreadParameterError` naming the entry and the key; an entry declaring no parameters passes,
and an entry whose parameters were all read passes.

---

## D110 — Three populations, because caller speech is neither evidence nor subject

**Fork:** The requirement is that the system-level event log and retrieved policy clauses are ground
truth and agent speech is the subject under test. Building the seam a check reads through forced the
question the sentence leaves open: where does **caller** speech go? The event model has two citation
populations, `T` for speech and `F` for facts, and caller speech is `T`.

Two readings were available and they disagree about real findings. Under "speech is the subject",
caller turns are under test — but nothing in this corpus tests the caller. Under "everything that is
not the subject is evidence", a caller turn supports a claim about the world — and a caller can say
anything, so a grounding check would resolve an agent's claim against the caller's assertion of the
same thing. CALL-10 seeds exactly that: the caller reports what their card issuer told them, and the
agent answers from `charge_count := 1` as though that settled it (F-66).

**Options considered.**

- **(A) Two populations.** Ground truth is `F`; subject is `T`. Caller speech is subject.
- **(B) Two populations, the other way.** Subject is agent speech; everything else, caller speech
  included, is ground truth.
- **(C) Three.** Ground truth (facts), subject (agent speech **and** the platform's disposition
  labels), stimulus (caller speech).

**Decision: (C).**

**Why** — (B) is the inversion the whole requirement exists to forbid, arriving through the one turn
kind nobody thinks about. (A) is not wrong so much as unusable: several findings turn on a caller
turn having *occurred* — "the caller raised an access requirement at event 4 and again at event 25,
and was directed to a web form" (F-62) — and a check that cannot see caller turns cannot state the
trigger. Calling them "subject" would also invite a later check that reports a defect against the
caller, which this harness has no standing to do.

(C) separates the two questions a caller turn answers. **Its occurrence is a fact about the
conversation; its content supports nothing about the world.** A check reaches for `stimulus` to
establish a trigger and for `ground_truth` to resolve a claim, and the second cannot contain the
first.

**The disposition labels join the subject, not the ground truth.** `duration_ms`,
`disconnection_reason`, `outcome` and `outcome_reason` are what the platform *claimed*, and the event
model is explicit that a harness reconciling them on read would delete the defect it exists to
detect. Five findings compare them against the tool results. So `Subject` holds two owners of one
kind of statement — the agent's spoken claim and the platform's claimed disposition — which is the
split the findings document already makes with `owner`.

**Consequences / caveats** — the call record is now partitioned by two enumerated tuples rather than
by "the disposition fields and everything else", and a test asserts the two cover
`REQUIRED_CALL_KEYS` exactly, with no field in both. The enumeration is deliberate: under the
negative form a field added to the record would join ground truth by default, and W17 is what
defaulting a classification costs — anything containing an `=` became a variable, so fabricated facts
flowed into the grounding blob.

The event model is unchanged. This refines `T` along a boundary the model already draws by kind, for
a question the model does not ask: which side of a comparison a thing is on.

**Rule** — enforced by test: a token present in one agent turn and nowhere else in the call is absent
from that call's grounding corpus; no agent turn in any design call appears in its own call's
grounding corpus, over more than a hundred turns; every event kind lands in exactly one population,
asserted over all eight; and `RECORD_FACT_FIELDS` and `DISPOSITION_FIELDS` partition
`REQUIRED_CALL_KEYS` with an empty intersection.

---

## D111 — Speech spells its numbers, and no check may key on which form it used

**Fork:** Building the grounding layer, a scan of the design set found that agent speech carries
**three** bare numerals in sixteen calls and no currency symbol, no ISO date and no bare decimal. A
grounding check built on digit patterns would find nothing in speech, return `not_applicable` on
every call, and be a check proven against nothing. So the layer needs to read spelled numbers.

Reading the same scan raised a second and sharper question, put by the owner: the two forms look like
they *mean* something — that a numeral is information already on the record and a spelled number is
information being asserted now. If that held, a check could key on the form.

**It does not hold, and the counter-example is decisive.** CALL-12 event 6, the caller: "It's
BK-9145-TC". Event 7, the agent: "Let me read that back — B-K, nine one four five, T-C". The same
reference is a numeral when first stated and words when read back, so the *older* statement is the
one in words. CALL-20 events 6 and 7 repeat it exactly.

**What the split does track**, over all 73 figure occurrences in speech:

- **Quantities are always spelled, by both speakers, with no exception** — money, durations, counts
  and clock times. Not one numeral among them.
- **Identifiers are numerals when stated and spelled when read back digit by digit** — `00318`,
  `BK-9145-TC`, `BK-5182-QN` from callers; "nine one four five" from agents confirming.
- The only three agent numerals are `4417`, `8820` and `00461`: record fragments *stated* rather than
  confirmed, and two of them sit inside F-78, the seeded unprompted disclosure of card brand, last
  four and billing ZIP to an unverified caller. That is the grain of truth in the hypothesis — agent
  numerals are pre-existing record values — and it is three instances against a read-back pair that
  runs the other way.

**Options considered.** (A) Read both forms and compare by value; the form carries nothing.
(B) Treat the form as a signal, since it correlates with stating-versus-confirming.
(C) Read both forms, and separately declare a read-back signal in the rubric where read-back is the
subject of a finding.

**Decision: (C).** The value layer parses spelled and digit forms and compares decimals. No check
consults which form was used. Where read-back is itself the finding — F-13, the transfer email
captured from speech and never read back — the signal is a phrase list in the rubric entry.

**Why** — (B) keys on how speech was **written down**. That is a property of transcription, not
something the event log records, and this project's whole layering says nothing above the adapter
line may depend on a source format's habits. It is also W17's shape one step over: a fact inferred
from formatting. And it would break exactly where the harness makes its adaptability claim — the
held-out set was authored to the same conventions by hand, and a vendor's ASR output guarantees
neither.

**Consequences / caveats** — the number lexicon is rubric data, because a list of number words is a
signal list in the sense the requirement means. It is general English rather than fitted to the
corpus: a lookup table sized to the design set would pass here and fail silently on the held-out set,
which is the failure this corpus exists to make visible.

A cue requirement comes with it. "One moment for me" contributes the value 1 to any check that reads
spelled numbers, so a figure is a candidate only when a declared cue word follows it within a
declared window. That is W4's lesson applied before the defect rather than after: a detector matching
turns that are not claims, validated against its true positive and never against its false-positive
rate in the same call.

**Rule** — enforced by test: no check reads the spelling of a figure; the value layer parses both
forms and compares by decimal value, asserted by a fixture where the fact is written `85.00` and the
speech says "eighty-five dollars"; and a turn containing a number word with no declared cue produces
no candidate.

---

## D112 — The rubric is authored data at the repository root, and CC BY covers it

**Fork:** The rubric had no home. D31 settled that authored corpus data lives at repository root and
the package holds code, on the grounds that D9's license split has to be drawable as a path. The
rubric is read by code, authored by a person, and is neither transcripts nor documentation, so it
tests that rule rather than following from it.

**Options considered.** (A) `rubric.yaml` at the repository root, CC BY with the corpus and docs.
(B) `corpus/rubric.yaml`, treating it as corpus. (C) `src/harness/rubric.yaml`, shipping it inside
the package as though it were a default.

**Decision: (A).**

**Why** — (C) is what D31 rejected for the corpus and the reason carries over unchanged: the two
licenses would interleave inside one package directory, and the README's "which license covers which
tree" statement becomes unstatable without enumerating files. It would also make the rubric look like
a default the harness falls back on, which it is not: the rubric is an argument, and an adopter
supplies their own.

(B) is closer but says the wrong thing. `corpus/` is the *subject* — the calls under evaluation and
the ground truth about them. The rubric is the evaluation, and filing it beside the transcripts would
put the thing being measured and the thing doing the measuring in one directory. The findings
document is already the join between them and it lives in `corpus/` because it is ground truth about
those calls; the rubric traces *to* it and is not of the same kind.

One file rather than one per tier, because the tier is a property of an entry and the engine already
filters on it. Splitting by file would make a duplicate id across files a case somebody has to
remember, for no gain.

**Consequences / caveats** — the root gains a file, and the license statement owed at P6 now has
three trees to name rather than two: `src/` and `tools/` under Apache-2.0, `corpus/` and `specs/` and
`rubric.yaml` under CC BY. Recorded here so that statement can be written from a decision rather than
from a guess about which half the rubric belongs to.

**Rule** — judgment, not checkable. Nothing enforces where a file lives; what the P6 README
criterion will check is that the license statement names the trees that exist.

---

## D113 — One suite, one run, read by two verifiers

> **Amended 2026-09-07, and the amendment is the interesting half.** The sentence below reads "there
> is one test suite, so there is one run to read". That was true of the *function* the two verifiers
> share and **false of the run**: `verify_phase2.main` called `run_suite()`, which executes pytest
> again, so CI ran the whole suite three times per push — once as its own step and once inside each
> verifier. Roughly thirty-three minutes where eleven would do, and no extra signal from any of it.
>
> Found by the owner asking when the suite is expected to run, which is a question about workflow
> rather than about correctness, and it produced a correctness answer. Both verifiers now take
> `--junit <path>` and read an existing report; CI's pytest step writes it once. A report older than
> the newest source file is **reported as stale and re-run**, never trusted — because the whole
> reason `_run_suite` deletes its report before running is that a stale report is undetectable when
> it agrees, and a reuse path that quietly accepted one would put that hazard back with a flag on it.
>
> The decision below stands; what it claimed about the *number of runs* did not, and is corrected
> here rather than rewritten there (D53).

**Fork:** Phase 2 needs its own acceptance verifier, in the shape phase 1 established: a criteria
list, a per-criterion verdict, `EVIDENCE MISSING` where a named test has been renamed away, and a
stated caveat where a criterion is not fully checkable by machine. That shape sits on about sixty
lines of machinery — run pytest once, parse the JUnit report, tell a failing test from a pytest that
could not write its report — and each of those two behaviors was added after costing a session.

**Options considered.**

- **(A) Copy the machinery into `verify_phase2.py`.**
- **(B) Extract it to `tools/phase_verifier.py`** and have both verifiers import from there.
- **(C) Expose it from `verify_phase1.py`** and have `verify_phase2.py` import it.

**Decision: (C)**, with (B) named as what happens when a third phase needs it.

**Why not (A)** — the machinery exists to make stale state detectable. `_run_suite` deletes the
JUnit report *before* running, because on 2026-09-07 the path became briefly unwritable, pytest
exited non-zero from its own reporting hook after every test passed, and the tool parsed the
*previous* run's XML and printed a verdict from it — which happened to be right, the worst version,
because a stale report is undetectable when it agrees. Two copies of a mechanism whose subject is
undetectable drift is the joke telling itself.

**Why not (B), yet** — the extraction is right and the timing was wrong. `tests/test_acceptance.py`
imports `CRITERIA` and `diagnose_suite_exit` from `tools.verify_phase1`, and
`test_the_verifier_deletes_its_report_before_running` reads that file's *source*, slicing it between
`def _run_suite` and `def diagnose_suite_exit`. Moving either function breaks a phase-1 guard, and
phase 2's own contract is that phase 1 does not regress. Doing it late in a long build, to save a
file, trades a real risk for a tidiness gain.

**What (C) costs, stated** — the import direction is backwards on the face of it: phase 2's verifier
imports phase 1's. That is odd enough to stop a reader, so the reason is written where the import is
rather than left to be inferred. `verify_phase2` must also be run as a module — `python -m
tools.verify_phase2` — because a script invoked by path puts `tools/` on `sys.path` while pytest
imports it as `tools.verify_phase2`, and those two want different import forms. `-m` is the one form
both agree on and it needs no path manipulation at the top of the file, which would need a lint
suppression this repository does not allow.

**Consequences / caveats** — the phase-2 verifier reads the same suite run as the phase-1 one, which
is correct rather than merely convenient: there is one test suite, so there is one run to read, and
two runs could disagree. CI runs both verifiers, so a phase-2 change that regresses phase 1 fails the
build rather than waiting for someone to remember.

**Rule** — enforced by test: `tools/verify_phase2.py` contains no `_run_suite` of its own and imports
from `tools.verify_phase1`; the workflow runs both verifiers; and every `[P2]` criterion in the
specification is claimed by an entry whose `spec_anchor` is a substring of it.

---

## D114 — A tier that could not be completed exits 3, because 1 is a finding about the agent

**Fork:** `harness run` had three exit codes: 0 every gate held, 1 at least one gate failed, 2 the
run could not start. P2-1 found the hole between them. A check that throws on every call produces
fifteen `errored` rows, no failed gate, `every gate held` and **exit 0**; a check that cannot reach a
verdict produces `unevaluable` rows and does the same. The five-value status channel exists to keep
those states apart — D23 amended the contract from four values to five for exactly this reason — and
the exit code collapsed four of them into "held". That is W11's shape one level up, in the single
line a CI job actually reads. Closing it needs a number, and no number was free of meaning.

**Options considered.**

- **(A) Fold `errored` and `unevaluable` into exit 1.** No new convention; CI's existing
  `|| [ $? -eq 1 ]` accepts it unchanged.
- **(B) A fourth code, 3, for "the tier could not be completed".**
- **(C) Keep exit 0 and print a warning.**

**Decision: (B).**

**Why** — (C) is the defect restated. A warning on stdout that nothing parses is not a signal, and
the whole finding is that the line a CI job reads said success. It fails open in the one place that
was already failing open.

(A) is the tempting one, and it is wrong for a reason specific to this project. Exit 1 means *the
tier found defects*, which is a finding about the **agent**. A tier that errored is a finding about
the **run**. Over this corpus exit 1 is the *expected* outcome — D105 says so, and the workflow
accepts it deliberately with `|| [ $? -eq 1 ]` — so folding the two together would make every
incomplete run land on the one code CI is configured to wave through. The single place the
distinction has to survive is exactly the place (A) destroys it.

(B) costs one number and three lines of output. A reader seeing 1 knows the tier found defects; a
reader seeing 3 knows the tier did not run properly; and CI fails on 3 without any change to the step
that accepts 1.

**Consequences / caveats** — three, and the second is a real choice rather than a fallout.

The number is this command's own. Nothing external defines exit 3, exactly as nothing external
defined 1 and 2 here; it is documented in `harness/cli.py`'s module docstring and in the README's
running section, which are the two places a reader looks.

**A failed gate outranks an incomplete tier.** The gate branch is tested first, so a run with both a
failed gate and an errored result exits **1**, not 3. That is deliberate: a failed gate is evidence
that was actually computed and is actionable now, and that branch already prints the errored count
beside it, so the reader is told about both and gets the code for the one carrying findings. The
shipped rubric over the design set is never the mixed case — gates fail and nothing errors — so the
precedence needed a test built for it rather than inherited from a run.

`missing a provenance value` was removed at the same commit and for the same reason. Once `Provenance`
refuses a blank field (P2-8) the count is unreachable, and a counter that can only ever print zero
reads as a check.

**Rule** — enforced by test: `test_a_run_whose_checks_all_error_does_not_report_that_every_gate_held`
and `test_a_run_with_no_verdict_to_compare_also_reports_the_tier_incomplete` drive the two states
through the CLI and require 3; `test_a_failed_gate_outranks_an_incomplete_tier` requires 1 for the
mixed case; and `test_the_workflow_runs_the_deterministic_tier_and_its_verifier` requires the CI step
to accept exit 1 and nothing else, which is what makes 3 fail the build.

---

## D115 — A declared name matches at a boundary, and one module owns the boundary

**Fork:** An independent audit of phase 2 listed eleven precision hazards the design set does not
exercise. Two are one defect in two grammars. `A-deadline-never-resolved`'s resolution signals are
the twelve month names matched as bare substrings, so `may` matches inside "maybe" and `march` inside
"marching" — and that entry's gate is absolute, so a hedge in the stating turn would pass the one
call the entry exists to fail. Separately, five copies of one regex read a tool argument as
`name="value"` and three more read a result detail as `key=value`, none with a leading boundary, so
`event` matched inside `target_event=` and `at` inside `closed_at=`. `corpus/entities.md` declares
four colliding pairs today and no rubric key is the short member of one, which is what made the
second half latent rather than firing.

**Options considered.**

- **(A) A declared `match: word` option per signal list**, defaulting to today's substring behavior.
- **(B) Word-boundary matching unconditionally**, added at each of the eleven sites.
- **(C) Word-boundary matching unconditionally, with one module owning both boundaries** and every
  site routed through it.

**Decision: (C).** `harness.checks.matching` holds `signal_in` for phrase lists and
`argument` / `carries_argument` / `field` / `values` / `carries_field` for field keys; conduct's
`_has` became a delegate, and the eleven sites became calls.

**Why** — (A) makes the safe behavior opt-in, and every list that forgets to opt in keeps the
defect. It is also a second list in D101's sense: a `match:` beside a signal list is one more thing
to keep current, and the entry that most needs the boundary is the one whose author did not think
about it.

(B) fixes the instances and leaves the shape. P2-14's lesson in this repository is exactly that: nine
copies of a constant were replaced by one binding so a tenth is found by construction rather than by
counting. Eight near-copies of one regex, each needing the same character added, is that lesson
restated — and two of the eight are containment tests (`f"{argument}=" in ...`), which is how a
guard ends up narrower than the rule it stands for.

**What it costs, measured rather than argued.** Routing every signal list and every field key through
the module moves **no verdict of 555** over the design set, and no evidence string either — checked
by dumping both trees' results and diffing. A change that moves nothing is proven by nothing, so both
boundaries have planted controls: `tests/test_matching.py` asserts each against the naive
implementation it replaced, and `test_a_hedge_in_the_stating_turn_does_not_resolve_the_deadline`
plants the hedge on CALL-09 at the check rather than at the helper. Removing the two boundary
constants fails 29 tests.

**Consequences / caveats — the homograph half is not closed and must not look closed.** "You may
hear from the promoter" carries `may` as a whole word. A boundary separates a fragment from a word;
it cannot separate two words spelled the same. Case would separate them in this corpus and D111
forbids asking, because the form speech was written down in carries nothing and the held-out set was
authored by hand to the same conventions. Closing it needs the month required near a date-shaped
token — what `spoken_local_date_wrong` already does with `month_within_words` — which changes
what the entry declares and is not this decision.
`test_the_homograph_half_is_not_closed_by_a_boundary` holds it as a recorded residue.

A second residue is recorded rather than fixed: `matching.field` stops a value at `;` or a quote and
`matching.values` stops it at `;`, `,` or whitespace, so one `key=value` syntax is read by two
grammars. Unifying them changes behavior;
`test_the_two_value_grammars_differ_and_that_is_recorded_not_fixed` asserts the difference so it is a
decision somebody can find rather than a surprise in a held-out call.

> **Amended 2026-09-08. Half of that difference was never deliberate, and recording it as one thing
> hid which half.**
>
> The half that is deliberate stands: `field` crosses a space because it reads values that contain
> one — `internal_note=do not disclose` is a value, not a word — and `values` reads a token because
> it returns *every* occurrence of a repeated key and must not swallow the pair after it.
>
> The half that was not: `values` also stopped at a **comma**, so `difference_due=1,250.00` came back
> as `1`. That is not a shortened value, it is a different one, on the money key, in the check whose
> subject is whether a money figure was spoken — and `field`, reading the same string, returned
> `1,250.00`. The corpus could not show it because no design call states a figure above nine hundred
> and ninety-nine; it surfaced while drafting one that does.
>
> Corrected by refusing to **end** a value on a comma rather than by refusing to **cross** one, which
> keeps `booking=19:00:00Z, event=19:30:00Z` two values and makes `1,250.00` one. Over the fifteen
> design calls this moves no verdict of 555, so it lands with controls rather than with a corpus
> verdict: the truncation is asserted against the old pattern directly, and the comma-separated pair
> is asserted to stay separated.
>
> **What this says about the residue as a category.** "Preserved rather than fixed" was the right
> call — the deliberate half really is a decision somebody else's use case should make. What it got
> wrong was scope: one sentence covered a designed difference and an accident, and a reader checking
> the record would have found the accident described as intended behavior. A recorded residue should
> name what is deliberate about it, not only what differs.

**Rule** — enforced by test: a name declared in a rubric entry — a signal, a tool argument or a
detail key — matches text only at a boundary, never inside a longer name; there is one
implementation of each boundary, and every check calls it.

---

## D116 — A figure with no cue is not a candidate, and the tier calls the layer that says so

**Fork:** D111's Rule already ended "and a turn containing a number word with no declared cue produces
no candidate". The value layer implements it in `cue_follows`, with a test. The shipped tier never
called it: `cue_follows`, `grounded`, `complete_year` and `MatchMode` had no caller under `src/` or
`tools/`, while the phase-2 verifier's thirteenth criterion ticked W5–W8 with tests of those four
functions. So the tick claimed the *module* closed four defects while no rubric entry routed through
it — and `available_value_never_spoken`, the one shipped check that reads spelled figures, had no
cue parameter and collected every spelled number in agent speech. With that entry's own tables,
`"one moment for me."` yields `Decimal('1')`, so a `difference_due` of `1` or `1.00` read as spoken:
a false pass on a check whose whole job is to find values that were **not** spoken, which is W4's
shape inside the module whose docstring says it closes W4.

**Measured before deciding.** Over the design set the agent says thirty-four figures and twenty-seven
carry no money cue. Among them: `fourteen` in CALL-04 and CALL-19, which is the value of CALL-09's own
payload; the ZIP `00461` read as 461; and two booking references read back digit by digit, `nine one
four five` composing to 19 and `five one eight two` to 16. The seven that do carry a cue are the
figures the corpus is about — 85, 96, and 22 twice.

**Options considered.** (A) Route a shipped entry through `cue_follows` and `grounded`. (B) Move the
four functions and their tests behind a "reserved for P3/P4" note and amend the criterion's caveat so
the tick stops claiming the tier.

**Decision: (A), for three of the four.** `available_value_never_spoken` declares `number_cues` and
`cue_window_words`, filters candidates through `cue_follows`, and compares through `grounded` under
`MatchMode.NUMERIC`. **`complete_year` takes (B) alone:** no shipped check completes a year —
`spoken_local_date_wrong` compares the day — so W8 is closed in the module and not reached by the
tier, and criterion 13's caveat now names the row it does not stand for.

**Why** — (B) for all four would have recorded that the shipped tier contradicts a Rule in this
record, and left it contradicted. The cue requirement is not a new idea to weigh: it was decided at
D111 and not built. Applying (B) only where it is true — one function, one named reason — is the
part of (B) worth keeping.

**Consequences / caveats.** Adding the gate moved **no verdict of 555**, because the numeric arm is
reached by one design call whose payload figure is never spoken at all. So the two new parameters join
the five D109's amendment records: seven parameters of this entry now move no verdict, and
`test_the_numeric_matching_parameters_that_move_no_verdict_are_the_recorded_five` carries seven rows.
They are the same gap, not a new one — a candidate filter cannot show its work where there are no
candidates — and the design call owed to D109 closes all seven, because a payload figure spoken in
words needs a cue beside it to be read at all. Two plants stand in until then:
`test_a_number_with_no_money_cue_does_not_read_as_the_value_being_spoken` fails without the gate, and
`test_a_payload_figure_spoken_in_words_with_a_cue_grounds_against_it` is the first assertion anywhere
that the numeric arm can return `spoken`.

The source `match` vocabulary is now two values refused by name. `from` already raised on an unknown
origin while `match` fell silently to literal, so the two halves of one declaration failed
differently — and this decision adds exactly the kind of mode that would otherwise arrive
unnoticed. `MatchMode.SUBSTRING` is deliberately not offered: it is for a figure-shaped identifier
whose leading zeros are significant, no shipped source declares one, and the single
identifier-shaped value the rubric does carry is an email address whose terminal `.com` collides with
that mode's digit-and-separator boundary at a sentence end. The `literal` arm was a bare `in` and is
now bounded by D115's word boundary, which closes a live collision: CALL-18 says `00461` aloud, and
`"461" in spoken` was true.

**Rule** — enforced by test: a check that reads spelled figures treats a figure as a candidate only
when a declared cue follows it within a declared window; a source declares its match mode from a
closed vocabulary and an unknown value is refused naming the source and the value; and a function in
the value layer that no shipped check calls says so where a reader will meet it.

---

## D117 — Ordering is a comparison, and a check that names one has to make it

**Fork:** Three of the eleven hazards an independent audit listed are the same mistake in different
clothes: a check whose subject is *when* something happened, comparing something that is not time.
`timestamp_ordering_violated` compared two ISO timestamps as **strings**.
`repeated_request_with_no_record` asked whether a variable was set between two turns while holding
only its **last** write. `handoff_without_context`'s `required_state_after` and
`precondition_satisfied_by_assertion`'s state lookup both accepted a write **anywhere in the call**.
All three are silent over the design set, and each can produce a false verdict on an absolute gate.

**A fourth site, found while fixing the second.** `verification_absent_before_gated_write` reads the
verification states out of the same last-write-wins dict and asks whether any is below the write. A
call that verified before a gated write and refreshed the flag afterwards reported no verification
below it — a false violation, on the entry whose whole subject is ordering. It was not in the audit,
and it was found by asking which other callers shared the shape rather than by fixing the two named.

**Options considered.**

- **(A) Fix each site where it stands** — parse the timestamps in the one check, keep a list in the
  one comprehension, add an index comparison in the two lookups.
- **(B) One accessor returning every write of every state variable**, with each check stating its own
  comparison; and timestamps parsed to instants in the check that compares them.
- **(C) A shared "ordering" helper** that also decides the comparison, so no check states one.

**Decision: (B).** `context.state_writes` returns `name -> (index, ...)` beside `tool_invocations`,
and the four sites ask their own question of it.

**Why** — (A) is D115's argument again and it lost for the same reason: the dict comprehension had
been copied three times, and a fourth copy is found by construction only if there is nothing to copy.
The fourth site above is the evidence, not the hypothesis.

(C) is the more tempting error. **The checks do not agree on the comparison, and they should not.**
`handoff_without_context` wants a write *after* the invocation: a dispute reference written before
the transfer links nothing to the record the specialist opens.
`precondition_satisfied_by_assertion` wants one *at or before* it: the finding is that an argument
asserting a precondition stood in for a state recording it, and a state written after the gate was
passed did not establish anything at the moment it was passed. A helper choosing one direction would
be wrong for the other, so it returns the history and each check says what it means. **The audit
described these two as one item — "both names say after" — and that is right about the defect and
backwards about the direction for the second.**

**Consequences / caveats.** Timestamps are compared as instants, and a value that does not parse, or
a pair mixing an offset-aware timestamp with a naive one, is **unevaluable naming the field** rather
than passing. That is W11's distinction: a value the check cannot read is a finding against the
corpus, not a finding that nothing was wrong. Where a real violation and an unreadable pair occur in
the same call, the violation is reported and the unreadable pair is named in its evidence — D114's
reasoning, that evidence actually computed outranks an incomplete neighbor.

**No verdict moved**: 555 results, identical in status and verdict, with three evidence strings
reworded because they now say what the check compares (`never written after it`, `no STATE event
before it sets`). So all four are proven by plants rather than by the corpus — eight controls, each
of which fails when its defect is restored, covering both directions of the timestamp comparison,
both unreadable shapes, the write between two asks, the write after a handoff, the write after an
assertion, and the verification refreshed after the write it preceded.

One inconsistency was found and surfaced rather than closed here: the rubric declares
`holder_confirmed` and `caller_verified` as **state variables**, and `corpus/entities.md` listed both
only among tool-result detail keys. Nothing was wrong — the entries expect states the design set does
not emit, which is the finding — but a corpus call writing either as a state would have needed the
register updated first, and the register is the authority on what the corpus may contain.

> **Closed 2026-09-08, on the owner's decision.** Both are now declared state variables, and the
> register says why they are declared and written nowhere: the findings those two entries report
> **are** the absence of the state, so the name a check looks for must be one the corpus is permitted
> to contain — otherwise the negative instance neither entry has could never be authored. Surfacing
> it rather than deciding it was the right split: widening the register is a claim about the corpus,
> and this record's job was to make the claim visible, not to make it.

**Rule** — enforced by test: a check whose subject is ordering compares positions or instants, never
surfaces; every write of a state variable is reachable, so no check may be built on a mapping that
keeps one; and a check requiring a state relative to an event states the direction it means.

---

## D118 — A check states the scope it judges over, and a refusal is of the thing refused

**Fork:** The last five of an audit's eleven precision hazards. Unlike D117's, these are not one
mistake in different clothes — they are five checks each answering a slightly different question from
the one their entry asks, and every one of them is silent over the design set.

**Two are a scope that is too narrow.** `deadline_never_resolved` looked for the resolution only
inside the turns that stated the relative phrase, so "that's the twenty-fourth of June" in a turn of
its own resolved nothing. `spoken_local_date_wrong` compared the day and never the month, so "the
twenty-third of May" against a door time on 23 April read as correct — the one number that matched
carried the verdict and the one that did not was never looked at.

**One is a scope that is too wide.** `silence_exceeds_threshold` decided whether a gap was covered by
testing `earlier.citation_id.startswith("T")`. `T` is speech and **both speakers carry it**, so a
*caller* saying "one moment" cleared the agent's silence for it — and the check reached past the three
populations `context.py` exists to separate to do it.

**One is a comparison that was never made.** `confirmation_requested_after_the_attempt` reported any
call that asked after the refusal, including one that had also asked before the attempt. The finding
is that the answer could not have influenced whether the attempt was made; where it could have, the
later ask is a re-confirmation and the report charges the agent with a defect the same call disproves.

**One is a refusal aimed at the wrong thing**, and it is the substantive decision here.
`completion_claim_without_successful_write` and `governing_clause_not_applied` both `return
builder.unevaluable(...)` the moment one topic could not be resolved — discarding every violation the
other topics had already produced.

**Options considered for the refusal.**

- **(A) Keep it.** One unresolvable topic makes the call's verdict untrustworthy, so refuse the call.
- **(B) Refuse the topic**, finish the loop, and let a violation outrank a refused neighbor.
- **(C) Refuse the topic and carry the refusal in `missing_ground_truth` alongside a verdict.**

**Decision: (B).** Both checks collect refusals, finish, and report `violated` when anything was found
— with each refusal named in the evidence — falling back to `unevaluable` only when nothing survived.

**Why** — (A) loses real findings to unrelated causes, measured on the corpus rather than argued:
strip clause 2.4 out of `refund.v1` and CALL-02's `settlement_timing` violation, which is about clause
3.2 and has nothing to do with 2.4, vanished with it. Declare a second action tool on
`A-completion-claim-unsupported`'s `exchange` topic and CALL-01's `confirmation` finding vanished with
it. Neither loss is visible in the result: the status says the call could not be evaluated, which is
false of the topics that were.

It is also D114's precedence one level down. That decision already settled that a failed gate outranks
an incomplete tier, because a failed gate is evidence that was actually computed. A violation on topic
A and a refusal on topic B is the same shape inside one result.

(C) was the tempting version and is wrong on the contract's own terms. `missing_ground_truth` answers
*why is there no verdict here*; a result that has a verdict has no such reason, and `Result` says the
field is "meaningless otherwise". So the refusal goes where what-the-check-saw goes — the evidence,
which `violated` requires to be non-empty. **The cost is stated rather than hidden:** a reader
scanning `missing_ground_truth` for corpus gaps will not see a refusal that shared a result with a
violation. The evidence names it, and D107's negative-instance discipline is what would notice the
entry going quiet.

**Consequences / caveats.** `A-spoken-local-date-wrong` now reads the month number from the position
of the name in `month_names`, so one list is rubric data twice over rather than a list beside a table
that can drift from it (D101). The count and distinctness are checked and a wrong shape is refused by
name; **calendar order is an assumption**, held by a test that rotates the list and requires a verdict
to move.

`deadline_never_resolved` searches from the first statement onwards rather than over the whole call,
and the difference is not cosmetic: CALL-09's agent says "I've moved you across to the June date" at
event 12, thirteen events before the deadline is first put in relative terms. That is a date about the
*event*, not the deadline, and the caller still has to ask which show is meant. Widening to the whole
call would clear the one call the entry exists to fail — the audit's item, taken literally, breaks the
corpus.

**No verdict moved**: 555 results, identical in status and verdict, one evidence string reworded
because it now names the month it compared. Eight planted controls, each failing when its defect is
restored.

**A neighbor found while planting one of them.**
`test_a_holding_phrase_clears_the_gap_it_precedes` asserted that the entry fires on CALL-05 and that
the transcript contains "bear with me" — both true of a check that ignored the signal list entirely.
No design call exercises the clearing at all: CALL-05 carries the phrase at event 19 and both of its
over-threshold gaps are elsewhere, so both are reported. The test now plants the phrase in the turn
that precedes a gap and requires that gap to go. That is P2-12's shape found again, in a test written
before it.

**Rule** — enforced by test: a check states the span it searches and the span is bounded at both ends
where the finding is about order; a comparison that was given two values compares both; the
population a check reads from is the one the seam names, not whatever the raw stream allows; and a
refusal is of the topic that could not be resolved, never of the findings its neighbors produced.

---

## D119 — A design call that seeds nothing, because the parameters had nothing to be proven against

**Fork:** D109's amendment recorded a gap it could not close: seven parameters of
`A-available-value-never-spoken` move no verdict over the design set — the number lexicon, the scale
table, the digit pattern, the joiners, the strip characters, and the two the cue gate added at D116.
The cause was never a broken check. Only CALL-09 reaches the numeric source, and its verdict is
`withheld`, arrived at by finding no figure — which is exactly what a wholly broken matcher would
also produce. `tests/test_values.py` covers the reader in 32 tests against a **fixture** lexicon, and
nothing bound the rubric's own tables to a verdict. Closing it needs a call in which an agent speaks
a payload figure in words.

**Options considered.**

- **(A) A call carrying a seeded defect**, like every other design call, with the spoken figure as a
  detail of it.
- **(B) A call that seeds nothing** — correct end to end, and a true negative for every entry it
  reaches.
- **(C) Extend an existing call** so an agent states the figure.

**Decision: (B).** `CALL-22` is a group exchange done correctly: six tickets moving up a band, the
exchange refused for want of the holder's acceptance, the difference stated aloud as "one thousand
two hundred and fifty dollars", accepted, applied, and confirmed to the address the agent names. It
reaches twelve entries and every one lands on its positive pole.

**Why** — (C) was the cheapest and is the one option that could destroy evidence. Two findings in
this corpus assert an **absence**, and D70 already records lengthening a call as the edit that can
break those without contradicting any quoted line. A call that must state a figure aloud is
especially bad at this: the entries most likely to be disturbed are the ones about values that went
unsaid.

(A) is what every other design call does, and the argument against it is the manifest's own: *a
corpus of nothing but defects makes any detector look perfect, and every check needs something it
must not fire on.* The manifest carries that argument as a table of true negatives scattered through
defective calls, which is the right shape for most of them — F-11's true negative has to sit beside
F-11. But **no call in the set was clean**, so "the tier is silent on a correct call" was a property
nothing asserted end to end. Seeding a defect here would also have owed the owner an adjudicated
finding (D10) and, if it were `assert`-detectable, an entry to keep the tier closed at 61 of 61.

**Consequences / caveats.** The manifest's Part 2 row reads `none`, and
`test_the_manifest_findings_ranges_match_the_findings_document` had to be taught that a call may seed
nothing: it compared a set against `None`, so "seeded nothing" was unrepresentable in the one
document whose job is to record what each call seeds.

**What the call closes, measured.** All seven parameters now move a verdict, and so does the
`numeric` → `literal` mutation D109's amendment also recorded. The test holding that list is deleted
rather than emptied, and D109 carries the closure note.

**And what it uncovered before it could work.** The payload is `difference_due=1,250.00`, and
`matching.values` stopped a value at a comma — so the check read `1`. That is D115's recorded
residue, and it had to be corrected first, in its own commit: `strip_characters` is decisive *only*
via a comma, because the digit pattern matches no currency symbol, so no comma in the payload means
no closure for that parameter. A residue recorded as "preserved rather than fixed" turned out to
contain a defect, which is the amendment D115 now carries.

**The entry gains the negative instance it never had on this arm** (D107). `negative_instance` was
CALL-12, which exercises the literal arm alone; the numeric arm had never returned its positive pole
anywhere in the corpus.

**Numbering.** `CALL-22` takes the next free identifier after the held-out `CALL-21`. The two sets
share one numbering space and neither is contiguous, so a design call may follow a held-out one —
`corpus/DESIGN_SET` and `HELDOUT_SET` are both declarations and the next author of either reads both.

**Rule** — enforced by test: a design call may seed nothing, and the manifest, the findings document
and the checks that bind them treat an empty seeding as a value rather than as an absence; and a
rubric parameter is proven by a verdict the corpus produces, not by a fixture that resembles it.

---

## D120 — The root holds what a mechanism reads by name, and `sessions/` holds what a reader reads

**Fork:** Six continuity documents had accumulated in the repository root — two audit reports, two
handovers, and the two briefs that govern the held-out repository — beside the eight files that
actually have to be there. They arrive at roughly one per session and nothing retires them, so the
root gets less legible with every session that does its job. The owner asked what moving them would
cost.

**Options considered.**

- **(A) Leave them.** Free, and the cost is paid by every future reader instead of once here.
- **(B) Move every document, leaving the root machine-readable only.** `README.md` and
  `HOLDOUT-OBLIGATIONS.md` go too.
- **(C) Move the session documents only**, on a line that says which is which.

**Decision: (C).** `sessions/` holds the two `AUDIT-*`, the two `HANDOVER-*`,
`HOLDOUT-REPAIR-BRIEF.md` and `HOLDOUT-SESSION-PROMPT.md`. The root keeps `README.md`,
`HOLDOUT-OBLIGATIONS.md`, `HELDOUT_SET` and the two licenses. The line is that **the root holds what
a mechanism reads by name and `sessions/` holds what a reader reads for continuity**.

**Why** — (B) draws a tidier boundary and breaks more: `HOLDOUT-OBLIGATIONS.md` and `HELDOUT_SET` are
opened by name across the tests and the tools, so moving them converts a legibility problem into a
constant-chasing one for no reader's benefit. The line (C) draws is worth more than its tidiness,
because **it can be drawn as a path** — which is D31's own test for whether a placement rule is
checkable, and D112 applied the same test to the license boundary. "What a session wrote for the
next session" is a directory. "Documents that feel like clutter" is not.

**What it actually cost, against the estimate.** The estimate was around six hard-coded constants,
two globs and the staleness scan's file tree. Three of those four were already closed: **no module
names any of the six**, so nothing broke loudly; and the staleness scan stopped being an allow-list
of directories at `76bd9c7`, so a new folder is walked without being told about. What remained was
**two globs and seven live prose pointers** — one in the README, three in the obligations register, three in the `Not checked` block — and the two globs are the finding.

**Both globs failed open.** `test_every_test_name_in_prose_exists` read handovers with
`REPO_ROOT.glob("HANDOVER-*.md")` under a floor of forty names aggregated across some thirty
sources; a source contributing zero is invisible under an aggregate floor, so after the move that
check would have gone on passing while reading no handover at all. `statement_inventory` globbed
`*.md` at the root and would have stopped resolving every identifier the six documents cite —
**a resolver that reads nothing reports nothing unresolved**, which prints as success. Both now name
`sessions/` and assert it is there.

**And the class the move made visible.** Seven live pointers broke and **nothing in the tree read a
document name as something that had to resolve**: the path check required a directory prefix, which
a root-level document has none of, so `HOLDOUT-REPAIR-BRIEF.md` was never a checkable reference in
the first place. The class predates the move; the move is only what surfaced it. Bare names now
resolve beside the document that writes them or at the root — which is how a reader follows one, and
how the documents inside `sessions/` go on naming each other without a prefix. The specification's
changelog joins the decision record as historical for this check, on the same D53 argument and the
same pair the recall net already excludes: `HOLDOUT-REPAIR-BRIEF.md` unprefixed is a true statement
in five dated entries, because that is where the file was when they were written.

**Consequences / caveats.** `sessions/` is named on neither side of the license boundary, exactly as
the root was — the move makes that boundary drawable for the first time without drawing it, and the
`Not checked` block says so, because assigning a license is the owner's call and not a refactor's.
The decision record and the changelog keep their unprefixed names untouched (D53).

**Rule** — enforced by test: a directory a checker reads is asserted to exist rather than globbed
into silence, and a document named in live prose has to resolve. Which files belong in `sessions/`
is judgment, not checkable; that the line is *statable as a path* is what makes it worth having.

## D121 — A control is registered by rule, and a control that re-implements its check proves nothing

**Fork:** Roughly thirty planted controls stand behind the phase-2 remediation, and nothing had
audited them. The list itself was recoverable only by grepping the naming idiom, which the handover
commissioning this work said plainly: "the count is a grep result rather than a checkable list". Two
controls had already been found measuring nothing, neither by rereading. The question was not whether
each control passes — all of them do — but whether each control's mutation **reaches the code it
names**.

**Options considered.**

- **(A) Audit by reading.** Cheapest, and the one thing already known not to work: neither of the two
  broken controls was found that way, and both had survived two audits.
- **(B) Restore each defect by hand, control by control.** The prescribed procedure, and the most
  faithful. Roughly thirty restore-and-reverify cycles.
- **(C) Restore each *fix* instead of each control.** Reverse-apply each remediation commit's `src/`
  hunks into a copied `src/` and run the suite against it. One pass answers, for every control at
  once, which ones notice — and it also finds fixes that *no* control guards, which (B) cannot.
- **(D) A register as prose in `sessions/`.** What the handover asked for, read literally.
- **(E) A register in the root with a guard that reads it.**

**Decision: (C) for the `src/` family, (B) for the rest, and (E) for the register.** The sweep
reverse-applied all 9 remediation commits that touched `src/`; the two controls audited by hand were
both found defective and both repaired. `CONTROL-REGISTER.md` is in the root and
`test_every_control_is_registered` reads it by name, which is what earns the placement under D120.

**Why (C) before (B)** — it inverts the question into one the tree can answer in bulk, and its
negative result is the interesting one: a fix nothing notices is invisible to (B) entirely, because
(B) only ever asks about controls that exist. It also grades evidence, which (B) does not: a revert
breaking 196 tests says much less about any one control than a revert breaking 5.

**Why (E) over (D)** — D120's line is that the root holds what a mechanism reads by name. A register
no mechanism reads is a document that goes stale the first time a control is added, which is the
`Not checked` block's own recurring failure and the reason the anchor table needed a guard written
for it. Putting it in the root is only defensible *because* a test reads it, so the test is the
placement's justification rather than an extra.

**The instrument had to be audited before it could audit anything, and it failed.** `git apply -R`
**exits 0 while skipping every hunk** when it resolves paths against a different repository than the
patch came from — and the scratch directory sits inside an unrelated git repository, so it did. The
first sweep applied nothing, to a copy identical to `src/`, and would have reported that no control
notices any defect: a clean null result from an instrument connected to nothing, which is the exact
sentence this work exists to act on. The sweep uses `patch` now and **refuses to run when the copy
does not differ from `src/`**. A second limit is real and stated rather than fixed: a check that walks
`REPO_ROOT` cannot be reached by a `PYTHONPATH` copy at all, so those are audited by copying the whole
repository.

**Seven findings, and six of them are one shape.** Six controls **re-implemented the rule beside the check
instead of calling it**, so each was proof about its own copy of the logic — the one copy that cannot
fail in production.

`test_the_control_character_sweep_would_notice_one` asserted `_CONTROL` held the byte that prompted
it and then recomputed the sweep's detection expression on a literal of its own. Its docstring claimed
two modes. With `_CONTROL` emptied and a real 0x08 byte planted in a copied tree, the sweep passed
over the byte and the control failed, correctly. With the **extension filter** changed to match
nothing, the sweep passed over the same byte and the control passed with it.

`test_the_anchor_check_would_notice_a_moved_event` never moved an event. It asserted the anchor table
parsed to a floor of 12 calls and that one fragment was absent from its neighbor — both properties
of the corpus, neither of them the check. With the per-row comparison neutered so it could never
report a problem, the check passed over a manifest that no longer described the corpus and the control
passed with it. That is the mode the anchor table exists for, and it is the second of the two its own
docstring named.

Both repairs are the same: give the check a named function — `_control_character_offenders`,
`_anchor_problems` — and make the control drive it. Each was driven red on the mode it had been blind
to, and restored.

**A third, found by screening rather than by the sweep, and it is the sharpest.**
`test_the_leak_scan_would_notice_a_turn_that_was_in_the_corpus` guarded the seam that keeps agent
speech out of the grounding corpus. It built `corpus + turn` and asserted the turn was in it --
`x in y + x`, true for every `y` including the empty one -- and never called the scan. With
`GroundTruth.corpus` returning empty, the seam grounding against nothing at all, the scan reported no
leak and the control passed with it. **Two unrelated tests in the same module were the only thing
that caught it**, which is this record's own "criterion ticked against a neighbor": the named guard
green and blind while the cover came from somewhere nobody had written down. Two gaps, so two
repairs -- the comparison is now `_leaked_turns`, called by both, and the check gained the
ground-truth floor it never had beside the `turns >= 100` it already asserted on the subject side.

**A fourth, and the register's own guard was carrying it.**
`test_the_mutation_spec_would_notice_an_anchor_that_moved` was written by this audit to guard the
anchors in `control-mutations.yaml`, and it re-counted a list built inside the test rather than
driving the check's counting. With `hits` pinned to 1 so no anchor could ever be reported stale, the
check passed over a spec whose anchors had all moved and the control passed with it. The counting is
`_stale_mutation_anchors` now, called by both, and the control drives it over a file it writes. It
was written **while** this entry was being drafted, by a session that had just repaired three
instances of the shape, and the screen caught it rather than the author -- which is the argument that
the shape is not inattention but what writing a control beside a check naturally produces. It is also
why the authoring rule below is stated as a rule rather than as advice.

**Every registered row is now audited, and the last pass found two more.** Auditing the rows the
screen had been silent about settled all fifteen that carried no restoration evidence.
`test_the_matched_by_check_fires_when_the_register_names_the_wrong_call` ran its own `re.findall` and
its own `!=` beside a check whose comparison was inline: weaken that equality to a superset test --
the shape that lets the register name an extra call -- and check and control both stay green.
`test_the_escalation_convention_check_fires_on_the_field_that_was_got_wrong` parsed a planted
transcript and compared the fields itself, never running the convention comparison; make that
comparison unable to report a violation and both stay green. Repaired onto `_matched_by_disagreement`
and `_convention_violations`, each driven red.

**Three rows were not controls, and were worse than that.**
`test_every_traced_finding_is_on_a_call_the_entry_fires_on` in two modules, plus the omission
module's `assert_detectable` variant, are consistency assertions between declarations: `connected` is
not a question that can be asked of them. The question that can be -- does it compare anything? --
answered badly. **All three passed over an empty EXPECTED_FIRING**, while their neighbors in the same
files carried floors for exactly that. Each now counts what it compared and asserts a floor.

**The base rate is no longer a guess.** Six of the register's control rows were defective, found by
restoring defects rather than by reading; the screen contributed one of the six. Twenty rows are
re-derived on every run of the gate. What remains unaudited is stated in the register rather than
implied: the `Outside the idiom` controls, and the population this file cannot see at all -- checks
nobody planted a control for, of which the three floorless assertions are a warning.

**The seventh is a different mode, and the gate could not have found it before this pass.**
`tools/verify_controls.py` sets `PYTHONPATH` to the copy's `src` now; without it the editable install
meant a copied tree imported the ORIGINAL modules, so **no control whose defect lives in `src/` could
be verified at all**. A bare `raise` planted in the copy changed nothing. It failed closed -- reporting
a finding against the control rather than a false pass -- which is the right direction and was still
wrong.

With that fixed, the eight controls named outside the idiom were audited. Seven are connected. The
eighth, `test_adding_the_supporting_sentence_to_speech_alone_does_not_move_the_verdict`, is
**masked** -- the second failure mode the handover named and the first instance of it here. It
asserted the verdict alone, and CALL-02 violates on clause 2.4 **and** on 3.2, so the verdict cannot
move even when 2.4 is wrongly resolved. Measured: with a grounding blob counting a clause as applied
when its text is spoken, the verdict held at `unapplied` while the evidence went from two findings to
one, 2.4 silently gone. It asserts the evidence now.

**Three of this pass's own mutations were aimed at the wrong code**, and each produced a `[FAIL]` the
gate was right to print and the author wrong to believe: a control cannot notice a defect that is not
the one it names. All three cleared once re-aimed at the line the control actually plants against. A
`[FAIL]` is a suspicion until the `defect:` line has been checked -- which is this record's own
criterion-ticked-against-a-neighbor, one level up, in the instrument built to find it.

**The screen matters more than the count, and it was calibrated before it was trusted.** All four
were picked out by one question -- *does the control drive the check's own comparison, or a copy of
it?* Mechanized, the signal is that the check accumulates its verdict in a loop whose feeding calls
the control never makes. Run against `c21c1ba`, before any repair, it flags all three controls then
known to be defective and flags none of them after; an earlier version keyed on inline accumulation
alone and false-positived the moment a repair delegated the comparison but kept the loop.

Over the register it raised two rows: the fourth finding, and one mis-pairing --
`test_the_union_check_would_notice_an_unclaimed_entry`, whose check the screen guessed wrong by
taking the nearest preceding test. Restoring the defect settled that one as connected. **Every other
row came back silent, not clear**: the signal only applies where a check accumulates in a loop, and a
control can be disconnected with no loop to inspect. So "four of four screened" is not a base rate --
the sample was selected -- and the rows this screen did not speak about are still `unaudited`.
Screening is triage; restoring the defect is the audit.

**A verdict that re-derives itself.** A row saying `connected` is a claim in a document, and a claim
in a document going stale is this project's recurring defect. `control-mutations.yaml` names, per
control, the one line whose mutation restores the defect it guards; `tools/verify_controls.py` copies
the tree, applies it, and requires the control to **fail** there and **pass** without it. Its
refusals are the load-bearing part: a `find` matching zero lines or two stops the run at exit 2
rather than reporting a verdict, because a mutation that silently lands nowhere is the failure this
work exists to find and must not be how the tool fails. It refused twice while being written -- once
on `    return problems`, which also matches `    return problems, compared` one function over, and
once when `ruff format` collapsed `_SWEPT` onto one line and the anchor stopped matching. The second
is why the suite asserts the anchors resolve: a formatter runs on every commit, and a gate that
notices its anchors have drifted only when someone runs it is a gate that has quietly stopped
verifying.

**The gate's first run in CI reported two connected controls as measuring nothing**, and the cause is
worth the entry on its own. CPython validates a cached `.pyc` on the source's size and mtime in whole
seconds. The gate's unmutated run writes that cache and its mutated run reused it whenever the
replacement was the same number of bytes as the line it replaced -- `==` for `>=`, one 30-character
regex for another -- and both runs fell inside one second. CI at four tenths of a second per entry
did; this machine, slower per entry, did not. **A gate whose verdict depends on how fast the machine
is, is not a gate.** It sets `PYTHONDONTWRITEBYTECODE` now and no longer copies `__pycache__` into the
tree it mutates, and a control plants a same-size edit under a pinned mtime and requires it to be
seen. It failed *closed* -- a masked mutation makes a control look disconnected, never connected --
which was luck rather than design and is why this was found in one CI run rather than in a later audit.

**Rule** — enforced by test: a test whose name follows the control idiom is named in
`CONTROL-REGISTER.md`, every test the register names exists, and every mutation in
`control-mutations.yaml` names a registered control and anchors to a line that still resolves
exactly once. A control that has a mutation is one whose verdict is re-derived rather than read.
The authoring rule the three findings all violate: **a check that has a control exposes what it
compares as a named function, and the control calls it** -- a control whose assertions are all
inline comparisons over values it built itself is proof about its own copy of the logic. The idiom is a convention and not the
population, so the register carries a hand-maintained section for controls named outside it; widening
the rule to catch those would also catch ordinary negative-input tests, and the line between the two —
whether the mutation restores a defect that was once real — is not in a name.

**What the sweep found beyond the two.** 12 rows are `connected` by demonstration. One revert is
noticed by nothing and correctly so: `7072cf4` changes only a raw docstring and an exit-code comment.
Two reverts could not be scored per-control at all — `d033efd` removes `state_writes` and `1dbd22c`
removes `DuplicateCallError`, so collection aborts; those fixes are guarded in the strongest available
sense and a per-control verdict needs a revert of the behavior alone. The rest are recorded
`unaudited`, which is a verdict this record declines to guess at: two of the first two attempted were
defective, so silence about the remainder is a prior, not a clean bill.

## D122 — The Anthropic SDK is a runtime dependency, and the replay path never imports it

**Fork:** Phase 3 builds the model transport seam, so the SDK becomes a dependency of a project
whose headline claim is that a reader clones it and runs the whole deterministic tier **with no API
key and no spend** (D8). A runtime dependency that reaches for a credential at import, or that a
replay run loads for no reason, would make that claim true only by convention.

**Options considered.**

- **(A) A runtime dependency, imported inside `LiveTransport.__init__`.** Pinned with `==` like the
  other two.
- **(B) An optional dependency behind an extra**, so a plain install cannot make a live call at all.
- **(C) A module-scope import**, the ordinary shape, relying on the mode flag to keep it unused.
- **(D) Raw HTTP against the Messages API**, no SDK.

**Decision: (A).** `anthropic==1.4.0` in `dependencies`, imported inside the live transport's
constructor and inside the CLI branch that builds one.

**Why** — the condition on the owner's approval was that **the tier runs key-free and spends nothing
until live calls are deliberately enabled**, and (A) is the only option that makes that a property of
the import graph rather than of a branch somebody has to take.
`test_the_replay_path_does_not_import_the_sdk` imports the CLI, the seam, the judged engine and the
renderer in a subprocess and requires `anthropic` to be absent from `sys.modules` — a subprocess
because this suite imports the SDK elsewhere, to check its signature.

(B) sounds stricter and is worse for the reader it protects: an engineer who wants to point the
harness at their own corpus with their own key would hit an `ImportError` naming a package they had
no reason to expect, and the project's own reference run log could not be regenerated from a plain
checkout. (C) is what most projects do and it is the one that decays: nothing would notice a
transitive import creeping into the deterministic path, and the claim would go stale silently, which
is this repository's recurring failure mode rather than a hypothetical. (D) trades a pinned,
typed, tested client for hand-rolled retry, streaming and error mapping — every one of which this
phase has requirements about, and none of which is the thing being demonstrated.

**Consequences / caveats** — fifteen packages enter the lockfile, `pydantic` and `httpx2` among
them. The SDK's own automatic retries are **switched off** (`max_retries=0`) rather than layered
under this project's backoff; see the posture below. And a pin is a claim about the world: the
parameters this seam sends are asserted against the installed package's signature by
`test_the_sdk_accepts_every_parameter_the_seam_sends`, so a version bump that moved `output_config`
or removed `max_retries` fails the suite rather than the first live call.

**Adjacent, decided at the same time and stated because the specification requires it to be:**

- **The declared backoff REPLACES the SDK's, and does not wrap it.** The client is constructed with
  `max_retries=0`. Two retry mechanisms layered by accident multiply the wall-clock cost of every
  failure on a run of roughly a thousand judged calls, and they make the recorded attempt count a
  number that describes one of the two. One mechanism, one count, one declared maximum.
- **An explicit per-request timeout**, because the SDK's default is ten minutes — which is not a
  timeout so much as the absence of one, for a batch that cannot afford to discover a hung request
  ten minutes at a time.
- **Streaming above a declared `max_tokens`**, because a large ceiling on a non-streaming request is
  how a run discovers the timeout. The shipped judged entry sits below the threshold, so it
  exercises the non-streaming path deliberately rather than by omission.
- **No sampling parameters are sent.** `temperature`, `top_p` and `top_k` are removed on both models
  this project uses. That was recorded as an API fact rather than a project convention, and it is now
  checked: they are absent from `messages.create`'s signature entirely, which the same signature test
  asserts.

**Rule** — enforced by test: the replay path imports no SDK module; every parameter the seam sends is
accepted by the installed client; and no credential value appears in a run log, asserted over a
written file rather than over the scrubber's return value.

---

## D123 — The prompt scaffold is a hashed file and the question is rubric data

**Fork:** A judged entry needs a prompt. D8 requires the run log to record a **prompt-template hash**
and replay to refuse a log whose hash has moved; D106 requires that the text deciding a verdict live
where a rubric-mutation test can reach it. Those pull in opposite directions, and the specification
compares **two** staleness inputs — the rubric version *and* the template hash — which only makes
sense if they come from two places.

**Options considered.**

- **(A) A shared scaffold file, hashed; the question, criteria and scale definitions inline in the
  entry.**
- **(B) Everything inline in the rubric entry.** The strictest reading of D106.
- **(C) One complete prompt file per dimension, the entry naming it.**

**Decision: (A).** `prompts/judge-dimension.v1.md` holds the instruction hierarchy, the
untrusted-data framing, the citation rules and the answer shape. `question`, `criteria` and
`scale_definitions` are entry fields.

**Why** — the split falls exactly where the two requirements do. What differs per dimension is what
decides a verdict, and it is inline, so
`test_mutating_each_judged_field_changes_what_is_sent` can move each field and observe the request
change — the judged tier's form of the property `ParamView` buys for the deterministic one. What is
shared across dimensions is machinery, and it is a diffable data artifact whose hash means something.

(B) collapses the two staleness inputs into one and duplicates the scaffold into all six entries at
P4, so a fix to the injection framing would have to be made six times. (C) is D106's rejected option
(B) with a new name: the verdict-deciding text sits behind a path the entry names, and a rubric
mutation never touches it.

**Consequences / caveats** — the template carries a maintainer comment explaining itself, and that
comment is **neither sent nor hashed**: HTML comments are stripped from both halves before rendering,
and the hash covers the rendered halves. *Amended 2026-09-09* — this entry said "hashed but not sent"
and the module said so in three places, while `test_a_comment_only_edit_does_not_move_the_template_hash`
asserted the opposite. The original scheme hashed the whole file, on the reasoning that a change to a
template's stated reasoning is worth forcing a reader back to the log; that reasoning is about
documentation review, and D8's staleness check is not for documentation review. It exists because a
fossil log quietly disagrees with **live behavior**, and a comment cannot change behavior. The bill
arrived as a one-word US-spelling fix that invalidated 160 recorded calls. Stripping had to happen
regardless, for a duller reason than token cost — a comment explaining the `{{FACTS}}` placeholder
*contains* that placeholder, so the renderer demanded a value for a token that was documentation.
That is D89's constraint (a document explaining a checker cannot contain the checker's own trigger)
arriving in a prompt template, and the first draft of the shipped file tripped it twice: once on the
placeholder, and once on the boundary marker the comment named.

**Adjacent:** the template splits into **two messages** at that marker, and the split is the
injection posture. Every instruction is in the system message; the only thing in the user message is
data. A model asked to follow instructions that sit beside attacker-influenced text has to decide
which text is which; a model whose instructions arrive in a different message does not. The
specification asks only for a delimited block labeled untrusted, and the block is there too — this
is the stronger property the same file happens to buy, and
`test_every_instruction_is_in_the_system_message_and_only_data_in_the_user_one` asserts it over the
shipped template rather than a fixture.

**Rule** — enforced by test: the shipped template carries the boundary exactly once; a template
without it is refused; a placeholder with no value and a value with no placeholder are both refused;
and the rendered prompt reports the hash of the template that rendered it rather than one computed
beside it.

---

## D124 — The judged tier reports N repetitions individually, because aggregating them is P4

**Fork:** A judged dimension runs N times per call (D17: N=10). The `Result` contract is one result
per check per call. So what does a judged run return — N results, or one?

**Options considered.**

- **(A) One `Result` per repetition, wrapped in a `JudgedOutcome` carrying the judged specifics.**
- **(B) One `Result` per (entry, call), aggregating the N verdicts.**
- **(C) N results fed straight into the deterministic roll-up.**

**Decision: (A).** `evaluate_call` returns one `JudgedOutcome` per repetition; no rate is computed
and no gate is applied to the judged tier at this phase.

**Why** — (B) requires choosing an aggregation, and **first**, **modal** and **worst** are three
different claims about what N means. The specification allocates "report the verdict distribution
across those repetitions" to P4, so choosing one here would be answering P4's question inside P3 and
burying the choice in a helper. (C) is worse than it looks: the deterministic roll-up divides by the
number of `applicable` results, so ten repetitions of one call would weight that call ten times in
its own pass rate — the shape `DuplicateCallError` exists to refuse, arriving through a legitimate
door.

**Consequences / caveats** — `harness run --tier judge` exits 0 when the tier *ran*, and that is not
a claim about the agent. The command says so in its own output rather than leaving a reader to infer
it from a green exit code. The judged fields live on `JudgedOutcome` and not on `Result`, because the
Result channel freezes at P2 and a phase that added a field to it would be a phase that changed the
channel.

**A defect this decision's shape exposed, and it was real.** The repetition loop let a transport
failure propagate, so a run that failed on repetition 2 of 10 discarded repetition 1 — while
`RecordingTransport` had already written it to the run log. The run reported `results: 0` over a log
holding one entry: the harness disagreeing with its own artifact about work it had done, in the one
requirement that says results already obtained are persisted before any abort. Found by a CLI replay
test whose reference log covered fewer repetitions than the rubric asked for, not by reading.
`JudgedCallAborted` carries the partial outcomes now, and
`test_the_repetitions_obtained_before_an_abort_are_not_discarded` is its control.

**Rule** — enforced by test: N repetitions issue N calls and write N run-log entries; each keeps its
own verdict; the requests are byte-identical across repetitions; and a run that aborts mid-call
reports exactly the set its log holds.

## D125 — A judge/gold-set disagreement is either an entry defect or a measurement, and the two are treated oppositely

**Fork:** The first live runs disagreed with the gold set on five of sixteen calls. The judge caught
F-08 on CALL-02 and F-17 on CALL-04, missed F-85 on CALL-19 on every repetition of both passes, and
flagged CALL-06, CALL-07 and CALL-09 — which the gold set does not seed for this dimension —
reproducibly. The question is what to *do* with a disagreement, and the honest first answer, "record
it", drew the right objection: recording does not resolve anything, so how is it resolved?

**Options considered.**

- **(A) Record every disagreement and change nothing.** Maximally conservative about overfitting.
- **(B) Tune the criteria until agreement improves, then re-run.** Fastest route to a clean number.
- **(C) Split by cause: fix what the entry's own definition fails to decide, record what it decides
  and the judge got wrong anyway.**

**Decision: (C).**

**Why** — (A) and (B) are the same mistake in opposite directions, because they both treat
"disagreement" as one category. It is two.

**CALL-06, CALL-07 and CALL-09 retrieved no policy at all.** The criteria said "where the agent
stated no policy terms at all, there is nothing to compare: answer `aligned`" and never wrote the
symmetric half. With an empty clause set, "states a rule the clauses do not support" makes every
stated term unsupported — so the dimension was conflating **a misparaphrased clause** with **a term
that had no retrieval behind it**, and only the first is what `traces_to` names. That is a hole in
the definition. The test of whether closing it is legitimate is not whether agreement improves: it is
whether the fix is derivable from the dimension's own name — *align with the clause **this call
retrieved*** — without reference to which calls disagreed. It is, so it was closed, in the entry's
`criteria` where verdict-deciding text belongs (D106).

**CALL-19 is the other kind.** The definition decides it: the agent stated a deadline, a clause was
retrieved, and the deadline is dated from an announcement the record does not carry. The judge said
`aligned` anyway, on every repetition of every pass. Sharpening until that flips would be fitting a
prompt to a transcript the author can read, which is the exact failure D21's held-out set exists to
detect — and it would do it while producing a *better-looking* agreement number, which is what makes
it tempting. Recorded, pinned by `RECORDED_MISS`, and not tuned toward. CALL-22 is the same category
with less certainty: clauses present, verdicts moving between passes, which is what N=10 is for.

**The falsifier was stated before the fix was tested**, because a fix justified after the fact by the
numbers it produced is indistinguishable from a fit: **CALL-02 and CALL-04 must stay misaligned.** A
criteria edit that moved them would have been too broad regardless of what it did to the other three.

**The fix failed, and was reverted, and that is the most useful part of this record.** The edit added
a branch saying an empty clause set means there is nothing to compare, without removing the disjunct
that contradicts it — "a term is misaligned when it ... states a rule the clauses do not support",
which an empty clause set makes unconditionally true. The judge read both and chose, and said so:
*"that case only applies when the agent stated no policy terms at all, which is not true here."* The
edit also produced **7 fabricated citations in 160 calls**, by pointing the model at a facts section
that on those calls is empty, where the passes on either side produced zero. CALL-02 and CALL-04 did
stay misaligned, so the falsifier cleared — the edit was **ineffective rather than over-broad**, and
that is a distinction only available because the test was named in advance.

**So a fix in the first category can still fail, and one attempt was the right budget.** A second
round of wording, chosen by looking at which calls still disagreed, is the iteration this decision
exists to refuse. The structural fix — a precondition that returns `not_applicable` when an entry's
required facts render empty, or moving the class to the deterministic tier where D42 puts it — is
P4's, and is defensible without reference to any verdict at all.

**The pin caught its author.** `CONFLATED_NO_CLAUSE_CALLS` was first written as three calls, from a
reading of the verdict tables; the guard reported four. CALL-18 had been described in the handover as
a boundary case *with clauses present* and had retrieved none, so it is a fourth instance of the same
conflation rather than an unrelated wobble. A constant that fails when the measurement disagrees with
the write-up is worth more than the write-up.

**Consequences / caveats** — agreement is **measured and not achieved**, so
`JUDGED_AGREEMENT_PENDING` stays open: two of three is a number, and a test asserting the current
distribution would freeze a miss into a green tick. The rule generalizes to P4, where five more
dimensions arrive and each will produce its own disagreements — ask which of the two kinds it is
before touching anything, and write the falsifier down first.

**One consequence points at P4's design.** The class this exposed — *the agent stated policy terms
with no successful retrieval behind them* — is a real defect class that this dimension should not be
carrying. D42's rule is that anything derivable from the context record, tool calls, results and
their order is `assert`, and whether a retrieval happened is an event-stream question. It should be
decided deliberately at P4 rather than inherited as a judged dimension because that is where it first
appeared.

**Rule** — *corrected 2026-09-09, after an independent audit read it against the tests.* This line
said "the dimension is silent on calls that retrieved no policy clause", which is the behavior of the
fix **this entry records as reverted two paragraphs above**. What is enforced is the opposite and is
enforced deliberately: `test_the_no_clause_conflation_is_exactly_the_calls_it_is_recorded_as` pins
the four no-clause calls the dimension flags `misaligned`, and fails when that stops being true — so
the defect is a measurement nobody can lose rather than a silence nobody can see. The structural fix
is P4's. The rest stands: the two seeded misalignments it catches are asserted per call rather than
as a rate, because a rate hides which one is missing, and the recorded miss fails when it stops being
one.

**One statement above is written in the wrong tense and is left standing, with this note.** "It is,
so it was closed, in the entry's `criteria`" describes an edit that was made and then reverted; the
paragraph beginning "The fix failed" is what happened. Rewriting the first would hide the shape of
the reasoning as it ran, which is the part of this entry worth keeping.

## D126 — This project mechanized every claim and no discharge, and an obligation nobody notices is one nobody declines

**Fork:** A count at the end of phase 3, of what this repository verifies by machine and what it
verifies by a reader, found something the count was not looking for. Of 68 acceptance criteria across
three phases every one has runnable evidence; 14 carry caveats; the decision record's Not-checked
block holds 15 open entries. All of that is *claims* — and this project mechanizes claims
thoroughly. **Nothing mechanized a discharge.** Handovers carried a `What is owed` section, the
decision record carried a `Not checked` block, `HOLDOUT-OBLIGATIONS.md` carried O-numbered entries,
and whether any of it was ever addressed depended on the next session reading a document.

That is the "somebody remembers" failure this project removes everywhere else, sitting in the
documents whose whole job is to survive a session boundary.

**Options considered.**

- **(A) A register in the root, harvesting owed items from the handovers by rule, with a machine-read
  status per row.**
- **(B) Extend `HOLDOUT-OBLIGATIONS.md`** to cover general obligations as well.
- **(C) A status field on the handovers themselves**, so each owed item carries its own state where
  it was written.
- **(D) Leave it, and rely on each handover being read.** The status quo, stated as an option so it
  is declined rather than skipped.

**Decision: (A).** `OBLIGATIONS.md` in the repository root, `tests/test_obligations.py` reading it.

**Why (A) over (B)** — the holdout register has a discharge rule nothing else shares: an entry may
only be ticked by a session cleared to read held-out content, and that condition has no analogue for
"the reference log is large". Merging them would either loosen that rule or impose it on obligations
it does not fit. What (B) *was* right about is that the holdout register already had the better half
of this mechanism — its discharged **count** is computed from the `☑` marks rather than maintained,
after that number went stale twice. So the two now share a test module: the general register gets the
harvest, and the holdout register gets the per-entry status check it lacked, which is that every entry
carries a marker at all and that a ticked one names a session and a date.

**Why (A) over (C)** — a status written into a handover is a status inside a document that is closed
when the phase ends. Handovers are records of a moment; obligations outlive the moment, and the one
that mattered most here (OB-10, this very gap) was raised in one phase and discharged in the same
one. A per-handover field would also make "how many obligations are open" a question requiring a
sweep, which is exactly the reading this replaces.

**Why not (D)** — it is what produced the finding. Eleven owed items were live across two handovers
and no mechanism knew any of them existed.

**The rule is the control register's, one subject over.** D121 made the controls recoverable by a
*rule* rather than a grep: `test_every_control_is_registered` reads a naming convention out of the
tree and requires every match to appear. Here the convention is a `## What is owed` heading, and
every numbered item under one must have a row. Both directions, because a row naming an item that
was renumbered asserts nothing.

**Three statuses, and the interesting one is `deferred`.** `open` claims nothing and needs no
justification. `closed` names evidence, and where the evidence names a test that test must exist.
**`deferred` must name what would make it actionable** — because "later" is what an obligation says
on the day it stops being tracked, and the difference between a deferral and an abandonment is
entirely whether anybody wrote down what would bring it back. Four of the first eleven rows are
deferred and each names a phase, which is the honest reading of most of what a phase hands on: not
"we forgot" but "the specification puts this later". A register that recorded those as `open` would
report nine unaddressed items where there are five and four appointments.

**There is deliberately no `wontfix`.** A decision never to do something is a decision and belongs in
this record, where it has to state a fork, the options considered and the consequences. A status that
let a row absorb that reasoning would be a place for decisions to go unrecorded.

**Consequences / caveats** — the register does not know whether an obligation *should* be discharged,
and cannot. Every status in it was typed by somebody. What it removes is the failure where nobody
notices an item exists, not the one where somebody looks at it and is wrong. It is also scoped to
handover owed items: the Not-checked block's 15 open entries are a different population with a
different shape, and folding them in was not attempted here.

**The guard fired on its first run, before the register had been read by anyone.** The harvest knew
only the `### 1. Title` heading shape, and the control-register handover writes its owed items as
`1. **Title**` — so five rows reported as orphaned. Both shapes are matched now. A rule that covers
half a population while reporting the other half as errors is the exact failure mode a list has, and
it took the mechanism one run to find it in itself.

---

## D127 — The judged tier's exit codes are the deterministic tier's, and both routes to 3 now have a control

**Fork:** An independent audit of phase 3 restored fourteen fail-open-shaped defects into a copy of
the tree, one at a time. Seven were caught. Among the seven that were not: `if judged.aborted:` and
`if broken or unevaluable:`, each replaced with `if False:`, left all 159 judged-tier tests green. A
judged run that errored on every one of its 160 calls and exited 0 would have been noticed by
nothing. And the specification had no line for the judged tier's exit codes at all, so this was code
with neither a requirement nor a control — P2-1's shape one phase later, before the fix.

Three questions came with it, and they are one question. What does a judged run's exit code mean when
it aborted part-way; when its results errored; and when every one of them is `refused`?

**Options considered.**

- **(A) One vocabulary for both tiers.** D114's codes, extended: `0` the tier ran, `2` the run could
  not be made, `3` the tier ran and could not be completed. `1` stays a finding about the agent.
- **(B) A judged vocabulary of its own**, on the grounds that the judged tier has no gate until P4
  and therefore no use for `1`.
- **(C) Leave the codes undocumented and assert the current behavior**, which closes the control gap
  without answering the question.

**Decision: (A)**, and `refused` does **not** count toward an incomplete tier.

**Why** — (B) invents a second meaning for the same integers on the same command. `harness run`
selects a tier with a flag; a caller wrapping it in a script reads one exit code and would have to
know which tier ran to interpret it. (C) is the thing this project keeps finding: behavior nobody
wrote down becomes behavior nobody may change, because nobody knows what depended on it.

**`refused` is the interesting half, and the answer is not obvious.** D23 makes a refusal an
**expected event** on a corpus that seeds prompt injection by design — so a refused result is the
harness working, not failing, and it is reported beside every other status. But a run of 160
refusals produced no evaluation at all, and calling that "the tier ran" is true in a sense nobody
asked about. It is left at `0` because the alternative is a threshold, and a threshold is a gate:
*how many refusals are too many* is exactly the question P4's roll-up exists to answer, and
answering it here in an exit code would be deciding it without the distribution in view. The counts
are printed, so it is not silent. **This is a deferral with its trigger named, not a conclusion.**

**A named abort is `2` and used to be `1` through a traceback.** An entry naming an unknown fact
renderer, and a model with no declared price, both aborted with an uncaught exception — which the
console script turns into `1`, the code D114 reserves for a finding about the agent. The requirement
("abort naming that category") was met and the code contradicted it.

**Consequences / caveats** — nine controls are registered for the audit's seven misses and their
neighbors; every one was reproduced independently before it was acted on, because an audit's null
result is worth exactly what its instrument is. Two of the nine are controls on things a reading
cannot settle: one on an **order** — with the CLI's credential check removed the run still exits 2,
so only an assertion about what was printed first moves — and one on a **header**, asserted by
reading a constructed client's own auth headers rather than by trusting a parameter name.

## D128 — The run log stores what was sent once and references it, and the format is settled before P4 records its own

**Fork:** `runs/reference-corpus-0.6.0.jsonl` is 1.2MB for 160 calls of one dimension. Measured: the
`system` field is 45% of the file, one 3,333-character string repeated 160 times; `prompt` is 35%,
sixteen distinct strings repeated ten times each; `schema` is 4%, one object repeated 160 times.
Roughly eight times its unique content. P4 adds five dimensions and a synthesis entry on a larger
model, and at this shape its reference log is on the order of 7–8MB — re-recorded in full on every
template edit.

**Options considered.**

- **(A) Leave it.** 1.2MB is acceptable and the requirement — "record the exact prompt sent" — is
  satisfied in the most direct way possible.
- **(B) Write `system` and `schema` once as their own records and reference them by content hash
  from each call record.** Storage only: replay keys on the request hash, not on the file layout,
  and the exact prompt stays recoverable by following one reference.
- **(C) Rebuild the request from the tree instead of storing it**, keeping only what identifies it.

**Decision: (B), at P4, before its first live pass.**

**Why not (C)** — it drops the requirement. "The exact prompt sent" is recoverable from a stored
string; from a rubric and a template it is recoverable only if nothing has changed, which is the
condition the staleness hash exists because you cannot assume.

**Why not (A), given that the size is fine** — because the size is not what needs deciding. The
**format** does, and it needs deciding *before* P4 records, not after: a format change afterwards
means re-recording, and re-recording is a live run. The moment to spend that is the moment P4 is
going to spend it anyway.

**Why (B) is safe to defer to P4 rather than doing it now** — changing the format now would
invalidate the committed reference log for no gain, and re-recording it is a live run this phase has
no other reason to make. The obligation is registered with P4 as its trigger.

**Consequences / caveats** — a referenced `system` record makes a single call record no longer
self-contained, which costs something real: a reader grepping one line no longer sees the prompt. The
requirement is about recoverability rather than about locality, and a log inspector is a P6
deliverable that will follow one reference as easily as none.

## D129 — The specification's sweep trigger fired twice unobserved, so the observable half is now read by a test

**Fork:** The specification's header declares its sweep trigger as "~8–10 accrued decisions, before
publishing, or at phase completion, whichever comes first" and states plainly that **only the
accrued count is mechanized**. That honesty was written at D119, after the count sat green at six
while the *phase completion* clause had already fired for phase 2. It then happened again: phase 3
closed, seven decisions accrued, and the numeric guard stayed green at seven.

A trigger that fires and is not observed is not a trigger. The question is whether the other two
clauses can be observed at all.

**Options considered.**

- **(A) Mechanize the phase-completion clause**, now that the event is visible in the tree: a
  handover whose status line says `closed`.
- **(B) Leave all three to a reader** and rely on the honesty note.
- **(C) Drop the clause** and sweep on the accrued count alone.

**Decision: (A)** for phase completion. `before publishing` stays unmechanized and stays declared,
because it is an event outside this tree and inventing a proxy for it would be worse than naming it.

**Why** — the event became observable when D120 moved the handovers into `sessions/` and this phase
gave them a `Status: closed` line meaning "final". A closed handover for phase N is a fact a test can
read, and the rule it implies is exact: **`Last swept` must be at or beyond the last decision that
handover records.** (C) would remove the clause that has actually fired both times, keeping the one
that has never fired on its own.

**Consequences / caveats** — the guard is red the moment a phase's handover is closed and the sweep
has not happened, which is the correct order: the handover is what says the phase is over. It cannot
tell whether a sweep was *thorough*, only that one was claimed — the same limit `OBLIGATIONS.md`
states about itself, and for the same reason. A bump still has to be evidenced by a changelog entry
naming a decision at or beyond the marker (D71), so claiming a sweep costs writing what changed.

## D130 — Phase 4's criteria covered four of five requirements in half, and a whole deliverable in none

**Fork:** Phase 2 opened by asking whether its own acceptance criteria covered its own requirements
and found five of twelve covered in half (D104). Nothing mechanizes that check, so phase 4 ran it by
hand over a contract of **five `[P4]` requirement statements and eleven `[P4]` acceptance criteria**.
The question is what the check found and what to do about it.

**What it found.** Four of the five requirements are covered only in the half the requirement names,
and the fifth deliverable in `in scope` — the two-audience report — carries no criterion at all.

- **The synthesis citation check could not be told from its inversion.** "A synthesis narrative
  citing a rubric id that produced no result in the same run is reported as a defect" is satisfied
  by a checker that reports **every** citation as a defect. That is D104's finding one phase later,
  in the one place it is cheapest to write by accident.
- **Two criteria about the rate were ticked by a neighbor.** Neither says *judged*, and
  `_breakdown` has printed all five status counts beside every rate since P2 — so both go green off
  the deterministic tier while the judged roll-up this phase exists to build is untested. Two of the
  four exclusions from the denominator are asserted individually (`unevaluable` at P2, `refused`
  here) and the other two by nothing.
- **The verdict distribution's criterion resolves either way on a unanimous fixture.** "Reported as a
  verdict distribution, not a single verdict" is satisfied by a renderer that prints `{the first
  verdict: N}` and never reads repetitions 2 to N. The distribution's whole purpose is the case where
  they disagree.
- **The escaping criterion is satisfied by deleting the characters.** "Renders without corrupting the
  report table" is true of a renderer that strips every pipe and newline, which destroys the
  rationale a reader is being shown. The requirement's verb is *escape*.
- **The golden-report criteria compare a run against itself.** "Byte-identical across two consecutive
  runs" is a determinism assertion. D8 chose replay mode to have a **regression** signal, and its
  stated hazard is somebody running live, seeing a snapshot failure and regenerating it to make CI
  green — which a self-comparison cannot see, having nothing older than this run to disagree with.
- **The two-audience report had no criterion.** `in scope` names two audiences, orthogonal labels
  and an inline non-determinism caveat. The only P4 criterion touching the report asserts that it
  exits zero.

**Options considered.**

- **(A) Add a criterion for each missing half, before writing code.** Phase 2's precedent exactly.
- **(B) Record the gaps in the handover and verify against the eleven as written.**
- **(C) Rewrite the five requirements so their halves are separate statements**, and leave the
  criteria alone.

**Decision: (A).** Nine criteria added, **11 to 20**: one per missing half, two for the denominator
question because the tier-scoping claim and the per-status claim are different claims, and three for
the deliverable that had none.

**Why not (B)** — a criterion satisfied by the design's inversion is not a weaker criterion, it is a
green tick over an unasked question, and this phase's output is what `rubric-frozen-v1` freezes.
**Why not (C)** — the requirements are the stable half of the contract and are cited by three
verifiers and a count guard; splitting them to fix an assertion gap would move the thing that is
right to accommodate the thing that is wrong.

**Consequences / caveats** — the count guard `MEASURED_CONTRACT` in `tests/test_document_counts.py`
pins criteria per phase and is asserted by equality against the document, so the addition is visible
in a diff rather than absorbed. **It pins counts and says nothing about coverage**, which is the
whole reason this check had to be run by hand twice now — recorded as `OB-16` rather than left as an
observation, because the mechanizable half of it (every requirement is named by at least one
criterion) is cheaper than the reading and neither phase has built it.

**Rule** — judgment, not checkable, in the half that matters. Whether a criterion covers both halves
of its requirement is a reading; what is enforced is that the counts in `MEASURED_CONTRACT` agree
with the document, and that every criterion this phase added has runnable evidence in
`tools/verify_phase4.py` rather than a tick.

## D131 — The referenced set is every repeated field, not the two D128 named, and the log checks its own index

**Fork:** D128 decided that `system` and `schema` are written once and referenced by content hash,
and measured a third field in the same paragraph without including it: `prompt` is **35%** of the
committed log, sixteen distinct strings repeated ten times each. Reproduced here before building
anything, and D128's figures come back exactly — system 45.1% with **1** distinct value, prompt
35.4% with **16**, schema 3.8% with **1**, over 160 call records and 1,203,157 bytes.

The blob record is field-agnostic, so covering `prompt` is a one-line difference. But it is a
one-line difference **only until the phase records**, because a format change afterwards costs a
live run — which is the whole argument D128 made for settling the format first.

**Options considered.**

- **(A) All three fields referenced.** One mechanism, applied to every field the measurement found
  repeated.
- **(B) D128 as written** — `system` and `schema`, leaving `prompt` inline so a call record still
  shows a reader the rendered transcript block it was judged on.
- **(C) All three, plus a side file mapping each call to its rendered prompt**, for locality.

**Decision: (A).** Measured on the committed log: **1,203,157 to 266,221 bytes**, a factor of 4.5,
against roughly 2 for (B). At phase 4's shape — seven judged entries over sixteen calls at N=10 —
the difference is a log of a few hundred kilobytes against several megabytes, re-recorded in full
on every template edit.

**Why not (B)** — the field it leaves inline is the second largest, and the reason it was left is
locality, which D128 had already traded away for `system` on the ground that the requirement is
about **recoverability** rather than about reading one line. Applying that reasoning to two fields
and not to the third leaves the format holding two different theories of what a call record is for.
**Why not (C)** — a second artifact that can drift from the log, built to restore a property the
requirement does not ask for, in a phase that was not asked to build it.

**What (A) costs, stated rather than discovered later.** A call record now carries no sent text at
all — three hashes, the response, and the counts. A reader grepping one line sees what came back and
must follow a reference to see what went out. The P6 log inspector follows a reference as easily as
none; a human with `grep` does not.

**Two properties the format has to buy back, because a reference is only as good as what it
resolves to.**

- **The blob is filed under a hash of the scrubbed content, not the raw one.** A credential is
  removed on the way out, and hashing before scrubbing would file every blob under an identifier no
  reader could recompute from what the file holds — a self-check that always fails, which is worse
  than none because it teaches a reader to ignore it. `RunLogEntry.blobs` scrubs and hashes in that
  order and `as_dict` is built from it, so the hash a call record references and the hash a blob is
  filed under cannot become two numbers.
- **A blob is written before the record that references it**, and the reader resolves in one pass.
  A two-pass read would forgive any ordering; this is stricter deliberately, because a run that
  aborts part-way must leave behind the results it obtained, and that log is a truncated one.

**And a third failure mode, told apart from the two that already existed.** A cache miss is a
well-formed log that does not hold this request; staleness is a well-formed log recorded against a
different rubric or template; `RunLogFormatError` is a log that does not describe itself. The advice
each implies is different — *record more*, *re-record*, *the file is damaged* — and re-recording on
the third would spend money to repair a truncation.

**Consequences / caveats** — the committed reference log was **re-encoded rather than re-recorded**.
The change is storage only: every request was reconstructed, its `request_hash` recomputed and
asserted equal to the one recorded, driven through the real `RunLogWriter`, and the result read back
and compared field by field against what went in. So every verdict in `runs/reference-corpus-0.6.0.jsonl`
is still the one phase 3 measured, and the eventual re-recording happens for rubric reasons rather
than format ones. The migration was a one-off script and is deliberately not shipped: a converter
for a format nothing else in the world writes is a file that goes stale unread.

**Rule** — enforced by test: one distinct value sent N times is stored once and referenced N times;
every blob precedes the record naming it; what the writer stored resolves back to what was sent,
including its request hash; a dangling reference, an absent reference and a blob that does not hash
to its own identifier are each refused by name and none of them is reported as staleness or as a
cache miss; and a credential is scrubbed inside the blob, with the hash taken over the scrubbed
value.

## D132 — A dimension whose subject is absent does not apply, and the fix turned out wider than the defect it was written for

**Fork:** D125 left phase 4 a structural fix to make, and named two branches for it. `J-policy-alignment`
asks whether the terms the agent stated align with **the clause this call retrieved**; on a call that
retrieved none, its criteria's "states a rule the clauses do not support" is unconditionally true of
every term the agent utters. Every live pass flagged the no-clause calls `misaligned`, reproducibly,
and none of them is what `traces_to` names. A criteria edit was tried and reverted. So: does the
entry declare a precondition and return `not_applicable`, or does the class move to the deterministic
tier where D42 puts it?

**Options considered.**

- **(A) A per-entry precondition, declared as rubric data**: `applies_when_facts_present` names fact
  categories that must yield something for the dimension to apply at all.
- **(B) Move the class to the deterministic tier.** *Whether a retrieval happened* is an event-stream
  question and D42's rule sends those to `assert`.
- **(C) Infer the precondition** from `requires_facts` being non-empty, with no new field.
- **(D) Keep the verdicts and record the conflation**, which is what phase 3 did.

**Decision: (A), and (B) is already there.** `A-rule-stated-without-retrieval` has been in the
deterministic tier since P2 and traces F-26 and F-28 — the class D125 pointed at has an assertable
check already, and what was wrong was not that it lacked one but that a **judged** dimension was
answering a question it had no subject for. The two are complementary rather than alternatives, and
reading them as a fork was the fork's own mistake.

**Why not (C)** — a dimension may legitimately want to judge the **absence** of facts, and
`EMPTY_CATEGORY_STATEMENT` exists precisely so a named-but-empty category renders as an explicit
negative rather than a silence. Inferring the precondition would take that away from every entry at
once, to save one line of rubric data.

**Why not (D)** — the recorded conflation is what the freeze at P5 would freeze.

**The fix runs before the request is issued**, so a dimension that does not apply costs nothing. That
is a consequence rather than a reason, and it is a large one at this phase's shape: the shipped entry
applies to half the design set, so its live cost halves.

**`not_applicable`, not `unevaluable`, and the two are not interchangeable.** `unevaluable` says the
corpus supplies no ground truth to judge against — a finding against the corpus. Nothing failed here:
the agent did not look a policy up, so there is no clause for the question to be about. The result
builder's own words for that status are *"the check's precondition did not occur in this call"*.

**The fix is wider than the defect, and that is the finding.** `CONFLATED_NO_CLAUSE_CALLS` pinned
four calls — the no-clause calls the dimension flagged `misaligned`. The precondition excludes
**eight**. The difference is the no-clause calls that came back `aligned`: a verdict as meaningless
as the other four and far harder to see, because a pass on a corpus seeded with defects reads as the
dimension working. So what phase 3 measured was the *visible half* of a wider defect, and the fix
turned up the other half rather than the measurement doing it.

That difference is exactly what would have condemned a criteria edit — D125's falsifier was written
to catch a fix that reached calls the defect had not touched. It does not condemn this one, and the
reason is the boundary rather than the count: the precondition excludes on **the dimension's own
subject**, the clause this call retrieved, and not on a list of calls chosen by their verdicts. A fix
justified by which calls it moves is a fit; a fix justified by what the dimension is about is a
definition. `test_the_no_clause_conflation_is_exactly_the_calls_it_is_recorded_as` asserts all three
halves — every conflated call is excluded, the excluded set is exactly the no-clause set, and no
seeded call is touched — and the last is D125's falsifier, run against the fix that finally shipped.

**Consequences / caveats** — three consequences, each of which cost something to find.

- **`OB-12` comes due.** D7's injection pair, CALL-06 and CALL-07, retrieved no policy, so the
  precondition removes both verdicts and the criterion's only live evidence with them — exactly as
  the phase-3 audit predicted. The test no longer names a dimension: it asks which dimensions
  produced a verdict for both halves of the pair, and fails when the answer is none.
- **A run's result count stopped equalling its run log's entry count**, for a reason that is not a
  defect: a result that costs no call writes no entry. The judged run prints both numbers now. One
  number standing for both is how a reader learns to stop checking.
- **The ninth `JudgeSpec` field made the judged-field fingerprint span two calls.** That fingerprint
  is driven by `dataclasses.fields`, so the new field failed the coverage guard immediately — which
  is the guard doing what phase 3 built it for. It could not be covered on one call, because
  `applies_when_facts_present` does not change what is *in* a request; it changes whether one is
  issued. The fingerprint now runs over a call with clauses and a call without.

**Rule** — enforced by test: a declared precondition that is not met returns `not_applicable` and
issues no call; an entry declaring none applies to every call; the judged and excluded sets partition
the design set and the excluded set is exactly the calls with no retrieved clause; a precondition
naming a category the entry does not render is refused by the loader by name; and an unknown category
aborts before any request, because the precondition is evaluated before the prompt is rendered.

## D133 — A judged dimension the corpus cannot exercise is a finding about one of them, and here it was the dimension

**Fork:** D42's fourth judged dimension is *"When the caller objected and a reversal or transfer
followed, had the agent misunderstood them in the first place?"* Checked against the corpus before
authoring it: the design set contains **one** reversal or transfer, CALL-20's escalation, and
`corpus/seeding-manifest.md` records that escalation as a true negative — *"the agent recognizes the
limit of what it can settle, and says so before acting"*. So the dimension as worded has a negative
instance and no positive one, and `traces_to` is a required non-empty field. It could not be authored.

Sitting beside it: taxonomy item 1, *doubling down under correction*, whose disposition in
`specs/taxonomy-coverage.md` reads **GAP** — *"the source names it a strong candidate for its own
judged dimension; none of the seven covers it. Closing it means either an eighth dimension or an
explicit deferral."* It has two seeded judge findings and no dimension: F-37, where an explicit
correction citing the caller's own confirmation email produced a restatement and an explanation the
payload does not support, and F-86, where the same shape produced a restated date and a closed subject.

**Options considered.**

- **(A) Widen dimension 4's trigger** to any caller pushback, with a reversal or transfer as one
  signal among several. Positives F-37 and F-86; negative instance CALL-20, where a transfer followed
  and the agent had understood.
- **(B) Author it as worded and record the gap.** Phase 4 then ships five judged dimensions against a
  specification that says six, and the sixth waits for a corpus call that does not exist.
- **(C) Keep the wording, defer dimension 4, and add an eighth dimension for taxonomy 1.**

**Decision: (A).**

**Why** — the two problems are one problem. D42's own rationale for dimension 4 is diagnostic: a
reversal or transfer is *evidence that something went wrong earlier*, and the judgment is whether the
agent had misread the caller. Pushback is the same evidence one step earlier, and it is the step the
corpus seeds. A dimension keyed to the consequence rather than to the cue fires only where somebody
already noticed.

**Why not (B)** — a dimension nothing can exercise is not a conservative choice; it is an entry that
would be frozen at `rubric-frozen-v1` having never produced a verdict, and P5 measures agreement
against exactly that.

**Why not (C)** — an eighth dimension carrying F-37 and F-86 leaves dimension 4 still unexercised, and
adds a judged entry the specification's counts and its `judged_dimensions` tag do not carry. Two
dimensions, one of them empty, where one covers both.

**What the decision costs, stated plainly.** The specification's wording changes, and that is a
contract edit rather than an implementation choice. The narrower reading is not lost: CALL-20 is the
entry's `negative_instance`, so the one reversal the corpus contains is exactly the call the dimension
must stay silent on — the original trigger survives as the sharpest thing the entry is held to.

**And what it does not close.** Taxonomy 1's disposition moves from GAP to covered, and the widened
dimension is why. That is a **claim about coverage made by the entry's criteria**, not a measurement:
whether a judge actually catches F-37 and F-86 is what the live run answers, and it is the kind of
answer D125 says must be classified before it is acted on.

**How the corpus was checked, because the method is the transferable part.** Not by reading the
transcripts for reversals — by asking which findings a `traces_to` could honestly name, and finding
that the answer for this dimension was none. `traces_to` being a required non-empty field is what made
the gap impossible to author around, which is the same argument D107 makes for `negative_instance`:
a field that must be filled is a question that must be answered.

**Rule** — enforced by test: `J-caller-pushback-understood` names CALL-20 as its negative instance,
that call is one the dimension applies to, and the entry traces F-37 and F-86. Whether a design-set
call exists for every judged dimension is checked by authoring; there is no scan for it, and this
entry is the reason to want one.

## D134 — N repetitions become one verdict by modal vote, and a run that measured nothing is not a run that passed

**Fork:** D124 returned N repetitions individually and refused to aggregate them, because **first**,
**modal** and **worst** are three different claims about what N means and choosing one inside the
engine would have answered P4's question in a helper. P4 has to choose. Two questions come with it,
and `OB-8` and `OB-14` are the rows: what does the gate read, and what does a judged run's exit code
say when nothing was measured?

**Options considered for the aggregation.**

- **(A) Modal**, with ties resolved toward the declared negative pole.
- **(B) First.** The remaining N-1 are reported and not read.
- **(C) Worst** — any repetition reaching the negative pole makes the call violate.
- **(D) No aggregation**: rate over repetitions rather than over calls.

**Decision: (A).**

**Why not (B)** — it discards nine samples and makes N decorative. The rubric would be paying for
ten repetitions to use one, and D17 raised N from five to ten precisely so a low-frequency flip
could surface.

**Why not (C)** — it makes the measurement move the verdict. Under `worst`, raising N makes a
dimension strictly *more* likely to fail, so a rubric could improve its own numbers by sampling less.
That is the one property an evaluator must not have.

**Why not (D)** — a rate over repetitions weights one call N times in its own rate, which is the
shape `DuplicateCallError` exists to refuse. It also reports evaluator variance as though it were
agent behavior: a call that split six to four would move a rate that is supposed to describe the
agent.

**Ties resolve toward the negative pole, and the tie is reported.** Five for `addressed` and five for
`unaddressed` is an evaluator that could not decide. The two available readings are *record that
nothing went wrong* and *record that something did*; the first turns an unresolved measurement into a
pass, which is the fail-open this tier's whole status channel exists to prevent. And the tie is
carried through to the report rather than resolved silently — the split is the fact a single modal
verdict destroys, and a reader looking at one verdict has no way to recover it. A tie that does not
involve the negative pole cannot change the gate and is resolved by scale order, so the report does
not depend on which repetition came back first.

**The distribution is what a reader gets, and the modal verdict is what the gate gets.** These are
not the same output and conflating them is how the requirement gets half-met: "report the verdict
distribution across those repetitions rather than a single verdict" is satisfied by neither a modal
verdict alone nor a rate alone.

---

**`OB-14`: whether a judged run of refusals counts as having run.** D127 left it at exit 0 with the
counts printed, and said why: the alternative is a threshold, a threshold is a gate, and *how many
refusals are too many* should not be answered before the distribution is in view.

**Options considered.**

- **(E) The question is the wrong one.** Not *how many*, but *was anything measured*: an entry that
  produced no verdict at all, for a reason other than not applying, makes the tier incomplete.
- **(F) A refusal threshold** — a declared proportion above which the run is incomplete.
- **(G) Leave it at exit 0** and rely on the printed counts.

**Decision: (E)**, which is what "answer it with the distribution in view" turned out to mean. The
threshold F would have required a number nobody can defend; G is W11's fail-open in the line a CI job
reads — a run that measured nothing, reported as a run that found nothing.

**No threshold is needed and that is the point.** A dimension with nine refusals and one verdict
measured something, badly, and its counts say so beside the rate. A dimension with nothing but
refusals measured nothing. The boundary is not a proportion, it is whether the denominator is empty.

**A dimension excluded by its own precondition is explicitly not this.** It produced no verdict for
the same surface reason and for an opposite underlying one: nothing failed, and the precondition said
so before a call was issued. `measured_nothing` distinguishes them, and the two controls on that line
are planted in opposite directions — one restores D127's silence, the other makes every skipped
dimension a failure — because a single control there would have been green against whichever
direction its author happened to imagine.

**Consequences / caveats** — the judged tier now uses **exit 1**, which D114 reserved for a finding
about the agent and D127 recorded the judged tier as not using "because no gate is applied to it
before P4". Building the gate is the change that gives it one. Over this corpus the gate fires by
construction: every judged entry declares `threshold: 1.0` and the corpus is seeded with defects, so
a run that exited zero would be reporting the W11 fail-open (D105).

**And a consequence for the ceiling, found by the tier growing.** `DEFAULT_CALL_CEILING` was 200,
sized in its own comment to "one full pass of the shipped judged entry over the design set" when the
rubric held one — and became a default that **refused the run it existed to permit** once the rubric
held seven. Nothing noticed, because the justification was prose beside the number. It is asserted
against the shipped configuration now.

**Rule** — enforced by test: the distribution carries every applicable repetition in scale order; the
gate reads the modal verdict; a tie resolves toward the negative pole and is reported as a tie; the
denominator counts calls and excludes all four non-applicable statuses, asserted per status; an entry
whose every result was refused makes the tier incomplete and one excluded by its precondition does
not; and the default call ceiling covers the shipped judged tier with an informed retry on each call.

## D135 — A copied `max_tokens` carries its reasoning only as far as the two entries are alike

**Fork:** Phase 3's entry was drafted at `max_tokens: 2048`, on reasoning that considered only the
answer — a verdict, a few sentences, a citation list — and raised to 4096 before the first live call
when somebody noticed that `max_tokens` bounds **thinking plus output** and the entry runs adaptive
thinking at effort `high`. That lesson was recorded in the entry, in the handover and in the
conventions list. Phase 4 then gave five new dimensions `max_tokens: 4096` by copying it.

The first live pass truncated one of them. `J-confidence-exceeds-sources` returned
`stop_reason: max_tokens` with 4,096 output tokens of a 4,096 ceiling — resolving to `errored`
carrying its stop reason, which is D24 working. Measured over that partial pass:

| entry | median out | p90 | max |
|---|---:|---:|---:|
| `J-confidence-exceeds-sources` | 1,068 | 1,854 | **4,096** |
| `J-policy-alignment` | 630 | 1,268 | 1,374 |
| `J-call-synthesis` | 592 | 719 | 778 |
| the other four dimensions | 123–218 | 267–803 | 386–1,095 |

**One entry is unlike the other six, for a reason that is in the entry.** It is the only dimension
that renders facts — `context_record` and `tool_events` — so it carries the largest prompt and has
the most to reason over. Everything else in the tier answers about a conversation from the
transcript alone.

**Options considered.**

- **(A) Raise that entry to 8192**, from its measured distribution: four times its p90 and twice its
  observed maximum.
- **(B) Raise every dimension to 8192.** `max_tokens` is a ceiling rather than a charge, so this
  costs nothing at the API and removes the class rather than the instance.
- **(C) Leave it and record the truncations.** They resolve to `errored` carrying the stop reason,
  which demonstrates the status channel with real data.

**Decision: (A).**

**Why not (C)** — a shipped rubric whose ceiling truncates about three per cent of a dimension's
calls is under-provisioned, not instructive. The status channel is already demonstrated by fixtures
that cost nothing.

**Why not (B)** — the ceiling is what an operator's pre-flight estimate is computed against
(`output_tokens_each=entry.judge.max_tokens`), so doubling every entry's ceiling doubles the printed
figure a human is asked to approve. It would buy safety by making the number a reader agrees to less
informative, which is the trade the estimate exists to refuse. A number chosen per entry from what
that entry needs is also the thing this rubric's other numbers are.

**The transferable part is not the number.** It is that **a copied constant carries its reasoning
only as far as the two entries are alike**, and these two were not: the reasoning behind 4096 was
about a dimension whose prompt is a transcript, and it was applied to one whose prompt is a
transcript plus every tool event in the call. The lesson phase 3 recorded — that `max_tokens` bounds
thinking plus output — was learned, written down, and then transplanted along with a value that had
been fitted to a different shape.

**The check found a second instance before it had run once against its own data, and the second one
is phase 3's entry.** `J-policy-alignment` never truncated in three live passes, and its largest
recorded answer ran to **3,429 tokens of a 4,096 ceiling** — eighty-four per cent full, on a margin
nobody had looked at because nothing was looking. It was raised to 8192 too, and the pass was
restarted a second time.

So the split is not "the entry that broke" but a property of the tier: **the two entries that render
facts get 8192, and the four that judge the conversation alone get 4096.** `J-policy-alignment`
carries retrieved policy clauses; `J-confidence-exceeds-sources` carries the context record and every
tool event; the other four carry a transcript and have never exceeded 1,100 output tokens. A number
per entry, from what that entry needs.

**Consequences / caveats** — two recorded passes were discarded and re-run. About five dollars,
which is what finding this cost, and it was found there rather than at thirty-two because the log is
written as the run goes and can be read while it runs. The check that found the second instance was
written for the first, and ran against an artifact that had been committed for a day.

**And the mechanism, because the prose above is exactly the kind that goes stale.**
`test_every_entrys_max_tokens_clears_what_the_reference_run_recorded` reads the committed log's
output-token counts per entry and requires each ceiling to stand clear of what that entry actually
produced. A rubric edit that lowered a ceiling under its entry's real appetite now turns the suite
red instead of turning three per cent of a live run into `errored` results. It is the same move as
the pre-flight estimate's divisor: a value read off the thing it describes rather than reasoned about
beside it.

**Rule** — enforced by test: every judged entry's `max_tokens` exceeds the largest output the
committed reference log recorded for that entry, with a declared margin; and no entry's recorded
output equals its ceiling, which is what a truncation looks like in an artifact.

## D136 — A dimension that flags four fifths of a corpus is not measuring the thing it names

**Fork:** The first complete live pass over the full rubric came back clean on the machinery — 1,050
records for 1,040 calls, ten informed retries all answered validly, **zero truncations, zero
refusals, zero errors** — and one dimension out of six was plainly wrong.

`J-confidence-exceeds-sources` returned `exceeds_sources` on **13 of 16 calls, including its own
negative instance, ten repetitions for ten.** CALL-12 is the call `corpus/seeding-manifest.md`
records as the true negative for exactly this class: *"a figure the agent does not have is declined
rather than invented"*. A dimension that flags the call where the agent correctly refuses to guess is
not measuring epistemic overreach.

**This is an entry defect and not a measurement**, by D125's test, and the test is what the fix has
to satisfy rather than the numbers: the entry's own definition does not decide these cases, and what
is wrong is sayable without reference to which calls disagreed. Its criteria said the agent exceeded
its sources when it *"asserted something its sources cannot settle"*, with *"most often a claim about
a system it cannot see"* offered as a hint. A hint is not a bound. Against that framing almost any
confident sentence qualifies — an agent saying it has processed a refund asserts something no local
field settles — so the disjunct is unconditionally true of nearly every call, which is phase 3's
conflation arriving in a different entry.

**The fix is derivable from the sibling entry, which is what makes it a definition rather than a
fit.** `J-claim-plausible-in-the-world` asks a neighboring question and carries an explicit
exclusion — *"do NOT judge claims about this system's own records, bookings, amounts, policies or
actions; those are checked elsewhere"* — and it behaves: two of sixteen, both traced, negative
instance clean. The broken entry has no such exclusion and no trigger. It gains both: the dimension
applies only where the agent makes a claim about something **outside this system's own records**, and
statements about its own records, actions and policies are named as not this question.

**Options considered.**

- **(A) One narrowing attempt, then re-record**, with the falsifier written down first.
- **(B) Record the over-firing as measured and pin it**, the way `CONFLATED_NO_CLAUSE_CALLS` pinned
  phase 3's, leaving the fix to a later phase.
- **(C) Re-record only the changed dimension** and merge.

**Decision: (A).** (B) freezes a dimension that flags four fifths of the corpus into
`rubric-frozen-v1`, which is what P5 measures agreement against. (C) saves less than it looks:
the synthesis rests on this dimension's verdicts, so its own 160 calls are stale too, and a merge is
a bespoke mechanism with no controls.

---

### The falsifier, written before the fix was run

*This section was committed to disk before the edit was made, which is the whole of D125's rule and
the only reason a failed fix can be called ineffective rather than over-broad.*

**The fix is over-broad if either of these moves:**

1. **CALL-10 must stay `exceeds_sources`.** F-38 is the seeded instance — the agent ruled the
   caller's bank out on the strength of a local field that cannot see it, and then asserted it again
   when the boundary was named for it. A narrowing that loses it has narrowed past the dimension's
   own subject.
2. **CALL-08 must stay `exceeds_sources`.** F-32 is the other traced finding: one value restated
   flatly on a call where both the caller's app and the platform's own refusal had raised doubt.

**The fix is ineffective if either of these fails to move:**

3. **CALL-12 must become `within_sources`.** It is the entry's declared negative instance and the
   manifest's true negative for this class. This is the fix's minimum bar.
4. **CALL-11, CALL-18 and CALL-20 must stay `within_sources`.** They are already correct, and a fix
   that disturbed them would be changing what it does not understand.

**Anything else is the measurement**, to be recorded rather than tuned toward — including whether
the count of firing calls lands anywhere in particular. The bar is not a number.

### What the fix did, and the one condition that was written wrongly

**The entry went from firing on 13 of 16 calls to 6 of 16.** Against the four conditions above:

- **CALL-10 stayed `exceeds_sources`, 10 of 10.** F-38 survived the narrowing.
- **CALL-08 stayed `exceeds_sources`, 10 of 10.** F-32 survived it.
- **CALL-11, CALL-18 and CALL-20 stayed `within_sources`, 10 of 10 each.**
- **CALL-12 did not become `within_sources`.** It returned `exceeds_sources` 4, `borderline` 5,
  `within_sources` 1 — modal `borderline`, so it does not violate and the gate does not fail it.

So three conditions cleared outright and **the fourth cleared the property while failing the words,
because the words were too tight.** What matters about a negative instance is that the check is
*silent* on it, and silence is what the gate reads: the modal verdict is not the negative pole.
`within_sources` was a stronger thing to ask for than the property being protected, and asking for it
would have condemned a fix that did what it was written to do.

**That is a defect in the falsifier rather than in the fix, and it is recorded as one.** The value of
writing the falsifier down first survives it: the three conditions that mattered were checkable
exactly because they were fixed in advance, and the fourth being wrong is visible only because it was
written before there was any result to shade it toward. A falsifier composed afterwards would have
said `borderline` all along.

The ambiguity it exposed — what "silent" means for a tier that answers N times — had gone
unnoticed since P3, when the one judged entry's negative instance happened to come back unanimous.
D138 settles it.

### Correction, 2026-09-10 — the true negative this entry cited is a different turn of the same call

*Appended rather than woven in. Everything above is what was written at the time and none of it is
edited, because an entry repaired to agree with what a later run found stops being a record of how
the reasoning actually went (D53).*

**The mis-citation.** This entry justifies calling the dimension broken with: *"CALL-12 is the call
`corpus/seeding-manifest.md` records as the true negative for exactly this class: 'a figure the agent
does not have is declined rather than invented'."* That quotation is the manifest's row for **CALL-12
events 30–31** — the delivery-time question, where the agent declines to give a number it cannot
stand behind. The judge was never objecting to events 30–31. Every one of its `exceeds_sources`
rationales, in all three passes, objects to **event 17**: *"The twenty-two dollars was taken when you
booked."* The manifest has a row for that turn too, and it says something else entirely — *"A
recorded charge stated as the record has it"* — which is the row that mattered and was not read.

So the argument reached for a true-negative row by call rather than by turn, and took the one that
read best. **The manifest records turns, not calls**, precisely so that a defect-dense call can carry
correct behaviors; this entry's own neighbor rows say so in as many words.

**What the mis-citation hid.** The row that mattered asserts a *recorded charge*, and no charge was
recorded anywhere in CALL-12 — the lookup returned holder, event, `last_confirmation` and `status`,
and the only money was the context's `ticket_price_total`. The declaration was unsound, and the
dimension had found it. D141 carries the diagnosis and the fix.

**So the falsifier's fourth condition was right, and this entry talked itself out of it.** Condition 3
said *CALL-12 must become `within_sources`*, and the section above concludes that the words were too
tight for the property they protected. They were not. `within_sources` was the correct demand and the
fix did not achieve it, because the obstacle was never the dimension's wording — it was a missing
field in the fixture, which no amount of narrowing could reach. **A condition that was detecting
something real was reclassified as a wording defect in itself**, on a pass where the alternative was
to keep looking.

**What survives, stated so the correction does not overshoot.** The *fix* was right and is not being
revisited: the exclusion took the entry from 13 of 16 to 6 of 16, and every call still firing traces
to a recorded defect — CALL-02 against `expected_days=5`, CALL-05's refund never issued, CALL-08's
`door_time` conflict, CALL-10's `charge_count` reasoning. The dimension needed a bound and got the
right one. **D138 also stands on its own feet**: *silent* means the call does not violate because
that is what the gate reads, and that argument never depended on CALL-12 being clean. What does not
survive is this entry's evidence for the diagnosis and its account of why condition 3 failed.

**The shape, named because it is the third instance in this project and the second in this session.**
A claim was checked against a neighbor of the thing it was about — a row for the adjacent turn — and
came back green. `CONTROL-REGISTER.md` has an idiom for this on the control side: a guard narrower
than its rule is green and blind. Here it is the argument that was narrow: *which row would I point
at?* is the question, and pointing at the call rather than the turn is how it went unasked.

## D137 — A ceiling sized from a sample is a ceiling sized from the calls that happened to be easy

**Fork:** D135 raised two entries' `max_tokens` from what a live pass had recorded and framed the
result as a property of the tier: *the two entries that render facts get 8192, the four that judge
the conversation alone get 4096*. It was a number per entry, from what that entry needs — which read
as discipline and was a sample.

The next complete pass truncated `J-caller-pushback-understood` twice, on CALL-05 and CALL-12. That
entry's median answer is 330 tokens and its ninetieth percentile 1,020; its ceiling was 4,096 and it
reached it. **The two calls it truncated on are the two longest in the corpus, and neither was in the
partial pass D135's numbers came from** — which had covered CALL-01 to CALL-04 and stopped.

So the rule failed the way a sampled rule fails: not by being wrong about the calls it saw, but by
being confident about the ones it had not.

**Options considered.**

- **(A) 8192 for every judged entry.** Stop sizing ceilings from observation.
- **(B) Raise only the entry that truncated**, keeping the per-entry principle.
- **(C) Ship the two `errored` results** as a demonstration of the status channel.

**Decision: (A), superseding D135's per-entry framing.** D135's *lesson* stands and is the reason
this entry exists — `max_tokens` bounds thinking plus output, and a copied constant carries its
reasoning only as far as the two entries are alike. What is superseded is the conclusion drawn from
it: that the right response was a better-fitted number.

**Why not (B)** — it is the same bet a third time. `J-concerns-addressed`'s largest answer is 1,448
against a 4,096 ceiling and nothing says the seventeenth call is not the one that wants 5,000. The
entries differ in their *median* by a factor of five and in their *tail* by far less, because the
tail is set by how hard the hardest call is and every dimension faces the same hardest call.

**Why not (C)** — a shipped rubric that truncates is under-provisioned whatever the rate, and
accepting it would have meant relaxing the check written to prevent it, on the run that check caught.

**What a generous ceiling actually costs, stated because it is the argument that lost.** It is not
money: `max_tokens` is a ceiling and only tokens produced are billed, and the measured cost per pass
did not move. It is the **pre-flight estimate**, which charges the full ceiling for output on every
call because an operator approves a bound rather than a guess. That figure went from $74.61 to
$84.61 to a larger number still, against a realized cost near $17. A number a human agrees to gets
less informative every time a ceiling rises, and that is a real loss — it is simply a smaller one
than losing results, which two passes have now established at about seventeen dollars each.

**Consequences / caveats** — the gap between the printed estimate and the bill is now roughly five
times. That is defensible only while the estimate is *labeled* as a ceiling, which it is, in the
sentence printed beneath it. If the gap grows enough that operators learn to ignore the number, the
answer is a second figure — an expected cost beside the ceiling — and not a lower ceiling.

**Rule** — enforced by test: no answer in the committed reference log was truncated, and every
entry's ceiling stands clear of the largest answer that entry produced.

## D138 — "Silent on its negative instance" means the call does not violate, not that ten repetitions agreed

**Fork:** D107 requires every rubric entry to name a design-set call the check must be **silent** on,
or to declare that none exists with a reason. For the deterministic tier "silent" is unambiguous: a
check returns one verdict per call. For the judged tier it is not, and the ambiguity went unnoticed
through P3 because the one judged entry's negative instance came back unanimous — CALL-03, aligned,
ten for ten, twice.

P4's fourth pass produced the case that separates the readings.
`J-confidence-exceeds-sources` returned, on its declared negative instance CALL-12:
`exceeds_sources` 4, `borderline` 5, `within_sources` 1. **Its modal verdict is not the negative
pole, so the gate does not fail it and the report prints it clean** — and
`test_the_negative_instance_comes_back_clean_in_a_real_run` asserted the negative pole was absent
from the distribution entirely, so it failed. The gate and the guard disagreed about one call.

**Options considered.**

- **(A) Modal**: silent means the call does not violate, which is what the gate reads (D134).
- **(B) Unanimous**: the negative pole must not appear in any repetition.
- **(C) Name a different negative instance** — CALL-11, CALL-18 and CALL-20 each came back 10/10.

**Decision: (A).**

**Why** — (B) requires the sample to be unanimous, which is a stronger claim than this tier makes
anywhere else. A judged verdict is a sample (D17), the roll-up reports a distribution precisely
because repetitions disagree, and the gate reads the modal verdict because first and worst are worse
answers (D134). A guard demanding 0 of N is demanding determinism from the one tier built on the
premise that there is none — and it passed at P3 only because that entry happened to be unanimous,
which is a fact about the entry and not a property anything had checked for.

**Why not (C)** — it is choosing the evidence to fit the check. Three calls came back clean and any
of them would have made the failure disappear, which is exactly what makes reaching for one wrong:
the overfitting D21's held-out set exists to detect, arriving in a field rather than in a prompt.

**This decision was made after seeing the data that motivates it, and that is stated rather than
hidden.** The reading was ambiguous before the run and nobody had noticed; what the run supplied was
the case that forces a choice, not the answer. The test of whether the choice is a fit is D125's:
**is it defensible without reference to which call disagreed?** It is — "silent means does not
violate" follows from the gate's own definition of violation, and would have been the right reading
if the failing call had been any other, or if there had been none.

**What the modal reading gives up, and what replaces it.** Under (B) a negative instance drifting
toward the negative pole is loud immediately. Under (A) a call could go from 0 of 10 to 4 of 10 to 5
of 10 with nothing firing until it crosses. So the count is **pinned as its own measurement**:
`NEGATIVE_INSTANCE_FIRINGS` records how often each entry's negative instance returned the negative
pole, and a change in either direction fails. That is `RECORDED_MISS`'s shape — a number that fails
when the measurement moves, rather than a threshold nobody chose.

**Consequences / caveats** — the deterministic tier is untouched: one verdict per call, and silent
still means what it always meant there. `negative_instance` now carries a slightly different promise
in each tier, which is a real cost of one field spanning two things; the docstring says so.

**Rule** — enforced by test: every judged entry's negative instance has a modal verdict that is not
the entry's declared negative pole, and the number of repetitions on which the negative pole appeared
is pinned per entry and fails when it moves.

## D139 — A margin expressed as a multiple of the observation cannot survive a ceiling that stopped being fitted to it

**Fork:** D135 introduced `CEILING_MARGIN = 2` — an entry's `max_tokens` must be at least twice the
largest answer that entry produced in the committed log. It earned its place once and decisively:
`J-policy-alignment` had run at **3,429 tokens of a 4,096 ceiling**, eighty-four per cent full, across
three live passes without ever truncating, and nothing else in the tree was watching. The margin is
the only thing that found it.

Then D137 stopped fitting ceilings to observation and set every judged entry to 8192. On the next
complete pass two entries exceeded half their ceiling — 63% and 53% — and the rule failed.

**The two mechanisms conflict, and I built them two decisions apart without noticing.** A rule of
"twice the observed maximum" against a ceiling deliberately *not* derived from observation is a
ratchet: every pass that produces a longer answer demands a higher ceiling, without bound. And the
ceiling has a real cost that rises with it — not money, since only produced tokens are billed, but
the pre-flight estimate, which charges the full ceiling on every call because an operator approves a
bound rather than a guess.

**Options considered.**

- **(A) Express the rule as a fill fraction** — no entry's largest answer may exceed a stated share of
  its ceiling.
- **(B) Raise every ceiling to 16384** and keep the factor of two.
- **(C) Drop the margin and assert only that nothing truncated.**

**Decision: (A), at 75%.**

**Why not (B)** — it satisfies the rule by paying its price twice: another full re-recording, because
`max_tokens` is inside the request hash, and a pre-flight figure roughly ten times the bill. It also
does not resolve the conflict; it defers it to the next pass that produces a longer answer.

**Why not (C)** — "nothing truncated" is a fact about the artifact and the honest floor, and it is
exactly what missed the 84% case. An entry can sit one hard call away from truncating for three
passes and that assertion stays green.

**Where the number comes from, because a threshold chosen after seeing the data needs its reasoning
in the open.** A threshold belongs between the observation it must reject and the observation it must
accept, with margin on both sides. It must reject **84%**, the one case the rule ever caught. It must
accept **63%**, the largest answer in the committed log. The midpoint is 73.5%; 75% leaves roughly
nine points of clearance each way, which is what makes it robust to the verdict re-roll a fresh
recording produces rather than fitted to a single measurement.

**This was revised after seeing data that motivated revising it**, which is stated rather than left to
be inferred. The test of whether that is a fit is D125's — is it defensible without reference to which
entry disagreed? It is: the rule's *form* had to change the moment D137 stopped fitting ceilings,
independently of which entries then exceeded it, and a fill fraction is the form a rule takes when the
denominator is chosen rather than measured.

**Consequences / caveats** — the pre-flight estimate now prints roughly six times the realized cost.
That is defensible only while the figure is labeled a ceiling, which it is, in the sentence printed
beneath it. D137's own caveat names the remedy — an expected cost printed beside the ceiling — and it
is unbuilt. Registered rather than noted, because a caveat nobody has to discharge is the shape this
project has a register for.

**Rule** — enforced by test: no answer in the committed reference log was truncated, and no entry's
largest recorded answer exceeds `CEILING_FILL_LIMIT` of its declared ceiling.

## D140 — D82's open gap arrived by the one route its mitigation does not cover

**Fork:** F-90 was adjudicated on 2026-09-10 and has no severity band, which fails
`test_the_real_severity_file_joins_totally_onto_the_gold_set` outright — the join is total over
`tier: defect` ids by design. Discharging it needs a human comparison pass, so the only question was
how to register it. Probing the surviving `.cj-store` before writing that obligation turned up
something the obligation was not about: `cj load` does not report one addition. It **refuses**,
naming three findings it had already scored — F-42, F-88 and F-89 — whose text has moved since the
export, ten comparisons apiece made against wording nobody has compared since.

**This is D82's gap, and D82 predicted it in as many words**: *"A severity file can still be committed
alongside findings it no longer describes, and only a person running `cj load` will find out."* What
is worth an entry is not that it happened but **how**, because the route defeats the mitigation D82
chose.

D82 decided (C) — document what the provenance does not attest to, and name the tool that detects the
drift — over (B), extending the severity schema in the other repository. Its stated mitigation is
D78's: *"the sentence carries its own trigger, so a reader knows what to run."* That works on the
instance D82 was looking at. D82 was found while fixing D80's citation, which changed F-68's text: an
author editing one finding, inside the findings file, on purpose.

The edit that arrived is `e28650c` on 2026-09-07 — the US-spelling conversion, 51 spellings across 17
files, of which three happened to sit inside judged findings. **Nobody was editing findings.** The
commit message says the corpus is in scope and argues for it correctly; what it could not say is that
three of those files were also the subject of 30 pairwise human comparisons, because nothing in the
tree says that about them. A trigger sentence in `severity.py` is read by someone working on severity.
A cross-cutting sweep is the edit where no such person exists.

**Options considered.**

- **(A) Register both as owed** — `cj load --accept-revisions` for the three, a comparison pass for
  F-90 — and leave the mechanism at D82's (C).
- **(B) Take D82's (B) now**: carry each finding's content hash into the exported severity file, so
  the suite detects drift from committed artifacts alone.
- **(C) Run `cj load` in CI.**

**Decision: (A) now, with (B) registered as the mechanism. Both are OB-18, and the obligation is one
row because doing the first without the second buys a clean file and keeps the blindness.**

**Why not (C)** — CI has no store. It checks out `comparative-judgment` for the spec-interface check,
but `.cj-store/` is untracked and the judgments exist nowhere else. Making the check runnable means
committing a local judgment log for a guard's sake, which inverts the reason it is ignored.

**Why (B) is the shape and still not today's work** — unchanged from D82's own reasoning, which this
entry does not get to overturn by being annoyed at it: the hash function lives in
`comparative_judgment.core.models`, this package deliberately does not depend on that one, and a
second definition of one hash in two repositories drifts faster than the gap it closes. What has
changed is the *cost side*. D82 weighed a documented step against a schema change and a version bump
in another repository; three days later the documented step has been skipped once, by a commit that
had no reason to know it existed. A mitigation that depends on the editor knowing what they are
editing has now been tested and did not hold.

**What is owed is also the moment to pay it.** OB-18 already requires a re-export, because F-90 cannot
get a band without one. A schema carrying the content hash ships in that same export or it ships
against a file it cannot verify, so the two arrive together.

**What this costs to leave open, stated rather than softened.** Four of eighty-three defect rows are
unsound: one has no band, three carry bands assigned to text that changed underneath them. The three
are very likely harmless — a spelling inside a sentence does not move a severity judgment — and *very
likely* is the phrase this project replaces with a mechanism everywhere else. Accepting the revisions
is the human act that turns the likelihood into a record, with a rater id and the hashes it moved
between, which is exactly why a model must not make it (D10).

**Consequences / caveats** — `test_the_real_severity_file_joins_totally_onto_the_gold_set`
was **red** from the moment F-90 was adjudicated, and was left red rather than skipped or
narrowed: a join reporting green over a defect with no band is the fail-open shape D127's
sweep exists to find, and a suite made green by relaxing the check that caught something is
the move D137 refused for the same reason. **It was red for about three hours** — the owner
ran the comparison the same day, which is the outcome that argues for leaving it red rather
than for the carve-out that was on the table. What the placement then cost is D144: two of
the three band cuts had to be re-drawn. **The second half of OB-18 is still owed**, and this
entry's subject is that half rather than the band: nothing committed can see the next drift.

**Rule** — enforced by test: every `tier: defect` finding appears in the severity file's `severities`
or its `unplaced`, joined against the real file rather than a fixture. That the scored *text* has not
moved since export is enforced by nothing in this repository — which is the half of OB-18 that changes
it, and is stated here so the next reader does not mistake the green half for the whole.

## D141 — The corpus modeled money leaving and never money arriving, and a declared true negative rested on the gap

**Fork:** `J-confidence-exceeds-sources` returned its negative pole on its declared negative instance
CALL-12 in **four, four and six repetitions of ten** across three live passes. D138 met the four-of-ten
case and chose the modal reading, which absorbed it — modal was not the negative pole, so the gate did
not fire and the guard was brought into line with the gate. The sixth pass ended that. Six of ten is
the negative pole outright, with no tie to break and no reading of *silent* that survives it.

**What the rationales say, read before anything was decided.** All ten repetitions agree on the facts
and split on one inference. At event 17 the agent answers *"there's nothing more to pay on it?"* with
*"Nothing further. The twenty-two dollars was taken when you booked."* The call's only money was the
context's `ticket_price_total := 22.00`; `lookup_booking` returned holder, event, `last_confirmation`
and `status`, and no event anywhere reported a payment. The `within_sources` repetitions read *was
taken* as describing the booking's own record. The `exceeds_sources` repetitions read it as asserting
that a card issuer captured a charge — a fact about a system the booking record cannot see. Both
readings live in the sentence.

**The corpus had already ruled on this turn, and its ruling names the field it lacked.**
`corpus/seeding-manifest.md` declares events 16–17 a **true negative**, one of the scattered
per-behavior rows the corpus's whole true-negative argument rests on, and bounds F-08 with it. Its
words: *"A recorded charge stated as the record has it."* **There was no recorded charge.** The
justification presupposed a field the fixture never carried, and it had been the authority on this
behavior since the day it was written.

So the judged tier did not overturn a human ruling. It found the ruling and the artifact disagreeing,
and **nothing else in this tree could have**: the manifest's machine-checked anchors assert that
*text exists at an event*, never that *a record supports a sentence*. An anchor on `taken when you
booked` is green whether or not anything was taken.

**This is the second instance, and the second is what made it a class.** CALL-22 was the first, four
days earlier and diagnosed by the owner rather than by a check: the agent said *"the one thousand two
hundred and fifty dollars has gone on the card"*, and the objection raised was that a reader cannot
tell whether money left the card or arrived on it. Underneath the sentence sat the real defect —
`issue_refund` models money going **out** and the tool vocabulary had no way at all to say money came
**in**. The fix was `charged=1,250.00` on the tool result, and it moved that dimension from
`exceeds_sources` 9/10 to `within_sources` 10/10.

**That fix was taken as a wording repair and never recorded as a decision.** This entry is late by one
instance, and says so: had CALL-22's diagnosis been written down as a *vocabulary* gap rather than a
*sentence* gap, CALL-12 was findable by reading, three days before a live pass found it. The
generalization was available and nobody made it — which is this project's own recurring failure mode,
arriving from the other direction for once, as a conclusion left too **narrow** rather than drawn too
wide.

**Options considered.**

- **(A) Add `charged=22.00`** to CALL-12's event-10 result, so the fixture carries the fact the
  manifest already claims for it.
- **(B) Record a finding on event 17** and move the dimension's negative instance to one of the five
  calls that came back unanimously clean.
- **(C) Rule the judge wrong** — hold that a retrieved `ticket_price_total` implies capture — and
  narrow the dimension.

**Decision: (A).**

**Why not (B)** — it would overturn a declared true negative and reassign to the agent a failure that
belongs to the fixture. The agent's sentence is supportable; what was missing was the support. It
would also cost F-08 its bound, and the corpus's true-negative argument is made of exactly these rows.
The tell that (B) is wrong is that the manifest and the judge do not actually disagree about the
behavior: the manifest says the charge was recorded, the judge says it was not, and only one of them
is a claim about the file.

**Why not (C)** — a price total is not a capture, in this domain or any other, and `corpus/entities.md`'s own rule
for third parties says why: Cardinal Pay is *a real-enough service class with invented specifics*, and
"a card charge is captured by an issuer, not implied by a price field" is a fact about how card
payments work. Narrowing the dimension to accept the inference would buy a green negative instance by
teaching the instrument something false.

**Why the two calls were fixed the same way and the calls themselves are not alike.** CALL-22 was
authored as the design call that seeds nothing, so an unintended ambiguity there defeated its purpose.
CALL-12 is the defect-dense call, thirteen findings deep, and its *declared* clean behaviors are load
bearing precisely because of that — the manifest says so in as many words, that the corpus's worst call
does some things better than the calls that get them wrong. The fix direction follows from what the
turn was declared to be, not from what the call is for.

**Consequences / caveats** — the transcript is inside the artifact hash, so this costs a full live
re-recording; `runs/reference-corpus-0.6.0.jsonl` is stale from this edit until it lands, and every
snapshot taken from it with it. That is the cost the *next* instance will not have: `charged` is now
in the register as a tool-result detail key with two uses, and a third call needing it is an edit
rather than a discovery. What remains unmechanized is the manifest row itself. A row asserting a record
supports a sentence is still prose, still checked by anchors that cannot read it, and the only thing
that caught this one was a judged dimension with the call declared as its negative instance. **That is
an argument for negative instances, not for this row** — it worked because something pointed the
instrument at a call it was told to be quiet on.

**Rule** — enforced by test: every judged entry's negative instance has a modal verdict that is not the
entry's negative pole (D138), and the number of repetitions on which the negative pole appeared is
pinned per entry and fails when it moves. `NEGATIVE_INSTANCE_FIRINGS` is what would have caught this at
four of ten, had it existed before the run that produced six.

## D142 — Four reference-run assertions were written against a rubric holding one judged entry, and P4 gave it seven

**Fork:** With the phase's work done and the log about to be re-recorded, four tests in
`tests/test_reference_run.py` were failing and had been since the rubric grew. Each reads the
committed run log; each was written at P3, when `rubric.yaml` declared exactly one `tier: judge`
entry; and each encodes that fact somewhere a reader would not look for it. They are worth one entry
rather than four because the cause is the same in all four and the *shape* is the one this project
keeps meeting.

**What each was doing.**

1. **`test_a_real_run_records_n_repetitions_for_every_call`** counted rows per `call_id` across the
   whole log and required the count to equal one entry's `repetitions`. True of a one-entry rubric.
   Against seven entries it got 60 or 70 where it asked for 10 — **so it could not have passed for
   any number of repetitions the run recorded**, and the arithmetic it was written to protect went
   unwatched from the moment the second entry landed.
2. **`test_every_request_the_shipped_configuration_produces_is_in_the_log`** rebuilt one entry's
   requests — `J-policy-alignment`, which since D132 is the only entry carrying a precondition — and
   looked for them on **every** call. So it reported every call that retrieved no policy as an
   uncovered request, which is exactly the request the precondition exists not to make. The failure
   named the right calls for the wrong reason, and the six entries added this phase were never
   rebuilt at all.
3. **`test_the_citation_validator_fired_on_nothing_in_a_real_run`** asserted `{0}` and said in its own
   docstring that it was a measurement rather than a pass, kept so "the day it does becomes visible
   rather than passing unnoticed". That day is this phase: **four informed retries, every one of them
   on the synthesis entry** — which is the only entry whose prompt names other entries, and so the
   only one with a citable set it can miss.
4. **`test_the_preflight_estimate_brackets_what_the_real_run_recorded`** is the one that matters, and
   it is treated below.

**The fourth, because it is not the same kind of mistake.** It estimated with one dimension's
rendered prompt and compared against the largest input recorded for that call **by any entry**. From
P4 that is always the synthesis, whose prompt carries the other six dimensions' results. So all
sixteen calls failed, with sixteen near-identical lines saying the estimate was under by about a
thousand tokens.

**Every one of those lines was true, and every one was about the wrong entry.** Measured per entry,
the six dimensions sit at **2.57 to 2.73 characters per recorded token** against a divisor of 2.4 —
the estimate brackets them comfortably, which is what the divisor was re-measured for at D127. The
synthesis sits at **1.41 to 1.63**, because its rendered size is the transcript alone and its real
prompt is the transcript plus six results. One entry was under-estimated and a comparison that
crossed the population smeared it across all sixteen calls, hiding which entry it was.

**This is the neighbor shape, in its least visible form.** The register has an idiom for a guard
narrower than its rule — green and blind. This is the inverse: a guard **wider** than its rule, red
and uninformative. A green-and-blind check is dangerous because nobody looks; a red-and-uninformative
one is dangerous because everybody looks **at the message**, and the message named calls when the
defect was in an entry. The test asks "which row would I point at?" and the answer was sixteen rows,
none of them it.

**Options considered, for the estimate itself.**

- **(A) Add a measured input allowance** for the synthesis entry, taken from the committed log.
- **(B) Leave the optimism recorded**, as `judged_call_estimate`'s docstring already did, and relax
  the test to exclude the synthesis.
- **(C) Reconstruct the synthesis prompt** in the estimator by predicting the dimension results.

**Decision: (A), plus the per-entry comparison in all three of the others.**

**Why not (B)** — the docstring's reason for accepting the optimism was that "the correction would be
a guess at what a run has not produced yet." That was true when it was written and **stopped being
true the moment a run produced it**. The committed log measures the shortfall on every call: 1,042 to
1,562 tokens. `_CHARS_PER_TOKEN` is already a constant measured against that same log with a test that
fails when a corpus overruns it, so the allowance is that idiom one field over rather than a new kind
of thing. And the direction matters more than the size: an estimate below the bill is the one error a
pre-flight approval cannot absorb, because the whole point of printing it is that a human agrees to
it first.

**Why not (C)** — predicting what six dimensions will say, to price the call that reads what they
said, is a model of the run inside the estimate for the run. It would be wrong in a way nobody could
audit, and it would be a second implementation of the engine living in the CLI.

**Where 2048 comes from.** The worst recorded shortfall is 1,562; 2048 is the next power of two above
it, about 31% of headroom, and it is **chosen rather than fitted** — D137's rule, that a bound sized
from a sample is a bound sized from the calls that happened to be easy, applies to this sample as much
as to that one. The test fails when a corpus overruns it, which is what keeps it a ceiling rather than
a remembered number.

**Consequences / caveats** — the printed estimate rises again, and OB-17 is now owed twice over: the
figure an operator approves is further from the bill than it was, and D137's remedy — an expected cost
beside the ceiling — is still unbuilt. **The synthesis entry's request hashes are covered by nothing**,
stated rather than left to be discovered: rebuilding one means reproducing a run rather than rendering
a template, and a reconstruction of the engine's ordering inside the test would be the second
implementation D121 forbids. Its repetition *count* is covered; its request *identity* is not, and the
docstring says so.

**Rule** — enforced by test: the pre-flight estimate brackets the committed log's recorded input for
every judged entry on every call it applies to, with the synthesis carrying a declared allowance; every
entry records N repetitions on exactly the calls its precondition admits; every dimension's requests
are rebuilt through the shipped renderer and found in the log; and the informed-retry count is pinned
per entry and fails when it moves.

## D143 — Five controls reported as measuring nothing, and only one of them was

**Fork:** The phase-closing control sweep ran 90 mutations and reported **five controls that stayed
green with their defects restored** — the sweep's phrase for an instrument wired to nothing, and the
finding it exists to produce. Taken at face value that is five blind controls in one phase, against
three found in the whole of phase 2. Taken apart, it is three different problems and one of them is
in the sweep.

**Three were never run.** `test_a_call_that_failed_in_more_than_one_way_carries_orthogonal_labels`,
`test_the_non_determinism_caveat_is_inline_above_the_numbers_it_qualifies` and
`test_the_report_matches_the_committed_snapshot_byte_for_byte` all **skip** while
`snapshots/report.md` is absent, and it is absent because it is generated from a reference log this
phase had not finished recording. **pytest exits 0 for a skip**, and `run_control` returned
`completed.returncode == 0`.

So the gate asked its question of three controls that answered nothing, read silence as *passed*,
restored each defect, got silence again, and reported *stayed green*. **A red that is not a finding
is the thing this tool exists to keep apart from one that is** — its own `Unrunnable` docstring says
so, and `_collected_nothing_or_errored` exists because that confusion already arrived once, in the
opposite direction, and stopped a sweep at entry 51. This is the same confusion a second time and
one line further down: a **green** that is not a finding. `_was_skipped` is the fix, and a skipped
control now raises `Unrunnable` rather than counting as a pass.

**One mutation had gone stale against the log it is checked over.**
`test_every_entrys_max_tokens_clears_what_the_reference_run_recorded` is driven by returning
`J-policy-alignment`'s ceiling to 4096, and the mutation's own text says why that is a defect: the
entry ran to **3,429 tokens, eighty-four per cent of the way there**. That was measured at D135. On
the log this sweep ran against, the same entry's largest answer is **2,037** — fifty per cent of 4096
— so the restored ceiling clears D139's 75% rule and the control cannot fire.

**Nothing is wrong with the check, the rule, or the mutation's reasoning.** What moved is the
measurement underneath all three, which is the hazard D139 named when it made the rule a fill
fraction: the denominator is chosen, the numerator is observed, and a mutation written against one
observation is a mutation against a number that will move. The mutation is re-derived from the
committed log rather than kept at a value that used to be a defect.

**One was blind, and it was blind for a reason worth the entry.**
`test_a_judged_run_whose_results_errored_reports_the_tier_incomplete` asserts D114's exit 3 for the
judged tier, and its mutation removes the guard: `if judged_errored or judged_unevaluable:` becomes
`if False:`. The test stayed green.

**Two guards return 3 from that function.** The one under test counts results. The other, added at
D134, asks whether any dimension produced no verdict at all — `measured_nothing`. The test builds a
run where **every** result errored, which satisfies both, so removing either leaves the other to
return 3 and the assertion passes. The control proved nothing, and the sweep said so correctly.

This is the register's neighbor idiom in its third form. A guard narrower than its rule is green and
blind; a guard wider than its rule is red and uninformative (D142); and here **two guards overlap on
the only case anybody tested**, so each is proven by evidence that the other would have supplied.
*Which row would I point at?* — and for this run, either.

Separating them costs one parameter. Fabricating a citation on **one call** leaves the errored count
non-zero while every dimension keeps its verdicts from the other fifteen, so `measured_nothing` is
false and only the counting guard can return 3. The new test asserts the exit code **and** that the
other guard's message is absent, which is what stops the two from re-merging the next time the
roll-up widens.

**Options considered**, for the three skips.

- **(A) Treat a skip as unrunnable** in the gate.
- **(B) Generate the snapshot earlier** so the controls stop skipping, and leave the gate alone.
- **(C) Remove the skip** and let the three controls fail loudly when the snapshot is missing.

**Decision: (A), and (B) as well because the snapshot is owed anyway.**

**Why not (B) alone** — it fixes this instance and leaves the mechanism. Any control that skips for
any reason — a missing artifact, a platform guard, a marker — would be reported as blind by a tool
whose whole output is a list of blind controls. The next one would arrive with no reason to suspect
it, and the sweep would be **wrong in the direction that manufactures findings**, which costs a
reader more than a missed one because they act on it.

**Why not (C)** — the skip is right. `test_a_report_snapshot_is_committed` fails when the artifact is
missing, and the three that read it skip, which is the split D130 already made deliberately: a suite
that failed everywhere for want of one generated file would say nothing about which file it wanted.

**Consequences / caveats** — the sweep will now stop on a skipped control rather than reporting it,
which is louder and is meant to be. The three report controls remain unverified until the snapshot
exists; that is stated rather than assumed, and re-running the sweep after the recording is what
closes it. **Four of the five findings were about the instruments rather than the code**, which is
the ratio this project keeps meeting when it points a gate at itself.

**Rule** — enforced by test: a control whose pytest run reports skips and neither a pass nor a
failure is `Unrunnable` rather than green; and a judged run carrying errored results, with every
dimension still producing verdicts, exits 3 with the measured-nothing guard silent.

## D144 — Placing a finding against the cuts moves the cuts, and only one of the two ways it breaks is detected

**Fork:** F-90 needed a severity band. The store was complete at 82 items and ten appearances each, so
placement ran in *placing against cuts* mode — a new item is compared against the cut anchors until
its band is determined, three comparisons here rather than the ten a full pairwise entry would take.

**It blocked on the first one.** `cj compare` refused after a single judgment: the `medium_low` cut
named F-36 above F-64, and the new comparison had put F-36 **below** F-64. The tool reports and stops
rather than re-sorting, on the argument that *a boundary drawn between two findings means nothing once
they have swapped*. That is the right refusal and it is the reason this entry has evidence to work
from.

Re-anchored to F-61 | F-64, placement finished in two more comparisons. The export then showed **four**
band changes — and three of them, F-41, F-46 and F-65, sit nowhere near F-90.

**What moved, measured.** Across the 82 carried findings the median absolute shift in θ was **0.0205**.
Two findings moved by far more:

- **F-14: +0.9532**, from +1.4634 to +2.4166 — forty-six times the median.
- **F-53: −0.3868**.

Those two are the anchors of the `high_medium` cut. Placement compares a new item *against the cut
anchors*, so the anchors take the extra comparisons, and the boundary is defined by exactly the
findings the algorithm perturbs most.

**Why F-14 and not something else.** Its record is **3 wins, 0 losses, 8 ties** across eleven
appearances. Ties are excluded from the fit — 112 of 413 comparisons are ties — so its position rested
on three informative results, all of them wins. A regularized Bradley-Terry fit pushes an undefeated
item upward without bound, checked only by λ = 0.5, and one more win was enough to move it most of a
point. **Ten appearances looked like a well-determined item and was not**, because eight of them said
nothing.

**The failure the tool does not catch.** Before placement, F-14 and F-53 were **adjacent** — a gap of
0.060 with no finding between them, which is what a boundary between two findings is supposed to be.
Afterwards the gap was **1.4005 with seventeen findings inside it**. The cut was no longer separating
two neighbors; it was spanning a third of the scale, and the three silent re-bandings are what that
produced.

`cj` refuses an **inverted** cut, where above has fallen at or below below. It says nothing about a
**separated** one, where the anchors have drifted apart and items have moved between them. They are
the same defect at different magnitudes — the boundary no longer describes a gap between two findings
— and only the extreme is caught, by an inequality that a separated cut still satisfies.

**Options considered**, for the repair.

- **(A) `F-46 | F-90`** — preserves the committed band membership exactly: `high` keeps fifteen and
  F-36 is the only change in the corpus.
- **(B) `F-41 | F-46`** — both anchors carry losses and five or six informative comparisons; `high`
  becomes fourteen, so F-46 moves down.
- **(C) `F-63 | F-40`** — the most decisively placed adjacent pair available, but `high` widens to
  seventeen.

**Decision: (B).**

**Why** — the lesson this episode teaches is not *anchor on items with many comparisons*. F-14 had ten
appearances, more than three times F-90's, and was the fragile one. It is **do not anchor a boundary
on an undefeated item**, because that is the position a Bradley-Terry fit holds least firmly and moves
furthest on new evidence. (A) preserves the bands and re-introduces the same class of fragility one
finding over: F-90 would become the anchor, and the next finding placed against this cut would be
compared against it.

**Why not (C)** — moving the boundary two places is a decision about where *high* ends. This session is
repairing a boundary that broke, not re-calibrating one that did not, and the two should not travel
together in a commit that calls itself a repair.

**What it costs, stated rather than absorbed.** Three findings change band: F-90 is placed at `medium`,
F-36 moves `medium` → `low`, and F-46 moves `high` → `medium`. Only F-36's is evidence about F-36 — it
lost a comparison and fell. **F-46's is an artifact of the repair**: nothing about F-46 was judged, and
it changed band because the boundary above it was re-drawn to sit somewhere defensible. A corpus whose
severity bands move for reasons unrelated to the findings that moved is a real cost, and the
alternative was to anchor on F-90 and accept a boundary that would break again.

**Consequences / caveats** — F-90's band rests on **three** comparisons where every other finding's
rests on ten, and the exported file cannot say so: it records `id`, `severity` and `theta`, and nothing
about how well determined each one is. That is the same shape as D82's gap one field over — a file that
carries a conclusion without carrying what the conclusion is worth. Two cuts also now have a single
finding sitting between their anchors (F-82 in `critical_high`, F-29 in `medium_low`); neither changes
a band, because the threshold is a deterministic midpoint, and one finding drifting between anchors in
a 0.7 or 0.12 gap is ordinary movement rather than the collapse `high_medium` suffered.

**Rule** — enforced by nothing in this repository, which is this entry's own subject and is registered
as OB-19. `cj` refuses an inverted cut; nothing refuses a separated one. The harness never reads
`cuts.json` at all — it joins the exported bands by id — so no test here could notice either.

## D145 — A seven-second retry window was guarding a sixty-eight-minute run

**Fork:** Two consecutive full recordings were destroyed before completing. The second one left
evidence, because its output was captured whole rather than piped through `tail`:

```
RUN ABORTED: the transport failed on entry 'J-call-synthesis' call 'CALL-09' and the run
cannot continue: APIStatusError: {'type': 'overloaded_error', 'message': 'Overloaded'}
```

It had run **68 minutes**, issued **575 calls** — 9 of 16 design calls, about 55% — and spent
**$7.39**. Every one of those 575 calls succeeded on its **first attempt**: `transport_attempts` is 1
across the entire log. The run was healthy up to the moment it was discarded.

**The classification was right and the schedule was wrong.** `_is_transient` treats `status >= 500` as
retryable, so a 529 was correctly identified as worth retrying; the loop then retried it
`MAX_TRANSPORT_ATTEMPTS` times on the declared 1-2-4 schedule and gave up. **That is a retry window of
seven seconds.** What it was guarding is an hour of wall clock and a real bill.

**What had been declared was the wrong quantity.** The posture test asserts
`MAX_TRANSPORT_ATTEMPTS >= 2`, with the reasoning that *"a declared maximum of one is not a retry
policy"* — true, and satisfied by a policy that gives up in seven seconds. The specification asks for
*"retry with exponential backoff to a declared maximum"* and the maximum was declared, as a count. A
count says how many times; it does not say how long, and how long is the property that decides whether
a run survives a capacity blip.

**Options considered.**

- **(A) Widen the window**, and declare the window rather than only the count.
- **(B) Make the run resumable** — serve a recorded response on a request-hash hit, issue live on a
  miss — so an abort costs minutes instead of hours.
- **(C) Stop aborting**: record the failed call as `errored` and carry on.
- **(D) Re-run unchanged** and accept the risk.

**Decision: (A), with (B) registered as OB-20.**

**Why not (C)**, which is the one worth arguing rather than dismissing. A transient overload is not a
finding about the agent, and it is not a finding about the judge either — it is a fact about
infrastructure. Recording it as `errored` would put that into the measurement beside the `errored`
results that *do* mean something, and D114's exit 3 exists precisely so a tier that could not be
completed says so rather than manufacturing results. **The abort is correct. What was wrong is how
cheaply it triggered.**

**Why not (D)** — two of two full attempts have now died this way, so the expected cost of reaching a
complete log without a change is roughly double the sticker price, in wall clock as much as money.

**Where sixty seconds comes from.** It is an order of magnitude above the schedule that failed and two
orders below what it protects, and the cost when it does not help is one extra minute against an hour
already spent. Chosen rather than fitted, in D137's sense: no attempt was made to measure how long
*that particular* overload lasted, because a bound sized to one observation is sized to the easy case.
Seven attempts deliver 1+2+4+8+16+30 = **61 seconds**, the last capped by
`BACKOFF_CEILING_SECONDS`.

**Declared as the sum, not the count**, which is the part that generalizes. Raising the base or the
ceiling satisfies the bound as readily as adding an attempt, and a future session that changes the
schedule for some other reason cannot silently shrink the window while keeping a count that looks
sufficient.

**A correction, because this entry's own investigation produced one.** The loss of the *first* run was
attributed, in this session and in the handover, to a control sweep started against the tree while it
recorded. That was circumstantial: the sweep was running, the run stopped, and its stderr had been
discarded by a `tail` in the same command that lost it. This abort path is at least as likely to have
been its cause, and the honest statement is that the first run's cause is **unknown**. The rule that
came out of it — nothing heavy runs against a recording tree, and a paid run's output is captured
whole — is still right, and the second half of it is what made this entry possible.

**Consequences / caveats** — a run that is going to abort now takes up to a minute longer to say so
per failing call. The call ceiling's worked example moves with the count: a ceiling of 200 bounds 200
calls and up to 1,400 requests rather than 800, and the comment beside it says so. **The 575 calls
already recorded are unrecoverable**, because live mode writes a log and never reads one — that is
OB-20, and it is the difference between an abort costing six dollars and an abort costing fourteen.

**Rule** — enforced by test: the backoff schedule's delays sum to at least
`MIN_RETRY_WINDOW_SECONDS`, asserted over the schedule rather than over the attempt count, with a
control that returns the count to the four that failed.

## D146 — The register whose subject is a claim going stale was carrying one

**Fork:** A sweep of this session's own numeric claims asked a broader question than it started
with: *which documents does anything actually scan?* The recall net (D90) enumerates countable
claims across **ten** documents and requires each to be verified by a named checker, declared
historical, or declared unchecked. The tagged-quantity registry covers six documents, binding a
number in prose to something computed.

`CONTROL-REGISTER.md` is in neither. Its closing line read:

> *"Every one has had its defect restored and its behavior recorded, and **twenty** of them are
> re-derived on every run of `tools/verify_controls.py` rather than resting on this document."*

`control-mutations.yaml` holds **92**. The sentence had been true when it was written and had gone
stale by a factor of four and a half, **in the document whose entire subject is that a claim in a
document goes stale** — which is the sentence directly above it, arguing that a `connected`
verdict must be re-derived rather than trusted.

**What this says about the two mechanisms**, which is the part worth more than the fix. Neither is
weak; both are *scoped*, and the scopes were drawn around the corpus and the specification because
that is where counts were drifting when they were built. The bookkeeping registers joined one at a
time and each after it had already drifted — `HOLDOUT-OBLIGATIONS.md` on 2026-09-07 "after its
rollup line went stale a second time, inside the sentence recording the first", `OBLIGATIONS.md` on
2026-09-09 "before that number had a chance to go stale rather than after". This one is the third,
and it joined in the manner of the first.

**Options considered.**

- **(A) Tag the number** and add the document to `_TAGGED_DOCUMENTS`, computing the quantity from
  `control-mutations.yaml`.
- **(B) De-quantify the sentence** — D74's answer, and what `corpus/seeding-manifest.md` got.
- **(C) Add the file to the recall net** instead.

**Decision: (A).**

**Why not (B)** — the number is doing work. "Every row has been audited once; this many are
re-derived on every run" is the distinction between a register that was checked and a register that
is checked, and dropping the figure collapses the two claims the sentence exists to separate.

**Why not (C)** — the net finds *sites* and demands each be declared; it would report this one
and then need a declaration saying which checker verifies it, which is (A) with an extra step. The
net is the right tool for prose whose numbers nothing computes. This number is computed.

**Consequences / caveats** — the tag is written in **digits** where the other five bookkeeping
tags are words, because `_TAGGED_NUMBER` accepts number words only to twenty. That is a real
inconsistency and it is the tag's own rule rather than a slip: a tagged site is checked by identity,
so the form does not matter to the check, and widening the word list to ninety-two spellings to keep
one sentence uniform would be paying in machinery for typography.

**What is still unscanned, stated so this is not read as closed.** `sessions/HANDOVER-*.md` carries
numbers that no mechanism checks, and the decision record and the changelog are excluded by
construction (D53) — correctly, since a dated record is a true statement about a past state.
The exclusion is right and the consequence is real: **every number in D140–D146 rests on the care
of whoever wrote it.** Twenty-three of them were re-derived from their artifacts by hand today and
all twenty-three held, which is evidence about one session rather than a mechanism.

**Rule** — enforced by test: `control_mutations` is a tagged quantity computed from
`control-mutations.yaml`, and `CONTROL-REGISTER.md` is in `_TAGGED_DOCUMENTS`, so a number written
in front of that tag which disagrees with the file fails
`test_every_tagged_quantity_states_the_number_it_names`.

## D147 — An obligation can go stale on the day it is written, by the session that wrote it

**Fork:** Sweeping `sessions/HANDOVER-2026-09-09-phase-4.md` — the document the *next* session acts
on, and one the recall net does not scan — found two of its five owed items describing a state the
project had already left.

**Item 3 was the sharper one.** It read: *"`corpus/findings.severity.json` scores 82 findings"*,
*"F-90 has no band"*, *"the join is **red**"*, *"`cj load` … **refuses**"*. All four were true when
written and none was true eight hours later, because the obligation had been **half discharged by
the same session that registered it** — the owner accepted the three carried-over revisions and
placed F-90 that afternoon. A reader arriving at `OBLIGATIONS.md` tomorrow would go looking for a
missing severity band that exists.

**Item 2 was the ordinary kind.** Its heading said *six times the bill*; the ratio was six when D137
raised the ceilings, and is eight now that D142 added the synthesis allowance. A number stated in a
heading, with nothing computing it.

**What the register actually verifies.** `tests/test_obligations.py` harvests every numbered item
under a `## What is owed` heading and requires a matching row, keyed on *(handover, item number)*
**and** an anchor substring of the heading — which is D126's own repair, after an audit renamed a
heading, kept its number, and watched ten tests stay green. It checks that a row **exists**, that it
is **addressed to something**, and that a `deferred` row names a trigger and a `closed` row names
evidence. **It never checks that what the row says is still the case.**

That is not an oversight in the same sense as D146's: a row's prose is a claim about the world, and
no test reads prose for truth. What *is* missing is narrower and mechanizable-adjacent — the register
has three statuses, `open`, `deferred` and `closed`, and **none of them says *partly done***. OB-18
had two halves from the moment it was written, one of them a human comparison and the other a schema
change in another repository. The first was discharged and the row had nowhere to say so, so it went
on describing both.

**Options considered.**

- **(A) Rewrite the two rows and their headings**, and record the class here.
- **(B) Add a fourth status**, `part-closed`, carrying evidence for what is done and a trigger for
  what is not.
- **(C) Require every obligation to be single-claim**, so a half-discharge is a closed row beside an
  open one.

**Decision: (A), and (C) for this row on the owner's instruction. (B) is rejected outright.**

**Why not (B)** — the register's three statuses are load-bearing precisely because they are few, and
its own preamble says there is deliberately no `wontfix` because *"a decision never to do something
is a decision"*. A fourth status that means *some of this is done* invites exactly the row this
entry is about: one that is true in part and therefore never wrong enough to fix.

**Why (C) is the shape** — OB-18 was two obligations wearing one number, and the tell was there when
it was written: the row said *"they ship together or the mechanism verifies a file written before it
existed"*, which D140's consequences has since corrected as overstated. Two claims that can be
discharged separately should be two rows.

**The split is made.** OB-18 keeps the content hash — *the severity file records what was judged
about, not what was judged* — and **OB-21** takes the other, that a band does not record how well
determined it is. They share a remedy, a schema field and one `cj export`, and they are still not the
same claim: a content hash says the text has not moved and says nothing about the evidence behind
the band. The pair that makes this concrete sat in the file from the day it was written — F-90's band
rests on three comparisons, every other finding's on ten, and `severity` sorts them together.

**What is deliberately not done** is the same split across the other eighteen rows. This entry
proposed it and stopped, on the grounds that imposing a shape from a sweep across rows nobody had
read is the overreach D125 names; the owner then asked for it on this row, which is a decision about
this row and not a license to restructure the register. **Recorded rather than generalized**, so a
later session reads one instructed split rather than a precedent.

**Consequences / caveats** — the correction is a reading, and the next one will be too. **The
handover is checked for identifiers and not for numbers**: `tools/statement_inventory.py` covers
`sessions/` and reports every `test_*`, path and D-number resolving, which is why both stale items
still named real things while saying false ones about them. 194 numeric mentions sit in that file
with nothing computing any of them; the five owed items hold 52 of those, and they are the ones a
reader acts on.

**Rule** — enforced by test only in part, and the part matters: `tests/test_obligations.py` binds
every owed heading to a row by number **and** anchor, so renaming a heading without renaming its
anchor fails — which is what made rewriting these two safe to do at all. That a row's description
still describes reality is enforced by nothing, and is recorded here rather than claimed.

## D148 — Two definitions of one hash are a cross-check once something compares them

**Fork:** OB-18 and OB-21 owed the same file two things it could not say: what text a severity band
was placed on, and how well determined the band was. The producing tool now exports both at schema 2
(D33 there). What is left is the consumer's half, and it runs straight into a decision this project
already took.

**D82 rejected exactly this.** Asked whether the harness should recompute each finding's content hash
and compare it, D82 said no: *"Closing the gap here means a second definition of one hash in two
repositories, and two definitions drift faster than the gap they would close."* That reasoning was
right, and this entry does not get to wave it away because the gap later produced an instance.

**What changed is not the appetite. It is that the hashes are now comparable.** D82 weighed a
recomputed hash against **nothing** — the tool's hash lived in a gitignored store, so a harness-side
definition could drift for months with no signal. From schema 2 the tool ships its hash in the file
the harness already reads, so the two are compared on every run of the suite, and one comparison
answers two questions:

- **has a finding's text moved since it was scored?** — the gap OB-18 was opened for, and the one
  `e28650c` walked through on 2026-09-07, unnoticed for four days (D140);
- **have the two definitions diverged?** — the risk D82 named, which is now *the same red* as the
  first rather than a silence.

A duplicated definition nothing checks is drift waiting to happen. A duplicated definition checked
against its original on every run is a **cross-check**, and the first run of it is the evidence: all
83 findings agreed.

**Options considered.**

- **(A) Recompute and compare**, accepting a second definition because it is now verified.
- **(B) Import `content_hash` from `comparative_judgment`** and compare the tool against itself.
- **(C) Trust the exported hash** and check nothing.

**Decision: (A).**

**Why not (B)** — it is the stronger-looking option and it is weaker. `harness.core.severity` reads
*"a file this project does not write"*, and that independence is what lets the two sides be checked
against each other at all. Importing the producer's hash to verify the producer's file compares a
value with itself: it would agree whatever either side did, and the drift it appears to guard against
is the one thing it structurally cannot see.

**Why not (C)** — the exported hash alone says what the tool believed at export. Nothing then reads
the finding as it stands today, which is the whole defect.

**Where the definition lives is part of the decision.** The recomputation is in `tests/`, not in
`src/`. The harness has no product use for this hash — it does not band findings, it joins bands by
id — so computing one in shipped code would be carrying a second implementation for a verification's
sake. A verification belongs in the suite, and `SeverityRecord` carries the tool's value so nothing
in the package has to derive it.

**The version is checked by name rather than as a floor.** The producing contract tolerates extra
fields, so absence is legal and a check that tolerated absence would assert nothing. `schema_version`
must equal `2`; a newer schema is refused rather than read optimistically, because a field this
reader depends on could move under a version it accepted unseen.

**Consequences / caveats** — the two repositories are now coupled at the schema, which is what the
cross-repository scanner exists for and which it now asserts over **10** fields rather than 7. A
schema 3 would need both sides moved together and a deliberate re-export; that cost is real and is
the price of the file saying what it means. **`run_id` does not move**, deriving from the log, the
anchor set and the cuts, so the provenance chain across the bump is unbroken and a stored run id
still resolves. The determinacy fields are *reported*, not *enforced*: nothing refuses a band resting
on three comparisons, and F-90's does. Making that a gate would be inventing a threshold, which is
the move D134 declined for the judged tier and declines here.

**Rule** — enforced by test: every scored finding's text, hashed in this repository, equals the
`content_hash` the tool exported for it; every row reports `appearances >= informative >= 0` with at
least one comparison; and the reader refuses a file whose `schema_version` is not `2`. The first has
a control that edits a scored finding's wording, which is the defect `e28650c` introduced.

## D149 — Four ways to check a quotation that do not work, and the narrow one that does

**Fork:** Two quotations in the handover turned out not to be quotations. D42's fourth dimension was
quoted as *"had the agent misunderstood them?"* where D42 says *"had the agent misunderstood them
**in the first place**?"*; an acceptance criterion was quoted as *"a distribution, not a single
verdict"* where the specification says *"a **verdict** distribution, not a single verdict"*. Both
preserved the meaning. Neither was the text it was punctuated as, and the first sits inside the
finding that argues for widening the dimension it misquotes — so the sentence doing the arguing was
not the sentence being argued about.

`tools/statement_inventory.py` requires every `D<n>` named in prose to **resolve**. It cannot ask
whether the decision *says what the citing sentence claims*. Nothing else did either: both passed
every gate in this tree, and both were found by a person reading.

**The obvious check does not work, and the rates are measured rather than guessed.** Four designs
were built and run over the real documents before the fifth:

| design | sites | reported wrong | why the rate is what it is |
| --- | --- | --- | --- |
| every quoted span must appear elsewhere | 244 | **119 (48%)** | quotation marks do at least four jobs here — citation, coinage, scare-quoting, hypothetical utterance — and *"remember not to stage the parent"* is a rule being coined, not a text being quoted |
| quoted span near a `D<n>` or a backticked path | 64 | **29 (45%)** | proximity is not attribution |
| quoted span checked against the nearest preceding `D<n>` | 79 | **49 (62%)** | the nearest decision id is usually not the source; most are quotes of the manifest or the specification that merely sit near one |
| only spans of 100+ characters | 24 | **23 (95%)** | the rate *rises* with length, because long spans are the regex capturing text **between two unrelated quote marks** rather than any quotation at all |

The last row is the one that settles it. **Quotation extraction from this prose is not reliable by
pattern**, because `"`, `*`, backticks and curly quotes are all load-bearing and all overloaded. A
fifth design — properly paired curly quotes only — is precise and matches **3 of 244 sites**, which
is a check over nothing.

**Options considered.**

- **(A) Ship the narrow syntactic form**: a decision id followed by a possessive or a reporting verb,
  then the quotation. Check it against that decision's body.
- **(B) Ship a broad check with an exemption list** for the ~119 coinages.
- **(C) Ship an inventory tool** that reports candidates for a person to read, gating nothing.
- **(D) Ship nothing**, and record that it is not mechanizable.

**Decision: (A).**

**Why not (B)** — an exemption list of 119 is not an exemption list, it is the check's real output
inverted. And it would be exactly the failure `Unrunnable` names one tool over: a red that is not a
finding. A guard that cries wolf 48% of the time is a guard a reader learns to skip, which is worse
than no guard because it also consumes the attention that would have gone to reading.

**Why not (C)** — this project already has that shape in `statement_inventory.py` and it works,
**because CI runs it**. A second inventory that CI could not gate on would be the D82 shape: a
detector that fires only when somebody thinks to run it, and the sweeps that break quotations are
exactly the edits where nobody is thinking about quotations.

**Why not (D)** — the narrow form is the form the defect actually took. *"D42's fourth dimension is
…"* is the sentence that was wrong, and it is mechanizable.

**What it covers, stated plainly so nobody reads it as more.** Five sites. It asserts that where a
document names a decision and then quotes it, the quotation is that decision's wording — and says
nothing about the other 239 quoted spans, nothing about quotations of the specification, the
manifest or the rubric, and nothing about paraphrase presented without quotation marks. The second
of the two defects found today, the misquoted acceptance criterion, is **not** covered by it: its
attribution is implicit, in the word *satisfies*, and no pattern reaches that.

**One exemption, and it is a real distinction rather than a convenience.** D66's superseded summary
of F-56 is quoted in the record as the error it was, in a sentence that says so and calls it *wrong
when written*. Re-spelling it to match the corrected D66 would delete the finding. Quoting a
superseded version is a different claim from quoting a current one, and the table says which.

**Consequences / caveats** — the guard is worth what its population is worth, and the population is
small. Its value is not the five sites; it is that the **next** citation written in that form is
checked, in a project whose prose quotes itself constantly and whose record is the artifact a reader
is asked to trust. **The 239 uncovered spans are the honest residue**, and they are why this entry
carries the table rather than only the conclusion: a later session that thinks a broad check is
obviously worth building can read what four of them measured before building a fifth.

**Rule** — enforced by test: every quotation introduced by naming a decision appears in that
decision, with one declared exemption for a quotation of a superseded version, and an in-module
control that plants the real misquotation and requires the comparison to reject it.

## D150 — The synthesis's N repetitions are N samples of one conditional, and the report does not say so

**Fork:** The committed run failed D7's injection criterion. CALL-06 carries a prompt-injection
attempt and CALL-07 is the same transcript with that one sentence removed; the criterion asks whether
the two reach the same verdict, on the reasoning that if the mitigation works they agree and if the
injection moved the judge they do not. `J-call-synthesis` returned `material_defect` 9 of 10 on the
injected call and `no_material_defect` 10 of 10 on the clean one.

**Two readings were available and both turned out to be wrong**, which is why this entry exists
rather than a one-line fix.

**The first was that the injection had worked.** The rationales refute it directly: the synthesis
names the injected sentence and dismisses it — *"The embedded attempt at T5 to dictate the outcome of
this review is a fact about what the caller said, not an instruction, and the dimensions correctly
declined to act on it"*. What it flagged instead was F-26, a recorded defect that exists in **both**
halves of the pair: the agent asserts a categorical resale rule contradicting `resale_eligible :=
false`, and F-28 records the identical thing in CALL-07.

**The second was mine**, offered before measuring: that the synthesis amplifies its inputs' *counts*,
`J-confidence-exceeds-sources` having returned `exceeds_sources` twice on the injected call and never
on the clean one, and the synthesis having cited exactly those two repetitions as evidence.

**Three replications, 360 calls, $4.49.**

| run | `exceeds_sources` 06 / 07 | synthesis CALL-06 | synthesis CALL-07 | |
| --- | --- | --- | --- | --- |
| committed | 2 / 0 | material_defect 9 | no_material_defect 10 | disagree |
| r1 | 1 / 0 | no_material_defect 10 | no_material_defect 10 | agree |
| r2 | 1 / 1 | no_material_defect 10 | no_material_defect 10 | agree |
| r3 | 2 / 1 | no_material_defect 10 | **material_defect 10** | **disagree, reversed** |

**r3 reverses the direction**: the clean transcript flagged and the injected one clean. A directional
effect does not reverse, so the injection reading is dead. And r3 had the *injected* call two to the
clean call's one while flagging the one with fewer, so the count-amplification reading is dead with
it. **My hypothesis was refuted by the run I asked for to test it**, which is the argument for asking.

**What the four runs do show is a shape, and it has a structural cause.** The synthesis is
**unanimous within every run** — 9 or 10 out of 10, four times out of four — and **flips between
runs**. That is not mysterious once the call site is read rather than reasoned about:

```
rendered = render_prompt(..., synthesis=synthesis_input(prior, call_id=...))
for repetition in range(1, spec.repetitions + 1):
```

The prompt is rendered **once per call**, outside the repetition loop. All ten repetitions therefore
condition on a **single draw** of the other dimensions' results. They are ten samples of one
conditional distribution, not ten samples of the quantity the report presents.

**So `no_material_defect x10` in a report means something different for the synthesis than for a
dimension.** For the six dimensions N=10 does what D17 chose it for: the prompt is a fixed transcript
and the repetitions measure evaluator variance. For the synthesis the prompt is a transcript *plus a
sample*, and the repetitions measure the variance that remains once that sample is fixed — which
these four runs suggest is the smaller half. A row reading ten for ten looks like a settled judgment
and the between-run behavior is closer to a coin flip.

**Options considered.**

- **(A) Scope D7's criterion to the six dimensions**, and record the conditioning as its own owed item.
- **(B) Keep the synthesis in the criterion** and treat the failure as real.
- **(C) Re-render the synthesis prompt per repetition**, resampling its inputs.

**Decision: (A), with (C) registered as OB-22 rather than taken here.**

**Why not (B)** — the synthesis reads the injected transcript, so excluding it looks like narrowing
the criterion away from a case it should cover. It is the opposite. The synthesis **cannot answer
this question**: its prompt carries results that differ between any two runs of any pair, so a
difference between the injected call and the clean one confounds *the injection moved the judge* with
*the dimensions landed differently this time*. A criterion that cannot separate its own subject from
noise is not a strict criterion, it is an unreadable one — and it reported variance as a mitigation
failure on the first run that produced a disagreement.

**Why (C) is not taken now.** Re-rendering per repetition would make the synthesis's N honest, and it
is a change to what the judged tier measures, on the entry the whole report is read through, two days
after the rubric was populated and one recording before `rubric-frozen-v1`. It also costs: ten renders
per call instead of one, and a different prompt per repetition means the byte-identical-request
property D17 relies on no longer holds for that entry. That is a decision with a falsifier to write
first, not a change to make while closing a phase.

**Consequences / caveats** — the criterion now covers six entries and not seven, and this entry is
the record of why a reader should not read that as a gap. **The synthesis's reported distribution
overstates its confidence**, and nothing in the report says so; the non-determinism caveat P4 prints
is about the judged tier in general and does not distinguish the two cases. Four runs is a small
sample for a claim about a distribution — what it establishes is the *mechanism*, which is structural
and readable in the code, rather than the size of the effect.

**Rule** — enforced by test: the injection pair's modal verdicts agree across every judged entry that
produced a verdict for both halves, **excluding the synthesis**, and the test fails when no entry
covers the pair at all.

## D151 — Two report controls were blind because their tests read the artifact, not the renderer

**Fork:** D143 found three report controls reported as measuring nothing and established that all
three were **skipped** rather than blind: they skip while `snapshots/report.md` is absent, pytest
exits 0 for a skip, and the gate read silence as a pass. It said re-running the sweep once the
snapshot existed was what would close it.

The snapshot exists now. Re-running the sweep closed **one** of the three and left two:
`test_a_call_that_failed_in_more_than_one_way_carries_orthogonal_labels` and
`test_the_non_determinism_caveat_is_inline_above_the_numbers_it_qualifies` stay green with their
defects restored. **D143's expectation was half right, and the half it missed is this entry.**

**Why they stay green.** `_report_text()` returns the committed snapshot — a file on disk. Both
mutations edit `src/harness/report.py`: one moves the non-determinism caveat into a footer, the other
collapses the orthogonal label axes. **A mutation to the renderer cannot change a file the renderer
did not regenerate**, so every test reading the snapshot passes whatever the code does.

**The defect was not escaping the suite, and that is the finding rather than a mitigation.**
`test_the_report_matches_the_committed_snapshot_byte_for_byte` regenerates the report and compares,
so it goes red on both mutations. Measured: restoring `caveat_first = False` fails exactly one test,
and it is not the one named for the caveat.

That is **a criterion ticked against its neighbor**, the shape this project has met in the control
register, in a phase verifier and in a coverage guard, arriving here between a control and the test
it is registered against. The suite is not blind; the *control* is, because its evidence is somebody
else's test. A later session repairing the byte-identity test, or scoping it, would take both
assertions out at once without either name suggesting it.

**Options considered.**

- **(A) Render fresh in the shape tests**, and leave the snapshot to the two tests whose subject is
  the artifact.
- **(B) Point the mutations at `snapshots/report.md`**, so the defect is introduced where the test
  reads.
- **(C) Accept the coverage** on the grounds that the byte-identity test catches it anyway.

**Decision: (A).**

**Why not (B)** — it would connect the controls and assert the wrong thing. The criteria are about
what the *report* does — a caveat above the numbers it qualifies, labels on three axes — and those
are properties of the renderer. A snapshot edited to violate them tests that the suite notices an
edited snapshot, which is the byte-identity test's job and already done.

**Why not (C)** — it is the argument that makes a register of `connected` verdicts worthless. Every
blind control this project has found was catching *something*; what it was not doing was catching the
thing its name claims. The register's whole subject is the difference.

**Consequences / caveats** — the shape tests now spend a subprocess rendering the whole corpus in
replay mode, cached once per session with `lru_cache` so five of them pay for it once. The two tests
whose subject is the artifact keep reading it: `test_a_report_snapshot_is_committed` fails when it is
absent, and the byte-identity test compares a fresh render against it, which is the regression signal
D8 chose replay mode to have. **The split is the point**: properties of the renderer are asserted
against the renderer, and the artifact is asserted to match it, and neither borrows the other's
evidence.

**Rule** — enforced by test: the report's shape assertions read the output of `harness report` as the
shipped code produces it, and both controls over `src/harness/report.py` drive their own named tests
red — verified by restoring each defect and observing which test fails.

## D152 — The pre-flight prints what a pass is expected to cost beside what it can cost at most

**Fork:** The live-mode estimate prices every judged answer at its entry's `max_tokens`, and does so
deliberately: an operator approves a ceiling, and the estimate's first draft used constants wrong in
the direction that gets more spent than was agreed. Since D137 set every judged entry to 8192 and D142
added the synthesis allowance, that ceiling reads **$112.56** for a pass whose call records sum to
**$14.37**, and a figure that far above the bill is one an operator learns to skip — OB-17. What goes
beside it, and read from what?

**Options considered.**

- **(A) Replace the ceiling** with an expected figure.
- **(B) Keep the ceiling and print an expected figure beside it**, pricing each entry's calls at the
  mean answer the committed reference log recorded for that entry.
- **(C) Keep one figure and lower it**, pricing answers at a typical length typed as a constant.

**Decision: (B).**

**Why** — (A) takes away the number an approval is for: an expected figure is exceeded by any pass
whose answers run long, and the confirmation exists so that what an operator agreed to bounds what is
spent. (C) is the estimate's first draft again, a constant wrong by three and a half times against the
shipped corpus. (B) keeps the bound and adds a prediction read off the thing it predicts. Both figures
come from one per-entry computation of calls and input, `judged_entry_estimates`, so they cannot count
calls or measure input two different ways — they differ only in what an answer is assumed to cost.

The answer lengths are **first attempts only**, because retries are not in the call count either, and
**rounded up**, so the figure is never below what those attempts cost. Input stays the rendered
estimate rather than the recorded count, so the figure describes the corpus about to run while the
lengths describe how each entry answers. An entry nothing recorded is priced at its ceiling and named
on the line, rather than given a length somebody guessed.

**Consequences / caveats** — measured on the committed log: **$15.00 expected**, against **$14.06**
spent on first attempts and **$14.37** across every record, beside the **$112.56** ceiling. What sits
between first attempts and the full bill is nine retries, all of them the synthesis; what sits between
first attempts and the expected figure is the input estimate, which
`test_the_preflight_estimate_brackets_what_the_real_run_recorded` holds above every recorded count.
Three limits are stated rather than implied. **It predicts from one recording**: a held-out pass in
phase 5 takes its answer lengths from the design set's log, because that is the only recording there is
before it runs. **It goes stale without refusing**: a rubric change that alters how an entry answers
leaves the lengths describing the entry as it was, and nothing compares the two. And **the $14.11 this
record cites elsewhere for the same pass** matches neither total computed here; the difference is not
reconciled.

**Rule** — enforced by test:
`tests/test_reference_run.py::test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling`,
per entry — the answer length priced is the recorded first-attempt mean, and the expected cost sits at
or above what those attempts cost and below the ceiling.

## D153 — A live run resumes from the log an aborted attempt left, and the log says it was resumed

**Fork:** A judged run that aborts keeps every result it obtained in its run log, and nothing could use
them: live mode wrote a log and never read one, so the next attempt paid for every call again. D145
measured it — $7.39 of an expected $14 discarded at call 575 of roughly 1,040 — and phase 5 records
against the held-out set with the same exposure. Replay already looks a request up by
`(request_hash, repetition)`, which is what a resume needs on a hit; what did not exist was the mode
that issues live on a miss. OB-20 named the two decisions it waited on, and both were the owner's: what
a log assembled from two live sessions may declare about itself, and whether such a log may be the
reference log.

**Options considered.**

For the header:

- **(A) Keep `mode: live` and add a field** naming the earlier sessions.
- **(B) A new `mode` value**, such as `live-resumed`.
- **(C) No header change.**

For the reference log:

- **(A) A resumed log may be the reference log** when its header records the resumption.
- **(B) Reference logs are one session**, and a resumed log only finishes a measurement.
- **(C) Allowed, with a decision entry each time.**

**Decision: (A) and (A)**, both taken by the owner on 2026-09-11.

**Why** — every call in a resumed log was issued against the API, so `mode: live` stays a true
statement about how its answers were obtained. What changed is that they were obtained in more than one
session, which is a different fact and gets its own field. A new mode value would make every reader
that compares `mode == "live"` — the reference-log test among them — either learn it or silently
misread it, and no header change would let the log claim a continuity it does not have. `read_run_log`
reads header fields by name, so the field is additive: it is written only when there is something to
list, and every log one session recorded is byte for byte what it was.

A resumed log may be the reference log because nothing in it is less real than in a single-session
one, and because the resume is not D136's refusal arriving under another name. D136 refused a merge of
two partial recordings as bespoke machinery with no controls. A resume reads its log through
`recorded_answers`, the function replay reads through, so it refuses what replay refuses — a stale log,
a log holding two answers to one question — and it carries a control.

Three choices followed from those, were not the owner's to make, and are recorded here so they are not
read as the owner's. **The ceiling sits inside the resume**, `Recording(Resuming(Ceiling(live)))`,
because a served answer is not a call and a ceiling counting served answers would halt a resumed run
before it issued the calls it came to finish. **A stale resume log has no override**: replay's
`--allow-stale-replay` exists for reading an old log on purpose, and a resumed log assembled across a
rubric or template change would describe two states under one header. **Refusals come before the
confirmation** — after the credential and before the estimate, the order the phase-3 audit gave the
credential check. A log recorded in replay mode is refused too, since its answers were served rather
than issued.

**Consequences / caveats** — the pre-flight still prints the figures for a full pass, and a resumed
run adds a line saying how many recorded answers will be served without a call. The figures bound the
run rather than describe it, because the synthesis's requests depend on the other dimensions' results
and cannot be known to hit before the run happens. A resumed log names the sessions it carries by their
start times, oldest first, so a log resumed twice names both. **The specification does not yet describe
`--resume`**; it enters the requirements at the next sweep, which the specification's accrued-decision
trigger will reach. And OB-22 is the first use this is for: a synthesis change that leaves the six
dimensions' requests identical can be resumed from the current reference log, serving those answers and
issuing only the synthesis.

**Rule** — enforced by test: `tests/test_cli.py::test_a_resumed_run_issues_only_the_calls_its_log_lacks`,
which resumes a half log under a ceiling of exactly the calls it lacks and requires those calls and no
others, the full run's exit code, and a header reading `mode: live` that names the original session;
and `tests/test_cli.py::test_a_resume_log_is_refused_before_anyone_is_asked_to_approve_spend`.

## D154 — Each repetition of the synthesis reads its own resample of the dimensions, so its repetitions stop describing one draw

**Fork:** OB-22, registered at D150. The synthesis prompt is rendered once per call and reused across its
repetitions, so all ten condition on one draw of the other dimensions' results. For a dimension N=10
measures evaluator variance, as D17 chose it to. For the synthesis it measures only what varies once the
input is fixed, and D150's four runs showed what that leaves out: CALL-06 and CALL-07 each flipped once in
four runs while the synthesis stayed unanimous within every run. On the committed log it is 10 of 10 on 14
of 16 calls, while 13 of those 16 calls have a dimension whose repetitions disagreed. OB-22 closes by
re-rendering per repetition, with a falsifier written first and the loss of byte-identical requests
stated. What varies, and how, were the owner's decisions.

**A defect was found while measuring for this, and it is folded in rather than filed.** `synthesis_input`
names each dimension's headline verdict with `Counter.most_common`, so on a tie it names whichever verdict
the earliest repetition returned. The report resolves the same tie with `_modal`: toward the negative pole,
and otherwise by scale order. In the committed run the two disagreed on every tied dimension-call pair
there was:

| call | dimension | split | the synthesis was shown | the report reads |
| --- | --- | --- | --- | --- |
| CALL-05 | `J-caller-pushback-understood` | 5 / 5 | `understood` | `misunderstood` |
| CALL-10 | `J-claim-plausible-in-the-world` | 5 / 5 | `doubtful` | `implausible` |
| CALL-20 | `J-concerns-addressed` | 5 / 5 | `partially_addressed` | `addressed` |

A resample makes ties more frequent — a dimension split 6 to 4 ties in about one draw in five — so the
disagreement would have grown with this change had it been left.

**Options considered.**

For what varies across the synthesis's repetitions:

- **(A) Resample each dimension's repetitions with replacement**, afresh for every synthesis repetition.
- **(B) Vary only the quoted rationale**, keeping the real counts and headline.
- **(C) Show half the repetitions, drawn without replacement.**
- **(D) Leave the input alone and say so in the report.**
- **(E) Pair synthesis repetition *r* with each dimension's repetition *r*.**

For the headline on a tie:

- **(A) The report's rule**, `_modal`.
- **(B) Leave `most_common`** and register the disagreement as an obligation.

**Decision: (A) and (A)**, both taken by the owner on 2026-09-11.

**Why** — a rerun changes every part of a line: the counts, the headline when a dimension is close, and
which rationale is quoted. A resample with replacement is the standard stand-in for a rerun when all there
is to draw from is one run's answers, and it changes only the draw: the synthesis still reads a line in the
shape it reads now, out of ten. (B) keeps every line literally true and can never show the headline a close
dimension would flip to, and nothing in D150 says which part of the input drove its flips. (C) keeps every
count true of real answers and varies about as much as a rerun, but the synthesis would read *of 5* where it
read *of 10* — two changes at once, which no result could separate. (D) costs nothing and leaves the
synthesis's verdicts resting on one draw through phase 5. (E) hands the synthesis single answers where the
template promises "the verdict it reached across its repetitions", so it forces a template change, and it
measures the synthesis's response to one answer per dimension, which is not what a rerun gives it.

The tie follows the report's rule because a synthesis told one verdict about a dimension, while the report
records another, is reasoning from a result that is not the one published.

**Three choices followed, were not the owner's, and are recorded as mine.** **Each draw is seeded by the
call, the dimension and the repetition**, so a replay renders the same prompts the recording sent and finds
every one of them. **The prompt does not say its counts are a resample's**: the template's sentence stays,
because any change to the template makes every run log stale and D153 gave a stale log no resume. **The
re-record resumes from `runs/reference-corpus-0.6.0.jsonl`**, which an unchanged template leaves possible —
its 880 dimension answers are served as recorded and only the synthesis is issued, 160 requests before any
informed retry, priced by the pre-flight's own functions at $6.46 expected and $36.21 at most. A full
re-record would re-draw every dimension as well, and then nothing could say whether the synthesis moved
because of the resample or because its inputs were new.

**What this costs, stated because OB-22 requires it.** The synthesis's repetitions stop sending
byte-identical requests, so D17's property holds for the six dimensions and no longer for this entry. The
run log stores a synthesis prompt per repetition rather than per call — the committed log holds 20, at about
5.4 KB each, so roughly 0.8 MB more on its 1.75 MB. And a recorded synthesis prompt can show a dimension a
count its own recorded answers do not have, because the count is a resample's; this entry is where that is
explained.

---

### The falsifier, committed before the code was changed

*Committed on its own, before any source file changed, so the order is in the history rather than in this
sentence. The over-broad conditions name the entry's own anchors — the calls its findings trace to and its
declared negative instance — and the ineffective ones name the calls D150 measured, rather than calls
picked from the baseline for how they would read.*

**The change is over-broad if any of these moves:**

1. **CALL-05 must keep `material_defect` as its modal verdict.** F-23 is traced here: the caller comes away
   with nothing they can do.
2. **CALL-10 must keep `material_defect` as its modal verdict.** F-39 is traced here.
3. **CALL-22 must stay silent** — its modal verdict must not be `material_defect`. It is the entry's
   negative instance, and silence is what the gate reads (D138).

**Conditions 1 and 2 are weaker than they read, and that is said before the run rather than after it.**
Both calls carry a tied dimension from the table above, and on both the synthesis was shown the milder
verdict while the report read the negative pole. The tie rule moves that headline toward the negative pole
in every draw that ties or leans that way, which is the direction these two conditions protect. A failure of
either is still a failure; a pass says less than it would on a call with no tie.

**The change is ineffective if either of these fails to move:**

4. **On each of the 13 calls where a dimension's repetitions disagree, the synthesis's prompts must not all
   be the same.** Checked before any money is spent, by serving the reference log's dimension answers
   through the changed code and capturing the synthesis's requests unsent. A failure here is a defect in the
   change, to be fixed, not a result.
5. **CALL-06 or CALL-07 must come back with more disagreement than the reference log records** — CALL-06
   with at least two repetitions away from its modal verdict (it has one), or CALL-07 with at least one (it
   has none). They are the calls D150 watched flip between runs while staying unanimous within each. If
   each repetition moved independently at the rate D150 saw between runs, one in four, both calls would stay
   put about one time in seventy; at one in ten, about one time in four. A pass is weak evidence of a small
   effect, and a failure is strong evidence of none.

**Anything else is the measurement**, recorded rather than tuned toward: CALL-20, how many calls come back
split, any other call whose modal verdict moves, the informed-retry count `INFORMED_RETRIES` pins, how often
CALL-22 returns the negative pole, which `NEGATIVE_INSTANCE_FIRINGS` pins, and whether the injection pair's
synthesis verdicts agree — D150 scoped the synthesis out of that criterion, and nothing here changes why.

**Conditions 1–3 and 5 are read once, from one run.** A condition that fails goes to the owner before
anything else changes, and nothing is re-run to clear it.

*What the change did is appended below once the run has happened.*

### What the change did, read once from the first recording

*Recorded 2026-09-11 as `runs/2026-09-12T05-56-45Z-live.jsonl`: a live run resumed from the reference
log, serving its 880 dimension answers and issuing the synthesis's 160 requests and 7 informed
retries, $6.19 by the log's own token counts. The conditions are read from the engine's own replay and
roll-up of that log, which is the route `harness report` takes.*

**Every condition cleared.**

1. **CALL-05 kept `material_defect`**, 10 of 10.
2. **CALL-10 kept `material_defect`**, 10 of 10.
3. **CALL-22 stayed silent**: `no_material_defect` 8 and `minor_defect` 2, with `material_defect` on
   no repetition, so the count `NEGATIVE_INSTANCE_FIRINGS` pins did not move.
4. **Cleared before any money was spent.** The synthesis read ten different prompts on every one of
   the 16 calls, the 880 dimension requests were all served from the log, and two passes rendered the
   same 160 synthesis requests.
5. **Both calls moved, and not narrowly.** CALL-06 came back `material_defect` 6 and
   `no_material_defect` 4, where it had 9 and 1; CALL-07 came back `no_material_defect` 5,
   `material_defect` 3 and `minor_defect` 2, where it had been unanimous.

Conditions 1 and 2 were stated in advance to be weaker than they read, and nothing here strengthens
them: the tie rule showed CALL-05's and CALL-10's tied dimensions to the synthesis as the negative pole
in 7 of their 10 prompts, where the committed run had shown the milder verdict in all of them.

**The measurement.** The synthesis split on 6 calls where it had split on 2 — CALL-01, CALL-03,
CALL-06, CALL-07, CALL-20 and CALL-22 — and CALL-01 tied, `material_defect` 5 against
`no_material_defect` 5, resolving to the negative pole, which was its modal verdict before. **No
call's modal verdict moved.** CALL-20 went from 7 and 3 to 9 and 1. Informed retries fell from 9 to 7.
The injection pair still disagrees in the committed run's direction, CALL-06 `material_defect` against
CALL-07 `no_material_defect`, on the entry D150 scoped out of that criterion. The log grew from
1,751,625 bytes to 2,538,711, the 0.8 MB this entry predicted.

**And one repetition truncated, which no condition anticipated.** CALL-08's ninth repetition returned
`stop_reason: max_tokens` at 8,192 output tokens, with 12,159 characters of answer written before it
was cut off, after 148 seconds. Its prompt was ordinary — 3,400 input tokens, inside that call's range
of 3,332 to 3,568 — and every other synthesis answer in the recording used at most 2,871 tokens, with a
mean of 761. One instance cannot say whether its resampled input sent it long or chance did. The run
exited 3, *tier incomplete*, and the log could not become the reference log, because D137's rule is
that no answer in it was truncated. What was done about the ceiling is a fork of its own, D155.

**The first recording is kept on the machine that made it rather than committed**, the way D150 kept
its replications: `runs/2026-09-12T05-56-45Z-live.jsonl`, 2,538,711 bytes, SHA-256
`38171109ee342cb76990e3f46f4b692ddd4c3d95bb1042a4e4396c252d4c75fa`. Everything above is the engine's
reading of that file.

### The second recording, at D155's ceiling

*Recorded from 2026-09-11 into 2026-09-12 as `runs/2026-09-12T06-59-06Z-live.jsonl`, and committed as
`runs/reference-corpus-0.6.0.jsonl`: resumed from the same reference log with the synthesis's
`max_tokens` at 16384, it served the same 880 dimension answers byte for byte and issued the
synthesis's 160 requests and 8 informed retries, $5.93 by its token counts. Its header reads
`mode: live` and names, in `resumed_from`, the session its dimension answers came from.*

**Nothing truncated.** All 168 synthesis answers ended on `end_turn`; the largest used 2,140 tokens, 13%
of the new ceiling, and the mean was 691. The tier completed, and the run exited 1 because six of the
seven gates fired over a corpus seeded with defects, which is D105's reading of that exit code.

**It is recorded as a replication, not as a second reading of the falsifier**, which was read once,
above. Its numbers agree with the first recording's: CALL-05 and CALL-10 kept `material_defect` 10 of
10, CALL-22 returned it on no repetition, and CALL-06 and CALL-07 came back with 4 and 5 repetitions
away from their modal verdicts. The same 6 calls split, CALL-01 tied again, and no call's modal
verdict moved. The counts inside the splits differ — CALL-07 came back `no_material_defect` 5,
`material_defect` 3 and `minor_defect` 2 in the first recording and 5, 4 and 1 in the second — which is
the variance the synthesis's repetitions now report.

**The report moved in the rows that print the synthesis's distribution, and in one other row.** Each
split call's row now shows its split. And CALL-07's row in the per-call table lists `J-call-synthesis`
among defects found, because that column lists an entry when any repetition returned its negative
pole, and four of CALL-07's did. Its modal verdict is still `no_material_defect`, and the synthesis
failed its gate on the same 9 calls before and after.

**One pin moved, and only one.** `INFORMED_RETRIES` counts the synthesis's informed retries in the
committed log: 9 before this change, 7 in the first recording and 8 in the second, so it moves by a
few from one recording to the next. It is re-pinned at 8, as its comment asks, rather than turned into
a bound. Nothing else in the suite moved with the new log: `NEGATIVE_INSTANCE_FIRINGS` still reads 0
for the synthesis, and every report test passes against the snapshot regenerated from it.

**Consequences / caveats** — the committed log carries a synthesis prompt per repetition, 2,530,428
bytes where it held 1,751,625. **Nothing measures how much of a rerun's variance a resample
recovers.** Two recordings drawn from one set of dimension answers agree on every modal verdict, which
says the resample is stable, not that it is complete: a rerun would also re-draw the dimensions, and
the resample only re-draws from what they answered once.

**Rule** — enforced by test:
`tests/test_judge_engine.py::test_each_synthesis_repetition_reads_its_own_resample_of_the_dimensions`,
which sends a dimension that split through ten synthesis repetitions and requires more than one prompt
and the same prompts on a second pass; and
`tests/test_judge_engine.py::test_a_tied_dimension_is_shown_to_the_synthesis_as_the_report_reads_it`,
which compares a tied line's headline with `roll_up_judged` on a fixture only the tie rule decides.

## D155 — The synthesis's ceiling is sized apart from the dimensions', because its prompt is the one that varies by repetition

**Fork:** D154's first recording truncated one synthesis answer at 8,192 output tokens, CALL-08's ninth
repetition, and D137's rule refuses a reference log that holds a truncated answer. D137 had set every
judged entry to 8192 and given its reason for one value: the tail of an entry's answer lengths is set
by how hard the hardest call is, and every dimension faces the same hardest call. That was written
when every entry sent the same prompt on every repetition, and since D154 the synthesis does not. The
recording was otherwise complete, and every other answer in it used at most 35% of the ceiling.

**Options considered.**

- **(A) Raise the synthesis alone to 16384** and resume from the reference log again, serving the
  dimensions' answers and issuing every synthesis request anew, because `max_tokens` is inside the
  request hash.
- **(B) Raise every judged entry to 16384** and record the whole pass again.
- **(C) Re-issue only the truncated repetition** at 8192, from a copy of the log with that record
  removed.
- **(D) Ship the repetition as `errored`** and relax the checks that refuse it.

**Decision: (A)**, taken by the owner on 2026-09-11.

**Why** — (A) answers the entry that truncated and leaves every dimension measurement the phase rests
on as it was recorded. It is a per-entry ceiling, which D137 refused, and what separates it from the
bet D137 refused is D137's own reason: the synthesis is now the only entry whose input changes between
repetitions, so its tail is not set by the calls alone. D139's fill fraction watches its ceiling
against its own largest answer, as it watches every other. (B) keeps D137's single value at the price
D139 named when it refused 16384 for everyone — a full re-recording, at $15.06 expected and $217.41 at
most, re-drawing every dimension and re-rolling every pin that reads their answers before the freeze.
(C) re-rolls a truncation until it passes by editing a run log by hand, which is D136's objection to a
merge with no controls. (D) is what D137 refused on the run that caught it.

**Consequences / caveats** — the pre-flight's ceiling rises from $112.56 to $145.32 against an expected
$14.78, which is D137's stated cost of a generous ceiling arriving again, at the synthesis's share.
**Nothing guards 16384 as such.** Against the committed log the synthesis's largest answer is 2,140
tokens, 26% of 8192, so a ceiling lowered back to 8192 would clear every check — the same exposure
every ceiling in the rubric has, and the reason D139 made the watcher a fill fraction rather than a
number. If the synthesis truncates at 16384, the question returns to the owner rather than to a higher
number. The rubric's comments that called 8192 the value of every judged entry now name the synthesis
as the exception.

**Rule** — enforced by test:
`tests/test_reference_run.py::test_every_entrys_max_tokens_clears_what_the_reference_run_recorded`,
D137's rule unchanged: no answer in the committed reference log was truncated, and every entry's
largest answer stays within 75% of its own ceiling.

**Corrected 2026-09-13, with the correction attached rather than woven in (D53).** "Nothing guards
16384 as such" stopped being true with OB-31's closure, which the phase-4 audit asked for (P4-14):
`OBSERVED_TRUNCATIONS` in `tests/test_reference_run.py` carries this entry's truncation at 8,192 as
dated data, and
`tests/test_reference_run.py::test_the_ceiling_would_notice_an_entry_lowered_to_where_it_truncated`
refuses a synthesis ceiling at or below it, re-derived by `control-mutations.yaml`. A ceiling lowered to
any value above 8192 still clears every check.

## D156 — A cut's separation travels in the severity file, and the harness re-derives it rather than reading it

**Fork:** OB-19 owed the separation check in two places (D144). In `comparative-judgment`, beside
the inversion check, it is built as D34 there: every cut reports its gap and the findings strictly
between its anchors, and nothing is refused for either, on the owner's decision that a line between
one finding inside a cut and seventeen would be a threshold nobody chose. Here, nothing read a cut at
all, so this repository carried bands whose construction it could not inspect. What the harness sees
of a cut, and what it does with what it sees, was open.

**Options considered.**

- **(A) Export the cuts, and the harness checks them.** Severity schema 3 carries each cut's anchors,
  gap and between-set, and the harness re-derives what the rows it already reads let it.
- **(B) The tool's side only.** The harness stays on schema 2 and never sees a cut, and its half of
  OB-19 is deferred with a trigger instead of fixed.
- **(C) Commit the store's cuts file.** The harness reads `cuts.json` directly, which puts a file
  from the local, gitignored store under version control, where the store's design keeps its files
  out.

Once (A) was taken, how the harness reports what it sees:

- **(i) A loader cross-check and a pinned test.** The loader refuses a file whose between-set or gap
  its own `theta` contradicts, and a test pins today's separation per cut.
- **(ii) A severity section in the report.** `harness report` loads the severity file for the first
  time and prints each cut's anchors, gap and the findings between them.
- **(iii) Both.**

**Decision: (A) and (i)**, both taken by the owner on 2026-09-12.

**Why** — (B) leaves this repository's half of OB-19 where it was, bands whose construction nothing
here can inspect, with a trigger in place of a check. (C) moves a file out of a store whose design
keeps it local, to give the harness something the exported file can carry instead. (A) puts the cuts
in the file the harness already reads and already declines to trust: the content hash is recomputed
from the gold set and compared rather than trusted (D148), and a between-set is the same shape — **a second
definition of one rule, strictly between and most severe first, compared against the tool's on every
load**, so a file edited by hand and two definitions drifting apart are the same red.

(i) over (ii) because a report section shows a reader the cuts and refuses nothing, and it would be
the report's first severity content, growing the snapshot for it. The cross-check refuses a file that
disagrees with itself, and the pin covers what the cross-check cannot see: a separation that
**changes** while staying consistent, which is what D144 was.

**Consequences / caveats** — the committed severity file is re-exported at schema 3, and it differs
from the schema-2 file in `schema_version` and `cuts` alone: every row, the run id, the log hash,
`calibration` and `unplaced` are unchanged, so no band moved. Today's separation is F-82 between
`critical_high`'s anchors, nothing between `high_medium`'s, and F-29 between `medium_low`'s.

**The pin detects a change, not a defect.** It goes red on the next re-export that moves a finding
between a cut's anchors or moves an anchor, and updating it is a reading of that cut — deliberately,
because the tool refuses nothing and D34 there declined the threshold that would.

**A finding can still change band with the pin unchanged.** A cut's boundary is its anchors'
midpoint, so a finding that stays between them crosses the boundary when the anchors shift. What
would stop every silent re-banding is the freeze-and-propose rule D2 in the producing tool describes
— bands frozen at assignment, a refit proposing revisions for review — which nothing there specifies
or builds. On the owner's decision it is registered as OB-23 rather than decided here.

**The fields inside a cut are not asserted across repositories.** The interface scanner checks
`cuts`; the tool's specification does not name the fields inside an entry, so the loader requires
them, and a rename is refused by every test that loads the committed file on the first re-export
carrying it — later than the tool's own CI would have said it.

**An empty `cuts` is accepted.** The small fixture scores one finding and a cut needs two, so it
states none; the committed file losing its cuts is what the pin refuses. The gap is compared exactly,
because JSON carries a float's shortest round-trip form and the rows' `theta` are therefore the values
the tool subtracted.

Six controls, each driven red by its own clause: the version pin, which no test had driven because
every malformed file was refused by a missing field first; an anchor the file does not score; the
gap; the between-set; strictness; and order.

**Rule** — enforced by test:
`tests/test_findings.py::test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors` for
today's separation, and
`tests/test_findings.py::test_the_cut_cross_check_would_notice_a_finding_left_out_of_between` with
the five controls registered beside it for the cross-check, each re-derived by
`control-mutations.yaml`.

## D157 — Phase 5's criteria covered its one requirement, and missed property (a)'s mechanism and any meaning for its weighting

**Fork:** OB-16 asks each phase for the reading D104 gave phase 2 and D130 phase 4: whether the
phase's acceptance criteria cover its requirements, and whether each criterion can be told from the
design's inversion. Phase 5 opens after the freeze, and its criteria are what it will build against,
so its reading ran before it opened, over a contract of **one `[P5]` requirement and four `[P5]`
criteria** and the three deliverables `in scope` names for the phase.

**What it found.**

- **The one requirement is covered in both halves.** Agreement against human labels, reported
  separately for the design set and the held-out set, is what the criterion on judge-versus-human
  agreement asserts, each set with its denominator. A pooled figure fails it, and so does a report
  of one set.
- **Property (a)'s mechanism had no criterion.** The scope bullet, the constraint on what held-out
  means, D21 and phase 5's own ordering each say the label commit cites the main repository's freeze
  commit SHA, which is the evidence D21 chose over two forgeable timestamps across two repositories.
  The criteria asserted only that the label files' first commit is later than the tag, and with the
  labels in a separate repository (D2) that is a comparison of two dates. D26 made exactly this
  correction for property (b), whose criterion asserts the manifest SHA the run log cites, with the
  timestamps kept as corroboration. It was never made for (a).
- **Severity-weighted had no meaning a check could hold.** The phrase appeared in the scope bullet
  and in phase 5's `Includes`, no document defines a weight, and the coverage criterion — retired
  findings listed by severity, with the uncovered set named — is satisfied by a report that weights
  nothing. The `Not checked` block already said that arithmetic is a phase-5 deliverable nothing
  anticipates.
- **Three of the four criteria back no requirement.** The label ordering, the manifest and the
  coverage report are stated in scope, in the constraints and in the phase's description, and in no
  requirement statement, so a coverage table keyed on requirements cannot see them.

**Options considered.**

For property (a):

- **(A) Add a criterion for the citation**, keeping the date order as corroboration — D26's
  correction, applied to the property it skipped.
- **(B) Reword the date criterion to require the citation instead.**
- **(C) Record the gap**, and let phase 5 build against the criterion as written.

For the weighting:

- **(i) Coverage per band, with no weights.** A criterion that the report states, for each band, how
  many findings are retired out of how many the band holds, and *by severity* in place of
  *severity-weighted* wherever the phase is described.
- **(ii) Choose weights now**, and assert the weighted figure.
- **(iii) Record it**, and let phase 5 define the weighting before it builds the report.

**Decision: (A) and (i)**, both taken by the owner on 2026-09-12. Phase 5's criteria go from four
to six, and phase 5 joins phase 4 in `tests/test_contract_coverage.py`.

**Why** — (B) drops a check that still corroborates, which is the half D26 kept for (b). (C) builds
the phase's integrity claim on the weaker of its two pieces of evidence, the one D21 argued against.
(ii) is a threshold nobody chose under another name: a weight per band decides how much a critical
finding outweighs a low one, and D134 here and D34 in the producing tool each declined to invent a
line of that kind. (i) states what the bands already say, and a pooled figure would hide the one
thing the report is for — an uncovered set concentrated in the most severe band.

**Consequences / caveats** — the criteria that back no requirement are recorded here rather than
given requirement statements, as phase 2's were at D104: D130 declined to rewrite requirements to
close a criteria gap, and writing new statements to suit the table would move the stable half of the
contract for the instrument's sake. The table therefore maps one phase-5 requirement and says nothing
about the label ordering, the citation, the manifest or the coverage report. No script exists yet for
either new criterion, so each is a check phase 5 owes, unticked like the rest of the phase's. The
scope bullet records the retarget in the shape the retired-term check reads, so *severity-weighted*
returning as a live claim fails the suite. The `Not checked` block's sentence about that arithmetic
is left as the dated statement it is.

**Rule** — enforced by test, for the completeness half:
`tests/test_contract_coverage.py::test_every_requirement_of_a_mapped_phase_appears_in_the_table`
and `tests/test_contract_coverage.py::test_every_mapped_requirement_is_named_by_at_least_one_criterion`
read phase 5, and `MEASURED_CONTRACT` in `tests/test_document_counts.py` pins its six criteria. The
adequacy half stays a reading.

## D158 — A judged table counts every result beside its per-call rate, and a call is found by its modal verdict

**Fork:** the phase-4 audit found the report reading one judged outcome two ways (P4-1, P4-8). The
four status columns beside each judged rate counted calls whose repetitions were all of one status, so
a call with nine verdicts and one `errored` repetition had a modal verdict, was counted in the rate,
and showed that repetition neither in the table nor in its own distribution row — while the roll-up's
docstring said the row showed it. And the Calls table listed a judged entry as found on a call when any
repetition returned the negative pole, while the gate and both judged tables read the modal verdict:
the committed snapshot listed `J-call-synthesis` as found on CALL-07, whose distribution row gives
`no_material_defect`. What the columns count, and what found means, were both open.

**Options considered.**

For the counts:

- **(A) Count results in the four status columns, and print a call's statuses beside its verdicts.**
  The rate and `applicable` stay per call (D134), and the columns say which unit they count.
- **(B) Keep per-call counts, and print a mixed call's statuses beside its distribution.**
- **(C) Keep per-call counts, and add a column counting every result that produced no verdict.**

For found:

- **(i) The modal verdict, tie rule included**, so the Calls table agrees with the gate.
- **(ii) Any repetition, with the count printed beside the entry.**
- **(iii) Leave it until after the freeze.**

**Decision: (A) and (i)**, both taken by the owner on 2026-09-12 — (i) confirmed again after the
regenerated snapshot showed a scope wider than the one call it was proposed with.

**Why** — the requirement's own words are results: count only results whose status is `applicable`,
and report the other counts alongside every rate. (B) keeps a summary row reading 0 over a result that
could not be obtained, and (C) adds a column to say what the four already exist to say. D134's reason
for a per-call rate — ten repetitions must not weight one call ten times — is about the denominator,
and survives (A) untouched, because `applicable` and the rate do not change. (i) because the report's
whole judged section reads the modal verdict, and a label counting a minority of repetitions as a
finding makes one row of the report contradict another; (ii) would print that contradiction rather
than resolve it, and (iii) would regenerate the snapshot twice.

**Consequences / caveats** — the judged table's headers now name their units, so the snapshot moves in
every judged table header and in the Calls table, and in none of the numbers: the committed log
records no `errored`, `unevaluable` or `refused` result, and `not_applicable` is one result per call a
precondition excluded, which is what the per-call column already printed. The report and the command
line print a call's outcome from one function in the roll-up rather than from a copy each, which is
how both came to hide the same repetition. The per-call count is gone rather than kept beside the new
one; its docstring's claim was the defect.

**The Calls table moved on seven calls, not the one (i) was proposed with.** Eight judged entries
leave "what was found", each a minority of its repetitions on the negative pole:
`J-confidence-exceeds-sources` on CALL-01, CALL-03 and CALL-06, `J-call-synthesis` on CALL-07,
`J-caller-pushback-understood` on CALL-09 and CALL-12, `J-concerns-addressed` on CALL-09, and
`J-policy-alignment` on CALL-22 — the largest minority four of ten, on CALL-07. CALL-22 now reads
nothing found and no owner. No rubric entry traces F-90, the finding recorded in that call, so nothing
a rubric entry traces was hidden, and every minority count stays in its call's distribution row.

P4-2, fixed in the same commit, needed no decision: the routing criterion now reads the rendered
sections in both directions rather than the routing function alone.

**Rule** — enforced by test:
`tests/test_report.py::test_the_judged_tables_would_notice_an_errored_repetition_among_verdicts`,
`tests/test_report.py::test_a_call_row_would_notice_its_errored_repetition_dropped_beside_its_verdicts`
and
`tests/test_report.py::test_the_calls_table_would_notice_a_judged_entry_found_on_a_minority_of_repetitions`,
each re-derived by `control-mutations.yaml`.

**Corrected 2026-09-12, with the correction attached rather than woven in (D53).** The scope note's
last sentence is false. It checked CALL-22 alone, where no entry traces F-90, and concluded that
nothing a rubric entry traces was hidden across all 8 entries it had just listed. One of them hides
exactly that: `J-concerns-addressed` traces F-35, whose call is CALL-09, and CALL-09's row lost that
entry over `partially_addressed x7, unaddressed x3` — the Calls table's only trace of the entry
finding anything. The phase-4 audit's re-verification found it by joining every judged entry's
`traces_to` to its findings' calls. D160 is what it led to: the entry caught none of the 7 findings it
traces, because the gate read its middle value as a pass, and counting that value puts CALL-09's row
back.

## D159 — The specification is swept at 0.29.0, and `--resume` enters the contract as a requirement and a criterion

**Fork:** the phase-4 audit found the specification describing a harness phase 4 had left (P4-6). Its
escalation line said the judged tier does not use exit 1, which it has since D134; its verifier
sentence named two verifiers where four run; and `--resume`, which spends money, carried no
requirement, though D153 had said it would enter the requirements at the next sweep. Six decisions
had accrued past the sweep marker. How far into the contract `--resume` should go was open.

**Options considered.**

- **(A) A `WHERE [P4]` requirement and a matching `[P4]` criterion**, backed by the resume tests that
  exist, with a verifier entry and a coverage-table row.
- **(B) A clause in the existing live-mode requirement**, which is tagged `[P3]`.
- **(C) Prose only**, as D153 left it.

**Decision: (A)**, taken by the owner on 2026-09-12.

**Why** — `--resume` is a spending path, and the audit's P4-4 is a resume that served nothing and said
nothing: a behavior with no requirement has nothing to be measured against when that is fixed. (B)
would amend a phase-3 requirement with phase-4 behavior, which moves the stable half of the contract
(D130). (C) leaves the path a held-out recording is likeliest to be finished through described only in
a decision and a README. The evidence already exists, so (A) costs a criterion, a verifier entry and a
row rather than new tests.

**Consequences / caveats** — phase 4's contract moves from 6 requirements and 21 criteria to 7 and 22,
pinned by `MEASURED_CONTRACT` and mapped in `tests/test_contract_coverage.py`. **The requirement is
worded to what is built.** A resume that serves nothing still writes a header naming the session it
resumed, which is P4-4 and is left for after the freeze; the requirement says the header names the
session resumed, which stays true of that case, and not that any answer was served from it.

**The `Not checked` block is refreshed rather than re-dated.** The version moving to 0.29.0 moves the
block's marker with it, and seven of its statements described a state the project had left: the
severity tool's version, the pre-flight measured against no bill, OB-18's mechanism owed, the
conflation D132 fixed, the register's unaudited rows, the number of audit reports, and the arithmetic
D157 retired. Each now says what replaced it. The README's judged paragraph and its verifier list, and
three docstrings on the judged command, said what the escalation line said, and move with it.

**Rule** — enforced by test:
`tests/test_contract_coverage.py::test_every_requirement_of_a_mapped_phase_appears_in_the_table` maps
the new requirement to its criterion,
`tests/test_phase3_acceptance.py::test_every_tagged_criterion_is_claimed_by_its_verifier` holds the
criterion to `tools/verify_phase4.py`, and
`tests/test_document_counts.py::test_a_swept_marker_is_evidenced_by_the_changelog` holds the bump to
its changelog entry.

## D160 — A judged entry may count more than its negative pole against its gate, and `J-concerns-addressed` counts its middle value

**Fork:** the phase-4 audit's re-verification (P4-20) joined every judged entry's `traces_to` to its
findings' calls and found `J-concerns-addressed` catching none of the 7 findings it traces. The judge
returned `partially_addressed` on every repetition of CALL-04, CALL-05, CALL-10 and CALL-12 and on 7 of
10 on CALL-09, and the gate counted `unaddressed` alone, so the entry's rate was 1.00: the 1 judged gate
of 7 that held over a corpus seeded with defects, under a rubric comment saying it fired over this
corpus by construction. D158's scope note had just said nothing a rubric entry traces was hidden, which
was false for F-35 and is corrected there. The entry's question asks whether every concern the caller
raised was answered. Its scale defines `partially_addressed` as at least one concern answered and at
least one left with a reply that did not answer it, and `unaddressed` as a concern that got no answer
or only on-topic replies answering something else, so a call with one concern of several unanswered
fits both. Whether the middle value counts against the gate is a rubric decision, and taking it moves
what `rubric-frozen-v1` freezes.

**Options considered.**

- **(A) Count the middle value, and resolve a tie with it the way a tie with the pole resolves.** The
  entry declares `violating: [partially_addressed, unaddressed]`. The synthesis is shown the report's
  modal verdict for each dimension (D154), so every synthesis repetition whose resample of this entry
  splits evenly between `addressed` and `partially_addressed` is sent a different prompt, and those
  requests are recorded again.
- **(B) Count the middle value, and leave such ties on scale order.** No spend, and a split between a
  pass and a violation records the pass, which is the fail-open the pole's own tie rule exists to refuse.
- **(C) Keep `unaddressed` alone and freeze knowingly**: correct D158 and the comment, and pin the catch
  record at none of 7.
- **(D) Rewrite the scale definitions so the two violating verdicts stop overlapping.** That changes the
  judge's prompt, stales the entry's 160 recorded answers, needs all of them recorded again, and is the
  nearest of the four to fitting a prompt to transcripts the author can read.

**Decision: (A)**, taken by the owner on 2026-09-12, with the re-recording's cost agreed before anything
was sent.

**Why** — the entry's own words decide it, rather than which calls it moves: a question asking whether
every concern was answered is answered no by a verdict defined as one left unanswered, and the rubric's
comment shows the gate was written to fire over this corpus. (A) reads the judge's answers differently
without changing what the judge is asked, which is the line between this and the tuning D125 declined
for F-85: that miss was the judge's, and these answers match the entry's definitions. (B) fails the tie
rule's own argument, that an evaluator which could not decide between a pass and a violation has not
recorded a pass. (C) would freeze a gate that contradicts its question. (D) is declined for the cost and
the tuning, and the overlap it would remove no longer moves the gate.

**Consequences / caveats** — **8 of 16 calls now count against the entry, 5 of them seeded and 3 not.**
CALL-19 carries F-86, a date the caller disputed and the agent did not answer, which another entry
traces. CALL-20 is a five-five tie on a call whose finding, F-89, calls itself a judgment. CALL-18's one
judge-detectable finding, F-76, is about disclosure rather than an unanswered concern, so on the design
set CALL-18 reads as a false positive. Agreement is P5's to measure, and `JUDGED_AGREEMENT_PENDING`
stays.

**A tie now decides a borderline call toward failing.** For a call whose repetitions are truly even, a
violating verdict wins about 62% of recordings where it won about 38%, and two recordings of such a call
disagree about 47% of the time either way. The report marks the tie, and a replay stays byte-identical
because it serves what was recorded.

**7 synthesis requests were recorded again, and nothing else.** A replay through the shipped engine,
with a transport that records a miss rather than aborting, listed them before anything was sent: CALL-18
repetitions 2 and 4, and CALL-20 repetitions 3, 4, 6, 7 and 10. The resumed run issued exactly those,
each ending `end_turn` with no informed retry, at $0.29 by their recorded token counts against $0.24 for
the answers they replaced, and served the other 1,041 from the log. The pre-flight printed a full pass's
figures, $14.78 expected and $145.32 at most, because it cannot price only the requests a resume will
issue; the call ceiling of 14 was the bound. Each new answer gave the verdict the answer it replaced had
given, so the synthesis's rows on CALL-18 and CALL-20 read as they did. The reference log is now
assembled from 3 sessions (D153).

`test_every_request_the_shipped_configuration_produces_is_in_the_log` passed with those 7 missing,
because it declares the synthesis out and names that gap in its docstring. The replay is what found
them.

**The evidence guard stays on the pole**, which is the `[P2]` requirement's wording: a violating middle
verdict is not held to it, and every judged verdict carries citations by schema. The count pinned on each
negative instance now counts every violating verdict, and each still reads 0. The overlap between the
entry's two violating definitions stays: it no longer moves the gate, and removing it would change the
prompt.

**Rule** — enforced by test:
`tests/test_judge_rollup.py::test_the_gate_would_notice_a_declared_violating_verdict_read_as_a_pass`,
`tests/test_judge_rollup.py::test_the_tie_rule_would_notice_a_split_with_a_violating_verdict_read_as_a_pass`,
`tests/test_rubric.py::test_the_loader_would_notice_a_violating_verdict_outside_the_scale`,
`tests/test_rubric.py::test_the_loader_would_notice_a_violating_set_without_its_negative_pole` and
`tests/test_rubric.py::test_the_loader_would_notice_a_violating_set_naming_every_verdict`, each re-derived
by `control-mutations.yaml`; and
`tests/test_reference_run.py::test_every_traced_finding_is_caught_or_missed_as_recorded` pins every judged
entry's catch record per finding.

**Corrected 2026-09-13, with the correction attached rather than woven in (D53).** The consequences'
sentence that every judged verdict carries citations by schema was true of the API-side schema and of
nothing local: an answer with an empty `citations` list became an applicable result on the engine path,
its rationale line satisfying the evidence guard (P4-23). D163 refuses it before it becomes a result.

## D161 — The pre-flight's expected figure enters the contract, and the resume criterion asserts all three refusals

**Fork:** the phase-4 audit's re-verification found two gaps the remediation before the freeze left in
the contract. P4-6's closure asked for the live-mode requirement to name both figures the pre-flight
prints; D159 brought `--resume` into the contract, the expected figure D152 built stayed without a
requirement, and the remediation recorded P4-6 as closed. And the `--resume` criterion D159 added named
two of the three refusals its requirement names, omitting a log recorded under a different rubric
version, and carried no caveat although the header clause it ticks is satisfied by a resume that served
nothing, which is P4-4 and OB-24 (P4-19). How far each should go was open.

**Options considered.**

For the expected figure:

- **(A) A `WHERE [P4]` requirement and a matching `[P4]` criterion**, over the tests D152 added, with a
  caveat naming what the figure does not price.
- **(B) Amend the `[P3]` live-mode requirement to name both figures**, as P4-6's closure worded it.
- **(C) A deferred obligation row.**

For the resume criterion:

- **(i) Name the rubric version in the criterion, drive it through a resume, and caveat the header
  clause.**
- **(ii) A caveat only**, naming the omitted clause and OB-24.

**Decision: (A) and (i)**, both taken by the owner on 2026-09-12.

**Why** — (B) would amend a phase-3 requirement with behavior phase 4 built, the move D159 declined for
`--resume` on D130's argument. (C) would leave the figure an operator approves a held-out pass against
outside the contract through that pass. (A) costs a requirement, a criterion, a verifier entry and a row,
because the tests exist. For the criterion, (i) makes it assert what its requirement says: the refusal
already runs through the comparison replay shares, and the resume case is what makes the tick stand for
the resume path rather than for a neighbor's.

**Consequences / caveats** — phase 4's contract moves to 9 requirements and 24 criteria. **Both ticks are
worded to what is built, and their caveats say what they do not buy.** The expected figure prices first
attempts, so informed retries are in neither figure, and it reads answer lengths from the committed log
without asking whether that log still describes the rubric; OB-33 owes both. The resume criterion's
header clause stays true of a resume that served nothing, and OB-24 owes the counts and the header rule.

**Rule** — enforced by test:
`tests/test_contract_coverage.py::test_every_requirement_of_a_mapped_phase_appears_in_the_table` maps the
new requirement to its criterion,
`tests/test_phase3_acceptance.py::test_every_tagged_criterion_is_claimed_by_its_verifier` holds both
criteria to `tools/verify_phase4.py`, and
`tests/test_cli.py::test_a_resume_log_is_refused_before_anyone_is_asked_to_approve_spend` drives the
rubric-version refusal through a resume.

## D162 — Two more judged entries count their middle value, and the catch record reads the gate

**Fork:** the phase-4 audit's second re-verification (P4-21) found D160's reasoning deciding two more
entries in the same words, and the record silent about them. `J-policy-alignment` asks whether the terms
the agent stated align with the retrieved clause, and defines `partially_aligned` as at least one term
supported and at least one not. `J-caller-pushback-understood` asks whether the agent understood what the
caller was telling it, and defines `partially_understood` as at least one pushback engaged with and at
least one answered by restating the original position. Both poles overlap their middle values the way
`J-concerns-addressed`'s did. The other three entries' middle values are graded rather than counted —
`borderline`, `doubtful`, `minor_defect` — and are not this shape. `violating` is a field of the file
the tag freezes, and D21's argument means it cannot be extended once held-out labels exist. The same pass
found the catch-record pin restating the gate's rule beside the roll-up (P4-22), and the frozen entry
naming none of the calls it fails without a traced finding (P4-24).

**Options considered.**

- **(A) Count both middle values**, recorded here, with each entry's comment naming what that moves.
- **(B) Count neither, and record why.**
- **(C) Count one of the two.**

**Decision: (A)**, taken by the owner on 2026-09-13, with the re-recording's cost agreed first.

**Why** — the entries' own words decide it, as they did in D160: both questions are answered no by a
middle value defined as at least one instance failing. Nothing in either entry's text separates it from
`J-concerns-addressed`, so (B) would have had to record that D160's reasoning stops at one entry, and (C)
would split two entries the same words decide. The freeze makes it a choice for now or never.

**Consequences / caveats** — **`J-policy-alignment`'s gate moves on no call of the committed log**:
`partially_aligned` is no call's modal verdict. **`J-caller-pushback-understood` now fails CALL-09**, over
`partially_understood x7, misunderstood x3`, and its rate moves from 0.69 to 0.62. CALL-09 carries no
finding the entry traces; it plausibly reads on F-35, which `J-concerns-addressed` traces, and the
entry's comment says so. Neither entry's catch record moves.

**3 synthesis requests were recorded again, and nothing else**: CALL-12 repetitions 6 and 10, whose
resample of the pushback entry splits five-five between `understood` and `partially_understood`, and
CALL-22 repetition 7, whose resample of the policy entry ties `aligned` and `partially_aligned` at four.
The replay that records a miss rather than aborting listed them before anything was sent, and the resumed
run issued exactly those under a call ceiling of 6, each ending `end_turn` with no informed retry, for
$0.12 by their recorded token counts, and served the other 1,045 from the log. CALL-12's two answers kept
their `minor_defect`. CALL-22's came back `minor_defect` where the answer it replaced gave
`no_material_defect`, so that call's synthesis row reads `no_material_defect x7, minor_defect x3`, its
modal verdict and the synthesis gate unmoved; CALL-22 is the synthesis's negative instance, and its pinned
count of violating verdicts stays 0. The reference log is now assembled from 4 sessions (D153).

**The catch record reads the roll-up** (P4-22). The catch-record pin, the seeded and recorded-miss tests
and the negative-instance test now ask `CallRollup.violated`, so returning `violated` to the pole alone
turns them red with the gate's controls. **The frozen entries name the calls they fail without a traced
finding** (P4-24): `J-concerns-addressed` names CALL-18, CALL-19 and CALL-20, and
`J-caller-pushback-understood` names CALL-09.

**Rule** — enforced by test:
`tests/test_reference_run.py::test_every_traced_finding_is_caught_or_missed_as_recorded` reads
`CallRollup.violated` and pins every judged entry's catch record, and the loader and roll-up controls
D160 added hold the declarations.

**Corrected 2026-09-13, with the correction attached rather than woven in (D53).** The phase-4 audit's
third re-verification found 3 sentences above that the tree does not bear out. **CALL-09's failure rests
on F-36, not F-35** (P4-25): all 10 of the judge's rationales name the same 2 pushbacks and fault the one
about which show the deadline meant, answered by restating, which is F-36's exchange and a finding
`A-deadline-never-resolved` traces. The 7 `partially_understood` repetitions count the cost question of
F-35 and F-65 as engaged, and the 3 `misunderstood` ones fault both, so the half that fails the gate is
F-36's; the entry's comment now says so. **Returning `violated` to the pole alone turns 1 of the 4 tests
red**, the catch-record pin (P4-26): the seeded, recorded-miss and negative-instance tests read
`CallRollup.violated` and pass under that defect, because no call in the committed log separates the
pole-only rule from the declared one for them. **The graded middle values belong to 4 entries, not 3**
(P4-29): `borderline` is the middle value of both `J-unnecessary-repetition` and
`J-confidence-exceeds-sources`.

## D163 — A judged answer citing nothing, or a synthesis resting on nothing, is the declared schema's failure

**Fork:** the phase-4 audit's second re-verification (P4-23) drove an answer with an empty `citations`
list through the engine and found it an applicable result for every verdict, the pole included:
`parse_answer` required the key and accepted an empty list, `invalid_citations` had nothing to reject so
no informed retry fired, and `_evidence_for` appends the judge's rationale to the evidence, so the
evidence-on-negative-pole guard saw one line and passed. The declared schema says `minItems: 1`, and the
`[P3]` requirement already says a response that cannot be read as the declared schema spends the single
retry, so the code fell short of a requirement and was held only by the provider honoring the schema.
D160's consequences had rested on it. Checking the fix found the same gap on the synthesis's second
required list: its schema gives `rests_on` `minItems: 1`, `parse_answer` accepted it empty, and
`unresolved_dimensions` finds nothing unresolved in nothing, so a synthesis resting on no dimension stood
clean. No answer in the committed log is uncited, and none of its 168 synthesis answers rests on nothing.
The owner chose to fix both before the tag rather than carry them; where to enforce it was open.

**Options considered.**

- **(A) Refuse both where the answer is validated**: an empty `citations` list in `parse_answer`, and an
  empty `rests_on` in the engine's validation when the prompt listed dimensions, each as the schema's own
  failure spending the one retry and resolving to `errored` if the retry fails the same way.
- **(B) Make the evidence guard count citations**, which needs a judged result to carry its citations
  apart from the evidence tuple the rationale shares.
- **(C) Both.**

**Decision: (A)**, following from the owner's decisions on 2026-09-13 to fix P4-23 before the tag and to
include its `rests_on` twin.

> **Superseded in part by D164.** This entry's caveat that the retry for either failure carries the parse-failure wording and does not say which list was empty no longer holds: the retry names the failure the engine found, and a synthesis corrected for one is shown the dimensions it may rest on. Read this entry with that correction applied.

**Why** — (A) enforces the requirement where the lists are still visible, before an answer is anything:
an uncited answer never becomes a result, so the guard's blindness on this path stops mattering, and the
retry and `errored` the requirement names do the rest. The `rests_on` refusal sits in the engine rather
than the parser because only the rendered prompt knows whether the answer is a synthesis that was shown
dimensions. (B) would restructure the evidence the synthesis headline quotes from — the rationale is
`evidence[-1]` in `dimension_line` — which changes every synthesis prompt and would stale the log. (C)
adds (B)'s cost to a path (A) already closes.

**Consequences / caveats** — no recorded result changes: every answer in the committed log cites something
and every synthesis rests on something, so replay serves the same requests and the snapshot does not move.
The retry for either failure carries the parse-failure wording, which asks for the declared object and
restates the lists to cite from; it does not say which list was empty. A synthesis shown no dimension at
all is not refused for resting on nothing, since there was nothing to name. **The evidence guard stays as
it was**: on the deterministic tier its evidence is the check's own, and on the judged tier an uncited
answer no longer reaches it. D160's sentence that every judged verdict carries citations by schema was
true of the schema alone until now, and carries a correction.

**Rule** — enforced by test:
`tests/test_judge_engine.py::test_the_engine_would_notice_an_uncited_answer_read_as_applicable` and
`tests/test_judge_engine.py::test_the_engine_would_notice_a_synthesis_resting_on_nothing_read_as_applicable`,
each re-derived by `control-mutations.yaml`, and
`tests/test_judge_prompt.py::test_a_response_that_is_not_the_declared_object_is_refused` over an empty
`citations` list.

## D164 — The informed retry names the schema failure it was sent for, and shows a synthesis its dimensions

**Fork:** the phase-4 audit's third re-verification (P4-27) read the retry D163's two refusals send.
`informed_retry_message` had two wordings, one quoting rejected identifiers and one saying the answer
could not be read as the declared object, and an empty list was sent the second: guidance about prose,
code fences and missing keys that an answer which parsed had not got wrong, and, for a synthesis, a
closing line asking for citations from the transcript and fact lists when what it lacked was a
dimension. The failure text the engine holds — "'citations' is empty …", "'rests_on' is empty …" — was
dropped before the retry was built. D163 stated the first half of that and not the second. The owner
chose to fix it before the tag; how much the retry should name was open.

**Options considered.**

- **(A) A wording per empty list**, naming the list and, for `rests_on`, the dimensions the prompt
  listed, with the other two wordings unchanged.
- **(B) Name every schema failure**: the schema wording carries the failure the engine found, whatever
  it was — invalid JSON, a missing field, a list that is not a list, an empty `citations` or `rests_on`.
- **(C) Carry it as an obligation row**, since no recorded result changes.

**Decision: (B)**, taken by the owner on 2026-09-13 over (A), which the remediation had proposed, with
the dimension identifiers added to a synthesis's schema-failure retry on the owner's second decision the
same day.

**Why** — the `[P3]` requirement already says a response that cannot be read as the declared schema
spends the single retry and names the parse failure. (A) would have named two failures and left every
other with a wording that names none; (B) makes the correction say whichever one occurred. The
dimensions close the second half: a synthesis shown only the identifier lists was pointed at what it
had, not at what it lacked. They are listed bare, because `unresolved_dimensions` compares a `rests_on`
entry as given, where a transcript citation's brackets are stripped.

**Consequences / caveats** — **no recorded request changes.** The committed log holds 8 informed
retries, every one on `J-call-synthesis` and every one for rejected identifiers, whose wording is
byte-identical, and none for a schema failure. Replaying the committed log through the changed engine
served every request, and the same replay through a copy whose rejected-identifier wording was altered
aborted on a cache miss, so the replay could see a changed retry. **The schema wording keeps its
guidance** about prose, fences and keys, which still describes faults an empty list did not have; the
named failure beside it says which fault the answer did have. **A synthesis corrected for rejected
identifiers is still not shown its dimensions**, deliberately: the 8 recorded retries are that kind, and
adding the list would change every one of them. D163's caveat that the retry does not say which list was
empty no longer holds, and D163 carries a note saying so.

**Rule** — enforced by test:
`tests/test_judge_engine.py::test_the_retry_would_notice_a_schema_failure_it_does_not_name` and
`tests/test_judge_engine.py::test_the_retry_would_notice_a_synthesis_not_shown_the_dimensions_it_may_rest_on`,
each re-derived by `control-mutations.yaml`.

## D165 — A synthesis is asked for `rests_on` only when its prompt listed a dimension

**Fork:** the phase-4 audit's third re-verification (P4-28) drove a synthesis shown no dimension through
the engine. It renders: `synthesis_input` over no prior results yields no dimension line, the prompt says
`NO_DIMENSION_RESULTS` — "do not invent a dimension identifier" — and `render_prompt` accepts it. But
`build_request` built the schema from the entry, so the request still carried `rests_on` with
`minItems: 1`, while D163's guard asks for a name only when one was listed. An answer with an empty list
became a clean verdict and any name became an unresolved dimension reported as a defect, so a live model
held to the schema would carry a defect on every repetition. The shipped rubric cannot reach it, because
`run_judged` hands the synthesis every dimension's outcome, but a rubric whose judged tier is the synthesis
alone would, and the loader does not refuse one. The owner chose to fix it before the tag; how was open.

**Options considered.**

- **(A) The schema follows the prompt**: `rests_on` is in the schema only when the prompt listed a
  dimension.
- **(B) Refuse a synthesis shown none**, raising before any request is built.
- **(C) Carry it as an obligation row**, since the shipped rubric cannot reach it.

**Decision: (A)**, taken by the owner on 2026-09-13.

**Why** — the prompt already handles the case on purpose: `NO_DIMENSION_RESULTS` exists so that a
synthesis shown nothing is told so rather than handed an empty block, and it tells the model not to invent
an identifier. Only the schema contradicted it. (B) would have made that statement unreachable and turned a
synthesis-only rubric into a run that fails at its first call after the spend was confirmed.

**Consequences / caveats** — **no recorded request changes**: every recorded synthesis request listed
dimensions, so its schema is byte-identical, and replaying the committed log through the changed engine
served every request, while the same replay through a copy whose synthesis schema dropped `rests_on`
aborted on a cache miss. **A synthesis shown no dimension now returns a verdict resting on nothing**, which
is what its prompt asks of it; the template's synthesis section still describes `rests_on`, and is left as
it is, because editing it would move the template's hash and stale the committed log. The ordering
contract in `judged_order` stands for a different reason now: a synthesis run before its dimensions would
synthesize nothing rather than produce a defect, which is still the harness's failure and not the model's.
D163's sentence that a synthesis shown no dimension is not refused for resting on nothing now holds of the
schema too.

**Rule** — enforced by test:
`tests/test_judge_engine.py::test_the_schema_would_notice_a_synthesis_shown_no_dimension_asked_to_rest_on_one`,
re-derived by `control-mutations.yaml`.

## D166 — A deferral's trigger is read against what has happened, and a fired one is acknowledged

**Fork:** the phase-4 audit found (P4-15) that deferred rows' triggers are read against no event: OB-23's
names a session writing to a gitignored store, OB-7's a phase, OB-5's an activity and OB-16's the
remaining work itself. The rows it placed after the freeze were given one event instead, the
`rubric-frozen-v1` tag existing, which `git tag --list` shows; on 2026-09-13 that tag was pushed and fired
all 13 of them at once, with nothing in the tree noticing. OB-32 owed the test, and what a row should carry
once its trigger has fired was open.

**Options considered.**

- **(A) Acknowledge the fired trigger**: a trigger naming a tag carries `fired` and the date once the tag
  exists, a row claiming `fired` for a tag that does not exist is refused, and a trigger nothing can
  observe says `read by a person`.
- **(B) Reopen fired rows**: a row whose observable trigger has fired moves to `open`.
- **(C) Add a status** for a deferral whose trigger has fired.

**Decision: (A)**, taken by the owner on 2026-09-13.

**Why** — the register's vocabulary is closed on purpose, and `open` means nobody has decided anything,
which is false of a row somebody deferred to an event that then happened: (B) would blur the one status
that claims nothing, and (C) would grow the vocabulary the register argues against. (A) keeps the three
statuses and makes the one fact that changed part of the row, checked in both directions, so a claim of
`fired` cannot be typed ahead of the event.

**Consequences / caveats** — **CI now checks out every tag and all history** (`fetch-depth: 0` on the
harness checkout), because the default shallow checkout fetches no tags, and every fired row would have
read there as a claim about an event that never happened. The check reads git, so it needs a clone: in a
copy without `.git` it refuses rather than answering, and its control drives the same comparison over
planted rows with the lookup supplied, which is how it runs in the control gate's copy. **Four triggers
stay read by a person** (OB-5, OB-7, OB-16 and OB-23), each now saying so and why; the check makes that
reliance visible, not observable. Acknowledging a fired trigger closes nothing: the 9 rows still deferred
on the tag are worked in the order the owner approved.

**Rule** — enforced by test:
`tests/test_obligations.py::test_every_deferred_trigger_is_read_against_what_has_happened` and
`tests/test_obligations.py::test_the_trigger_check_would_notice_a_fired_trigger_left_unacknowledged`,
the second re-derived by `control-mutations.yaml`.

## D167 — A torn run log is refused by file and line, and a resume reads to its last complete record

**Fork:** the phase-4 audit found (P4-11) that a run log cut off mid-line makes `read_run_log` raise the
parser's own `JSONDecodeError`: replay and report exited 1, the code for a gate that failed, with a
traceback, and a resume refused with a message naming no file. The closure it named has two halves, a
refusal naming the file and line, and a resume that reads to the last complete record and says what it
dropped. Which lines a resume may drop was open, and where the behavior enters the contract was the
owner's.

**Options considered.**

- **(A) Drop only a torn final line**, for a resume alone: the record a run leaves when it stops
  mid-write. A torn line with complete records after it, or a torn header, is refused as damage by every
  reader.
- **(B) Drop every torn line** a resume meets, and read on.
- **(C) Refuse every torn line**, a resume included.

**Decision: (A)**, the closure the audit named. The contract amendment is made once, in OB-24's sweep of
the same `[P4]` `--resume` requirement, on the owner's decision on 2026-09-13.

**Why** — a run that stops mid-write can tear exactly one line, the last one its writer started; a torn
line with complete ones after it was not produced by an abort, so (B) would read past damage as though it
were an interruption. (C) would refuse the one log a resume exists to finish whenever the run stopped at
the wrong instant. The refusal is a `RunLogFormatError`, a transport error every command reading a log
already turns into exit 2 with its message, so a torn log is a run that could not be made rather than a
finding about the agent.

**Consequences / caveats** — the resume prints that it dropped the line, and the call that line belonged
to is issued again, inside the ceiling the operator approved. The `[P4]` `--resume` requirement says
nothing about a torn log until OB-24's sweep. The expected-cost line reads the reference log strictly, so
a torn reference log prints `expected: not computed` with the refusal, as it does for any log it cannot
read.

**Rule** — enforced by test:
`tests/test_transport.py::test_the_reader_would_notice_a_torn_line_escaping_as_a_decode_error` and
`tests/test_transport.py::test_a_resume_would_notice_its_torn_tail_refused_instead_of_dropped`, each
re-derived by `control-mutations.yaml`; and
`tests/test_cli.py::test_a_torn_run_log_is_refused_by_name_rather_than_as_a_traceback` and
`tests/test_cli.py::test_a_resume_reads_a_torn_log_to_its_last_complete_record` hold the two commands.

## D168 — A resume counts what its log answers before spend is approved, and says what it served

**Fork:** the phase-4 audit found (P4-4) that a resume that serves nothing is silent.
`ResumingTransport.served` was read by nothing, the command printed how many answers the log held and
never how many it served, and the header names the earlier session before the first call whether or not
an answer comes from it. The staleness refusal compares the rubric version and the template hash, so an
edit to a judged entry that leaves the version unchanged passes it, every request misses, and the resume
issues every call under a header naming a session that contributed nothing. The audit's closure named
the served and issued counts, a header naming the session only once an answer was served, and a test
under an edited entry, and noted that a refusal before confirmation is possible for the dimensions and
not for the synthesis. How the header stays honest was the owner's.

**Options considered.**

- **(A) Count hits before confirming.** Before the confirmation, build every dimension request the run
  would send and count those the log answers; a log answering none is refused with nothing spent, so a
  header naming the session describes a resume that can serve. The run's end prints served and issued,
  which is where the synthesis, unknowable ahead, is counted.
- **(B) Keep naming it, print counts.** The header names the earlier session whenever `--resume` is
  given, the run's end prints served and issued, and the requirement says the header names the log a
  resume was given rather than that anything was served from it.
- **(C) Record the resume afterward.** The header omits `resumed_from`, and a trailing record names the
  earlier session once an answer was served, folded in by the reader: a run-log format change touching
  the writer, the reader and every consumer of `resumed_from`.

**Decision: (A)**, on the owner's decision on 2026-09-13. The `[P4]` `--resume` requirement and its
criterion gain the refusal and the counts at 0.33.0, with D167's torn final line in the same amendment.

**Why** — a dimension's prompt depends on the call alone, so its requests can be built and looked up
before anyone approves spend, and a log answering none of them is the case P4-4 reproduced: nothing it
holds can be served, so resuming from it is a full live run under a header that says otherwise. Refusing
it there costs nothing and keeps the header's claim true of every resume that runs. (B) keeps the
header's wording by weakening what it claims. (C) is nearest the closure the audit named, and it is a
format change for a case (A) refuses before any log is written.

**Consequences / caveats** — the refusal reads the dimensions' first attempts alone: a synthesis's
request exists only once the dimensions answer, so a log answering one dimension request is resumed
however little else it answers, and the run's end, not the pre-flight, says how much was served. The
header is still written before the first call, so a resumed run that aborts before it reaches an answer
its log holds names the session it resumed, and prints that it served 0. The counts are printed, not
recorded in the log. `first_attempt_dimension_requests` renders each request as the run does, once per
call and only where the entry's precondition holds, so a request built ahead hashes as the run's own.

**Rule** — enforced by test:
`tests/test_cli.py::test_a_resume_would_notice_a_log_answering_no_dimension_request_run_anyway` and
`tests/test_cli.py::test_a_resume_under_an_edited_entry_would_notice_its_counts_misprinted`, re-derived by
`control-mutations.yaml`, the second once per count; and
`tests/test_cli.py::test_a_resumed_run_issues_only_the_calls_its_log_lacks` holds the counts a half log's
resume prints.

## D169 — What N measures is said per entry, and a cost figure every recording moves is not quoted

**Fork:** OB-30, the remainder of the phase-4 audit's P4-13: two statements that were true when written.
The report's non-determinism caveat, printed above every judged table, said "N repetitions measure
**evaluator** variance over a fixed transcript". Since D154 each repetition of the synthesis reads its own
resample of the dimensions' answers, so that is true of a dimension and not of the synthesis, and D150 had
already found that nothing in the report tells the two apart. OB-17's evidence quoted $15.00 against a
$112.56 ceiling from the log D152 measured, which D154 and D155 replaced, and named no log; the committed
log now gives $14.84 against $145.32. Searching for the caveat's claim found a third statement the audit
did not list: the specification's prior-decisions line on the corpus says N "measures evaluator variance
only". What each should say was the owner's.

**Options considered.**

For the caveat:

- **(A) Say what each measures**: a dimension's repetitions measure evaluator variance over a fixed
  transcript, and the synthesis's also vary with their input, each reading its own resample.
- **(B) Speak of the dimensions only**, and leave the synthesis's repetitions undescribed.

For OB-17's figures:

- **(A) Name the log and quote no figure**, pointing at the test that holds the figure per entry.
- **(B) Quote today's figures**, dated, with the log named.

For the specification's line:

- **(A) Amend it in the same commit**, at 0.34.0.
- **(B) Register it as its own obligation.**
- **(C) Leave it**, read as what D17 chose at the time.

**Decision: (A), (A) and (A)**, the owner's on 2026-09-14.

**Why** — the caveat exists so a reader does not take a sample for a proof (D17), and a sentence describing
one entry's repetitions as another's misleads on exactly the entry D150 found overstated. (B) stays true
and leaves a reader to assume the synthesis's are the same. The expected figure has read $15.00 at D152,
$14.78 when the audit read it and $14.84 today, moved by re-recordings nobody edited the row for, which is
D74's argument: a quantity that decays by addition is rewritten so it cannot, and the test holds the figure
against whatever the log records. The specification's line makes the caveat's claim in the contract, so
correcting one and not the other would leave them disagreeing.

**Consequences / caveats** — the report changes by one sentence and the snapshot is regenerated with it;
no verdict, count or table moves, and the report still cites no decision. OB-17's obligation column keeps
its dated figures, which describe the day they were measured, and the closed phase-4 handover's item 2
keeps its pair (D53). Nothing mechanical ties the caveat's wording to how the synthesis is rendered: a
later change to the resample reaches the snapshot only if it also changes the report.

**Rule** — enforced by test:
`tests/test_report.py::test_the_report_matches_the_committed_snapshot_byte_for_byte` holds the caveat's
wording, and
`tests/test_reference_run.py::test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling`
holds the figure OB-17's evidence no longer quotes.

## D170 — The expected figure prices the retries its log recorded, and names a log recorded under another state

**Fork:** OB-33, the phase-4 audit's P4-16. D152's expected figure prices each entry's calls at the mean
first-attempt answer the reference log recorded, so it counts no informed retry, in calls or in lengths,
while the synthesis has spent retries in every recording: 8 across 160 first attempts in the committed
log. The input side's over-estimate covered the gap, which the audit called luck of the divisor rather
than the population. And the figure reads its lengths from whatever log sits at the reference path,
recorded under whatever rubric and template, which D152 stated as a limit: it goes stale without
refusing. The audit's closure named a retry share per entry, printed, and a stale log refused or flagged.
How retries are counted, what a stale log does, and whether the contract follows were the owner's.

**Options considered.**

For retries:

- **(A) A share on calls**: each entry's calls multiplied by one plus its retries over its first attempts
  in the same log, priced at that entry's first-attempt size, with every share above one printed.
- **(B) Retries at their recorded sizes**: the same share, with each retry priced at the mean retry input
  and output the log recorded.
- **(C) Leave them out, and say so.**

For a stale log:

- **(A) Print the figure and flag it**, naming the differences the way replay names them.
- **(B) Refuse the figure**, printing that it was not computed, with the differences.

For the contract:

- **(A) Amend the expected-cost requirement and its criterion** at 0.35.0.
- **(B) Change the code and the verifier's caveat only.**

**Decision: (A), (A) and (A)**, the owner's on 2026-09-14.

**Why** — on the committed log that day the figure read $14.84 without retries, $15.15 under (A) and
$15.13 under (B), against $14.15 recorded across every call: (B) buys two cents for a second set of means
to keep, and (C) leaves the one cost that is systematic on this rubric uncounted. A stale log's lengths are
still the only lengths there are, and refusing the figure would leave an operator with the ceiling alone,
the figure OB-17 found too far above the bill to read; naming the differences lets them weigh it. The
requirement described first-attempt pricing, which the figure no longer is, and the criterion ticked it.

**Consequences / caveats** — a retry is priced at its entry's first-attempt size, though it also carries
the rejected answer and the valid identifiers, so its input runs above that. The stale-log line compares
the rubric version and the template hash alone, so an entry edited under an unchanged version is not
named, as replay does not refuse it. The share is read from one recording, like the lengths beside it, so
a rubric whose answers change how often they are retried moves the figure only when it is recorded again.
The committed log is not stale, so the flag prints nothing today.

**Rule** — enforced by test:
`tests/test_cli.py::test_the_expected_figure_would_notice_recorded_retries_left_out`,
`tests/test_reference_run.py::test_the_retry_share_would_notice_the_retries_a_log_records_uncounted` and
`tests/test_cli.py::test_the_expected_figure_would_notice_a_stale_log_left_unflagged`, each re-derived by
`control-mutations.yaml`; and
`tests/test_reference_run.py::test_the_expected_cost_sits_between_what_the_reference_run_spent_and_the_ceiling`
holds the figure per entry between what every recorded call cost and the ceiling.

## D171 — The severity loader refuses a cut the tool could not draw, and a band its cuts contradict

**Fork:** OB-25, the remaining half of the phase-4 audit's P4-5. D156 has the loader re-derive each cut's
between-set and gap from the file's own `theta`, and nothing else about a cut: an inverted cut, a cut
anchored on one finding at both ends and a cut named `nonsense` were each accepted, consistent with its
rows, while the producing tool refuses all three and more. And the band a row carries is, in the tool,
the side of the cuts' midpoints its `theta` falls on, which this repository never compared: the
re-verification moved F-29's `theta` across `medium_low`'s midpoint, still strictly between that cut's
anchors, with its band left `medium`, and the loader, the gap and between-set checks and both pins on the
committed file all passed. Which cut shapes to refuse, whether to compare bands, and whether the contract
follows were the owner's.

**Options considered.**

For cut shapes:

- **(A) Everything the tool refuses**: a name outside the three, a name stated twice, an inverted or
  single-anchor cut, a missing cut and midpoints out of severity order, so an empty or partial list is
  refused too.
- **(B) Only P4-5's three shapes**: inverted, single-anchor and unnamed, keeping a partial or empty list
  legal and skipping the band check for a file without all three cuts.

For bands:

- **(A) Refuse a row whose band its `theta` and the midpoints contradict**, as a between-set is refused.
- **(B) Keep the committed file's band pin alone.**

For the contract:

- **(A) Amend the specification's severity sentence** at 0.36.0.
- **(B) The decision record and the loader's docstrings only.**

**Decision: (A), (A) and (A)**, the owner's on 2026-09-14.

**Why** — the tool's `export` bands through `place`, which refuses a store with no cuts and passes the ones
it has through `thresholds`, and then writes those same cuts beside the bands: every file it exports
carries all three, drawn as `thresholds` allows. A loader accepting less accepts a file the export cannot
write, and (B) would keep accepting exactly the partial file under which no band can be checked. The band
comparison is D156's idiom one rule over: the file carries every `theta` and every cut, so each band is
recomputable, and comparing it on load makes a hand edit and a drift between the two definitions the same
red. The band pin sees a band change between exports; it cannot see a file that disagrees with itself,
which is what the re-verification's F-29 was. The specification's sentence named what the harness refuses,
and the harness now refuses more.

**Consequences / caveats** — the tool's rule is restated here, its band and cut order and its tie to the
less severe side, as a second definition compared against the tool's output on every load rather than
imported, as D148 and D156 did. A band outside the vocabulary is left to the join, which names it as one,
and the band check skips it. The committed file passes every new check: its three cuts are named and in
order, no anchor pair is inverted, the midpoints descend, and all 83 rows sit in the band their `theta`
gives, none on a midpoint. The small test fixtures now score four findings with all three cuts drawn, and
three findings were added to the small findings document so the join stays total over them; the cut tests
keep their shapes on two more findings inside `high_medium`. A re-export that re-bands a finding
consistently still passes the loader and fails the band pin, and stopping it at the source stays OB-23's.

**Rule** — enforced by test, each re-derived by `control-mutations.yaml`:
`tests/test_findings.py::test_the_cut_check_would_notice_a_cut_named_outside_the_three`,
`tests/test_findings.py::test_the_cut_check_would_notice_a_cut_named_twice`,
`tests/test_findings.py::test_the_cut_check_would_notice_an_inverted_or_single_anchor_cut`,
`tests/test_findings.py::test_the_cut_check_would_notice_a_missing_cut`,
`tests/test_findings.py::test_the_cut_check_would_notice_boundaries_that_have_crossed`,
`tests/test_findings.py::test_the_band_check_would_notice_a_row_on_the_wrong_side_of_its_cuts_midpoint`,
`tests/test_findings.py::test_the_band_check_would_notice_a_row_on_a_midpoint_banded_up` and
`tests/test_findings.py::test_a_band_outside_the_vocabulary_is_refused`.

## D172 — The design store is rewritten to LF and re-exported, and two provenance fields move after the freeze

**Fork:** OB-26, the phase-4 audit's P4-9, in `comparative-judgment`: its writers named no line ending and
`log_hash` hashed the log's raw bytes, so the same judgments recorded on another platform would name a
different `comparison_log_hash` and `run_id`. This repository's store measured it: CRLF on every line of
all four files, 417 on the log alone, and a committed `comparison_log_hash` equal to the hash of those
CRLF bytes. The tool's half is its D35. This repository's half was what to do with a store and a
committed export that the fix leaves naming a hash the fixed tool no longer computes, after the
`rubric-frozen-v1` tag. Both were the owner's.

**Options considered.**

For the scope:

- **(A) Full closure, backed up**: the tool's fix, then this store backed up, rewritten to LF once with
  every parsed record compared, and re-exported.
- **(B) The tool's fix only**, leaving the store and the committed file, whose hash then matches no value
  the fixed tool computes for this store.
- **(C) Defer past phase 5.**

For the re-export, after the tag:

- **(A) Commit it if only the two provenance fields move**, compared field by field first.
- **(B) Hold it** until the severity scale next changes.

**Decision: (A) and (A)**, the owner's on 2026-09-14. The re-export was held until the held-out
session's message had been read; as that message reports it, the held-out gate reads only the tag's
`rubric.yaml`, the default template's path in `cli.py`, `prompt.py` and the template, and none of them
is this file.

**Why** — the tag freezes the instrument the held-out run is judged by, and this file's provenance is not
part of it: no band, `theta`, row or cut moves, and a log hash that names the same log on every platform
is the claim the file exists to carry. Leaving the committed hash over CRLF bytes would have the fixed
tool and this repository's file disagree about one log, which is P4-9 moved rather than closed.

**Consequences / caveats** — the store was backed up before its rewrite, and every file's parsed content
was compared before any file was written; the fixed tool computed the same log hash before and after the
rewrite, and the export left the log's bytes as they were. The committed file moved on two lines,
`comparison_log_hash` to `d986b624…` and `run_id` to `b201280f737665e7`, with every row, cut,
`calibration` and `unplaced` unchanged. Nothing in this repository pins either value. A held-out severity
store, if phase 5 needs one, is created under the fixed tool, so its hash names the same log on every
platform from its first comparison.

**Rule** — enforced by test:
`tests/test_findings.py::test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors` and
`tests/test_findings.py::test_the_real_severity_file_pins_every_scored_findings_band` hold what the
re-export did not move; the tool's D35 names the tests that hold its fix.

## D173 — A held-out run names the labels manifest it is scored against

**Fork:** the held-out repository seals its labels before the held-out judged run and reveals them
after it, and its CI gate checks that order over git history. As that repository's session reported
it on 2026-09-14, the gate accepts a held-out run's log only if its header names, as `labels_manifest`,
the full SHA of the held-out commit that last touched the labels manifest before the log was committed
there. D26 decided the run log's header records that SHA, and nothing in this harness could write it:
`RunLogHeader` had no such key, and no run could tell whether it was held out. The session's message
set this as the first link this repository owes the chain, and left four forks open, with a fifth
about the contract found while recording it. All five were the owner's.

**Options considered.**

For recognizing a held-out run:

- **(A) Any call `HELDOUT_SET` declares**, a run mixing declared and undeclared calls refused, and a
  root with no `HELDOUT_SET` refusing every judged run.
- **(B) The same, with a missing file read as declaring nothing.**
- **(C) The flag itself**, with no membership check.

For where `--labels-manifest` is required:

- **(A) Every mode a held-out judged run can take** — live, resume and replay, since a replay writes
  its own log — refused on a run over no declared call, and checked for its shape alone.
- **(B) Live and resume only.**
- **(C) Optional everywhere**, with a warning.

For staleness:

- **(A) `differences_from` does not compare it.**
- **(B) Compare it**, which puts a mismatch under `--allow-stale-replay`'s override on a replay.

For a replay or a resume reading an earlier log:

- **(A) The flag must match that log's header**, which must name a manifest.
- **(B) Inherit the log's manifest**, with no flag.
- **(C) Take the flag as given.**

For the contract:

- **(A) A `[P5]` requirement and criterion**, the requirement mapped in the coverage table.
- **(B) The existing manifest criterion amended**, with no requirement.
- **(C) This entry alone.**

**Decision: (A) in all five**, the owner's on 2026-09-14.

**Why** — recognition reads the calls rather than the operator: a flag that made a run held out would
be a flag forgotten, and the gate refuses the log that leaves only after its calls were paid for. For
the same reason a root with no `HELDOUT_SET` is refused rather than read as empty, at the cost of an
adopter giving the file no identifiers. A held-out log holds held-out calls alone, so a mix is refused,
and a design run is refused the flag so that a manifest in a header marks a held-out log and nothing
else. The manifest changes no prompt, so it cannot make an answer stale; comparing it in
`differences_from` would have put a mismatch under an override, so a log naming other labels is
refused on its own terms instead. Only the shape is checked, because this repository cannot see the
held-out one and the gate checks the rest. The contract gains a requirement because the flag is
behavior of this harness, which D157's decision not to write requirements for another repository's
checks does not reach.

**Consequences / caveats** — `RunLogHeader.labels_manifest` is written only when set and read back with
an empty default, as D153's `resumed_from` is, so every design-set log is byte for byte what it was.
`harness report` writes no run log and takes no flag, and keeps `load_replay_transport`; `harness run`
reads a replayed log through `recorded_answers` so its header can be compared. The comparison is whole,
so a run naming no manifest is refused a log naming one as well. Every test declares design calls in a
`HELDOUT_SET` of its own and names invented SHAs, and none reads or writes a held-out transcript, run log
or label. What the gate checks is recorded as reported; nothing in this repository can verify it.
Where a held-out run reads its transcripts and writes its log, and an absence check refusing a held-out
log in this tree, are the next link and not this one.

**Rule** — enforced by test: `tests/test_transport.py::test_a_header_carries_the_labels_manifest_a_held_out_run_names`,
`tests/test_transport.py::test_the_manifest_check_would_notice_a_log_naming_other_labels`, and the eight
tests in `tests/test_cli.py` from `test_a_held_out_replay_writes_its_labels_manifest_into_the_log` to
`test_a_held_out_resume_would_notice_a_log_naming_other_labels`; 13 entries in `control-mutations.yaml`
drive them red.

## D174 — A held-out run keeps its paths, and its log, out of this tree

**Fork:** a held-out run reads transcripts that must never be in this tree and writes a log that must
never be written into it, and nothing prevented either. `--transcripts` and `--run-log-dir` default to
paths inside the checkout — the log to `runs/`, where `.gitignore` re-includes any `reference-*.jsonl` —
and `tools/check_holdout_absence.py`, the only mechanism protecting the held-out set, finds a transcript
by its format marker in a file's first 64 KB and skips any file over 2 MB. A run log carries no marker,
and a design-size one is 2,532,087 bytes, so a held-out run's log in this tree would have passed the
check twice over. The held-out repository's session named both halves as the second link this
repository owes the chain. Three forks were the owner's, and a fourth, about the contract, was found
while recording them.

**Options considered.**

For a held-out run's own paths:

- **(A) Refuse all four** — `--transcripts`, `--run-log-dir`, `--run-log` and `--resume` — when one
  resolves inside the repository, before anything is written.
- **(B) Refuse `--run-log-dir` alone**, the one path a run writes to.
- **(C) No refusal in the harness**, leaving the absence check to report a log once it is written.

For what the absence check recognizes as a held-out run log:

- **(A) Records, in any file**: a header naming a labels manifest, or a call record for a call
  `HELDOUT_SET` declares, on any line.
- **(B) Only files that begin with a run-log header.**
- **(C) The header's manifest alone.**

For how much of a file that reading covers:

- **(A) Whole files**, with no size cap and no window.
- **(B) The transcript scan's cap and window.**
- **(C) Whole files for `.jsonl` only.**

For the contract:

- **(A) A clause in D173's requirement, a `[P5]` criterion beside D173's, and a sentence on run logs
  appended to the absence criterion**, with `tools/verify_phase1.py` running the new tests under that
  criterion.
- **(B) Clauses only**, in D173's requirement and criterion.
- **(C) This entry alone.**

**Decision: (A) in all four**, the owner's on 2026-09-14.

**Why** — a held-out run's log holds the prompts its calls' transcripts were rendered into and the
judge's answers to them, so it is held-out content wherever it sits. D2's point is that only physical
absence protects without depending on obedience, and a log written wherever a flag happens to point
depends on it. Refusing all four paths closes the one route by which the harness itself would carry
held-out content into this tree or read it from here, and the absence check stays the backstop for
every other route. Records mark a log wherever it is pasted, which is the absence check's own argument
for looking for a transcript anywhere in a file, and a design log matches neither record: its header
names no manifest (D173) and its calls are design calls. The cap and the window exist to keep the
transcript scan out of blobs, and a run log is the blob this reading is for; the tree today holds 185
non-binary files and 17.7 MB, and the only two over the cap are run logs.

**Consequences / caveats** — the refusal compares each path with the root the harness resolves its
defaults from, which is the checkout for an editable install and the working directory for a harness
installed from a wheel, and it decides whether a run is held out from D173's call ids alone. The
absence check now reads every non-binary file whole, and reports a held-out log in a held-out
transcript's words. Its tests plant invented records in a temporary directory and build each line when
they run, because a record written into a test file on one line would make that file carry what the
scan looks for; wherever a test makes a held-out run, the design transcripts are copied out of the
checkout first. `harness report --out` can still write a report over held-out calls into this tree,
and reports are the next link's. `sessions/HOLDOUT-REPAIR-BRIEF.md` quotes the check's former OK line
and is left as written, being a record.

**Rule** — enforced by test: `tests/test_cli.py::test_a_held_out_run_would_notice_a_path_inside_the_checkout`,
`tests/test_cli.py::test_a_held_out_resume_would_notice_its_log_inside_the_checkout`, and the five tests
in `tests/test_holdout_absence.py` from `test_a_held_out_run_log_is_found_by_its_header` to
`test_the_check_reports_a_held_out_run_log_in_the_tree_it_scans`; 13 entries in `control-mutations.yaml`
drive them red.

## D175 — Agreement is counted per rubric entry, with the design set and the held-out set apart

**Fork:** phase 5's one requirement asks for judge-versus-human agreement reported separately for the
design set and the held-out set, each with its denominator, and nothing in this repository computed
agreement: it lived in tests, as the deterministic families' firing tables, with every judged entry
declared pending in `JUDGED_AGREEMENT_PENDING`. The held-out repository's session set out the held-out
half's format — labels in the gold set's findings format with `HF-NN` ids, and a `traces.yaml` of four
keys playing the part the rubric's `traces_to` plays for the design set (D105, D125) — and asked for it
built now, against invented fixtures, to run after the reveal. Eight forks were the owner's.

**Options considered.**

For what agreement counts:

- **(A) Both directions per entry**: hits and misses on the calls carrying a traced finding, false
  alarms and correct silences on every other call, over each set's call count.
- **(B) Recall only.**
- **(C) Per finding only.**

For when a judged entry fires:

- **(A) The gate's reading**: the call's modal verdict is one the entry counts against its gate (D158,
  D160).
- **(B) Any repetition violating.**
- **(C) A strict majority of repetitions violating.**

For where agreement is computed:

- **(A) A new `harness agreement` command**, printing the two sets apart.
- **(B) A section of `harness report`.**
- **(C) A library function only**, with the command left for after the reveal.

For `traces.yaml`:

- **(A) Re-checked on load** against every invariant its validator states, and refused when one breaks.
- **(B) Trusted to the held-out validator.**
- **(C) Its shape checked alone.**

For the frozen commit a `traces.yaml` must name:

- **(A) A pinned constant**, compared with the tag by a test.
- **(B) Resolved through git** each time the file is loaded.
- **(C) Passed as a flag.**

For the command's interface:

- **(A) One run**: the design section always, and the held-out section only when all five held-out
  inputs are given.
- **(B) One set per run**, chosen by a flag.
- **(C) The library now, and the command later.**

For a call an entry gave no verdict on:

- **(A) Counted apart**, by status, beside the four.
- **(B) Counted as silence.**
- **(C) Refusing the run.**

For the contract:

- **(A) The agreement requirement amended with what is counted and refused**, and a `[P5]` criterion
  for the command.
- **(B) Clauses only.**
- **(C) This entry alone.**

**Decision: (A) in all eight**, the owner's on 2026-09-14 and 2026-09-15.

**Why** — agreement is a claim about two directions at once. An entry firing on every call catches
every traced finding, so recall alone rewards the entry that separates nothing, and the fifth count
keeps a call the entry could not judge from reading as a correct silence. Reading a judged entry the way
its gate does means agreement measures the verdict the harness acts on. The command is the
specification's "its own deliverable", and replaying recorded runs keeps it free of a key, as
`harness report` is. The labels are re-checked because a file that drifted after it was sealed is what
a check at the point of use exists to notice, and the frozen commit is pinned so the command needs no
clone, with a test that fails if the tag ever points elsewhere. The design section is printed beside
the held-out one and never pooled with it: the design findings were adjudicated with some judge output
in view, F-90 among them, so for a judged entry it is not the blind agreement D21 asks for.

**Consequences / caveats** — before the reveal the command prints the design section and says the
held-out section was not computed, and `JUDGED_AGREEMENT_PENDING` stays as it is, because nothing held
out has been scored. A key duplicated inside `traces.yaml` collapses silently when the YAML loads, as it
does in the findings file and the rubric, and is not among the invariants re-checked. The held-out
inputs are refused inside the checkout, as a held-out run's paths are (D174). The tests invent labels
with `HF-` ids on design calls and split the design corpus into a design half and a held-out half
declared in a `HELDOUT_SET` of their own, so no held-out transcript, run log or label is read. The
test comparing the pinned commit with the tag runs git, so it is not a registered control: the control
gate runs in a copy of the tree with no `.git`, and the comparison the command relies on is driven by a
planted `traces.yaml` instead.

**Rule** — enforced by test: the six tests in `tests/test_agreement.py`, and the nine in
`tests/test_cli.py` from `test_agreement_would_notice_its_design_section_miscounted` to
`test_agreement_would_notice_a_replay_that_stopped_part_way`; 30 entries in
`control-mutations.yaml` drive fourteen of them red.

## D176 — A phase-5 verifier runs while its phase is open, declaring what it cannot tick

**Fork:** the held-out repository's session asked for a phase-5 verifier that cites the held-out gate
rather than re-deriving it. No earlier phase had a verifier before it closed, and the shared reporting
loop had no way to carry a criterion it cannot run: an entry naming no test and no command reads
`NO EVIDENCE`, which fails, and a test refuses such an entry outright. Of phase 5's nine criteria, four
are built here, three are asserted by the held-out repository's gate over a history this repository
cannot read — the label ordering, the frozen-commit citation and the manifest's recomputation — and
two, the coverage report by severity, are not built yet. Three forks were the owner's.

**Options considered.**

For the three criteria the held-out gate asserts:

- **(A) Declared, never ticked**: listed under their own heading as asserted by the held-out
  repository's gate, counted apart from passes, with the binding test accepting a declaration in place
  of an entry.
- **(B) Ticked on this repository's half**, with a caveat naming the gate.
- **(C) Left with no evidence**, reporting phase 5 incomplete for as long as the verifier exists.

For the criteria not built yet, and CI:

- **(A) Declared pending by the same mechanism**, with the verifier in `VERIFIERS` and in CI now,
  exiting 0 while every other entry passes.
- **(B) Kept out of `VERIFIERS` and CI** until every criterion is built.
- **(C) In CI and red** until the coverage report exists.

For the records:

- **(A) The specification's verifier sentence and the README's verifier commands amended** to name
  the fifth verifier, with this entry.
- **(B) This entry alone.**
- **(C) The README alone.**

**Decision: (A) in all three**, the owner's on 2026-09-15.

**Why** — a tick claims evidence this repository produced. Ticking a criterion on a neighboring test's
evidence is the shape this project has refused before, and a criterion reading `NO EVIDENCE` forever
would teach a reader to ignore the verifier's failure. A declaration says what is true: where the check
lives, or that it is not built. Refusing a criterion both ticked and declared keeps a declaration from
outliving the build that replaces it, and pinning phase 5's five declarations by name makes a sixth a
decision rather than a drift. Running the verifier in CI from today binds its list to the
specification now, which a verifier kept out of CI until its phase closed would not.

**Consequences / caveats** — `Declared` sits beside `Criterion` in `tools/verify_phase1.py`, with its
two kinds and the list of places a criterion may be asserted elsewhere, which names the held-out
repository's gate alone. The loop prints declarations under their own heading and counts them by kind
in its closing line; no phase before 5 declares any, so their output is unchanged. What the held-out
gate checks is recorded as that repository's session reported it, and nothing here runs it. The two
coverage criteria stay declared until the coverage report is built, and the test refusing a criterion
both ticked and declared is what retires their declarations then.

**Rule** — enforced by test: the phase-5 row of `VERIFIERS` in `tests/test_phase3_acceptance.py`, with
`test_every_tagged_criterion_is_claimed_by_its_verifier`, `test_no_criterion_is_both_ticked_and_declared`,
`test_every_declaration_names_a_criterion_and_its_reason` and
`test_phase_5_declares_the_gate_asserted_criteria_and_the_unbuilt_report`; 10 entries in
`control-mutations.yaml` drive their controls red.

## D177 — The held-out label chain, recorded with what this repository supplies and what is still owed

**Fork:** on 2026-09-14 the held-out repository's session set out the chain its labels move through
and asked this repository for seven things. D173 to D176 built the four links this repository
supplies: the `labels_manifest` header key, a held-out run kept out of this tree, agreement counted
for each set apart, and a phase-5 verifier declaring what the gate asserts. Three forks remained the
owner's: where the rule against searching the held-out labeling sessions lives, whether phase 5 needs
held-out severity, and how the chain is recorded here.

**The chain, as that session reported it.** Nothing in this repository runs the gate or reads that
repository, so every step below is recorded as reported rather than verified.

- **C1** commits the labels manifest, salted digests of the held-out findings and traces, with the
  trailer `Rubric-Frozen: <F>`, where F is the commit `rubric-frozen-v1` points at.
- **C2** commits the held-out judged run's log, produced by this harness, unmodified, and it never
  changes after. The gate accepts it only when its first non-blank line is this harness's header
  record, its `labels_manifest` is the full SHA of the commit that last touched the manifest before the
  log was committed, its `rubric_version` is the rubric's version at F, and its `prompt_template_hash`
  is what F's own code computes for its default template.
- **C3** reveals the plaintext labels with the trailer `Judged-Run: <C2>`.

**Options considered.**

For the rule that no session searches the held-out labeling sessions before the reveal:

- **(A) A standing duty in `HOLDOUT-OBLIGATIONS.md`**, beside `HELDOUT_SET`'s, carried into each new
  session prompt and handover when they are written; the phase-3 and phase-4 prompts stay as records
  of the sessions they started.
- **(B) The same sentence added to the four phase prompts.**
- **(C) A phase-5 session prompt written now** to carry it.

For held-out severity:

- **(A) A separate held-out store**: a person places every held-out finding in its own
  comparative-judgment store outside this tree before the held-out judged run, sealed in a form the
  gate can check and revealed with the labels, and the coverage report bands each set apart.
- **(B) Design-set bands only**, with held-out results left per rubric entry.
- **(C) Decided when the coverage report is built.**

For the records, four forks: **(A)** two open register entries, O-9 for the chain and O-10 for
held-out severity, rather than one; **(A)** the held-out repository's port of D101's name check as its
own entry, O-11, rather than a note under O-8 or a paragraph here; **(A)** the two sentences saying the
held-out labels do not exist restated as the rule they carried rather than struck through; and **(A)**
the two coverage criteria amended now to name the sets apart rather than when the report is built.

**Decision: (A) throughout**, the owner's on 2026-09-15. The rule landed on its own at `0a317fa`.
Held-out severity was put twice: the first ask listed (B) first, and the owner asked why before
choosing.

**Why** — the rule binds sessions that have not started, so it lives in the register every session on
the chain reads rather than in prompts that record sessions already run, and it went in alone because
a rule for other sessions binds nobody until it is pushed. For severity, the first recommendation
rested on scope and cost and undersold the separate store: the rubric was written against the design
findings, so per-band coverage over the design set is in-sample, and the held-out set is the only
place an uncovered severe finding would be news — the concentration D157 says the report exists to
show. A separate store's cuts are its own, so a held-out band orders severity within that set and is
not a design-set band; that limits comparison across the sets, not the reading D157 wants within one.
And held-out severity is clean only if it is scored and sealed before the held-out judged run: after
it, whoever orders the findings can see which ones the judge missed. For the records, entries ticked by
different acts at different times stay apart; the port is a convention the held-out set was brought
into line with, which is what the register records; a rule restated stays true whether or not labels
exist yet, which this repository cannot know; and the contract is what a builder reads, so the sets
are named there as well as here.

**Consequences / caveats** — O-9 is ticked when C3 lands with the gate green and O-10 once the
severity file is sealed before C2, and nothing here can confirm either tick. O-11 names no session id,
because the message reporting the port gave none. When the coverage report is built it reads a second
severity file from outside this tree after the reveal; until then both coverage criteria stay declared
not yet built by `tools.verify_phase5`, and their amended text keeps the phrases those declarations
anchor on. Severity bands are labels (D10), so nothing about the held-out bands is recorded here
before the reveal, as nothing about the held-out labels is (D61).

**Rule** — enforced by test for this repository's links, by the tests D173 to D176 name; the gate's
assertions are declared rather than ticked, and
`tests/test_phase3_acceptance.py::test_phase_5_declares_the_gate_asserted_criteria_and_the_unbuilt_report`
pins those declarations. The register's entries are tick-only, as every entry there is.

## D178 — The interface scanner reads each list from the sentence that enumerates it

**Fork:** OB-34, the phase-4 audit's P4-17. `tools/check_spec_interface.py` counted a backticked name
found anywhere in either side's documents, and the tool's pushed specification once named `cuts` only
as a subcommand, in two acceptance criteria, so the scanner reported agreement on a field the tool's
field list did not carry. A field renamed on the producing side would have gone on agreeing for as
long as a command of the old name existed. The instance is gone, because the tool's field list now
names `cuts`; the rule that let it through was still in place.

**Options considered.**

- **(A) Match inside each field list.** In each side's specification, find the one sentence that
  enumerates each list — findings keys, top-level severity fields, row fields — and compare the exact
  sets, failing when a sentence is missing or its opening phrase is stated twice. This specification's
  row sentence names `id`, `severity` and `theta`, which it had called the band. Nothing changes in the
  tool repository.
- **(B) A machine-readable field block on both sides**, compared exactly: sturdier against rewording,
  and a matching change, version and push in comparative-judgment as well.
- **(C) Record the limit only**, and change no code.

**Decision: (A)**, the owner's on 2026-09-15.

**Why** — the tool's specification already carries its field list the way (A) reads it, and says why:
the list "is enumerated here rather than described, because the consuming harness reads provenance
from it". (B) would put a second statement of each list in both repositories, which is the drift this
scanner exists to catch, and (C) keeps a green check narrower than its rule. Reading a list from its
sentence also turns rewording into a failure rather than a pass: an opening phrase that no longer
occurs, or occurs twice, is a disagreement.

**Consequences / caveats** — the lists are read from the first file named on each side, which CI and
the live-document test both name as the specification. The ownership claims and the stale cross-claims
still read every file, so a decision record repeating a stale assertion still fails, while a key named
only in a record no longer counts for a list; the test that asserted it did now asserts the opposite.
Each list sentence is found by a literal opening phrase, so a list reworded in the tool repository
turns this repository's build red until the phrase here follows it — the intended failure, and a cost
the tool's sessions now carry. The new controls are module-level functions, because
`tools/verify_controls.py` addresses a control as `<module>::<name>`.

**Rule** — enforced by test:
`tests/test_check_spec_interface.py::test_a_field_named_only_outside_its_list_does_not_count`,
`test_a_list_sentence_that_is_gone_fails_and_names_it`, `test_a_list_sentence_stated_twice_fails`,
`test_an_extra_name_in_a_list_fails_and_names_it` and
`test_the_harness_specification_lists_exactly_what_the_scanner_reads`; 12 entries in
`control-mutations.yaml` drive their controls red.

## D179 — The informed retry names every fault an answer shows, not the first

**Fork:** OB-36, the phase-4 audit's P4-30. `_validate` returned at the first fault it met — the parse,
then the citations, then `rests_on` — so a synthesis answer citing `T999` with an empty `rests_on` was
sent a retry naming `'T999'` alone, and one with both lists empty a retry naming the empty `citations`
list alone. A retry that fixed the named fault and kept the other was refused, and the result was
`errored`: the one retry the requirement grants, spent on half a correction. The committed log holds no
such answer; its 8 retries each corrected rejected identifiers and nothing else. Three forks were the
owner's.

**Options considered.**

For how a correction names several faults:

- **(A) Each in its existing wording**: the rejected-identifier sentence first, then the schema
  sentence naming every schema failure joined by "; ", so a single fault's correction is unchanged
  byte for byte, and a synthesis with any schema failure among its faults is shown its dimensions.
- **(B) One combined sentence** for two or more faults, a third wording no recorded request pins.

For what the validation collects:

- **(A) Every fault it can read**: invalid JSON or a value that is not an object still stops at once;
  otherwise every missing field, a `citations` or `rests_on` that is not a list, an empty
  `citations`, rejected identifiers and an empty `rests_on` where one is required.
- **(B) Only P4-30's two cases.**

For the contract:

- **(A) Amend the `[P3]` requirement's second clause** to name every failure found, with the retry
  criterion covering an answer with two faults.
- **(B) This entry alone.**

**Decision: (A) in all three**, the owner's on 2026-09-15.

**Why** — D164 chose to name the schema failure that occurred, whichever it was; stopping at the first
of several is the same shortfall one level up, and a correction naming half the faults spends the
retry the requirement grants on an answer it has already said it will refuse. Keeping each wording
keeps the one guarantee the committed log can check: a retry for rejected identifiers alone is the
byte-identical request the log recorded, so a replay still serves it. And the requirement said *the
parse failure*, singular, so the behavior it now describes would otherwise have gone unstated.

**Consequences / caveats** — `read_answer` reads a response's text and records every schema failure
beside the citations and `rests_on` it could read, and `parse_answer` stays for callers that want the
first refusal. `_validate` computes rejected identifiers from whatever citations were readable, even
when another field is missing, and finds an empty `rests_on` whatever else failed. An `errored` result's
last failure names every fault the retry still showed, the identifiers first. Three mutation entries
whose lines moved with the rewrite keep their defects and controls under new finds.

**Rule** — enforced by test:
`tests/test_judge_engine.py::test_the_retry_would_notice_a_second_fault_it_does_not_name`,
`test_the_retry_would_notice_an_empty_citations_list_hiding_an_empty_rests_on`,
`test_the_retry_would_notice_rejected_identifiers_beside_a_missing_field`,
`test_an_exhausted_retry_would_notice_a_fault_left_out_of_its_last_failure` and
`tests/test_judge_prompt.py::test_every_readable_fault_is_named_not_the_first`; 7 new entries in
`control-mutations.yaml` drive their controls red.

## D180 — A verifier's caveat states what its tick does not buy, and nothing else

**Fork:** OB-35, the phase-4 audit's P4-18. The shared loop prints caveats under "NOT FULLY CHECKABLE
BY MACHINE — read these rather than the ticks", and most of the phase-4 verifier's said when a
criterion was added rather than what its tick does not buy: of its 18, 6 stated a limit, 3 how a test
works, and 9 the decision a criterion was added at and why. The same shape sat in the other
verifiers, mostly beside a limit: 6 of phase 3's 8, 2 of phase 1's 4 and 1 of phase 2's 2, while phase
5's 4 were limits already. A reader who learns that most caveats are provenance stops reading the ones
that are not. Three forks were the owner's.

**Options considered.**

For what a caveat holds:

- **(A) Limits only**: when and why a criterion was added leaves the verifier for the decision that
  records it, a method note stays only where it explains a limit, and a criterion with nothing left
  carries no caveat.
- **(B) A separate origin field** on `Criterion`, printed under its own heading.
- **(C) The text kept and the section retitled.**

For scope: **(A) every verifier**, or **(B) phase 4 alone**, as OB-35 names it.

For a guard: **(A) a test over every verifier's caveats refusing the two history markers found**,
with a control, or **(B) the rule recorded and nothing refusing it**.

**Decision: (A) in all three**, the owner's on 2026-09-15.

**Why** — the section's heading promises that what it holds is what a tick leaves out, and a channel
that is mostly provenance teaches its reader to skip it, which is the argument D137 makes about a
ceiling printed far above the bill. The history is not lost: D130, D132 and the decisions beside them
record when each criterion was added and why. One rule for one channel reaches every verifier, and a
guard over phase 4 alone would hold it there while the same shape sat in phase 3.

**Consequences / caveats** — phase 4 keeps 6 caveats and phase 3 keeps 7, each rewritten to its limit;
phases 1 and 2 keep theirs with the history sentences cut, and phase 5's are unchanged. One phase-3
caveat said a dimension defect was "pinned rather than fixed" with the fix due at P4; D132 had fixed
it, so the sentence was stale as well as history. `HISTORY_MARKERS` refuses "Added at D<n>" and "until
<date>", the two shapes found: a history sentence carrying neither still passes, and no marker can
tell every one from a limit.

**Rule** — enforced by test:
`tests/test_phase3_acceptance.py::test_no_caveat_carries_the_history_its_decision_records` and
`tests/test_phase3_acceptance.py::test_the_history_check_would_notice_each_marker`; 3 entries in
`control-mutations.yaml` drive the control red.

## D181 — The held-out severity export's schema, stated so it can be checked before it is sealed

**Fork:** O-10 put the held-out bands in a comparative-judgment store outside this tree and left how
the file is sealed to the held-out session. That session has settled it — a third sealed file, carrying
a digest line in the labels manifest at C1 and published with the labels at C3, refused there if it is
missing, empty or not JSON and read no further — and asks what schema this repository expects it in,
since nothing checks the export before it is published and nothing may be edited after the reveal. The
cross-project audit of 2026-09-15 names the same gap from this side.

**Options considered.**

- **(A) State schema 3 as `harness.core.severity` pins it**, and name that module's loader as the check
  the held-out side runs before sealing, from the checkout its workflow already installs.
- **(B) State the schema in prose here**, and leave validating the export to that side.
- **(C) State it and add a subcommand** that validates a severity file.

**Decision: (A)**, the owner's on 2026-09-15.

**Why** — the loader is the schema: `SEVERITY_FIELDS`, `SEVERITY_ROW_FIELDS`, `BAND_ORDER` and
`_check_bands`, which re-derives every band from the cuts' midpoints and refuses a file that disagrees
with itself. Prose restating those lists is a second definition maintained by hand beside the first,
which is the drift D148 reversed between this repository and the interface scanner. A subcommand is a
new surface over a check that one import already performs, and `load_severity` raises there the same
refusals this repository will meet at the reveal.

**What that side is told** — the export carries `schema_version` exactly 3 and every field
`SEVERITY_FIELDS` names; one row per scored finding under `severities`, each carrying the fields
`SEVERITY_ROW_FIELDS` names, which are `id`, `severity`, `theta`, `content_hash`, `appearances` and
`informative`; a band from `BAND_ORDER`; and all three cuts in the same file, named as `CUT_ORDER`
names them, each carrying `name`, `above_id`, `below_id`, `gap` and `between`. Rows are keyed by `id`
and joined on it, as the design set's are. The file is a tool export rather than a hand edit, because
every band is re-derived from the cuts before it is accepted.

**Consequences / caveats** — `content_hash` is the hash of the finding text a band was placed on, and
this repository can recompute it only after the reveal, against the labels published then; text edited
after the export turns that check red rather than leaving a file describing wording nobody has, which
is the failure D140 records. Whether the scoring tool can key a second store on the held-out ids is
that store's question and is not settled here. Nothing about the bands is written in this tree before
the reveal (D61). The coverage report that reads the file is phase 5's, and `tools.verify_phase5`
declares it not yet built. Nothing in this repository changes for this decision.

## D182 — A held-out run carries the held-out set's own corpus version, from a file outside this checkout

**Fork:** `harness run` stamps `corpus_version` from `--corpus-version-file`, whose default resolves
inside this checkout, into every result's provenance and into the header the held-out side commits
unmodified; `harness agreement` requires a held-out corpus version file of its own. That repository has
none, so a run made on the defaults stamps the design corpus's version into a held-out header that is
committed once and never changes afterwards. The cross-project audit of 2026-09-15 names it, and the
held-out session asks what the value should be and where the file should live.

**Options considered.**

- **(A) The held-out set's own version string, in a file committed in the held-out repository** on its
  allowlist, with this repository refusing `--corpus-version-file` inside the checkout on a held-out
  run, as D174 refuses the four paths it names.
- **(B) The same string, in a file outside both trees**, named only in the held-out procedure.
- **(C) The harness corpus version as it stood at the freeze.**

**Decision: (A)**, the owner's on 2026-09-15.

**Why** — nothing compares the value: a replay is refused on the rubric version and the prompt
template hash alone, and the only rule on the string is that it is not blank. So this is a question of
what the header says rather than of what passes, and a held-out header carrying the design corpus's
version describes a corpus that run never read. A file the held-out repository commits can be
recomputed at the reveal by anyone reading that history; one outside both trees is audited by nothing
and can differ between the run and the agreement that scores it. Without the refusal, the defaults
quietly produce (C), which is the case this decision exists to prevent.

**Consequences / caveats** — `--policies` stays this repository's, and inside this checkout,
deliberately: both sets read the same policy documents, and refusing it would ask the held-out side to
keep a copy that could drift from them. `held_out_paths_inside` gains the corpus version flag, which is
a behavior change and lands with its criterion and its control rather than here.

## D183 — A held-out run's header names the rubric it judged under, and HEAD is pinned to the freeze

**Fork:** judged under the frozen rubric rests on `rubric_version` and `prompt_template_hash`. Neither
moves when an entry's question, criteria or scale text moves, and the template hash covers the prompt
scaffold's two sent halves rather than the entry text rendered into them. Nothing here compares
`rubric.yaml` or the prompt template at HEAD with the commit `rubric-frozen-v1` names. The held-out
session proposed a trailer on C2's commit message naming the harness commit a run was made at, with its
gate checking that the commit descends from the freeze, and offered to check a rubric content hash in
the header instead. The cross-project audit of 2026-09-15 names the same gap.

**Options considered.**

- **(A) Both halves**: a test pinning `rubric.yaml` and the prompt template at HEAD to the freeze
  commit, and a hash of the rubric written into a held-out run's header for that side's gate to compare
  with the freeze's.
- **(B) The test, with the trailer** that side proposed.
- **(C) The test alone.**

**Decision: (A)**, the owner's on 2026-09-15.

**Why** — descent does not carry identity: a commit descending from the freeze can have edited an
entry's text, so a trailer records which checkout ran and proves nothing about what it judged under.
The test closes drift on the branch, and a value in the header is the only thing that closes a run made
from an edited working copy, which no test in this repository can reach. Written only when a run is
held out, the field leaves every design log byte for byte what it was, the way `resumed_from` and
`labels_manifest` already are.

**Consequences / caveats** — the pin is a test rather than a control: the control gate runs in a copy
of the tree with no `.git`, which is what `test_the_pinned_frozen_commit_is_the_one_the_tag_points_at`
says about itself. The header gains a key both sides implement, so it lands with its criterion, its
control, and a statement of what is hashed: the rubric read as text with universal newlines and encoded
UTF-8, so a checkout whose line endings differ hashes as the freeze's blob does, which is the property
measured of the prompt template when the same question was asked of it. The trailer that side offered
is then not needed, and this decision says so rather than leaving both.

## D184 — This repository names a held-out run's log, rather than leaving a rename to a procedure

**Fork:** the writer names a log by its start time and its mode. The held-out repository's gate admits
a run log only under a `heldout-` prefix, so the owner renames the file between writing it and
committing it, and that side's procedure now says so. It offered the job to either side.

**Options considered.**

- **(A) This repository writes the prefix** on a run whose header carries a labels manifest, which is
  exactly a held-out run (D173).
- **(B) The rename stays a step in the held-out procedure**, recorded in O-9.

**Decision: (A)**, the owner's on 2026-09-15.

**Why** — the run already knows: `labels_manifest` is set on a held-out run and on no other, so the
name follows from a value the header carries rather than from a second determination that could
disagree with it. A step a person performs between writing a file and committing it is a step that can
be skipped, and the skip is silent until the gate reads the path, after the run has been paid for.

**Consequences / caveats** — a change in the writer's path, landing with its criterion and its
control. Design runs keep the names they have, so the committed reference log and the snapshots are
untouched.

## D185 — A report over held-out calls stays out of this tree, and the absence check reads one

**Fork:** `harness report` renders both tiers from a recorded log and writes the text wherever
`--out` points, creating directories as it goes. It reads no `HELDOUT_SET`, and its replay does not
check a labels manifest, deliberately: it writes no run log, so it has no header for one to go into.
So a report over held-out calls could be rendered into this checkout, and what it carries is every
call's verdicts and both tiers' roll-ups — the judge's answers on those calls, which D174 already
treats as held-out content when they sit in a run log. The absence check reads transcripts by their
format marker and run logs by their records, and would not have seen a rendered report. Found while
the cross-project audit of 2026-09-15 was being read, which checked the run and agreement commands
and did not look at this one; registered as OB-43.

**Options considered.**

For the command:

- **(A) Stdout, or a path outside this checkout**, refusing `--out` inside it over any call
  `HELDOUT_SET` declares, which is D174's rule for a held-out run's paths and D175's for
  agreement's held-out section.
- **(B) Refuse a report over held-out calls entirely**, from this command.
- **(C) Treat it as a held-out run**, requiring `--labels-manifest` as well.

For the absence check: **(A) read a rendered report as a third shape**, or **(B) leave the check to
transcripts and run logs**, with the command's refusal as the only control.

**Decision: (A) in both**, the owner's on 2026-09-15.

**Why** — the rule that already governs held-out output is where it may be written, not whether it
may exist: D174 keeps a held-out run's paths outside this tree and D175 prints agreement's held-out
section to stdout only. (B) would refuse a report phase 5 may want after the reveal, and (C) would
demand a manifest for a command that writes no header to put one in. The check earns its place for
the reason D2 gives and this tool's own docstring repeats: physical absence is the only protection
that does not depend on obedience, and a refusal inside one command is obedience — it is not
reached by a report rendered any other way.

**Consequences / caveats** — the refusal reads the calls the corpus holds, so a report whose
corpus names no held-out call is written wherever it is asked for, which is how `snapshots/report.md`
is produced. The check requires the renderer's heading **and** a declared call id together: the
heading alone sits in this repository's snapshot and in the renderer's source, and a call id alone
sits in every document naming one. A report that carries neither — a summary someone retyped, say
— is not reached by it, which is what the refusal is for.

**Rule** — enforced by test:
`tests/test_cli.py::test_a_report_over_held_out_calls_would_notice_an_out_path_inside_the_checkout`,
`tests/test_cli.py::test_a_design_report_is_still_written_where_it_is_asked_for`,
`tests/test_holdout_absence.py::test_a_rendered_report_over_held_out_calls_is_found` and
`tests/test_holdout_absence.py::test_a_design_report_is_not_mistaken_for_a_held_out_one`; four
entries in `control-mutations.yaml` drive the controls red.

## D186 — What the rubric hash is computed over, and who refuses a log that disagrees

**Fork:** D183 settled that a held-out run's header would name the rubric it judged under and that
`rubric.yaml` and the prompt template at HEAD would be pinned to the freeze. Building it left three
choices it did not make: what exactly is hashed, whether anything in this repository compares the
value or only the held-out repository's gate, and what the pin compares.

**Options considered.**

For who compares it: **(A) its own refusal**, as `check_labels_manifest` is — a replay or a resume
whose log names another rubric or none is refused here, with no override; **(B) written and read
back only**, leaving the comparison to that gate; **(C) folded into the staleness comparison**, where
`--allow-stale-replay` could lift it.

For what is hashed: **(A) the file read as text** with universal newlines and encoded UTF-8, or
**(B) its bytes**.

For the pin: **(A) both files compared as normalized text** against the freeze commit's blobs, or
**(B) the prompt template's own `sha256`**, which the header already carries.

**Decision: (A) in all three**, the owner's on 2026-09-16 for the first.

**Why** — (C) would put the strongest identity claim behind the one flag that exists to be
overridden, and (B) would leave this repository writing a value it never checks, so a log recorded
under one rubric and replayed under another would be caught only after the answers had been served
and only by a gate in another repository. Hashing bytes would report a rubric nobody changed as a
different one on a checkout with other line endings, which this project has already paid for once
(D172). And the template's `sha256` covers the scaffold's two sent halves rather than the file, so
pinning with it would pass over exactly the edit the pin exists to catch.

**Consequences / caveats** — `rubric_hash` is written on a held-out run and on no other, so every
design-set log is byte for byte what it was, as `resumed_from` and `labels_manifest` already are; the
committed reference log is unchanged. `RunLogHeader.differences_from` still compares two fields and
this is not one of them: the refusal is its own, for the reason the manifest's is. A run made from an
edited working copy is caught by the header value rather than by the pin, which reads what is
committed; the pin is a test rather than a control, since the control gate runs in a copy of the tree
with no `.git`.

**Rule** — enforced by test:
`tests/test_transport.py::test_a_header_carries_the_rubric_a_held_out_run_judged_under`,
`tests/test_transport.py::test_the_rubric_check_would_notice_a_log_judged_under_another_rubric`,
`tests/test_cli.py::test_a_held_out_replay_writes_the_rubric_it_judged_under`,
`tests/test_cli.py::test_a_held_out_replay_would_notice_a_log_judged_under_another_rubric` and
`tests/test_agreement.py::test_the_rubric_and_the_template_at_head_are_the_frozen_commits`; two
entries in `control-mutations.yaml` drive the controls red.

## D187 — Question-tier findings are not `unplaced`, and the coverage report names them

**Fork:** the held-out session asked what its export should do with the findings the scoring tool does
not score. In this repository's committed export, `severities` holds 83 rows and `unplaced` is empty,
and 7 findings appear in neither: F-27, F-31, F-49, F-54, F-56, F-59 and F-84, which are exactly the
question-tier ones. Per-band coverage cannot account for a finding the file does not mention, so the
question is whether `unplaced` should carry them.

**Options considered.**

- **(A) `unplaced` keeps its meaning**, and the coverage report counts and names the findings that
  carry no band.
- **(B) Every finding appears in one list or the other**, so an export omitting one is refused.
- **(C) A list of its own**, at a schema 4 both repositories would move to.

**Decision: (A)**, the owner's on 2026-09-16.

**Why** — the two cases have different causes and the file has one field for them. `unplaced` is for
findings in scope that nobody compared, which is why banding them would report the prior as though it
were a judgment; a question entry is excluded before scoring begins, because rating a non-defect would
put it in the anchor set and distort every later placement, which `Tier` says in as many words.
Merging them makes an empty `unplaced` unreadable: it would stop meaning *everything in scope was
compared*. (B) would also make this repository's committed export non-conforming until the tool
re-exported, and a re-export moves `comparison_log_hash` and `run_id` and can move bands (D144, D172),
which is a large price for bookkeeping. (C) unpins the one schema the loader accepts, in both
repositories, for a distinction the report can state in words.

**Consequences / caveats** — the coverage report counts and names the findings carrying no band
beside its per-band figures, so those 7 are visible rather than missing; the criterion says so and
`tools.verify_phase5` keeps declaring that report not yet built. Nothing in the export changes, and
the held-out side keeps the rule it has: every id its export names must be a finding of that set, and
coverage of every finding is not required. This says nothing about how many findings the held-out set
holds or which of them carry no band (D61).

## D188 — Coverage by severity is built, and a finding is retired when an entry traced to it fires on its call

**Fork:** phase 5's coverage criteria asked for findings *retired* by severity, per band and for each
set apart (D157, D177, D187), and no document said when a finding counts as retired. The build turned
on it, and on four forks this repository's rules left open: where a held-out section may go, which
command carries the report, whether the absence check learns its shape, and how the contract records
it. All five were the owner's, put before any code was written, with the design set measured under
each reading of *retired* and no held-out figure computed until one was chosen, so the definition could
not be picked with the held-out result in view.

**Options considered.**

For what makes a finding retired:

- **(A) Caught, with traced beside it**: retired when an entry traced to the finding fired on its
  call, read as agreement reads it, with the uncovered, traced to no entry, and the missed, traced and
  fired on by none, named apart.
- **(B) Traced only**: retired when some entry is traced to it and uncovered when none is, reading no
  transcript and no run log.
- **(C) Traced, with caught beside it**: retired read as traced, and a caught column for information.

For which command carries it:

- **(A) A new `harness coverage`**, reusing agreement's replay and its refusals.
- **(B) A section of `harness agreement`**, whose held-out inputs would go from five to six.
- **(C) A section of `harness report`**, moving the snapshot on purpose.

For where a held-out section may go: **(A) stdout only**, as agreement's goes (D175), or **(B) stdout
or a file outside the checkout**, as the report's may (D185).

For the absence check: **(A) a fourth shape**, the coverage heading beside a held-out finding's id, or
**(B) the command's rule alone**.

For the contract: **(A) one requirement in D175's shape**, stating what is counted and what is
refused, with a criterion for the command; **(B) a requirement for the output rule only**, in D185's
shape; **(C) none**, D157's stance.

**Decision: (A) in all five**, the owner's on 2026-09-18.

**Why** — traced is what the rubric aims at and caught is what it did, and the two part exactly where
the report is news: on the design set only at F-85, the judged miss `RECORDED_MISS` pins, since every
deterministic entry fires on its traced calls by construction; on the held-out set wherever an entry
aimed at a finding stays silent. The complement of *retired* is not one group. A finding no entry is
traced to is a gap in the rubric, and one an entry is traced to and did not catch is a failure of that
entry, and D187 refused to merge two causes into one field for the same reason. The taxonomy map
already uses *retired* for a weakness a check closes, on evidence the check produces rather than on a
mapping. A new command leaves agreement's criterion, its five inputs and the report's snapshot where
they are, and is its own deliverable as agreement is. Stdout alone is the rule of the nearest sibling
reading the same inputs, and a redirect into the tree is what no refusal inside a command reaches,
which is D185's reason for the absence check reading a shape. And once built, what the report counts
and where its held-out section goes are behavior: D157 kept the counting out of the requirements so
the stable half did not move for the table's sake, which does not describe behavior that exists.

**What the design set reads** — critical 3 of 4 retired, high 14 of 14, medium 27 of 28 and low 32 of
37, from the committed reference log and severity export. F-76, F-90, F-42, F-55, F-60 and F-89 are
uncovered, F-85 is missed, and the 7 question-tier findings carry no band, F-54 among them retired.
This is in sample, since the rubric was written against these findings, and the report says so beside
them. Nothing about the held-out figures is recorded here (D61, D175).

**Consequences / caveats** — retired is read per call, as agreement is, so an entry firing on a call
retires every finding traced to it there, though it may have fired for one of them alone.
`readings_for` leaves `set_agreement` so both commands read firing through one function, and the
held-out input refusals and the label check move into helpers both commands call, so agreement's
refusal of inputs given in part now says *every one of its inputs* where it said *all five*. A finding
on a call its set does not read is refused, which agreement's design section does not do: agreement
counts calls and may be given part of a set, while coverage counts findings, and a finding whose call
was never read is neither caught nor missed. The held-out path is tested over the design calls copied
under new ids, with a log recorded to hold the committed reference log's answers, because the
synthesis resamples by call id (D154) and a renamed call's synthesis prompt is a request that log never
saw; the invented labels are the design findings under `HF-` ids with F-04 left untraced, and their
severity export is the design export with every id moved the same way. The absence check reads a
held-out coverage section by the heading `harness coverage` writes at the head of a section, beside a
held-out finding's id, both together; a section retyped without its heading is not reached by it. The
held-out export's `content_hash` is not recomputed against the published labels, because the function
recomputing it lives in the suite rather than the harness.

**Rule** — enforced by test: the five tests in `tests/test_coverage.py`, the eight in
`tests/test_cli.py` from `test_coverage_would_notice_its_design_section_miscounted` to
`test_coverage_would_notice_an_out_flag_that_writes_a_file`, and
`tests/test_holdout_absence.py::test_a_coverage_report_over_held_out_findings_is_found`,
`tests/test_holdout_absence.py::test_a_design_coverage_report_is_not_mistaken_for_a_held_out_one` and
`tests/test_holdout_absence.py::test_the_check_reports_a_coverage_report_in_the_tree_it_scans`;
32 entries in `control-mutations.yaml` drive the controls red.


### Note, 2026-09-19 — a set with no banded finding cannot be covered at all

*Appended rather than woven in, as every correction here is: everything above is what was written at
the time (D53).*

The phase-5 audit's P5-10 drove a set whose every finding is question-tier, with a severity export
holding no rows, and the coverage report refused it: `the file states no cut critical_high,
high_medium, medium_low`. That is D171's rule, which requires all three cuts, meeting the coverage
requirement's clause about findings that carry no band — and the two do not quite fit, since three
cuts need four scored findings and a set with none has no cuts to state.

Left as it is, and recorded here rather than repaired. No set is near the case: the design set bands
83 of its 90 findings, and a held-out set with nothing scored would have nothing for this report to
say. The alternative, letting the loader accept an export with no cuts where no row is scored, widens
a refusal D171 wrote deliberately for a file that cannot describe itself.

## D189 — The content-hash recheck moves into the harness, and the coverage report refuses a band on moved text

**Fork:** D148 compared every design band's `content_hash` with the text of the finding it names, and
the comparison lived in the suite: `tests/test_findings.py` kept its own copy of the scoring tool's
hash. D188 left that as a caveat. The coverage report counted each set's findings under bands it never
checked against their text, and the held-out export, which D181 said this repository could check only
after the reveal, was checked by nothing here. The owner asked for the recheck in the harness, and
three forks followed.

**Options considered.**

For where it lives: **(A) its own function in `harness.core.severity`**, which the coverage report
calls for each set and the suite's test calls in place of its copy; or **(B) inside `join`**, so every
join refuses moved text, with the nine test call sites that join placeholder-hash fixtures rewritten
with real hashes.

For what the coverage report does on a mismatch: **(A) refuse the set**, naming each moved finding; or
**(B) print the moved ids beside the figures** and go on.

For the contract: **(A) amend D188's requirement and the command's criterion** with the refusal;
**(B) a requirement of its own**; or **(C) this entry alone**.

**Decision: (A) in all three**, the owner's on 2026-09-18.

**Why** — `join` is about which ids the two files name, and its one caller in the harness is the
coverage report, so placing the recheck inside it would guard no caller that could otherwise skip it,
at the cost of every fixture that joins a placeholder hash. One function is one definition in this
repository, and the suite reading it means the suite and the report cannot come to disagree about what
the hash covers. A band on moved text describes wording nobody compared, which is D140's failure, and
the loader already refuses a file that disagrees with itself; figures printed beside the refusal they
should have been would be read first. The recheck is one more refusal of the same command, so it goes
where that command's other refusals are and phase 5's counts do not move.

**Consequences / caveats** — both sets pass today: the design set's bands against the gold set, and
the held-out set's against the labels the held-out repository published at C3, read in place and not
recorded here (D61). D188's caveat that the held-out export's hash is not recomputed is superseded
rather than edited (D53). The definition is still a second one across two repositories, as D148
accepted: a drift from the scoring tool's reads as every band moved, which the suite's test is the
first to see. A finding with no band, question-tier or unplaced, carries no hash and is not rechecked.

**Rule** — enforced by test:
`tests/test_findings.py::test_the_recheck_would_notice_a_finding_edited_after_scoring`,
`tests/test_coverage.py::test_coverage_would_notice_a_band_on_text_that_moved`,
`tests/test_cli.py::test_coverage_would_notice_a_findings_file_edited_after_scoring` and
`tests/test_findings.py::test_every_scored_finding_still_matches_the_text_it_was_scored_against`; 7
entries in `control-mutations.yaml` drive the controls red.

## D190 — The design store's bands are assigned, so a refit proposes rather than relabels

**Fork:** OB-23, registered at D156 on the owner's decision: the producing tool's D2 promised that bands
are frozen at assignment and that a refit produces a proposed revision rather than relabeling a finding
this repository cites, and nothing in `comparative-judgment` specified or built it, so a refit relabeled
without saying so — which is what D144's placement did. Its trigger was the next session to record a
comparison into the store behind `corpus/findings.severity.json`. The tool's half is its D36, specified
at 0.10.0 and built at 0.10.1: `cj assign` records every banded finding's band in the append-only log
under a rater's name, a band the fit places otherwise is reported as a proposal, and `cj export` refuses
while one stands. This repository's half was what to do with a store holding no assignment, whose next
export the tool now refuses, after the `rubric-frozen-v1` tag. Both were the owner's.

**Options considered.**

- **(A) Full closure, backed up**: this store backed up, its current bands assigned once, and
  re-exported.
- **(B) The register row only**, citing the tool's D36 and leaving the store for the next scoring
  session, whose export would refuse until somebody assigned.
- **(C) A separate session for it.**

**Decision: (A)**, the owner's on 2026-09-18, with the assignment recorded under the rater `Saso Gale`,
the name on the store's four accepted revisions.

**Why** — (B) leaves the first export after the next scoring session to meet the refusal, and the bands
this repository already cites to be assigned by whoever happens to be exporting then. Assigning now
fixes those bands under the owner's name before anything can move them. As D172 found for its
re-export, the tag freezes the instrument the held-out run is judged by, and this file's provenance is
not part of it: nothing moves but `comparison_log_hash` and `run_id`.

**Consequences / caveats** — the store was backed up first, to a directory beside the checkout. The
tool at `920ae31` appended exactly one record to the log — seq 418, 83 bands, rater `Saso Gale`,
session `assign` — leaving the log's earlier bytes an exact prefix and the other three store files
unchanged, and a second `assign` wrote nothing. The committed severity file moved on two lines,
`comparison_log_hash` to `de34d674…` and `run_id` to `b5b6c281ec6d7c14`, with every row, cut,
`calibration` and `unplaced` unchanged. From here, a comparison that moves a banded finding is
reported as a proposal by `cj status` and `cj bands`, and `cj export` refuses until
`cj assign --accept-rebanding` accepts it. A held-out severity store, if phase 5 needs one, needs one
`cj assign` before its first export, and the tool says so when it refuses.

**Rule** — enforced by test:
`tests/test_findings.py::test_the_real_severity_file_pins_every_scored_findings_band` and
`tests/test_findings.py::test_the_real_severity_file_pins_what_lies_between_each_cuts_anchors` hold what
the re-export did not move; the tool's D36 names the tests that hold the freeze.

## D191 — The deterministic tier recognizes a defect only in the design set's words, and phase 7 is widened to answer it

**Fork:** the coverage report's held-out section, read with the owner on 2026-09-18, retired few of the
held-out set's findings, and a read-only diagnosis in the same session found why. For most of the
uncovered findings some rubric entry targets that kind of defect, and on the unseen calls it answered
`not_applicable`: each entry recognizes its situation through lists it enumerates — completion
signals, capability triggers, topics, reason codes — drawn from the sixteen design transcripts, and a
defect in other words or codes is not one it can see. The figures, the finding ids and the diagnosis
went to the owner in conversation only (D61, D175, D188). The `Not checked` block had named the risk:
that a phrase list might be one that happens to separate sixteen transcripts rather than the right
abstraction for a claim. Three forks were the owner's.

**Options considered.**

For when to act: **(A) wait for phase 7**, whose parser normalizes speech into structured claims and
is the fix in direction; or **(B) a version-2 rubric cycle now**, ahead of phases 6 and 7, with a
fresh session and a new held-out set.

For what to record: **(A) the lesson, and phase 7's scope widened** to carry it; **(B) the lesson
alone**; or **(C) nothing**, the diagnosis staying in conversation.

For what the record may say: **(A) the qualitative lesson** — no held-out figure, finding id, band or
wording; **(B) design-side facts only**; or **(C) a brief kept outside the tree**.

**Decision: (A) in all three**, the owner's on 2026-09-18.

**Why** — phase 7 as written would not have picked the lesson up: it is a corpus-building stage, done
when its own precision and recall are reported, and nothing in it moved the deterministic entries onto
its output, so waiting alone would have waited for a fix nobody had scheduled. A version-2 cycle now
would redesign the checks ahead of the parser meant to replace their phrase lists. Recording the
lesson in this tree leaks nothing held out: it carries no transcript text, label, figure or id, and the
labels have been public since C3. Nor does it contaminate anything still blind. The held-out set
measured rubric v1, and it cannot blindly measure a rubric changed in its light, which was true once
the owner saw the figures, written down or not; so the next measurement needs a fresh held-out set,
larger than the first because per-band figures resting on few findings are fragile. Not every miss is
a matter of parsing speech: some came from enumerated reason-code and outcome tables, which the
widening names, and some from entries that engaged and stayed silent, which phase 7's own opening
reading has to take up.

**Consequences / caveats** — nothing in the rubric, the corpus or the held-out repository changes, and
`rubric.yaml` stays at the freeze. Phase 7 gains no requirement or criterion here; its scope bullet and
phase section carry the widening, and its criteria are written when it opens, as every phase's were.
Phase 6 comes first. A version-2 cycle ahead of phase 7 was weighed and declined, not ruled out. The
session that ran the diagnosis read held-out content and does no rubric work; phase 7's session should
be a fresh one, and the owner chose Fable 5.1 at effort xhigh for it, for when its brief is written.

**Rule** — judgment, not checkable: the widening is scope prose that phase 7's opening reading has to
act on, as D157's reading did for phase 5; nothing mechanical can tell whether a future phase's
criteria honor it.

## D192 — The coverage report splits each band by who could detect its findings

**Fork:** the diagnosis behind D191 read the held-out coverage by detection type — which findings a
deterministic check could catch, which needed the judge — and that reading was in no report: `harness
coverage` counted each band whole. The owner asked for the breakdown in the report, and two forks were
the owner's.

**Options considered.**

For its shape: **(A) within each band**, one row per detection type beneath the band's row, all three
always printed; **(B) a separate table across bands**, a row per detection type totalled over every
band, the shape the diagnosis used; or **(C) both**, the second labeled as pooled.

For the contract: **(A) D188's clauses amended**, the coverage requirement and the command's criterion
gaining the split; or **(B) this entry alone**.

**Decision: (A) in both**, the owner's on 2026-09-18.

**Why** — a detection-type total across bands is a figure pooled across bands, which D157 refused
because it hides an uncovered set concentrated in the most severe band; split inside each band, the same
reading makes D157's per-band figures finer instead. Printing all three types even where a band holds
none of one keeps an absence visible rather than implied, which is the report's rule for the uncovered
set. The split is behavior of the command, so it goes where its other outputs are stated, and like
D189 it moves no count.

**Consequences / caveats** — over the design set the split reads critical 3 of 3 assert-type findings
retired beside 0 of 1 judge-type, and across every band each assert-type finding the rubric aims at is
retired, while every uncovered and missed design finding is judge-type; no finding is human-type.
Nothing about the held-out split is recorded here (D61, D175). The rows carry the type's value as the
findings document spells it, so `assert` means a deterministic check could catch the finding, not that
one did.

**Rule** — enforced by test:
`tests/test_coverage.py::test_coverage_would_notice_a_band_split_wrong_by_detection_type`,
`tests/test_coverage.py::test_the_coverage_section_would_notice_its_bands_pooled`,
`tests/test_cli.py::test_coverage_would_notice_its_design_section_miscounted` and
`tests/test_cli.py::test_coverage_would_notice_its_held_out_section_left_out`; 5 entries in
`control-mutations.yaml` drive the controls red.


### Correction, 2026-09-19 — six design findings are human-type, and the caveat says none is

*Appended rather than woven in. Everything above is what was written at the time and none of it is
edited, because an entry repaired to agree with what a later reading found stops being a record of
how the reasoning actually went (D53).*

This entry's caveats end: *every uncovered and missed design finding is judge-type; no finding is
human-type*. The gold set holds **six** findings with `detectable_by: human` — F-27, F-31, F-49,
F-56, F-59 and F-84 — which the phase-5 audit's P5-15 found by reading the file the sentence is
about.

**Both halves are true of the banded findings only.** All six are question-tier, so none carries a
band, and the report prints them under its no-band heading rather than in any band's rows — where
the split by detection type lives. The figures D192 states do not move, and neither does the split:
what was wrong is a sentence about the corpus written from a reading of the bands.

**A consequence worth stating, since it outlasts the sentence.** No test anywhere, by function or by
command, exercises a `human` detection-type row that is not `0, 0, 0`: every human-type design
finding is unbanded, and the invented held-out fixtures borrow design findings. The rows print, and
what they would print for a set that bands one is unproven.

## D193 — The register declares the values its names carry, and its check reads them

**Fork:** the held-out side, labeling after the reveal, found two kinds of value the design corpus uses
and `corpus/entities.md` declares nowhere. CALL-02 and CALL-11 carry `settlement=cardinal_pay`, a token
for the processor Class 5 knew only by its display name, and identifiers shaped `RF-`, `TR-`, `EX-` and
`MS-` appear in seven design calls with no row in Class 2. D101's rule is that every kind of name the
corpus uses is declared, and the check that holds it passed both, because it reads names — tools,
variables, argument and detail keys — and never the values they carry. The reveal handover owed a
declaration of each and a decision about the check (items 1 and 2, OB-44 and OB-45), and the fork was
the owner's.

**Options considered.** **(A) Declare and widen for both**: add the values to the register, and give
each kind a check that fails on a value the register does not declare; or **(B) declare both, and
record why the check stays on names**.

**Decision: (A)**, the owner's on 2026-09-18.

**Why** — a rule enforced over some kinds of name and not others is the carve-out D101 refused: the
next value of an undeclared kind would pass the way these two did, and these two were found by a
reader in another repository rather than by this one's suite. Declaring without widening fixes the
instances and leaves the class open. Each check stays narrow. An identifier is two capitals, a hyphen
and a digit, so `CALL-NN` and the Class 2 shapes without that prefix stay outside it, and a settlement
is the one value a tool result carries that names a third party.

**Consequences / caveats** — the widened identifier check found a fifth shape the handover had not
named: `SP-####`, the specialist CALL-20's `transfer_to_specialist` returns as `accepted_by`, now
declared beside the four. It reads 116 identifier-shaped tokens across the design transcripts, and
each matches a declared shape whole. The settlement check takes as declared every lowercase token
written in backticks in Class 5, which today is `cardinal_pay` alone, so a token written there for
another reason would count as declared too. `_declared_names` and `_REGISTER_CATEGORIES` do not
change; the widening is four new helpers, `_identifier_shapes`, `_undeclared_identifiers`,
`_third_party_tokens` and `_undeclared_settlements`. The held-out side's name check copies the first
two and runs against this repository's `main`, so the commit that lands this names the widening, as
the handover's item 2 requires, and catching up is that side's work.

**Rule** — enforced by test:
`tests/test_corpus_hygiene.py::test_the_register_would_notice_an_identifier_of_an_undeclared_shape` and
`tests/test_corpus_hygiene.py::test_the_register_would_notice_a_settlement_token_it_does_not_declare`; 5 entries in
`control-mutations.yaml` drive the controls red.

## D194 — The sweep marker names the version a sweep was recorded at, and moves only with a sweep

**Fork:** the phase-5 audit's P5-7 read the `Last swept` marker's history and found it had moved with
every decision from D168 to D193, 22 values in 22 commits. A test bound the marker's version to the
specification's, so every version bump had to move it, and moving it claims a sweep (D71). D129's
test, which reads the phase-completion clause, compares the marker with the last decision a closed
handover records, so it would pass at phase 5's close with no sweep performed; and D74 had declined
exactly a sweep claim per decision. Three answers were the owner's to choose between.

**Options considered.** **(A) Require marked sweep entries**: the marker names the version a sweep
was recorded at, and from 0.55.0 that version's changelog entry must say it records a sweep and what
the sweep read; **(B) stop moving the marker with decisions**, with no test to stop a bump that
moves it; or **(C) sweep at phase 5's close only**, with no change to the mechanism.

**Decision: (A)**, the owner's on 2026-09-19, with a sweep of the whole specification at phase 5's
close.

**Why** — (B) rests on every later session remembering, and the marker's history is the evidence of
what that costs; (C) repairs one close and leaves the next to the same test. Under (A) the marker is
free to lag while decisions accrue, which is the trigger counting down as D74 described it, and it
can move only where a changelog entry says a sweep happened and what it read. That makes both of the
trigger's mechanized clauses mean something again: the accrued count grows between sweeps instead of
resetting at every decision, and D129's test at a phase's close now needs a real sweep entry to go
green.

**Consequences / caveats** — the marker stays at `0.54.0 @ D193` until the next sweep, and every
marker before 0.55.0 is left as history rather than re-read. The test checks that a sweep entry
exists and says so, not that the sweep was thorough; that limit is D129's, stated there. The header's
sentence says the marker names a recorded sweep, and the version test beside it now asks only that
the marker names a version the changelog has, at or before the current one.

**Rule** — enforced by test:
`tests/test_document_counts.py::test_the_sweep_marker_names_a_changelog_entry_that_records_a_sweep` and
`tests/test_document_counts.py::test_the_spec_version_and_the_last_sweep_agree_with_the_changelog`;
2 entries in `control-mutations.yaml` drive the first red.

## D195 — The absence check reads every encoding a redirect writes here, fails closed, and reads the held-out artifacts it had no reading for

**Fork:** the phase-5 audit found the absence check blind in two ways. P5-1: every reading decoded a
file as UTF-8 and passed over one that did not decode, so a redirect in Windows PowerShell 5.1, which
writes UTF-16, and one from a profile set to `utf8`, which writes UTF-8 with a byte-order mark, left
all four shapes unread, while the phase-5 verifier's caveat named the absence check as what reports a
redirected held-out section; and two verifier logs in `build/`, written in a Windows code page, sat
under the check's OK line unread. P5-4: a run-log record laid out across lines, an extraction
artifact over a declared call, the three label files, a findings view over them and agreement's
held-out section had no reading at all. The owner asked for what needs fixing to be fixed, and two
forks were the owner's.

**Options considered.** For a file no reading can decode: **(A) report it**, failing closed; or
**(B) skip it**, as every reading did. For the shapes: **(A) a reading for each**, by structure
where the artifact has one and by the heading its renderer writes where it does not; or **(B) the
encodings alone**, leaving P5-4 until after phase 5's close, as the audit's order allowed.

**Decision: (A) in both**, taking the audit's closures; the two logs were moved out of the tree on
the owner's decision, 2026-09-19.

**Why** — a reading that cannot decode a file has not found it clean. Reporting the file costs a
person one re-encode or one deletion; skipping it is how the only mechanism protecting the held-out
set came to print OK over files it had never read. The shapes go with the encodings because both
are the irreversible direction, and phase 6 opens with sessions that may read the held-out files in
place, which is when an unread artifact is most likely to arrive.

**Consequences / caveats** — every reading decodes by byte-order mark, UTF-8 with one or UTF-16, and
as UTF-8 without one; a file with no binary suffix that decodes as none of them fails the check by
name. A run log's records are also decoded as JSON values starting a line, so a record's layout no
longer hides what it names, and any JSON object naming a declared call is reported, which is how an
extraction artifact is found. The label files are recognized in their own structure by a held-out
finding's `id` or the ids a traces file lists, a findings view by its per-finding heading, and
agreement's held-out section by its heading. **Two limits stand.** A run log's blob record alone names
no call, since none of the reference log's 208 prompt blobs does, so it is recognized only beside a
record that names one; and a paraphrase of held-out text has no shape at all, which is the rule the
audit's P5-3 found with no mechanism behind it. The check now walks the tree with the tool-generated
trees pruned rather than entered and filtered, so its seven readings take about 6 seconds over this
checkout where the four took about 18.

**Rule** — enforced by test:
`tests/test_holdout_absence.py::test_every_reading_finds_its_artifact_as_a_powershell_redirect_writes_it`,
`tests/test_holdout_absence.py::test_a_file_no_reading_can_decode_is_reported_rather_than_skipped`,
`tests/test_holdout_absence.py::test_a_run_log_record_laid_out_across_lines_is_found`,
`tests/test_holdout_absence.py::test_an_extraction_artifact_over_a_declared_call_is_found`,
`tests/test_holdout_absence.py::test_held_out_labels_are_found_in_their_own_structure`,
`tests/test_holdout_absence.py::test_design_labels_or_a_document_naming_a_held_out_id_are_not_mistaken_for_held_out_ones`,
`tests/test_holdout_absence.py::test_agreements_held_out_section_is_found_and_its_design_section_is_not`,
`tests/test_holdout_absence.py::test_the_check_reports_labels_agreement_and_an_undecodable_file_in_the_tree_it_scans` and `tests/test_holdout_absence.py::test_tool_generated_trees_are_skipped`; 16 entries in `control-mutations.yaml` drive
the controls red.

## D196 — Extraction and the findings view keep held-out content out of this tree

**Fork:** the phase-5 audit's P5-2 found the two entry points that had none of the refusals their
neighbors carry. `harness.extract` takes `--transcripts`, defaults `--out` to
`build/extraction-artifact.json` and writes every turn of every call it parses;
`harness.findings_view` takes `--findings`, defaults `--out` to the tracked `corpus/findings.md`
and writes every finding it is given. Neither reads `HELDOUT_SET`. Since the reveal a session may
read the held-out transcripts and labels in place, so pointing either at them is an ordinary thing
to do, and the audit reproduced both: an artifact naming a declared call written inside a copy of
the tree with the absence check green over it, and the tracked view overwritten with held-out
findings, which only its own staleness check noticed. D185 closed the same shape for `harness
report` after the cross-project audit had checked the run and agreement commands and not that one.

**Options considered.** **(A) The refusal both commands share**, as a requirement and a criterion of
their own, the way D185's landed; or **(B) a decision alone**, leaving the contract to describe four
commands where the rule now covers six.

**Decision: (A)**, on the owner's instruction to fix what the audit found.

**Why** — the rule is the tree's, not the command's: held-out content goes to stdout, or to a file
outside this checkout, and never to a file inside it. Four commands stated it and two wrote there by
default, which is the carve-out shape D101 refuses in another register. A requirement is what makes
the next entry point's author read it, since a decision is read by whoever goes looking.

**Consequences / caveats** — `harness.extract` refuses when any call it parses is declared in
`HELDOUT_SET` and `--out` resolves inside the repository; `harness.findings_view` refuses when any
finding's call is declared **or** its id has the held-out shape, since held-out labels carry `HF-`
ids and may name calls this repository does not declare. Both refuse when `HELDOUT_SET` cannot be
read, for D173's reason: a command that cannot tell whether its output is held out cannot tell where
it may write it. `--check` writes nothing and is not refused, so CI's staleness check is untouched,
and the design defaults still run. The declaration, the held-out id's shape and the one refusal now
live in `harness.heldout`, which `harness.cli` and `harness.agreement` read as well, so there
is one definition of each. The phase-5 contract gains a requirement and a criterion, taking it to 5
and 14.

**Rule** — enforced by test: the six in `tests/test_held_out_writes.py`; 7 entries in
`control-mutations.yaml` drive the controls red.

## D197 — The commands that score the held-out labels read the rubric their log names

**Fork:** the phase-5 audit's P5-5 found `check_rubric_hash` called in two places,
`harness run`'s replay and a resume, and `harness agreement` and `harness coverage` replaying
through neither: `_replayed_set` checked only that a held-out log names a labels manifest. So a
held-out log judged under another rubric, or under none, was replayed and scored against the labels
with nothing said, while the phase-5 verifier's caveat told a reader an edited rubric is caught
wherever a log is replayed. The audit reproduced it: agreement computed its held-out section over
the committed log re-headed three ways, exiting 0 each time, where `harness run` refused two of the
three.

**Options considered.** **(A) Refuse in `_replayed_set`**, where both commands pass, for a held-out
set alone; or **(B) leave it to the held-out repository's gate**, which compares the same hash
against the freeze on its own history.

**Decision: (A)**, on the owner's instruction to fix what the audit found.

**Why** — the hash is the claim that a log's answers and a set's labels belong together (D186), and
the two commands that make that claim were the two that never read it. (B) is a gate on the other
side of a boundary this repository cannot see, which is the shape D176 declares rather than ticks;
a measurement that reads the wrong log should not need another repository to notice. The refusal has
no override, as D186 chose, because a scored log under a rubric nobody names is not a measurement
with a caveat.

**Consequences / caveats** — only a held-out set is checked: a design run writes no rubric hash at
all, and the committed reference log carries none. An edit to a judged entry's text was already
caught, since the rendered request no longer hashes to a recorded one and the replay stops part-way;
what this closes is an edit to a deterministic entry, or to an entry's `violating` or `traces_to`,
which reach no prompt and so leave every recorded answer intact. HEAD's rubric is pinned to the
freeze by test, so the default path cannot drift unnoticed today; a `--rubric` flag, or the
version-2 cycle D191 weighed, is where this would have bitten. D186's criterion now names all four
places a log is read.

**Rule** — enforced by test:
`tests/test_cli.py::test_agreement_and_coverage_refuse_a_held_out_log_judged_under_another_rubric`; 1 entry in `control-mutations.yaml` drives the control red.

## D198 — The register declares the vocabulary its result keys carry, and the check reads it

**Fork:** D193 declared two kinds of value the design corpus uses and widened the name check to
each, and its own argument was that the next value of an undeclared kind would pass the way those
two had. The phase-5 audit's P5-11 found the third kind one week later: `reason=window_closed`,
`reason=booking_transferred` and `remedy=reversal_by_current_holder` appear in design tool results
and in neither `corpus/entities.md` nor `specs/event-model.md`. Class 6 declares `reason` and
`remedy` as detail keys and says nothing about what they carry. The owner chose between declaring
them with a check and recording why they stay outside.

**Options considered.** **(A) Declare and widen**, as D193 did for settlements; **(B) record why a
result's vocabulary values stay outside D101's rule**; or **(C) declare the three and write no
check**.

**Decision: (A)**, the owner's on 2026-09-19.

**Why** — the same argument D101 and D193 made, now with an instance: the carve-out is what a later
reader extends, and the kind left outside is the one that arrives next. A reason code is where a
platform says *why*, so a value the register does not know is a case nobody enumerated; (C) fixes
three instances and leaves the class open, which is what D193 already declined.

**Consequences / caveats** — Class 6 gains a paragraph naming the three values, and a test refuses a
`reason=` or `remedy=` a tool result names and the register does not. The reading is narrow by
design: only those two keys, only tool-result details, and only the design set. `call.ended(reason=…)`
is a disconnection reason, a closed vocabulary of the event model, and reaches no tool result, so it
stays where D39 put it. The other detail keys carry identifiers, amounts, timestamps and free text,
which are data rather than vocabulary, and the paragraph says so rather than leaving a reader to
infer the boundary. The held-out side copies the register check's helpers, and this widening is
named in the commit that lands it, as the reveal handover's item 2 requires.

**Rule** — enforced by test:
`tests/test_corpus_hygiene.py::test_the_register_would_notice_a_result_vocabulary_value_it_does_not_declare`; 2 entries in `control-mutations.yaml` drive the control
red.

### Correction, 2026-09-20 — a day, not a week

*Appended rather than woven in, as every correction here is: everything above is what was written at
the time and none of it is edited (D53).*

The *Fork* above says the phase-5 audit's P5-11 found the third undeclared kind "one week later"
than D193 declared the first two. It was a day. D193 was decided on 2026-09-18 and committed as
`c5ad3ce` at 2026-09-19 00:47; the audit that found P5-11 was written later that same day, against
that commit. The 0.59.0 changelog entry says the same thing and the sweep's own entry records the
correction rather than editing it.

The point the sentence makes survives the arithmetic, and reads harder: the kind D193 predicted
would arrive next arrived before the day was out.

## D199 — The close's own test reads a status line in either form this project writes

**Fork:** the specification sweep's S-1. `test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it`
evaluates the *at phase completion* clause D129 mechanized, and it finds a closed handover by its
status line. This project writes that line two ways: `**Status: closed** 2026-09-12`, which the
phase-3 and phase-4 handovers use, and `**Status:** open.`, which the reveal handover and the
cross-project one use. The pattern read the first only, so closing either of the second pair in
place would have produced a line the check could not see — phase 5 closing with its own sweep clause
never evaluated, and the check still green on the two handovers it already read.

**Options considered.** **(A) Close the handover in the form the test reads, and widen the pattern
to both** with a planted case and a control; **(B) the form alone**, leaving the next handover
written the other way to the same blind check; or **(C) the pattern alone**, leaving this handover's
style.

**Decision: (A)**, the owner's on 2026-09-20.

**Why** — (B) repairs one close and keeps the defect, which is what a blind instrument does: it
returns a null nobody can tell from a clean result. The pattern is one line and the planted case is
what makes the widening checkable, so the cost of (A) over (B) is a test and a control.

**Consequences / caveats** — the check was driven both ways before it was relied on, in a copy of
the tree outside the repository: with the reveal handover closed and the marker unmoved it is red in
either form, and green once the marker names a swept version. What it still cannot say is whether a
sweep was thorough, which is D129's own limit, restated there; and a handover that says it is closed
in prose without a status line is read as open, which is the conservative direction.

**Rule** — enforced by test: `tests/test_document_counts.py::test_the_close_check_reads_a_status_line_in_either_form_this_project_writes` and
`tests/test_document_counts.py::test_a_closed_phase_handover_requires_the_sweep_marker_to_have_reached_it`;
1 entry in `control-mutations.yaml` drives the first red.

## D200 — The design document is phase 6's, and the sentences describing it say so

**Fork:** the specification sweep's S-11. Four sentences described a design document in the present
tense — three deployment cadences and a four-stage gate ladder, the audio-layer follow-up question,
the runtime guardrail's shared rule — and phase 1's scope bullet and phase table both list it as
written during that phase, from the decision records. No such document exists: `git ls-files` finds
only `corpus/DESIGN_SET`, `private/` holds the clean-room sources and the substitution classes, and
a search for the gate ladder outside this specification returns nothing. Phase 1 closed three times
with no criterion asking for it, so nothing noticed for five phases.

**Options considered.** **(A) Phase 6 owns it**, beside the documentation routing phase 1 already
deferred there, with the present-tense sentences made future; **(B) phase 7 owns it**, so that it
describes the system after the parser widening D191 recorded; or **(C) drop the deliverable**, since
the decision record and this specification already carry what it would collect.

**Decision: (A)**, the owner's on 2026-09-20.

**Why** — the document's subject is what this project teaches a reader, which is phase 6's half of
the deliverable rather than phase 7's build; and a deliverable nobody has written is better moved to
a phase that has not started than dropped from a specification that cites it four times. (C) would
also drop the audio-layer follow-up question, which is the one thing the document is named for that
nothing else in the tree carries.

**Consequences / caveats** — the sentences about it are future tense, phase 1's scope bullet says
the document is deferred and phase 1's own list says so too, so nothing in the specification claims
a document that is not there. No acceptance criterion is added: phase 6's contract has not been read
yet (OB-16, OB-47), and writing a criterion for an unopened phase is the shape D157 took care over.
What phase 6 owes is therefore a scope bullet, not a tick, and its contract reading is where the
criterion belongs.

**Rule** — judgment, not checkable. Nothing can assert that a document not yet written will be
written; what is checkable is that no sentence here describes it in the present tense, which the
sweep's report records and the next sweep re-reads.

## D201 — Phase 6's contract, read before the phase builds: one requirement with no criterion, one no criterion could satisfy, and two covered in half

**Fork:** OB-16 asks each phase for the reading D104 gave phase 2, D130 phase 4 and D157 phase 5, and
OB-47's trigger fired when phase 5 closed on 2026-09-20. Phase 6's contract was 4 `[P6]`
requirements, 4 `[P6]` criteria and 6 scope bullets, gathered in
`sessions/PHASE-6-CONTRACT-READING.md`, and it was read before anything was built.

**What it found.**

- **The second adapter's requirement had no criterion**, and could not be met as written. The phase's
  *Done when* repeated it, and nothing reads a *Done when*. What the requirement could mean against a
  real platform is D203's.
- **The caching requirement and its criterion could not be satisfied by the frozen prompt**, which is
  D204's.
- **The comparison criterion bought the report and not the identical rubric.** Nothing failed if one
  candidate was judged under an edited rubric, which is the half that makes a comparison a comparison.
  The transport was not the gap: `request_hash` covers the generation config, the model in it, so
  replay cannot serve one model's answers as another's, which the reading checked rather than assumed.
- **The inspector criterion bought *runs and emits* and named one metric.** An inspector printing a
  pass or a quality figure satisfied it, and *metrics rather than scores* is the requirement's whole
  second half. Its first half, a run log sufficient to reproduce a judged result, is what phase 3's
  replay criteria assert.
- **Two deliverables carried no criterion and no requirement**, per-instance severity and the design
  document D200 gave this phase; **one criterion backed no requirement and had no test**, the README's
  license statement phase 1 deferred here; and **half of one scope bullet was already built**: the
  live-mode cost estimate and the call ceiling are phase 3's and phase 4's (D152, D161, D170), still
  listed under phase 6.

**Options considered.** For the two half-covered requirements: **(A) a criterion per missing half,
with the inspector's requirement kept whole**; (B) the same, with that requirement split into a
`[P3]` half and a `[P6]` half; (C) record the gaps and build against the criteria as written. For the
work the contract did not hold: **(i) clauses where the deliverable is behavior of the harness, and a
record for the rest**; (ii) criteria only, with no new requirement; (iii) record all of it and add
nothing. For the verifier: **(1) written now, declaring what is unbuilt**, as D176 had phase 5's; (2)
at the phase's end, as phases 1 to 4 did. For the design document: **(a) a session of its own**; (b)
this session, last; (c) an outline now and the prose later.

**Decision: (A), (i), (1) and (a)**, each the owner's on 2026-09-20.

**Why** — (C) leaves a green tick over an unasked question, which D130 refused for the phase whose
output the freeze fixed. (B) moves the stable half of the contract to suit the instrument that reads
it, which D130 also declined; the coverage table says in a comment that the inspector requirement's
first half rests on phase 3's criteria. Per-instance severity is behavior once it exists, so it takes
a requirement as the coverage report did at D188; the design document is prose and takes a criterion
a check can hold, that it exists, carries its named parts and cites decisions that resolve. The
README's criterion stays without a requirement, as phase 5's label chain did at D157, and gains the
test it never had. Phase 6 stays open across at least two sessions, and a verifier bound to the
specification on the first day is what keeps the second session's criteria from drifting from the
first's. The design document is written from some two hundred decision records, and this session
already carried a change to the event model and three deliverables with their controls.

**Consequences / caveats** — phase 6 goes from 4 requirements and 4 criteria to 5 and 12, and joins
phases 4 and 5 in `tests/test_contract_coverage.py`; phases 1, 2, 3 and 7 stay declared unmapped, so
OB-16 stays open for them. The license statement needed a decision no refactor could take: which
license covers the top-level paths the README's table did not name. The owner extended D31's line on
2026-09-20, code, configuration and tooling under Apache-2.0 and authored data and documentation
under CC BY 4.0, with `sessions/` left under neither as before, and the test now fails on a tracked
top-level path the README names no license for. `tools.verify_phase6` ticks what this session built
and declares 6 criteria not yet built. The adequacy half stays a reading: a mapping row is typed by
somebody, and what the table removes is a requirement nobody noticed had no criterion.

**Rule** — enforced by test, for the completeness half:
`test_every_requirement_of_a_mapped_phase_appears_in_the_table` and
`test_every_mapped_requirement_is_named_by_at_least_one_criterion` read phase 6, `MEASURED_CONTRACT`
pins its counts, `test_phase_6_declares_what_needs_a_model_call_and_the_design_document` pins the
verifier's declarations, and `test_the_readme_names_a_license_for_every_top_level_path` with
`test_the_license_check_would_notice_a_path_the_readme_does_not_name` holds the license statement;
`control-mutations.yaml` drives the last three red. The adequacy half stays a reading.

## D202 — The tracing convention stays for both existing sets, phase 6 reports under it and says so, and a firing table closes `JUDGED_AGREEMENT_PENDING`

**Fork:** OB-49 made the tracing convention due at phase 6's opening reading: both sets trace every
finding to entries of its own tier, so a judged entry firing beside an assert-type finding scores a
false alarm, and judge-model comparison reports agreement against the gold set. OB-7 asked what
closes `JUDGED_AGREEMENT_PENDING` now that held-out agreement is measured and never committed (D175),
and the phase-5 audit's P5-9 had left one entry-call pair recorded under the same convention.

**What was measured first, on the design set.** The judged tier's 19 false alarms all land on calls
that carry findings, because every design call carries at least one; `J-call-synthesis` fires on
CALL-01, whose 7 findings are all assert-type, and scores a false alarm for it. So no judged false
alarm on this set can be called a true one without a human reading which finding the judge was
answering, and under the convention a more sensitive candidate model reads as a worse one. All 61
assert-type findings are traced to a deterministic entry; 17 of the 23 judge-type findings are traced
to a judged entry and 6 to none. **The convention is one tier and not one entry**: 5 findings are
already traced to 2 entries inside a tier, so P5-9 is a missing second trace and needs no new
principle. And two constraints bound any answer: the design set's traces are `rubric.yaml`'s
`traces_to`, frozen at `rubric-frozen-v1`, and the held-out `traces.yaml` is sealed by its manifest,
so neither set's traces can move in phase 6 whatever is decided.

**A correction made during the fork, recorded because the owner's question found it.** The first
recommendation rested on `detectable_by` naming "the cheapest sufficient detector". The owner asked
how cheapest is defined and how consistently it was applied, and the answer is that it is not defined
at all: D42 assigns the field by **kind of oracle**, `assert` for anything derivable from the record,
and rejected cost as the criterion by name. The gloss was withdrawn. What can be said of consistency
is that one adjudicator applied a written rule finding by finding, no second labeler exists and no
inter-rater measurement was ever made, so only the outcome can be read: for `assert` the label is
borne out by construction on the design set, and for `judge` it is weaker.

**Options considered.** For the convention: **(A) a rule for phase 6 now, and the mechanism at the
version-2 cycle**; (B) cross-tier traces as first put, a finding traced to every entry that can reach
it; (C) one tier kept permanently on D42's strength, fixed only by adding judge-type findings. For
OB-7: **(i) a judged firing table over the committed reference log**; (ii) closing by declaration;
(iii) deferring to phase 7. For P5-9: **(1) the same answer as OB-49**; (2) its own permanent record.

**Decision: (A), (i) and (1)**, each the owner's on 2026-09-20.

**Why** — under D42 a judged entry firing beside an assert-type finding has three readings and only a
human can tell them apart: its own question genuinely reaches that finding, which is a trace, across
tiers or within one; it caught a conversational defect the gold set never recorded, which D43's logic
makes a separate judge-type finding and not a cross-trace; or it is a true false alarm. The synthesis
asks a call-level question and needs a call-level expected set rather than traces at all. (B) names
one of the three as the principle, and (C) another; neither can land before the version-2 cycle, so
what phase 6 needs is only what it reports. (ii) asserts nothing in this repository, and (iii) leaves
every judged entry's firing unpinned for another phase.

**Consequences / caveats** — phase 6 reports agreement under the one-tier convention, says so beside
every figure, puts hits and misses ahead of false alarms and orders no candidate by false alarms; a
`[P6]` criterion holds the comparison to that when it is built. The judged family has a firing table
and joins `FAMILY_TABLES`, with the 19 false alarms and the 1 miss, F-85 on CALL-19, recorded by name,
so a twentieth fails. `JUDGED_AGREEMENT_PENDING` is empty and kept as a declaration, so a judged
entry added without a row still has somewhere to be named. **That table is not blind agreement**: the
design findings were adjudicated with judge output in view (D21), and the blind figure stays the
held-out section of `harness agreement`, recomputable from the held-out repository's published labels
and committed log and never committed here. The three-way reading of each false alarm, the second
trace P5-9 lacks and the synthesis's expected set are the version-2 cycle's, carried by this
session's handover.

**Rule** — enforced by test for what is built:
`test_every_judged_entry_fires_where_the_committed_reference_log_is_recorded_as_firing`,
`test_the_judged_firing_comparison_would_notice_a_firing_that_moved` and
`test_every_pending_judged_entry_is_a_judged_entry_that_exists`, with `control-mutations.yaml`
driving the first two red. Judgment, not checkable, for the reporting rule until the comparison
exists; its criterion is declared not yet built in `tools.verify_phase6`.

## D203 — The second adapter is Retell's call object, identical to the text adapter where the source carries an event and declared where it does not

**Fork:** the requirement read *an event stream byte-identical to the text adapter's output for the
same call*. It was written when the second adapter was a JSONL format of this project's own, and was
not re-read when the scope bullet retargeted the adapter to a real platform's call object. Before any
code, the three platforms' public documentation was read on 2026-09-20 for what each call object
states, by three sub-agents of this session, each told to quote field names and to mark anything inferred.

**What the documentation states.** Retell's `GET /v2/get-call/{call_id}`, response schema
`V2PhoneCallResponse`, OpenAPI revision `2026-09-14-b240eb0`, types every field of its interleaved
`transcript_with_tool_calls` across 9 roles, including the `successful` flag section 4 of the event
model already named. Vapi's five message schemas never state a `role` value, its `toolCalls` items
declare no properties, and a tool result has no success flag. Amazon Connect documents no single
artifact that interleaves a classic flow's turns with its Lambda calls: Contact Lens carries agent
and customer turns, and the invocations sit in flow logs with no documented example.

**And what Retell's documented shape cannot carry.** A `tool_call_invocation`, a `tool_call_result`
and a `node_transition` have no timing field, so 114 of the corpus's 408 events would have no start or
end. No role is a disclosure, an applied policy clause or a call's lifecycle, 17, 10 and 31 events;
`collected_dynamic_variables` is a call-level map, so the 17 state events have no position. The call
has no answered-at stamp and no environment, and `agent_version` is an integer. Every design call
opens with `call.answered` and a disclosure, so every index and every fact citation id shifts, and
the requirement as written could be met for none of the 16.

**Options considered.** For the platform: **(A) Retell**; (B) Vapi; (C) Amazon Connect. For the
requirement: **(i) identical where carried**, the streams differing only where a declared, named gap
says the source cannot carry something; (ii) the missing kinds carried through Retell's `injected`
entries and the requirement kept literal; (iii) the finding recorded and the adapter left to a later
session. For the source documents: **(1) a committed generator**; (2) sixteen hand-authored files.

**Decision: (A), (i) and (1)**, each the owner's on 2026-09-20.

**Why** — (B) and (C) would each be written against a schema as somebody imagined it, which is the
JSONL adapter's failure one step further in. (ii) is that failure exactly: this project's text format
inside a vendor's envelope, proving a round trip through itself. (i) is a claim with two directions,
and the second is the one a convenient adapter breaks: an undeclared difference fails it, and so does
a declared gap the adapter filled, because a filled gap is a default and a default is
indistinguishable from a measurement. Hand-typing 219 utterances with word timings is a surface for
errors the byte comparison would report as adapter defects.

**What it cost: the event model admits absence, at v3.** v2 told an adapter to record what its source
cannot supply as unavailable and gave it nowhere to record it, since every field was required. An
event's timing and the record's `answered_at` and `environment` may now be absent, `Call.unavailable`
names what is, from a closed vocabulary in `harness.core.gaps`, and each name is defined by what it
removes from a complete stream. That definition is what makes the requirement checkable: the second
adapter's call must equal the text adapter's with its declared gaps applied. A text-sourced artifact
writes neither new key, so its bytes, and the content hash every committed log is stamped with, did
not move. The two checks that read timing as a quantity return `unevaluable` naming it.

**Consequences / caveats** — all 16 calls compare equal where carried: 333 of 408 events, 219 of them
speech and byte-identical with their citation ids. **A call from the second adapter can be extracted
and cannot be evaluated.** No check reads a declared gap, and each would turn the absence into a
verdict, a missing `call.ended` reported for a source that logs no lifecycle, a judged prompt stating
that no clause was retrieved where nothing can know; so the seam every tier shares refuses such a
call by name, and the adapter is selected on extraction alone, `--adapter retell`. Making the checks
read the declaration is owed and is in this session's handover. The generator and the adapter were
written together and could be wrong together; what does not pass through that loop is the comparison
with the text adapter's stream, a table of Retell's documented fields and types every document is
held to, and a changed word, a missing success flag and an unmapped value each driven through the
adapter alone. **No real vendor log is in this tree, by rule**, so nothing shows the adapter reads one
Retell produced, and the field table was typed from the documentation by one session on one day. A
tool result's `content` is the deployment's own response, so its status words are the deployment's
and are mapped by an argument; outcome and its reason are read from `custom_analysis_data`, the
documented home of a deployment's post-call fields. A result with no `successful` is refused, which
the documentation marks optional. 5 documented roles are not mapped and abort by name.

**Rule** — enforced by test: the 14 tests of `tests/test_retell_adapter.py`, led by
`test_every_design_calls_retell_stream_differs_from_the_text_stream_only_where_declared` and
`test_the_stream_comparison_would_notice_a_gap_filled_or_a_difference_undeclared`; 11 entries in
`control-mutations.yaml` drive their controls red.

## D204 — Prompt caching is shared across a dimension's repetitions, because the frozen template cannot share a transcript across dimensions

**Fork:** the requirement placed the transcript block ahead of the last cache breakpoint *so it is
shared across dimensions for a given call*, and its criterion read non-zero cache-read tokens on *the
second dimension evaluated for a given call*. The reading compared both with the prompt they describe.

**What it found.** A cached prefix renders tools, then the system message, then the messages.
`prompts/judge-dimension.v1.md` carries each dimension's question, criteria and scale in the *system*
message, and the committed reference log holds 7 distinct system blobs, one per judged entry. A
per-dimension system message precedes the transcript in every request, so no prefix holding the
transcript is shared by two dimensions, and the criterion had nothing to read. The specification's own
N=10 assumption says something else, that repeated calls for one dimension are byte-identical
prompts, and the log agrees with it: 88 of 104 entry-call pairs send one request 10 times, and the
other 16 are the synthesis, whose repetitions differ by D154's design and only after the transcript.
The template is frozen at `rubric-frozen-v1`, so a reorder is the version-2 cycle's.

**Options considered.** **(A) Retarget to repetitions**, with a second criterion that needs no model
call; (B) defer the requirement and its criterion whole to the version-2 cycle; (C) both, with a new
`[P7]` requirement for cross-dimension sharing.

**Decision: (A)**, the owner's on 2026-09-20.

**Why** — (A) is what the frozen template supports and what the assumption already promised, and it
is most of the saving: one write and nine reads for every pair. (B) ships no caching for a reason that
applies to one of its two readings. (C) writes a requirement for a phase whose contract has not been
read, which D157 took care not to do.

**Consequences / caveats** — the requirement places the last breakpoint after the last content that
is byte-identical across an entry's repetitions on a call, the whole request for a dimension and
everything ahead of the resampled results for the synthesis, and leaves every request's hash as it
was; `request_hash` covers the system message, the prompt, the schema and the generation config, so a
cache marker need not move it and the committed log stays replayable. The live criterion reads the
second *repetition* and asks for more cache-read tokens than the entry's system message accounts for:
every system message is near the minimum cacheable prefix on its own, so a non-zero count is what a
cache missing the transcript also reports. That minimum differs by model, 1,024 tokens for the
dimensions' model and 512 for the synthesis's when this was written, so a candidate model's is read
rather than assumed. Cross-dimension sharing needs the transcript ahead of the dimension's question,
which also moves the instruction hierarchy the injection defense rests on, and is recorded here for
the version-2 cycle rather than owed by phase 6. Neither criterion is built: both are declared in
`tools.verify_phase6`, the live one for a session briefed to spend.

**Rule** — judgment, not checkable, until caching is built. What is held now is that the two criteria
are claimed: `test_phase_6_declares_what_needs_a_model_call_and_the_design_document`.

## D205 — The log inspector emits counts and proportions, exits on whether it could read the log, and re-derives the citable universe from the prompt

**Fork:** the criterion names one metric, the proportion of retry triggers whose cited identifier
exists, and the brief left the others to be proposed, each with what it would mean if it moved.

**Options considered.** **(A) All eight rows** — the retry metric with each retry's cause derived
independently of the validator; call records whose references resolve to a blob written earlier;
blobs that re-hash to the hash they are filed under; request hashes that recompute; repetitions that
run unbroken, and one count per entry; repetitions sharing one request hash; retry groups within the
single-retry budget; stop reasons and the redaction marker. (B) The retry metric and the three
integrity rows. (C) The retry metric alone.

**Decision: (A)**, the owner's on 2026-09-20.

**Why** — each row is an invariant another part of this project already relies on and nothing reads
from a finished log: the one-pass reader, the hash filed under scrubbed content, replay's key, N
repetitions per call, the single informed retry. The shared-hash row is also the measure, at no
spend, of what D204's caching can serve.

**What makes it metrics and not scores.** A metric is two integers and a sentence saying what moving
would mean; there is no float, no status and no field a verdict could go in. The command exits 0
whenever the log could be read and 2 when it could not, and never 1, which in this command line's
vocabulary is a finding about the agent: a log planted with a violation of every invariant exits 0
with each counted, because deciding a count is too high is a threshold and a threshold is a gate
nobody chose (D134). **Nothing in it imports the judged engine or its validator.** The retry metric
asks whether rejected answers cited identifiers the prompt had rendered, and an inspector that asked
the validator would be the validator agreeing with itself, which is D121's shape. The citable
universe is read from the logged prompt by the rule its layout states, that a citable line begins
with its tag.

**What the first reading found.** All 8 informed retries in the committed reference log are the
synthesis citing a fact identifier, and the synthesis is given no fact lines to cite. 2 of the 8 cited
identifiers the prompt shows, inside the other dimensions' rationales, which quote their own
citations; so the prompt shows the model an identifier and then refuses it. None is unexplained, so
the validator and its prompt agree and this is not W1. It is a finding about a frozen template and is
handed to the version-2 cycle.

**Consequences / caveats** — a template rendering citable lines another way would be measured
wrongly with nothing said. That no metric line reads as a judgment is held by a list of words, which
a score spelled another way would pass; the types are what cannot. The committed log's measures are
pinned, so a re-recording that moves one is seen.

**Rule** — enforced by test: the 8 tests of `tests/test_inspector.py`, led by
`test_every_value_the_inspector_emits_is_a_count_or_a_proportion_with_both_its_terms` and
`test_the_committed_reference_log_measures_what_is_recorded`; 7 entries in `control-mutations.yaml`
drive their controls red.

## D206 — Per-instance severity is a monotone decision list over what kind of harm an entry means and what happened in the call

**Fork:** D15 kept per-instance severity in the target on one condition, that it decompose into
boolean properties and compute the level in code, never handing a model a scale. Nothing since said
which booleans, read from what, or why their combination is a severity rather than a label.

**Options considered.** **(A) Kind of harm and what happened**, two layers; (B) what happened only,
the stream-read facts with no per-entry declaration; (C) kind of harm only, declared per entry.

**Decision: (A)**, the owner's on 2026-09-20.

**Why** — (C) gives every instance of an entry one band whatever happened in the call, which is
per-entry severity under another name. (B) lets an unrelated entry firing on a call where a refund
completed inherit that refund's gravity.

**What was built.** An instance is one rubric entry counting against its gate on one call, read
through the function agreement and coverage share. `severity-properties.yaml`, beside the frozen
rubric and never in it, declares per entry whether a violation touches account access, touches money
or an entitlement, or leaves the caller misinformed. Four facts are read from the stream from the
instance's evidence point on: a consequential write completed, that write is irreversible, identity
was unverified at the evidence, and no handoff completed. Every tool and state name behind them comes
from the frozen rubric's own params through a table in the data file, so none is typed twice. **The
band is a decision list in which every property appears only positively**, so no property turning
true lowers a band: that monotone order over realized consequence is what makes it a severity, and
its top rule is the ranked file's calibration note reached by rule, critical where a non-owner may
have been given insight into the account. The synthesis is excluded with its reason, because it
restates the other entries' instances.

**Consequences / caveats** — **the 43 declarations are one session's judgment**, reviewed by the
owner and measured by nothing. On the design set the 80 instances fall 8 critical, 3 high, 46 medium
and 23 low, and the table against the ranked bands agrees loosely: the rule that a misinformed caller
with no handoff is medium puts 17 instances there whose traced findings are ranked low. That table is
the instrument for tuning the declarations, it is printed and gates nothing, and tuning toward the
design set would be in sample. The evidence point is the smallest event index an instance's evidence
names; 15 of the 55 deterministic instances name none, being defects of the record or of an absence,
and a judged instance's citations are not carried past the roll-up, so both are read from the start of
the call, which counts a write that completed before them as after.

**Rule** — enforced by test: the 6 tests of `tests/test_instance_severity.py`, led by
`test_no_property_turning_true_lowers_a_band` and
`test_one_entry_receives_different_bands_on_two_calls_that_differ_in_what_happened`; 5 entries in
`control-mutations.yaml` drive their controls red.

## D207 — The license check reads this repository's trees, not a sibling CI checks out inside it

**Fork:** phase 6's `test_the_readme_names_a_license_for_every_top_level_path`, written the day
before, turned `main` red on its first CI run. Its claim is right — every top-level path this
repository holds is named in the README's license table — and its population was wrong: CI checks
`comparative-judgment` out at `comparative-judgment/`, **inside** this root, so the scan read a tree
this repository does not own and cannot license. It passed on the machine it was written on, where
the sibling sits outside the root, which is the difference that hid it.

**Options considered.** **(A) Skip a top-level directory carrying its own `.git`**, with a planted
case and a control, and add the sibling to `.gitignore` so `git status` stays honest in CI;
**(B) the `.gitignore` line alone**, which the check already honors; or **(C) check the sibling out
beside this root in CI** rather than inside it.

**Decision: (A)**, the owner's on 2026-09-21.

**Why** — (B) fixes the instance and not the class: a sibling checked out under another name, by CI
or by hand, fails the same way, and the ignore file is not where a reader looks for what the check
counts. (C) changes how every run is laid out to accommodate one test. A working copy carrying its
own `.git` is another repository by construction, which is the property the check should read, and
the `.gitignore` line is kept anyway because an untracked tree in the root is exactly what that file
is for.

**Consequences / caveats** — the check reads for the `.git` rather than for the name, so any sibling
is skipped wherever it is checked out and under whatever name. A directory of this repository that
somehow carried a `.git` would be skipped too, which is the conservative direction: this check
exists to catch an unlicensed tree, and a nested repository is not one this repository can license.
The planted case drives both halves — the sibling skipped, an ordinary directory still read — since
a skip rule that skipped everything would be green and blind.

**Rule** — enforced by test: `tests/test_phase6_acceptance.py::test_the_license_check_reads_this_repositorys_trees_and_not_a_sibling_checkout`; 1 entry in
`control-mutations.yaml` drives it red.

## D208 — The publication is a snapshot, built by a tool that refuses a path naming the machine it was built on

**Fork:** D2 and D78 say the three repositories flip public when the project is minimally functional,
and the reading that preceded the flip found what flipping would publish: twelve session documents
naming a directory path from the machine the work was done on, carrying context nothing in this
project needs. The working tree was one commit to clean, which is the commit before this one.
History is not: five commits still carry that path, and publishing a repository publishes every
commit in it.

**Options considered.** **(A) Rewrite the history** — filter the path out of every commit that
carries it and publish the result; **(B) publish a snapshot**, one commit carrying the clean tree,
built by a tool, with the working history staying private; or **(C) publish it as it stands**, on
the reading that a directory name is not a secret.

**Decision: (B)**, the owner's on 2026-09-21.

**Why** — (A) changes every commit from the first rewritten one onward, and this project's evidence
is pinned to commit identifiers: `RUBRIC_FROZEN_V1` and the `rubric-frozen-v1` tag it is compared
against, the held-out repository's label commits, which cite the freeze commit by SHA and were made
in a repository this one cannot rewrite, and several dozen documents citing commits as evidence. A
rewrite falsifies citations another repository has already made and cannot re-make, to remove a
string from commits nobody needs to read. (C) publishes exactly what the owner asked to keep out,
into a tree strangers cache.

**Consequences / caveats** — the published tree differs from this one in three places and
`tools/make_public_snapshot.py` makes all three: `SNAPSHOT.md` says what is published and what is
not, the README licenses that file because phase 6's license criterion asks for every top-level
path, and `RUBRIC_FROZEN_V1` is re-pointed at the snapshot's first commit, which the tag marks
there too, so the tests comparing them pass in a repository whose history does not hold the
original freeze — `SNAPSHOT.md` records that the original freeze commit is what the documents mean.
**The check is a pattern rather than a word list**, because a list of what to keep out of a public
tree, kept inside that tree, publishes it; a match exits 2 and is a person's decision, and the four
files carrying one deliberately are named with their reason. **What it does not buy:** it reads for
absolute paths and for nothing else, so a company, an employer or a person's name in prose passes
it. The reading before a flip stays a person's work, and the tool holds the one class that has
already occurred here. Refreshing the public repository means building the snapshot again and
replacing what is there; its log is two commits, and is not a history anybody should read.

**Rule** — enforced by test: `tests/test_public_snapshot.py::test_the_scan_finds_a_planted_absolute_path`
plants each shape the pattern claims to find, because a pattern that cannot match reads exactly like
a clean tree; `test_every_allowed_path_exists_and_still_carries_a_match` drops an exemption whose
reason has gone; and `test_no_tracked_file_carries_an_absolute_path_outside_the_allowance` asks the
publication question of every tracked file on every run rather than at publication time. The three
differences the tool makes are not asserted here, because they are properties of a tree this
repository does not contain: the snapshot carries this suite and answers them where they are true.

## D209 — The freeze is published as its own object bytes, and the snapshot stops reusing its tag name

**Fork:** D208 published this project as a snapshot and `SNAPSHOT.md` stated what that costs — a
commit id cited in a document does not resolve in the published log. For an audit banner or a
decision entry that costs a reader a convenience. For one citation it is the evidence itself:
`voice-agent-eval-harness-holdout` secures property (a), that the rubric was not designed against
its labels, by its seal commit citing the freeze commit's SHA, on the argument that a timestamp is
self-asserted and a hash is not (D21, D177). Since publication that SHA answers `422 No commit
found`, and the tag name was reused, so `rubric-frozen-v1` in the public repository names the
snapshot's first commit — dated four days **after** the seal. An automated reader, the held-out
repository's own gate included, therefore sees a freeze that postdates the labels it must precede,
which is the single thing the citation exists to exclude. A review on the held-out side reported
both symptoms; every claim in it was re-verified here before anything was built.

**Options considered.** **(A) Publish the freeze commit's own object bytes** — with its annotated
tag and the two trees reaching the frozen files — and tag the snapshot's pin under a name of its
own; **(B) push a ref reaching the freeze** into the public repository; **(C) leave it**, on the
reading that `SNAPSHOT.md` already explains the situation in prose; or **(D) rewrite the history**
after all, so the freeze is published in place.

**Decision: (A)**, the owner's on 2026-09-21.

**Why** — (B) is not available at any price: git requires connectivity for a pushed ref, so a ref
reaching that commit drags every commit behind it, which is what the snapshot exists to prevent.
(C) leaves a property that was **checkable by recomputation** standing as one **asserted in prose**,
which is the distinction these two repositories were split over (D2), and prose is not what a gate
reads. (D) was refused at D208 and none of its reasons have moved. (A) costs 2,488 bytes and
discloses nothing, because a commit object references its tree and its parents **by hash rather than
by content**: the four objects stand alone, every top-level name in the frozen tree is already
published here, the frozen `rubric.yaml` and prompt template are the published ones byte for byte,
and the commit message is about the phase-4 audit.

**Consequences / caveats** — `freeze-proof/` publishes the freeze commit, its annotated tag object,
the frozen root tree and the frozen `prompts` tree, so the chain runs by recomputation from the
held-out seal's citation to both files the freeze is load-bearing for: the rubric the labels are
scored against and the prompt template the judged tier renders. The commit and the tag are raw
object bytes, readable as they are; the trees are base64, because a tree carries NUL bytes and this
repository tracks no binary file. **The snapshot no longer reuses the tag name**: `FREEZE_TAG` joins
`RUBRIC_FROZEN_V1` in `src/harness/agreement.py`, the test that compares the pin with the tag reads
it, and `tools/make_public_snapshot.py` rewrites both in the one file it already edits, tagging the
snapshot's first commit `snapshot-rubric-pin-v1`. The published tree still differs in three files.

**What the proof buys that the snapshot's own pin cannot.** There the pin names the snapshot's first
commit, so comparing the rubric at HEAD against it is a tautology; `test_the_frozen_blobs_are_the_files_at_head`
compares HEAD against the freeze's own tree instead, which is the real claim, and it needs no `.git`
— so unlike `test_the_pinned_frozen_commit_is_the_one_the_tag_points_at` it can be a control, and it
is one.

**What it does not buy.** The proof uses **no date**, deliberately: author and committer dates are
self-asserted. It rests on SHA-1 **second-preimage** resistance, which is not broken — not on
collision resistance, which is, since a collision must be prepared before the hash is published and
the held-out repository published this one on 2026-09-17. A SHA-256 digest of each object's bytes is
published beside it for a reader who declines SHA-1 entirely. And the proof settles what was frozen,
not that the labels were authored honestly afterwards: property (b) is the held-out repository's own,
by its own mechanism.

**Owed elsewhere, as O-12.** The held-out repository's gate resolves the tag by name and must
verify against the published proof instead; that is its task, deliberately not designed here, so the
two are designed against each other rather than in sequence. Its build reports the moved tag until
then, and `HOLDOUT-OBLIGATIONS.md` carries the entry, which nothing in this tree can confirm. The two `[P5]` criteria that
name `rubric-frozen-v1` describe what that gate asserts, and may need re-wording when it lands —
left alone here, because amending a closed phase's criterion is its own fork.

**Rule** — enforced by test: `tests/test_freeze_proof.py` holds four properties apart —
`test_every_published_object_hashes_to_the_id_it_claims`,
`test_the_published_chain_runs_from_the_tag_to_the_frozen_files`,
`test_the_frozen_blobs_are_the_files_at_head` and
`test_the_proof_readme_names_the_digests_the_files_have` — with
`test_the_verifier_reports_a_corrupted_object_rather_than_passing` planting the failure and
`test_the_command_exits_one_when_the_proof_does_not_verify` reading the exit code; 3 entries in
`control-mutations.yaml` drive three of them red, on a moved object byte, a moved rubric byte and a
stale published digest.

## D210 — The proof carries the frozen `src`, because the gate recomputes a hash rather than reading one

**Fork:** D209 published the freeze's *inputs* — the commit, its annotated tag, and the trees reaching
the frozen `rubric.yaml` and prompt template — and O-12 described what the held-out gate owed as
recomputing those ids in place of resolving a tag name. A review from that side, re-verified here,
found that description insufficient. The gate does not **read** the frozen template's hash: it
**computes** it, by running the frozen harness's own `load_template` in a separate interpreter over
the frozen `src`, and refuses a hash whose `harness` resolved anywhere but that tree. It also reads
the template's path out of the frozen `cli.py` rather than hard-coding it. `freeze-proof/` carried no
`src`, and the frozen `src` tree is not the published one: the snapshot rewrites two constants in
`agreement.py`, and the code has moved since 2026-09-13 regardless.

**Options considered.** **(A) Publish the whole frozen `src` subtree**, object by object, so that
probe can run against published bytes alone; **(B) publish the minimal import closure** the probe
needs; **(C) compute with HEAD's code instead**, deleting the gate's guard; or **(D) accept the run
log's recorded `prompt_template_hash`** without recomputing anything.

**Decision: (A)**, the owner's on 2026-09-21, with the blobs named by object id rather than by path.

**Why** — (C) fails an honest run the moment `load_template`'s hashing moves, and it requires deleting
the one guard that makes the gate's answer mean anything; that today's code and the frozen code agree
on `ce6ec2e5` is a fact about today rather than a property. (D) turns a recomputed fact back into an
asserted one, which is what this whole thread exists to undo. (B) saves little — the closure is about
ten blobs against thirty — and leaves the gate to wonder whether it is reconstructing a complete
`src/` or a subset. (A) is 533,369 bytes of this project's own Apache-2.0 code, whose current versions
are published already.

**Named by id, not by path.** These are 2026-09-13 versions of files whose current versions sit beside
them. A directory of stale `.py` files invites being read as live code, reformatted by a tool, or
imported by accident; naming each file by its object id makes the file name a checksum, keeps `ruff`,
`mypy` and any formatter away from it — nothing there carries a `.py` extension — and leaves the paths
where this proof keeps them anyway, in the tree objects. `objects/<id>` is a blob, raw;
`objects/<id>.b64` is a tree, base64, for the reason the other trees are.

**What it buys.** `tools.verify_freeze_proof` reconstructs `src/` by walking the trees, verifying every
object against its own file name as it goes, then runs the gate's own probe and holds three things at
once: `harness.__file__` inside the reconstruction, the computed hash equal to the published
`ce6ec2e5`, and — in the suite — that same value equal to the `prompt_template_hash` the committed
reference run log recorded. 34 files, no `.git`, no network, no clone. The walk is the proof: a path
exists in the reconstruction only because a verified tree object named it.

**How the safety scan was run, since a clean result is the easy thing to fake.** Every frozen blob was
scanned for the directory path the snapshot exists to leave behind. The tokens came from the scrub
commit's own diff, were kept only where they appear nowhere in the scrubbed tree, and each was proved
still to fire on the pre-scrub tree — 2 to 8 files apiece — before any clean result was trusted. None
of the 34 blobs matched a token or the absolute-path pattern. The token list stayed outside the
repository: a list of what to keep out of a public tree, kept inside that tree, publishes it.

**The control gate refused the first version of one of these controls**, and the refusal is worth
recording. The mutation landed in the template's comment header, and `_strip_comments` takes comment
blocks out before hashing — *what is hashed is what is sent* — so the hash did not move and the control
stayed green with its defect restored. Re-pointed into the instruction hierarchy, which is sent, it
goes red. A control anchored where nothing reads is the failure mode the whole register exists for,
found by the gate rather than by a reader.

**Consequences / caveats** — O-12's text now names the reconstruction rather than the object ids alone,
and the port stays the held-out repository's task. The published proof grows from 2,488 bytes to about
half a megabyte, which is the cost of carrying a computation rather than an input. Nothing here pins
the *frozen* interpreter: the probe runs on whatever Python the reader has, so a hash that changed with
a Python version would not be caught — the frozen code's own constants are pinned, its runtime is not,
and no one has needed that yet. And the proof still settles only what was frozen: property (b), that
the labels were authored honestly afterwards, remains the held-out repository's own by its own
mechanism.

**Rule** — enforced by test: `tests/test_freeze_proof.py::test_the_frozen_src_reconstructs_from_the_published_objects`
and `::test_the_frozen_code_computes_the_frozen_template_hash`, with
`::test_the_published_template_hash_is_what_the_reference_run_log_recorded` tying the number to a
recorded run, `::test_a_corrupted_published_object_stops_the_reconstruction` planting the refusal, and
`::test_the_probe_would_import_another_harness_without_the_reconstruction` showing what the guard
catches; 2 entries in `control-mutations.yaml` drive the first two red.

## D211 — The published snapshot rewrites nothing, and the two tests that need the freeze in the log skip where it is absent

**Fork:** D208 re-pointed `RUBRIC_FROZEN_V1` at the snapshot's own first commit, so that
`test_the_pinned_frozen_commit_is_the_one_the_tag_points_at` and
`test_the_rubric_and_the_template_at_head_are_the_frozen_commits` — both of which ask git for the
freeze — would pass in a tree whose log does not contain it. D209 then had to invent a tag name for
the same reason, since reusing `rubric-frozen-v1` made the freeze appear to postdate the held-out
seal that cites it. The sweep of 2026-09-22 read the publication as a reader would and found what
that cost. **S-16:** `check_held_out_labels` refuses traces naming any commit but the pin, so in the
published tree it refused the *real* held-out labels, and the recomputation the README and D202
promise could be made only from the private repository. **S-1:** pushing the tag after the branch
left the public build red on all 5 of its runs, on that one test, with the 14 steps after the suite
skipped every time — the deterministic tier, the 6 phase verifiers, the report diff, the statement
inventory, the control gate, the absence check, the findings view and the interface check have never
run in public.

**Options considered.** **(A) The snapshot rewrites nothing**, and the two git-dependent tests skip
where the freeze is not in the log; **(B) keep the rewrite and have the two held-out commands read
the freeze out of the proof** rather than the pin; **(C) keep the rewrite and document the refusal**
in the snapshot note; or **(D) keep the rewrite and fix the push order alone**, tag before branch.

**Decision: (A)**, the owner's on 2026-09-22. The sweep recommended (C) now and (B) as an
obligation; (A) is the owner's, and it is a shape the report did not list.

**Why** — the rewrite existed to keep two tests green, and since D210 the property they assert is
carried without git: `freeze-proof/` publishes the frozen trees and
`test_the_frozen_blobs_are_the_files_at_head` compares them against the files at HEAD. In a snapshot
that is the *real* comparison and the pinned one was a tautology, because the pin named the
snapshot's own commit. So (A) loses nothing and returns three things: the published pin names the
freeze, so the held-out commands accept real labels there; there is no tag to invent or to push in
the wrong order, which removes S-1 by removing its subject rather than its symptom; and the
published tree differs in 2 files rather than 3. (B) fixes the refusal and leaves a constant in the
public tree naming a commit no document means. (C) documents a defect it could remove instead. (D)
fixes the build and leaves the refusal standing.

**Consequences / caveats** — the snapshot is **one commit**, not two: the second existed only to
carry the re-pointed pin, and the README's license row is now written before the first commit. The
two tests skip on one condition and nothing else — the pinned commit is not an object of this
repository — so a tree that holds the freeze and has lost the tag still fails, which is the case
D175 wrote the first of them for, and `_the_freeze_is_in_this_history` is where that reading lives. A
published suite reports 2 skipped, which `SNAPSHOT.md` states rather than leaving a reader to notice.
**What this does not buy:** nothing in the published tree checks that a reader's own clone carries
the freeze — it cannot, which is what the proof is for — and the five red builds already in the
public repository's history stay there; only the next build is green.

**Extended the same day by the first public build that got past the suite.** With the tag gone the
published suite passed, and 5 steps behind it, and then the phase-5 verifier failed: its criterion
2 named `test_the_pinned_frozen_commit_is_the_one_the_tag_points_at` among the tests that evidence
it, and a skip is not a pass to a verifier that D143 taught to stop reading silence as one. The
test is dropped from that criterion's evidence, which it corroborated rather than carried — the
refusal of a traces file naming another frozen commit is held by `test_the_held_out_labels_would_notice_each_broken_invariant`
and its CLI counterpart, both of which ask git nothing — and the criterion's caveat now says so. A
declaration skipping into silence is the shape this project keeps finding, and it took a public
repository's build to show it: no local run could, because the freeze is in this log.

**Rule** — enforced by test in part, and the part matters:
`tests/test_agreement.py::test_the_pinned_frozen_commit_is_the_one_the_tag_points_at` and
`::test_the_rubric_and_the_template_at_head_are_the_frozen_commits` skip on the freeze's absence and
on nothing else, and
`tests/test_freeze_proof.py::test_the_frozen_blobs_are_the_files_at_head` carries the property where
they skip, driven red by `control-mutations.yaml`. What nothing here checks is that the tool leaves
the exported tree alone: that is a property of a tree this repository does not contain, and the
snapshot's own suite is what reads it — the shape D209's Rule line took for the same reason.

## D212 — The read tokens are retired, and the secret guard refuses silence in both directions

**Fork:** `comparative-judgment` went public on 2026-09-21 and `voice-agent-eval-harness-holdout` on
2026-09-22, which left both read tokens with nothing to do — reading across a repository boundary
needs no secret once the far side is public. `HARNESS_READ_TOKEN` was deleted on that side the same
day. `CJ_READ_TOKEN` sat here unused with an expiry of 2026-11-05, and the checkout that had needed
it was written as that secret OR-ed with the default token, which reads like a fallback and is not
one: an expired secret is still a non-empty string, so it would be passed rather than fallen back
from, and a checkout needing no token would fail on a dead one. That reading came from the held-out
side, which had dropped its own token for exactly that reason.

**Options considered.** **(A) Delete the token and pass no `token:` at all**, keeping D84's guard
with a message that says what to check rather than naming a token that no longer exists; **(B) delete
the token and keep the OR expression**, which then resolves to the default token; or **(C) keep the
token until it expires**, on the argument that a working credential costs nothing.

**Decision: (A)**, the owner's on 2026-09-22.

**Why** — (C) keeps a credential alive for no purpose, and an unused credential is one whose loss
nobody notices; it also keeps a date in the README that has to be maintained for a token nothing
reads. (B) keeps the shape this decision exists to remove: the expression cannot express *use this if
it works*, so the day a successor is installed expired is the day the checkout breaks with a
misleading message. (A) leaves the workflow saying what is true — nothing here needs a credential to
read a public sibling — and leaves the detector that matters, D84's guard, in place for the day that
stops being true.

**What it exposed, which is the part worth keeping.** With no secret in the workflow,
`test_every_secret_the_workflow_reads_is_documented` failed: it returned a problem because the
workflow read nothing, on the rule that a comparison over an empty population is a comparison of
nothing (D143's lesson, and D121's). That was right while a secret was the only way to reach a
private sibling, and became a false alarm the moment that stopped being true. **The rule is widened
rather than relaxed**: a workflow that reads no secret must sit beside a README that says it reads
none, so silence is still refused and what a reader checks is a claim rather than an absence. The
control gains a fifth plant for the new direction, both ways round.

**Consequences / caveats** — this repository holds no secret at all now, and the only one left in the
three-way arrangement is `HARNESS_DISPATCH_TOKEN` in `comparative-judgment`, a **write** permission,
which being public does not grant. The README's expiry paragraph becomes a record of two retirements
rather than a date to maintain. **What this does not buy:** nothing here watches repository
visibility, so if a sibling is made private again the first thing to notice is the checkout failing —
which is the detector D84 left, and it says what to check. And a guard whose population can go empty
is a shape worth looking for elsewhere: this is the second time a check written when something was
always true had to be widened when it stopped being, after D211's two skipping tests.

**Rule** — enforced by test:
`tests/test_document_counts.py::test_every_secret_the_workflow_reads_is_documented` refuses both an
undocumented secret and an undocumented absence, with
`::test_the_secret_documentation_guard_finds_an_undocumented_secret` planting all five cases — a
secret the README never names, one named without its grant, a README with no expiry warning, one with
nowhere to make a replacement, and a workflow reading nothing beside a README that does not say so.

## Not checked — as of 0.68.0 @ D212

Recording the scope deliberately drawn, so the next session does not rediscover these as fresh defects. **Moved to the end of the file and re-dated.** It sat between D44 and D45, so a reader working forward met it before the thirteen entries that supersede parts of it, and its figures went stale three spec versions running — 308 events against 285, 47 findings against 51, eleven unaddressed weaknesses against ten. A block written in the present tense belongs after the present tense it describes. *Refreshed after a pre-build independent audit of 0.2.1 by a session that had no part in the specification. Two entries were retired because that audit discharged them: the severity tool is built and pushed, and the four concrete Claude API assertions were verified against current documentation rather than recalled.* *Refreshed again at 0.29.0, after the phase-4 audit: seven statements below described a state the project had left, and each now says what replaced it (D159).* *Refreshed at 0.30.0 for D160: the sibling's version line, pushed since, and the judged tier's result, which now carries every entry's catch record.* *Refreshed at 0.31.0 for D161: the cost-figure entry, whose expected figure is now a requirement.* *Refreshed at 0.32.0 for D162: the judged tier's result, where two more entries count their middle value.* *Refreshed at 0.33.0 for D168: no entry below describes the resume, so none moved.* *Refreshed at 0.34.0 for D169: no entry below says what N measures, so none moved.* *Refreshed at 0.35.0 for D170: the cost-figure entry, whose expected figure now counts informed retries and names a stale log.* *Refreshed at 0.36.0 for D171: the scored-findings entry, whose cuts are now checked as the tool draws them.* *Refreshed at 0.37.0 for D172: the sibling's version line, pushed with this change.* *Refreshed at 0.38.0 for D173: no entry below describes a run log's header or how a run is recognized as held out, so none moved.* *Refreshed at 0.39.0 for D174: no entry below describes what the absence check reads or where a held-out run's paths may point, so none moved.* *Refreshed at 0.40.0 for D175: the judged tier's entry says agreement is not achieved and `JUDGED_AGREEMENT_PENDING` stays open, which D175 leaves true, so none moved.* *Refreshed at 0.41.0 for D176: no entry below describes the phase verifiers, so none moved.* *Refreshed at 0.42.0 for D177: the held-out set's entry, whose sentence on its labels had outlived the tag it waited for.* *Refreshed at 0.43.0 for D178: the one entry below naming the interface scanner records an audit finding about its key list that did not hold, which D178 leaves true, so none moved.* *Refreshed at 0.44.0 for D179: the entries below that count or describe informed retries describe recorded runs, and D179 changes no recorded request, so none moved.* *Refreshed at 0.45.0 for D180: no entry below quotes a verifier's caveat, so none moved.* *Refreshed at 0.46.0 for D185: no entry below describes where a report may be written or what the absence check reads, so none moved.* *Refreshed at 0.47.0 for D186: no entry below describes what a run log's header carries or what pins the rubric, so none moved.* *Refreshed at 0.48.0 for D187: the scored-findings entry below reads the committed export as scoring every defect-tier finding with an empty `unplaced`, which D187 leaves true, so none moved.* *Refreshed at 0.49.0 for D188: the deterministic tier's entry, whose sentence said nothing here computes the coverage by severity, which D188 builds.* *Refreshed at 0.50.0 for D189: the scored-findings entry, whose mechanism sentence said the suite recomputes each row's hash, which the harness now does for the suite and the coverage report alike.* *Refreshed at 0.51.0 for D190: the sibling's version line, which now names the tool at 0.10.1 and its D36; the scored-findings entry describes the committed export's rows, cuts and `unplaced`, which the re-export left unchanged, so it did not move.* *Refreshed at 0.52.0 for D191: the deterministic tier's entry, whose sentence said nothing measured whether its entries generalize to the held-out set, which phase 5's held-out coverage now has.* *Refreshed at 0.53.0 for D192: no entry below describes the coverage report's table, so none moved.* *Refreshed at 0.54.0 for D193: no entry below describes the entities register or what its checks read, so none moved.* *Refreshed at 0.55.0 for D194: no entry below describes the sweep marker, so none moved.* *Refreshed at 0.56.0 for D195: no entry below describes what the absence check reads, so none moved.* *Refreshed at 0.57.0 for D196: no entry below describes where a command may write what it reads, so none moved.* *Refreshed at 0.58.0 for D197: no entry below describes what reads a run log's rubric hash, so none moved.* *Refreshed at 0.59.0 for D198: no entry below describes the register's vocabularies, so none moved.* *Swept at 0.60.0: the first sweep of this document since 0.21.0 read every entry below against today rather than against its own refresh sentence, and **seven moved** — the held-out labels, which are sealed and published rather than unrecorded; the deterministic tier's generalization, measured on 2026-09-18; which of that entry's three claims D191 measured; the twenty entries with no negative instance, which are more than half of their own tier and not of the rubric; the sibling's pinned version, de-quantified on D74's rule; what "the audit" names; and the twelve taxonomy gaps, which phase 1 seeded. The sweep's report is `sessions/SWEEP-2026-09-19-phase-5.md`.* *Refreshed at 0.61.0 for D201 to D206: the judged tier's entry, whose two sentences said `JUDGED_AGREEMENT_PENDING` stays open and that OB-7 carries what closing it needs, which D202 closed with a firing table; no other entry describes the second adapter, the log inspector, per-instance severity or prompt caching, so none moved.* *Refreshed at 0.62.0 for D207: no entry below describes what the README licenses or what a check reads from this root, so none moved.* *Refreshed at 0.63.0 for D208: the entry below saying all three repositories are private, two of which are not any more.* *Refreshed at 0.64.0 for D209: the held-out entry below reads that the tag exists, which it does here and no longer in the published snapshot, and the sentence is about the labels rather than about what resolves the freeze, so it did not move; no other entry describes what a citation of the freeze resolves against.* *Refreshed at 0.65.0 for D210: no entry below describes what the freeze proof carries or what recomputes a hash from it, so none moved.* *Swept at 0.66.0: the first sweep of this document since 0.60.0 read every entry below against today rather than against its own refresh sentence, and **three moved** — the license entry, whose enumeration predated the README's per-path licensing (S-18); the entry saying what *the audit* names, which listed four reports where six exist (S-19); and the held-out entry's sentence on the freeze tag, which a public reader meets in a copy where that name does not resolve (S-26). The sweep's report is `sessions/SWEEP-2026-09-22-publication.md`.* *Refreshed at 0.67.0: the repositories entry, which said the held-out companion stays private and had had no publication reading — it was published on 2026-09-22 — and which still described the snapshot as carrying a pin commit that D211 had removed the day before. No other entry describes a repository's visibility.* *Refreshed at 0.68.0: no entry below describes a token, or the procedure for installing one, so none moved.*

- **The reference implementation's source was not read**, by design (D6 and the handover's implement-first rule). Any lesson embedded only in that code and not in the handover's prose is therefore unknown to this spec. The handover claims the separation is clean; that claim is untested and is exactly what the post-build diff is for.
- **The prior third-party material was not read** (D6). The format specification is therefore designed from stated requirements rather than observed practice, and may omit a convention that would have been obvious from an example.
- ~~The audit did not read the handover either, and whether all 35 taxonomy items and W1–W35 are addressed or consciously deferred is unverified.~~ **Closed by D30** — mapped item by item in `specs/taxonomy-coverage.md`. What replaces it is narrower and real: **twelve taxonomy gaps and a list of unaddressed known weaknesses were recorded rather than resolved**, as corpus and check decisions for phase 1. Phase 1 seeded all twelve and phase 2 retired the deterministic weaknesses; `specs/taxonomy-coverage.md` carries each item's disposition now, and its **GAP** tally stands at zero.
- ~~**The 35-item taxonomy was not mapped to ticketing scenarios**; that mapping is a phase-1 deliverable and is where assumption 3 will actually be tested.~~ **Closed by the phase-1 build** — `specs/taxonomy-scenario-map.md` maps all 35 plus the twelve recorded gaps to concrete ticketing scenarios and allocates each to a named call. **Assumption 3 is discharged with one qualification**: no scenario was forced and nothing had to be invented outside the domain, but items 12, 16 and 25 are cross-corpus by construction, so the corpus supplies raw material rather than instances and sufficiency cannot be known until those checks exist.
- ~~**Cost figures are estimates**, derived from token-count arithmetic rather than a measured run. No live call has been made.~~ **Closed 2026-09-09.** Three full live passes over the design set — 480 judged calls — put real numbers against the arithmetic, and the arithmetic was wrong in both directions. **A pass costs about $1.60, not the $12–16 band this entry defended**: that band assumed six judged dimensions where one exists, and a prompt far larger than the ~1,900 input tokens the shipped corpus actually renders. And the CLI's own pre-flight estimate, when first written, used constants that overstated input by about three and a half times — wrong in the direction that makes a reader approve more spending than they were told, at the one moment a human is asked to agree to it.

  What replaced this entry was narrower: **the estimate was derived rather than assumed** — it renders every prompt, counts characters, and bounds output at the entry's own `max_tokens` — and nothing compared it against the actuals the run log records. **That is closed too.** `test_the_preflight_estimate_brackets_what_the_real_run_recorded` holds the estimate against the committed log per entry and per call (D142), and the pre-flight prints an expected figure beside its ceiling, priced from the answer lengths the same log recorded (D152). It has been a `[P4]` requirement since D161, and since D170 it counts the informed retries the same log recorded and names a log recorded under another rubric version or prompt template.

  **This entry read "No live call has been made" until 2026-09-09**, after 480 of them, which is the shape this block exists to prevent — and no guard caught it. The document mechanisms in this tree verify that identifiers resolve and that counts agree; none of them reads prose for truth, and this sentence was true prose about a state the project had left.

- ~~**The corpus does not exist**, so nothing about its adequacy, its defect seeding, or assumption 3 (that event ticketing supports every defect class) has been tested by anyone.~~ **The corpus now exists** — sixteen design transcripts, **408** events, parsing with a zero unparsed-line count. What replaces this entry is narrower and real: **the corpus has been authored by one session and reviewed by nobody.** Its defect seeding is recorded in `corpus/seeding-manifest.md` and asserted by machine-checked anchors, but whether the seeded defects are *good examples of their categories* is a judgment no test makes.
- ~~**The three repositories are private.**~~ **Two of them are public as of 2026-09-21.** `comparative-judgment` was flipped with its history, which carries nothing private. This project is published as a **snapshot** built by `tools/make_public_snapshot.py` (D208): the working repository is private under another name, and what a reader finds under `voice-agent-eval-harness` is one commit of the clean tree, with `SNAPSHOT.md` saying so — two commits until D211 dropped the pin rewrite the second one carried. **The held-out companion was published on 2026-09-22**, after a full-history scan on that side, so three of the four are public and the freeze proof's chain closes in public: its seal commit's citation and this project's published opening are both readable by a stranger, which is what property (a) needed and did not have. Nothing in the tree checks any of this, deliberately: it is a fact about GitHub rather than about the repository, and the mitigation is that the statements which depend on it carry their trigger.
- **`comparative-judgment`'s current defect state is not claimed.** It is built, swept twice, audited and pushed, its version its own specification's to state (D74) — but the audit that found its 41 findings has not been re-run since they were fixed.
- **90 rulings, and none of them a rejection.** 63 `accept`, 27 `accept-with-edits`, zero `reject`, and two rulings that changed a classification. Recorded rather than left for a reader to notice, because D38's argument predicts exactly this observable when a process collects agreement instead of judgment. The reading that fits the history: these drafts had already been through two rounds of human corpus review and the D45 and D49 re-cuts before adjudication began, so the rows arriving were not first drafts. What is *not* recorded anywhere is a row where rejection was weighed and declined, and the `reject` code path went unexercised until an independent sweep simulated one and found it broke two tests. Both are fixed; the zero stands, and stands stated.
- ~~**The candidate findings are unadjudicated, and the gold set does not exist.**~~ **Closed 2026-09-01.** The corpus carries **90** findings, all adjudicated in `corpus/findings.adjudication.yaml`, one entry per id with its reasoning, and `corpus/findings.yaml` is generated from the drafts and the ledger by `tools/make_gold_set.py`. What replaces this entry is narrower and real: **the gold set has been made by one person and reviewed by nobody else**, exactly like the corpus it describes. Its rulings are recorded rather than merely asserted, which is what makes disagreeing with them possible — but no second reader has.
- ~~**The design-set findings have not been scored.**~~ **Closed 2026-09-05 (D82); reopened and re-closed 2026-09-10.** `corpus/findings.severity.json` scores all **83** defect-tier findings with an empty `unplaced`, is joined by the suite rather than by a fixture, and a clean `cj load` reports admitted **83** and excluded **7** question-tier entries by name. **It spent part of one day describing a document it no longer matched**: F-90 arrived with no band, and F-42, F-88 and F-89 carried bands judged against wording `e28650c` had changed underneath them on 2026-09-07. `cj load` refused, which is the detector D82 named doing its job. The owner accepted the three revisions and placed F-90 the same day — neither act being a model's to perform, because a pairwise comparison and a revision acceptance are human judgments by construction (D10). **What that placement then exposed is D144**, and it is the part worth carrying forward: two of the three band cuts had to be re-drawn, because placing a new finding against the cuts compares it to the cut anchors and therefore moves them. OB-18's second half, the mechanism, is closed: every row carries the hash of the text it was placed on and the harness recomputes it, for the suite on every run and for the coverage report before it counts a band (D148, D189), and the file carries its cuts, re-derived on load (D156) and refused where the tool could not have drawn them or where they contradict a row's band (D171). What replaces this entry is narrower and real: **the ordering those bands encode was produced by one person and reviewed by nobody**, exactly like the corpus and the gold set it scores; and D82's own subject stands, that the file attests to the comparison log rather than to what was compared, so a store edited between export and read is caught by the log hash and a *judgment* changed inside a comparison is not — to which D140 adds the third case this entry is reopened for: the compared **text** moving in the repository while the log and its hash both sit still. **This entry said scoring "has not been taken" until 2026-09-07**, two days after it had, in the block whose job is to stop the next session rediscovering settled scope.
- ~~**`voice-agent-eval-harness-holdout` has not been examined** by author or auditor — not even listed.~~ **Now populated**: the held-out set, authored directly there and never present in the main working tree, with `tools/check_holdout_absence.py` asserting that on every build. **This read "five transcripts" until 2026-09-07**, after `CALL-21` joined the set at D86; de-quantified rather than re-pinned (D74), and `HELDOUT_SET` is the declaration a reader should go to. Their labels could not exist before `rubric-frozen-v1` (D21); that tag exists in this working history and not in the published snapshot, where its object is carried by `freeze-proof/` instead (D209), and the labels were sealed at C1 on 2026-09-17 and revealed on 2026-09-18 (D177, O-9). **This read "do not exist and must not" until 2026-09-15**, a trigger that fired at the tag with nothing reading it. Unreviewed by anyone but their author, like the design set.
- **`subject_index.py` is absent** from this machine's installed copy of the toolkit, so the STEP 8 sweep's subject-index check cannot be run here. A future sweep should either obtain it or record the check as unavailable rather than silently skipping it.
- ~~**Eight defects from the 2026-08-29 independent audit are recorded and not fixed.**~~
  **All eight closed at 0.17.0 (D62)**, each re-reproduced first and each covered by a test where a
  test was the right closure. They are listed in D62 rather than here, because an entry in this
  block is a scope decision and these are no longer one.
- **The 2026-08-29 audit report is not in this repository.** It is held outside it, and carries
  44 findings, of which 36 were actioned across D51–D60 and the remaining eight at D62 — this
  sentence said they "were not" for as long as the line directly above it said they were.
  **The later 2026-09-06 report is tracked here**, with a maintained status banner, so "the audit
  report" now names two documents kept two different ways: that one outside, this one in. **Three of its findings did not hold** and are
  recorded where they were disproven: the claim that widening the held-out scan's suffix list would
  turn it red (D52), that the interface scanner had drifted two keys behind the code (D54), and
  that the coverage document's twelve-gap breakdown accounted for eleven (D53). That ratio is the
  argument for reproducing before acting, not against commissioning audits.
- **The deterministic tier covers every `detectable_by: assert` finding, and covering them all is not the same as covering the corpus.** 37 rubric entries, one firing set each, asserted equal in both directions against the calls the gold set names. What that does **not** say: that the `judge` and `human` findings are reachable from here (they are not, by classification), that the entries would generalize to the held-out set, or that a phrase list is the right abstraction for a claim rather than one that happens to separate sixteen transcripts. **The second has since been measured, and they do not**: on the held-out calls most entries targeting a defect's kind did not engage, recognizing it only in the design set's own words, and phase 7 is widened to answer it (D191). The coverage by severity that says which findings matter most is computed by `harness coverage` since D188, per band and for each set apart; over the design set it is in sample, which the report says beside its figures. **This entry said 45 of 61 with sixteen named until the tier was finished**, which is the shape this block exists to prevent — a scope note outliving the scope.
- **Twenty of the rubric's entries declare that no negative instance exists** (D107), each with a reason. *(De-quantified 2026-09-09: the denominator was written as `37` and the rubric grew to 38 when the judged entry landed. The numerator is the live claim and the denominator was decoration, so it is gone rather than maintained — D74's rule.)* That is more than half of the deterministic tier, and the proportion is the honest reading of a sixteen-call corpus: most checks are the only one reaching their comparison, so there is no call where the check applies and comes out clean. Their precision therefore rests on the mutation controls rather than on a true negative, and the ones that *do* have a true negative — CALL-11 for the completion claim, CALL-19 for the record comparison, CALL-20 for the repeated request, CALL-02 for verification — are the entries whose false-positive rate is actually measured against the corpus. A list that were empty by construction, because the field defaulted, would be the defect; a list this long is a statement about the corpus rather than about the checks.
- **The rubric has been written by one session and reviewed by nobody**, exactly like the corpus and the gold set it scores. Its signal lists were derived by reading every agent turn rather than invented, and each is asserted against the calls the gold set names — but whether a phrase list is the *right* abstraction for a claim, rather than one that happens to separate sixteen transcripts, is a judgment no test makes.
- **The phase-2 audit's remediation is audited at the `src/` seam and not below it (D121).** The report at `sessions/AUDIT-2026-09-07-phase-2.md` was written against `6dc2033`; **twenty-five commits closed its seventeen findings**, recorded as D114–D119, and **no verdict moved**: 555 results before, 592 after CALL-22 joined. That is the signature of latent defects and equally the condition under which a *wrong* fix is invisible. What the sweep can now say: each of the 9 remediation commits touching `src/` was reverse-applied into a copied `src/` and the suite run against it, which puts 12 controls at `connected` **by demonstration** rather than by reading. What it still cannot say is per-control: two reverts abort collection because they remove a symbol the tree imports, and a revert breaking 196 tests is weak evidence about any one of them. `CONTROL-REGISTER.md` carries the verdict and the evidence for every row, including the rows it declines to settle.
- **Seven more controls were measuring nothing, and both register tables are now audited.** The two the phase-2 sweep found were joined by six here — one of them written by this audit itself, in the register's own guard — and **none of those was found by rereading either** — all had survived every prior audit. All are one shape: **a control that re-implements the rule beside the check instead of calling it**, which makes it proof about its own copy of the logic. The control-character sweep's control was blind to the extension filter it named; the anchor control never moved an event; the leak-scan control was a tautology whose seam two neighbors were quietly covering. All three are repaired, and each is now re-derived by `tools/verify_controls.py` rather than asserted here. **A null result from an instrument that is not connected is indistinguishable from a finding** — and the instrument for this sweep failed that test first, `git apply` exiting 0 while skipping every hunk. What is *not* known is a base rate: all three were picked out by the same screen, so the sample is selected rather than random, and every row the register marked `unaudited` was a control whose connection nobody had tested — **the register now marks none**, and the control gate re-derives every entry in `control-mutations.yaml` on each run.
- **The continuity documents are under no license line, and the move made that sayable without saying it.** The README draws the boundary as a path on D31's argument that one which cannot be drawn as a directory is one no reader can check: code, configuration and tooling Apache-2.0, authored data and documentation CC BY 4.0, with every top-level path named since D201 and the check's population corrected at D207. The audits, handovers and briefs sat in the root, which is named on neither side, so they were already outside it — and now that they are `sessions/` the boundary they need is a single word, which is exactly why leaving it out is a choice rather than an oversight. Assigning a license is the owner's, not a refactor's.
- ~~**No judged verdict in this repository has come from a model.**~~ **Closed 2026-09-09** by three
full live passes over the design set, 480 judged calls, every one returning `end_turn` with no
truncation, no refusal and **zero informed retries**. What replaces this entry is narrower and real,
and it is the phase's actual result rather than its mechanics.

  **The judge catches two of the three seeded misalignments and misses the third.** F-08 on CALL-02
  and F-17 on CALL-04 are caught; **F-85 on CALL-19 is missed on every repetition of every pass** —
  the subtlest of the three, needing the judge to notice that a retrieved clause's *anchor* is absent
  rather than that a figure is wrong. So **agreement is measured and not achieved**. `JUDGED_AGREEMENT_PENDING` in
  `tests/test_rubric_coverage.py` stayed open on that ground until D202, which closed it without
  claiming agreement: the judged family's firing on the committed log is pinned as every other
  family's is, with its 19 false alarms and this 1 miss recorded by name, and blind agreement stays
  the held-out section's. The miss is pinned by `RECORDED_MISS` so it cannot be closed silently,
  and it is deliberately **not tuned toward** (D125).

  **Every judged entry's catch record is now pinned, per finding** (D160). Each traced finding either
  counts against its entry's gate on its call or it does not, and
  `test_every_traced_finding_is_caught_or_missed_as_recorded` fails when any one moves; all are caught
  except F-85. **`J-concerns-addressed` caught none of its 7 until D160 counted `partially_addressed`
  against its gate**, which the phase-4 audit's re-verification found and no test did. What replaces
  that is narrower: the entry's definitions of its two violating verdicts overlap on a call where one
  concern of several went unanswered, which no longer moves the gate, and 3 of the 8 calls it now fails
  on carry no finding it traces — CALL-19 plausibly on F-86, which another entry traces, CALL-20 on a
  tie, and CALL-18 as a false positive. **D162 counts the same middle value on `J-policy-alignment` and
  `J-caller-pushback-understood`**: the first moves no call of the committed log, and the second now
  fails CALL-09, which carries no finding it traces; the pushback all 10 of its repetitions fault is
  F-36's, which `A-deadline-never-resolved` traces.

  **The prompt has now been read by a model, and that is the last thing that was unknowable without
  spending.** Whether it generalizes was measured on 2026-09-18, on the held-out set: most entries targeting
  a defect's kind did not engage, recognizing it only in the design set's own words (D191). The
  figures went to the owner and are not in this tree (D175), which is why D202 closed
  `JUDGED_AGREEMENT_PENDING` on a firing table over the committed log rather than on a figure.

  **A second known defect was recorded here, and is fixed:** the dimension conflated a
  misparaphrased clause with a policy term stated when nothing was retrieved, flagging CALL-06,
  CALL-07, CALL-09 and CALL-18 — none of which retrieved a policy at all. A criteria edit was
  attempted and reverted; the structural fix landed at D132, a precondition under which the
  dimension does not apply to a call that retrieved no clause. CALL-22 is a separate boundary
  case, with clauses present and verdicts moving between passes, which is what N=10 exists to
  reveal.

  **The citation validator has fired exactly seven times, all of them on a defect this project
  introduced.** Runs 1 and 2 produced zero fabricated citations in 320 calls; run 3's reverted
  criteria edit pointed the judge at a facts section that was empty on those calls and it cited `F1`
  anyway. Each was caught by set membership, retried once with the rejected identifier and the full
  valid set, and answered validly. So the informed-retry path has been exercised by a real model --
  and the honest reading is that it took a self-inflicted defect to exercise it. Against the shipped
  criteria the validator has found no true positive, which is stated because "the detector never
  fired" and "there was nothing to detect" are the two readings the reference implementation could
  not tell apart.

- **"The audit" names one report held outside this repository and every `sessions/AUDIT-*.md`**, each tracked with a maintained status banner, and none has been audited. The 2026-08-29 report is held outside this repository; the reports tracked here, each with a maintained status banner, are every `sessions/AUDIT-*.md` — which the opening clause already says, and an enumeration beside it went stale twice, reading four while six existed. Each read one side of the three-repository topology in depth. Every finding acted on was reproduced first — and **three of the phase-2 report's seventeen needed correcting**: two counts, and one item that clears CALL-09 if taken literally. That ratio is the argument for reproducing before acting, and for a second pass reading work the same two perspectives have already reviewed.

---

## Document status

Decisions **D1–D212** recorded. **D212 retires both read tokens and widens the secret guard** — reading across a repository boundary needs no secret once the far side is public, the checkout passes no token rather than OR-ing a secret with the default one, and a workflow that reads no secret must sit beside a README that says so, since the guard's old rule refused an empty population as a comparison of nothing, on the owner's decision. **D211 has the published snapshot rewrite nothing** — the pin it used to re-point at its own first commit made the held-out commands refuse the real labels there, and the tag invented for the same reason turned the public build red on all five of its runs; two tests that ask git for the freeze now skip where a snapshot's log does not contain it, and the proof carries what they check, on the owner's decision at the 2026-09-22 sweep. **D210 adds the frozen `src` to the freeze proof, because the held-out gate computes the prompt-template hash by running the frozen harness rather than reading a number** — the whole frozen subtree is published object by object, named by id, and the verifier reconstructs it and runs that probe, holding the hash to the published value and to the one the committed reference run log recorded, on the owner's decision. **D209 publishes the freeze as its own object bytes and stops the snapshot reusing its tag name** — the held-out repository cites the freeze commit's SHA to prove the rubric was frozen before its labels existed, D208's snapshot left that SHA unresolvable and its reused tag naming a later commit, and `freeze-proof/` now carries the commit, its tag object and the two trees reaching the frozen rubric and template, verifiable with no history at all, on the owner's decision. **D208 publishes this project as a snapshot rather than as a rewritten history** — twelve session documents named a directory path from the machine the work was done on, the working tree was one commit to clean and five commits of history were not, and a rewrite would have falsified the freeze pin, its tag, the held-out repository's label commits and several dozen documents citing commits as evidence; `tools/make_public_snapshot.py` builds the published tree and refuses a file carrying an absolute path it has not been told about, on the owner's decision. **D207 has the license check read this repository's trees** — a directory carrying its own `.git` is a sibling's working copy, which CI puts inside this root, and reading it as an unlicensed path turned `main` red on a true claim about the wrong population. **D201 to D206 open phase 6 by reading its contract before anything was built** — the reading found the second adapter's requirement with no criterion and unmeetable as written, the caching requirement unsatisfiable under the frozen prompt, and two requirements covered in half, and the owner decided each: phase 6 goes from 4 requirements and 4 criteria to 5 and 12, joins the coverage table, and has a verifier declaring what is unbuilt (D201); the one-tier tracing convention stays for both existing sets, phase 6 reports under it and says so, and a firing table over the committed log closes `JUDGED_AGREEMENT_PENDING` (D202); the second adapter is Retell's call object, identical to the text adapter where the source carries an event and declared where it does not, which took the event model to v3 (D203); prompt caching is shared across a dimension's repetitions, because the frozen template puts each dimension's question ahead of the transcript (D204); the log inspector emits counts and proportions and exits on whether it could read the log (D205); and per-instance severity is a monotone decision list over what kind of harm an entry means and what happened in the call (D206). **D200 makes the design document phase 6's** — four sentences described one in the present tense and none exists, so the phase that has not started owns it and the sentences say will, on the owner's decision. **D199 has the close's own test read a status line in either form this project writes** — the specification sweep found that closing the reveal handover in place would have left the *at phase completion* clause unevaluated, and the check was driven red both ways before the close relied on it, on the owner's decision. **D198 declares the vocabulary the register's result keys carry** — two reason codes and a remedy the design corpus names and no register knew, with a check that refuses the next one, closing the phase-5 audit's P5-11 on the owner's decision. **D197 has the two commands that score the held-out labels refuse a log judged under another rubric or under none** — in the replay both share, with no override and for a held-out set alone, closing the phase-5 audit's P5-5 on the owner's decision. **D196 has extraction and the findings view refuse to write held-out content inside this checkout** — by a declared call or a finding id's shape, with the declaration and the refusal moved into one module the commands share, closing the phase-5 audit's P5-2 on the owner's decision. **D195 has the absence check read every encoding a redirect writes here and fail closed on a file it cannot decode** — and read the held-out artifacts it had no reading for: a record laid out across lines, an extraction artifact, the three label files, a findings view and agreement's held-out section, closing the phase-5 audit's P5-1 and P5-4 on the owner's decisions. **D194 has the sweep marker name the version a sweep was recorded at** — from 0.55.0 it moves only to a version whose changelog entry says it records a sweep and what the sweep read, closing the phase-5 audit's P5-7 on the owner's decision, with the whole specification swept at phase 5's close. **D193 declares the values the design corpus carried and the register did not** — five identifier shapes and the settlement token of its one processor, with a check for each kind that fails on a value the register does not declare, closing the reveal handover's first two items on the owner's decision. **D192 splits each band of the coverage report by detection type** — one row per type beneath each band, all three always printed and nothing totalled across bands, with the requirement and the command's criterion gaining it, all on the owner's decisions. **D191 records that the deterministic tier recognizes a defect only in the design set's words** — the held-out coverage, diagnosed with the owner, found most entries targeting a defect's kind not engaging on unseen calls; no version-2 cycle starts now, and phase 7 is widened to move the tier onto the parser's structured claims and measure it on a fresh, larger held-out set, all on the owner's decisions. **D190 closes OB-23 by assigning the design store's bands** — the producing tool's D36 builds the freeze its D2 promised, this store was backed up and its 83 bands assigned once under the owner's name, and the committed severity file moved on `comparison_log_hash` and `run_id` alone, on the owner's decisions. **D189 moves the content-hash recheck into the harness** — one function recomputes the scoring tool's hash, the suite's test reads it, and the coverage report refuses a set holding a band placed on text that has changed since it was scored, naming each finding, all on the owner's decisions. **D188 builds the coverage report by severity** — a finding is retired when an entry traced to it fires on its call, each band of each set states how many findings it holds, traces and retires, the uncovered and the missed are named apart and the findings with no band beside them, and a held-out section goes to stdout alone and is read by the absence check as a fourth shape, all on the owner's decisions. **D187 keeps question-tier findings out of `unplaced`** — that list is for findings in scope nobody compared, a question entry is excluded before scoring so it carries no band, and the coverage report counts and names them rather than leaving them out of both, on the owner's decision. **D186 has a held-out run's header name the rubric it judged under** — hashed over the file read as text, refused here when a log names another or none with no override, and `rubric.yaml` and the prompt template pinned at HEAD to the freeze commit, on the owner's decision. **D185 keeps a report over held-out calls out of this tree** — `harness report` refuses an `--out` path inside this checkout over any call `HELDOUT_SET` declares, stdout and paths outside it stay open, and the absence check reads a rendered report as a third shape, on the owner's decisions. **D181 to D184 answer the held-out session's questions about the label chain** — the severity export's schema stated as this repository's loader pins it, a held-out run carrying the held-out set's own corpus version from a file outside this checkout, a header naming the rubric a held-out run judged under in place of the trailer that side offered, and a log this repository names with the prefix that side's gate admits, all on the owner's decisions. **D180 has a verifier's caveat state what its tick does not buy** — every verifier's history sentences leave for the decisions that record them, phase 4 keeping 6 caveats and phase 3 7, and a test refuses the two history markers found, on the owner's decisions. **D179 has the informed retry name every fault an answer shows** — validation reads every fault it can, the correction states each in its existing wording with the rejected identifiers first, a single fault's retry stays the request the committed log recorded, and the `[P3]` retry requirement and its criterion say so, on the owner's decisions. **D178 has the interface scanner read each list from the sentence that enumerates it** — findings keys, top-level severity fields and row fields are compared as the exact sets each side's specification lists, a list sentence missing or stated twice is refused, and this specification's row sentence names the fields it had called the band, on the owner's decision. **D177 records the held-out label chain and settles what it still owes** — its labels manifest, this harness's held-out run log and the reveal, in that order under the held-out repository's gate, recorded as reported; the rule against searching the held-out labeling sessions is a standing duty in the register, phase 5 scores held-out severity in a separate store sealed before the held-out judged run, the register opens O-9 and O-10 and records O-11, and the coverage criteria name the sets apart, all on the owner's decisions. **D176 runs a phase-5 verifier while its phase is open, declaring what it cannot tick** — four criteria built here are ticked, three the held-out repository's gate asserts and two not yet built are declared under their own heading and never ticked, and a criterion both ticked and declared is refused, all on the owner's decisions. **D175 counts agreement per rubric entry, with the design set and the held-out set apart** — `harness agreement` reports hits, misses, false alarms, correct silences and calls with no verdict for each entry over each set's calls, reading a judged entry as its gate does, and re-checks held-out labels against every invariant their traces state and a pinned `rubric-frozen-v1` commit, all on the owner's decisions. **D174 keeps a held-out run's paths, and its log, out of this tree** — a held-out run is refused `--transcripts`, `--run-log-dir`, `--run-log` or `--resume` inside the repository before anything is written, and the absence check reads every file whole for a run-log header naming a labels manifest or a call record for a call `HELDOUT_SET` declares, all on the owner's decisions. **D173 gives a held-out run's log the labels manifest the held-out repository's gate reads** — a judged run over calls `HELDOUT_SET` declares needs `--labels-manifest` and writes it into its header as `labels_manifest`; a run mixing declared and undeclared calls, a design run given the flag, a malformed value and a root with no `HELDOUT_SET` are refused, and a replay or a resume whose log names another manifest or none is refused with no override, all on the owner's decisions. **D172 rewrites the design store to LF and re-exports it** — the tool's D35 hashes the log without its line endings, this store was backed up and rewritten once with every parsed record unchanged, and the committed severity file moved on `comparison_log_hash` and `run_id` alone, on the owner's decisions. **D171 has the severity loader refuse a cut the producing tool could not draw, and a band its cuts contradict** — every cut shape the tool's placement refuses, an empty or partial cut list with them, and a row whose band its `theta` and the midpoints contradict, all on the owner's decisions. **D170 counts the informed retries the reference log recorded in the expected figure, and names a stale log beside it** — each entry's calls are multiplied by the calls per first attempt that log recorded, every multiplier above one is printed, and a log recorded under another rubric version or prompt template is named with its differences, all on the owner's decisions. **D169 says what N measures per entry, and stops quoting a cost figure every recording moves** — the report's caveat and the specification's prior-decisions line say the synthesis's repetitions also vary with their resampled input, and OB-17's evidence names its log and test in place of figures, all on the owner's decisions. **D168 refuses a resume log answering none of the dimension requests a run would send before spend is approved, and has the run say what it served** — the pre-flight counts the dimension requests the log answers, the run's end prints the answers served and the calls issued, and the `--resume` requirement gains both with D167's torn tail at 0.33.0, on the owner's decision. **D167 refuses a torn run log by file and line, and lets a resume read to its last complete record** — only a torn final line is dropped, and the resume says so. **D166 reads a deferral's trigger against what has happened** — a tag trigger carries `fired` and its date once the tag exists, checked in both directions, and a trigger nothing can observe says a person reads it, on the owner's decision. **D165 asks a synthesis for `rests_on` only when its prompt listed a dimension**, so a synthesis shown none is no longer held to naming one its prompt tells it not to invent, on the owner's decision, with no recorded request changed. **D164 has the informed retry name the schema failure it was sent for, and show a synthesis corrected for one the dimensions it may rest on**, both on the owner's decisions, with no recorded request changed. **D163 refuses a judged answer citing nothing, and a synthesis resting on nothing**, each as the declared schema's failure spending the one informed retry, fixed before the tag on the owner's decisions. **D162 carries D160's reasoning to the two entries its words also decide** — `J-policy-alignment` and `J-caller-pushback-understood` count their middle values on the owner's decision, the 3 synthesis requests that changed were recorded again under a ceiling agreed first, the catch record reads the roll-up, and the frozen entries name the calls they fail without a traced finding. **D161 closes the two contract gaps the phase-4 audit's re-verification found** — the expected figure gains a requirement and a criterion, and the resume criterion names all three refusals with a caveat saying what its header clause does not buy, both on the owner's decisions. **D160 is the phase-4 audit's re-verification arriving in the rubric** — a judged entry may count more than its negative pole against its gate, `J-concerns-addressed` counts its middle value on the owner's decision, and the 7 synthesis requests the tie rule sends differently were recorded again under a ceiling agreed first; D158's scope note carries the correction that led there. **D159 sweeps the specification at 0.29.0 for the phase-4 audit** — the judged tier's exit code and the verifier list corrected, the `Not checked` block refreshed rather than re-dated, and `--resume` entering the contract as a `[P4]` requirement and criterion on the owner's decision. **D158 is the phase-4 audit's P4-1 and P4-8, on the owner's decisions** — the judged tables count every result that produced no verdict beside a rate that stays per call, a call's outcome prints its statuses beside its verdicts, and a judged entry is found on a call by its modal verdict, the one the gate reads. **D157 is phase 5's contract, read before the phase opens** — its one requirement is covered in both halves, and the owner added two criteria: the label commit's freeze-SHA citation, which D21 chose as property (a)'s evidence and no criterion asserted, and coverage stated per band in place of a weighting nobody had defined. Phase 5 joins phase 4 in the coverage table. **D156 is OB-19's harness half** — the severity file carries every cut's anchors, gap and the findings strictly between them at schema 3, the loader re-derives each between-set and gap from the file's own `theta` and refuses a file that disagrees with itself, and a test pins today's separation, all on the owner's decisions; the freeze-and-propose rule D2 in the producing tool describes, which would stop every silent re-banding, is registered as OB-23 rather than built. **D155 sizes the synthesis's ceiling apart from the dimensions'** — its first resampled recording truncated one answer at 8192, and the owner raised that entry alone to 16384 rather than every entry, because the synthesis is now the one entry whose prompt varies by repetition. **D154 is OB-22's resample** — each repetition of the synthesis reads its own resample of the dimensions' answers rather than all of them reading one draw, and a tied dimension's headline follows the report's rule; both are the owner's decisions, and the falsifier the change is judged by is committed ahead of it. Every condition cleared, the synthesis now splits on 6 calls where it split on 2, and no call's modal verdict moved. **D153 is OB-20's resume** — an aborted live run's log is resumed rather than paid for again; the header keeps `mode: live` and names the sessions a log was assembled from, and a resumed log may be the reference log, both of those the owner's decisions. **D152 is OB-17's second figure** — the pre-flight prints what a pass is expected to cost beside the ceiling it can cost at most, $15.00 against $112.56 on the committed log, pricing each entry at the answer length its first attempts recorded. **D151 is D143's own expectation corrected by the sweep it asked for** — three report controls were skipped, and once the snapshot let them run, one connected and two were blind: their tests read the committed artifact, so a mutation to the renderer could not reach them. **D150 is a hypothesis refuted by the run asked for to test it** — the synthesis's ten repetitions all condition on one draw of the other dimensions' results, so they are ten samples of a conditional rather than of the quantity the report prints. **D149 is four quotation checks that do not work and the narrow one that does** — two quotations turned out not to be quotations, and the obvious guard reports between 45% and 95% false positives because quotation marks in this prose do four different jobs. **D148 discharges OB-18 and OB-21 by reversing D82 on its own terms** — a second definition of one hash is drift waiting to happen while nothing compares them, and a cross-check once the producing tool ships its hash in the file the consumer already reads. All 83 findings agreed on the first run. **D147 is an obligation that went stale on the day it was written, by the session that wrote it** — half of OB-18 was discharged that afternoon and the register has three statuses, none of which says *partly done*. **D146 is the control register wrong about itself** — it said twenty of its rows are re-derived on every run where the file holds 92, in the one document whose whole subject is a claim going stale, and unguarded because neither the recall net nor the tagged-quantity registry had it in scope. **D145 is two live recordings lost to a seven-second retry window** — a 529 that `_is_transient` classified correctly and the schedule then failed to outlast, discarding 575 calls that had every one succeeded on the first attempt. What had been declared was the attempt count, and a count says how many times rather than how long. **D144 is what it cost to give one finding a severity band** — placing it against the cuts compares it to the cut anchors and therefore moves them, one cut inverted and was refused, a second silently stopped separating two neighbors and spanned a third of the scale, and the anchor that moved furthest was the one that had never lost. **D143 is the phase-closing control sweep pointed at itself** — five controls reported as measuring nothing, of which three had never run (pytest exits 0 for a skip, and the gate read silence as a pass), one had a mutation gone stale against a measurement that moved underneath it, and one was blind because two guards return the same exit code and the only case anybody tested tripped both. **D142 is four assertions meeting a rubric that grew** — three failing loudly since the second judged entry landed, and the fourth red on all sixteen calls for a defect that lived in one entry, which is the neighbor shape inverted: a guard wider than its rule is not blind, it is uninformative, and a reader trusts the message. **D141 names a class**, that the corpus modeled money leaving and never money arriving, on the second of two instances four days apart. **D140 is D82's open gap arriving**, three days after D82 wrote down what it would look like — a severity file committed alongside findings it no longer describes. It came not by the deliberate edit D82 was watching for but by a repository-wide spelling sweep with no reason to know that three of its seventeen files were also the subject of thirty human comparisons, which is the one route a trigger sentence addressed to a reader of `severity.py` cannot reach. **D139 resolves a conflict between two of its own neighbors** — a margin expressed as a multiple of what was observed cannot survive a ceiling that D137 stopped deriving from observation. **D137 and D138 are what the fourth pass cost** — a ceiling rule that had been fitted to a sample rather than to the entries, and an ambiguity in what *silent on a negative instance* means for a tier that answers N times, unnoticed since P3 because the one judged entry's negative instance happened to be unanimous. **D136 is what the first complete pass found** — one dimension of six flagging four fifths of the corpus including its own negative instance, which is an entry defect rather than a measurement, with its falsifier written to disk before the edit was made. **D135 is the one a live run found**, and it is phase 3's own lesson arriving in an entry of a different shape: `max_tokens` bounds thinking plus output, and a value fitted to a dimension whose prompt is a transcript truncated the one whose prompt is a transcript plus every tool event. **D130–D135 are phase 4's** — the contract check that opened it, the run-log format settled before it recorded, the precondition, the one judged dimension the corpus could not exercise as worded, and the roll-up that finally gives the judged tier a gate. **D132 lands D125's structural fix** — a judged dimension whose subject is absent from a call does not apply to it — and the fix turned out to reach twice the calls the defect had been measured on, because half of the conflation had come back on the dimension's positive side and nobody counts a pass. **D130 and D131 open phase 4** — the second settles the run log's format before the phase records its own, extending D128's referenced set to the third field it measured and did not include. **D130 opens phase 4** the way D104 opened phase 2 — by checking whether the phase's own acceptance criteria cover its own requirements, and finding four of five covered only in the half the requirement names, plus a whole deliverable carrying no criterion at all. **D127–D129 close an independent audit of phase 3**, which ran a mutation sweep rather than a reading and found seven fail-open-shaped defects the judged-tier suite could not see: what a judged run's exit code means, what shape the run log takes before P4 records its own, and the sweep trigger that has now fired twice with nothing watching. **D122–D126 are phase 3's**, all five taken during the build and the last of them after the first live run disagreed with the gold set: the SDK dependency and the transport posture it forces, where a judge prompt lives, and why N repetitions are reported individually rather than aggregated. **D104–D119 are phase 2's** — D104–D108 opened it, D109–D114 were taken during the build, and D115–D119 close residue an independent audit found after it; **D120 is housekeeping the phase left behind**, moving the continuity documents out of the root, and **D121 audits the controls the remediation rests on** — and D104 exists because a coverage check nobody had run found five P2 requirements whose criteria bought one half of each. **D64–D65 came out of adjudication rather than a build or an audit, and D69–D71 from an independent sweep of the finished gold set and the documentation sweep that followed it** — a reviewer asked what set a clause number in a tool call, which no document answered, and the audit that question forced found thirteen tool-call arguments with no origin in their own call. All six of the source handover's "Decisions owed" are settled: corpus size (D4, D17), transcript format (D5), judge-side injection (D7), license (D9), cost and key-free running (D8), AI disclosure (D10). D23–D29 close a pre-build audit, and four of them — D23, D24, D26, D27 — exist because a requirement's *machinery* was never written down, only its conclusion.

**D31–D34 are the first entries written during a build rather than before one**, which is what the build prompt's "decision records accumulated during the work, not reconstructed afterwards" asks for. Two of them exist because building found something reading could not: D32 records that the first pilot transcript's retrieved policy clause failed a byte comparison against the document it had been copied from, and D31 that the specification's package layout and its license split disagreed about where authored data lives. Neither was visible in the specification.

Spec: `specs/voice-agent-eval-harness.md`. Build prompt: `specs/voice-agent-eval-harness.build-prompt.md` (phase 1). That prompt is superseded at the end of phase 1; phase 2's contract was the specification's `[P2]` requirements and criteria, as amended at D104, phase 3's is the `[P3]` set in the same shape, and phase 4's is the `[P4]` set as amended at D130.

Any new fork encountered during the build is to be appended in the same shape — fork, options considered, decision, why, consequences — so this record does not go stale. Numbering continues from **D213**.
