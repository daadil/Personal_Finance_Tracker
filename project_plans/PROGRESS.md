# PROGRESS

**Now:** Stage 0 code is built and tested on made-up data; waiting for real exports to close its gate.
Append-only, newest at the end.

## 2026-10-19
- Repo set up from the brain vault: CLAUDE.md, hardened .gitignore, branch renamed master -> main.
- `main.py` rewritten (D1-D4): inbox/ to master/master.csv, header preview, duplicate check by count,
  export deleted after load.
- `test_main.py`: 6 tests on made-up data, all pass.
- Not verified: no real export has been run. AMEX and Discover column names are guesses
  (ACTION-ITEMS #3).
- Two Capital One exports loaded (2024-10-21 to 2026-10-19). Dry run first, then the real run: 318 rows,
  no blanks, exports deleted, nothing visible to git. Capital One column names are now verified.
- 46 negative rows: 36 were card payments (payee "CAPITAL ONE MOBILE/AUTOPAY/ONLINE PYMT"), 10 were
  refunds, adjustments and cash-back credits. Added `PAYMENT_WORDS` (D6) and removed the 36 from the
  master (backup kept as `master/master.csv.bak`, gitignored). Master is now 282 rows. Tests still pass.
- Not verified: master totals against a real statement (Stage 0 gate).

## 2026-10-19 (later)
- David gave the project's goal (D7) and reference material (D8): old script, config, Mapping.xlsx,
  workflow PDF, and the Expense Tracker sheet. Read all of them; recorded in ARCHITECTURE and ACTION-ITEMS #13-18.
- Decided: cash-back credits and refunds are kept.
- New inbox folders for Ally, BoA and Chase accounts. Verified with `git check-ignore` that data files,
  `master/` and `reference/` are ignored and `git ls-files` lists no csv/xlsx/pdf.
- Dry run (nothing written or deleted) over the credit-card folders: BoA Cash 19 files, BoA Premium 18,
  Capital One 2 more, all parse. BoA payments were loading as spending, so BoA payment wording was added to
  `PAYMENT_WORDS` (tests still pass). This confirms the BoA column names on real data.
- Not done: loading the BoA and older Capital One files for real.

## 2026-10-19 (evening)
- Loaded for real: 2 more Capital One files, 37 BoA card files. Master 1,261 rows, no blanks. Both reruns report an empty inbox.
- Rebuilt `main.py` around one `ACCOUNTS` table: checking and savings are now read. Header line is found by
  required column names (BoA bank exports have summary lines on top); thousands commas and Ally's padded
  names handled. Master columns changed to Account + Account Type (D9), existing rows migrated, backup kept.
- Loaded Ally Joint Checking (153), Ally DA Personal Savings (41), Ally Joint Savings (5), BoA Savings (36).
  Master 1,496 rows, 2021-09-15 to 2026-10-19. 9 tests pass.
- Decisions from David: diagram in draw.io; categories first (D10).
- Not done: `master` branch on GitHub still exists (needs the GitHub website; no `gh` on this Mac).
  Chase / BoA Checking / AMEX / Discover formats still unverified. Transfers between own accounts not labelled (#14).

## 2026-10-19 (night)
- Gate passed: David checked a month against a statement. Stage 0 closed with 7 of 14 accounts (David's call:
  the others are out of date, he will find the data later).
- Measured how much of the master the old category sources cover (`measure_categories.py`, read-only):
  79% of money-out rows but 22% of dollars; 70% of dollars are transfers (D11). So transfers first.
- David chose: old 38-name list, proposal-and-approve review file for new payees (D12).
- Wrote the Stage 1 spec in BUILD-STAGES with 1.1 in full. Nothing built yet.

## 2026-10-19 (night, later)
- Built `categorise.py --transfers-only` and `test_categorise.py` (8 tests pass; earlier tests still pass).
- Measured the date window (D14): 8 pairs at every window from 1 day up; set to 3.
- Real run: 122 transfer rows (16 paired, 106 by wording). Roughly two thirds of money-out dollars are transfers.
  Writes only the transfer report; `master.csv` untouched.
- Two large unlabelled rows in checking looked like payments, not category spending; David explained both (D15).
- Gate NOT closed: needs David's checks (a), (b), (c).

## 2026-10-29
- `categorise.py` failed on David's Mac: the runbook's venv had never been created (I had used a temporary one).
  Created `~/venvs/finance-tracker`, installed requirements, reran all tests and the report. Runbook steps were right.
- Step 1.1 gate PASSED on David's three checks (D15).
- Measured the 63 non-transfer Ally Checking rows: no payment to a loaded card appears there, so no double
  counting today; payments to a closed store card are the only record of that card's spending (D15, ACTION-ITEMS #19, #20).
- Wrote the step 1.2 spec in full in BUILD-STAGES. Nothing built.
- Moved all personal data into one gitignored folder, `private_data/` (D16): inbox, master, reference, plus new
  rules, review and test_output. Code paths, runbook and docs updated; all 17 tests and a real rerun pass.
- Audit: no csv, xlsx, pdf or data folder has ever been committed on any branch. Real totals and two named
  transactions had reached docs and two pushed commits; scrubbed from the files (details moved to a local notes file).

## 2026-10-29 (later)
- Built `import_rules.py` and `test_import_rules.py` (5 tests; 21 tests pass in all).
- Real run: 302 rules, 23 of 38 categories used, 1 category outside the list, 2 conflicts, 81.9% credit-card row
  coverage (D17). Three corrections to the spec, all from the data (D17).
- Gate NOT closed: David fills `Map To` (1 row) and `Chosen` (2 rows).
- David answered the review files and edited four rules (D18). Backed up his rules file; `import_rules.py` now
  refuses to overwrite it. Added `--category-list` and `private_data/rules/categories.csv` (39 categories, 16 with
  no rules yet). Gate for 1.2 PASSED. 22 tests pass. Wrote the step 1.3 spec in full.
