# CLAUDE.md

## This project

Personal finance tracker (GitHub `daadil/Personal_Finance_Tracker`). A Python/pandas script that reads
bank and credit-card CSV exports, normalises them to one format and (planned) categorises, totals and
charts them. Started as a one-file script by Julia Wu (2023); David is taking it over.

- **Financial data never goes in git.** The CSV exports and the script's `Output/` are gitignored
  (see `.gitignore`). The script expects its inputs outside the repo, in a folder tree of
  `<account type>/<organisation>/<account name>/*.csv`. Never commit, paste into a doc or send anywhere
  a real transaction, balance or account number.
- Plans live in `project_plans/` (see "Documents" below). Nothing is built until the plan is agreed.
- Runs on the MacBook Air (zsh, throwaway venv outside the repo, `/venv/` is gitignored).

---

## How David works

**He reads code, he does not write it.** Code is documentation he audits by eye. So:
simple over clever, comments that say *why* rather than *what*, no abstraction that
exists only to be elegant. A function he cannot follow in one pass is a function he
cannot approve.

**"Commit" means commit to `main` AND push, in every repo.** No feature branches. An unpushed
commit lives on one disk, and work on a side branch is work he cannot see as landed. Never leave
work committed locally, or on another branch, and call it done. (Said 2026-10-17: "the commit
logic is for all repos and it's always for main.")

**Hand off commands as bare numbered steps.** He is executing, not evaluating. Put the
rationale in the docs and the commands in the message — not interleaved. If he has to
read three paragraphs to find the command, the handoff failed.

**Finish the current stage before offering the next one.** Do not start, plan, or
suggest later-stage work while the current stage has an unmet gate. He will ask when he
wants to move.

**Say what was tried and failed, not only what worked.** A session that reports three
successes and hides two dead ends teaches nothing and will be repeated by the next one.

---

## The brain vault is the master record of David

`~/Documents/GitHub/brain` (Obsidian). This repo's own docs hold the project; the vault holds what is
true about *him* across every project. At the start of a session read `About David.md` and
`Memory/MEMORY.md`, then the notes the task needs. Read `Private/preferences.md` (sizes, family,
gifts; local only, never on GitHub) only when personal details matter.

When you learn something durable about him, write it back to the vault in the same session: a
one-fact note in `Memory/` plus its index line, or a line in `About David.md`. PII goes only in
`Private/`. Stage vault paths by name, commit to main and push: the Obsidian Git plugin
auto-commits the rest every 5 minutes. Full rule: `Memory/brain-vault-is-the-master.md`.

---

## Measure, do not reason

**The single most reliable source of error is a number chosen by argument.**

Worked example, and it happened three times in one session:

- A name-similarity threshold set to 0.75 because it sounded strict. The exact pair it
  was written to catch scored **0.69** and passed straight through.
- A meaning-similarity threshold set to 0.80 for the same reason. The real case scored
  **0.701** and passed through too.
- Both times, the correct band was **already written down elsewhere in the repo** from
  an earlier measurement, and was not consulted.

So: before setting any threshold, interval, limit or timeout, **write the script that
measures it against real data**, and keep the script. If a number cannot be measured
yet, say it is unmeasured rather than picking one that looks reasonable.

**And when the measurement contradicts you, report the measurement.** Four separate
attempts to improve a classifier by giving it more information produced no change; that
non-result is now the most useful paragraph in the build plan.

---

## Compute before you act

**Any stage that writes somewhere durable gets a read-only stage before it.**

The pattern that worked: one stage computed a ranking and deliberately acted on none of
it, so the ranking could be judged while being free. The next stage wired the decision
logic as a **dry run over real data** and connected the write to nothing — printing what
it *would* do. Only then was it allowed to write.

That dry run caught a rule that would have silently filed three things wrongly. It cost
one afternoon and the mistakes would have been permanent.

**Corollary:** build the thing that *records* mistakes before the thing that can *make*
them. A feedback loop cannot be reconstructed from runs that did not keep the data.

---

## Boundaries beat flags

**If something must not happen, remove the means — do not add a check.**

- Two credentials, one per trust level, rather than one credential and a sensitivity
  field. A bug then picks the wrong *key* and the request is refused by something that
  is not this code.
- Two endpoints over one dataset rather than one endpoint with a filter. The boundary is
  which door you came through, not a field the code has to evaluate correctly every
  time.
- An agent that must never do X is given **no tool** that does X. A prompt saying "never
  do X" is a preference; an absent capability is a boundary.
- A denylist checked *before* the call, not after. A guard that notices afterwards has
  already spent what it existed to protect.

A flag is a promise the code has to keep every time. A boundary is one it cannot break.

---

## Alerting

**An alert that cries wolf gets ignored, and then the real one arrives.**

- **A deliberate hold is not a failure.** If a worker can succeed, fail, *or* wait for a
  person, it returns three outcomes — not a boolean. Returning `False` for "waiting"
  fires the failure alert every time the system works as designed.
- **Monitoring must not compete with what it monitors.** A health check that read
  through the same locked resource failed *because* the service was alive — the busier
  the service, the likelier the false alarm.
- **Alert on absence, not on events.** "Nothing has reported for N minutes" survives the
  failure of the thing that would have reported.
- **No daily all-clear.** A message that says "nothing is wrong" every day is the purest
  form of the alert that teaches you to ignore alerts.
- Word alerts for the person reading them at 2am. One of this project's alerts was
  reworded because it read like a security breach while describing a missing field.

---

## Verify on the real thing

A passing test suite is necessary and not sufficient.

- A schema migration is verified against the **existing** database, not a fresh one.
- A deployment is verified by asking the running process, not by reading the commit.
- A scheduled job is verified by checking the state it should have changed.
- `docker compose start` resurrects the old image; `up -d` recreates. An equivalent trap
  exists in every deployment tool — find it before trusting a restart.

If a result is surprising, **suspect the measurement before the system.** A diagnostic
reporting "no analysis exists" for thirteen items turned out to be checking a path that
only existed inside a container.

---

## Documents: one authoritative home each

The rule that keeps them usable: **every fact lives in exactly one file.** A fact in two
places is a fact that will disagree with itself.

**The project documents live in a `project_plans/` folder**, so the repo root shows what is
actually in the repo — code, config, `README.md` and `CLAUDE.md` — and the planning record sits
in one place beside it. `CLAUDE.md` and `README.md` stay at the root: Claude Code loads
`CLAUDE.md` from there, and GitHub renders `README.md` from there.

| file | holds | not |
|---|---|---|
| `project_plans/ARCHITECTURE.md` | what exists and how it works | why it was chosen |
| `project_plans/DECISIONS.md` | why, including what was rejected and what it cost | how it works |
| `project_plans/BUILD-STAGES.md` | the plan: ordered steps with verification gates | what happened |
| `project_plans/PROGRESS.md` | what actually happened, append-only, newest at the end | the plan |
| `project_plans/RUNBOOK.md` | commands and symbols for the person operating it | reasoning |
| `project_plans/ACTION-ITEMS.md` | known problems, **permanently numbered** | anything resolved in prose |

**Permanent numbers matter.** Items are referred to by number in commits and in
conversation, so a resolved item keeps its number and loses its detail block — the
reasoning moves to the commit message and to `ARCHITECTURE.md`.

**A stale note is worse than no note.** Two caught in one session: a gate table saying
four gates were open when two were, and an emoji reference describing one meaning for a
symbol that had since acquired a second and commoner one. When behaviour changes, the
document that describes it changes in the same commit.

**Put a pointer to the present at the top of any append-only file.** A 3,000-line log is
unusable without one.

---

## Build discipline

**Ordered steps, each with a gate, and never proceed past a gate that has not passed.**

A gate is a thing that can be observed, not a feeling. "Analyse a saved video" is not a
gate; "hook, pacing and differentiator are populated and the methodology is
implementable" is.

- **Some gates cannot be closed by writing code.** A week of a human judging output is a
  legitimate gate and is usually the most important one in the stage. Say so rather than
  finding a proxy.
- **Every stage ships tests for its own logic, and later stages keep earlier tests
  green.** That is the whole regression guard.
- **When a gate fails, report the failure.** Do not move the bar. A stage that fails its
  gate with an explained reason is more useful than one that passes a weakened one.
- **Map every acceptance criterion to a step.** Criteria with no step are the ones that
  silently never get built — and an orphan is often a sign the requirement has expired.
- **A requirement can expire.** One unit here existed to handle a cold start; by the time
  it was due, the system was no longer cold and its own exit condition was already met.
  It was recorded as superseded, with the reasoning kept, rather than built.

---

## Commit messages

Long, explanatory, and written for whoever is confused in six months — usually the
author.

The shape that works:

1. **A subject line that states the finding**, not the change. "Monitoring stops
   competing with the thing it monitors" beats "fix watchdog".
2. **What was wrong, and how it was noticed.**
3. **What was measured** — actual numbers, including the ones that did not support the
   change.
4. **What was tried and abandoned**, and why. This is the part that stops the next
   session repeating it.
5. **What is still unverified**, named as such.

If a defect was the author's own, say so plainly and move on. No apology, no
self-flagellation, just the correction and what it cost — that is what makes the record
trustworthy.

---

## Correcting the record

**Do not rewrite pushed history to tidy a mistake.** A `git add -A` once swept unrelated
work into a commit whose message described something else. The fix was a follow-up commit
explaining it, not a rebase — and a note to stage paths by name when a session may not be
the only thing editing the repo.

**Verify before telling him something is broken.** Three times in one session a confident
diagnosis was wrong: the measurement was at fault, not the system. State what was checked
and how.
