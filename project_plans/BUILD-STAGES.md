# BUILD-STAGES

The plan: ordered steps, each with a gate that can be observed. What happened: PROGRESS.md.
Later stages stay at decision level until their turn.

## Stage 0: Ingest accounts into one master (DONE 2026-10-19)
Gate passed: David checked one month of the master against a real statement and it matched. Scope: 7 of 14
accounts (Capital One, both BoA cards, Ally x3, BoA Savings; 1,496 rows). Closed without the other 7 (AMEX,
Discover, both Chase cards, BoA Checking, Chase Checking and Savings): their data is very out of date and David
must dig for it. Each is a drop-in later: add the export to its folder, run `main.py`. Their formats stay
UNVERIFIED (ACTION-ITEMS #3, #13) until a real file arrives.

## Stage 1: labelling and categories (current)
Decided by David (D10, D12): old 38-name category list; unknown payees are proposed in a review file he approves.
Measured first (D11): 70% of money-out dollars are transfers between his own accounts, so transfers are
labelled BEFORE categories, or every total is meaningless. `private_data/master/master.csv` stays the raw record and is never
edited by this stage; results go to a new derived file, `private_data/master/categorised.csv` (gitignored), made by a new
script `categorise.py`. Rules live in `private_data/rules/` (gitignored: personal merchants).

### 1.1 Find transfers (read-only report; nothing is written except a report file). PASSED 2026-10-29 (David: (a) pairs correct; (b) the large unlabelled rows are real spending or payments on cards not loaded; (c) the excluding-transfers total is plausible)
Why read-only first: a wrong transfer label hides real spending, and the master is the only copy of the exports.
1. Build `categorise.py` with a function that pairs money-out in one account with money-in in a different
   account: same amount, dates within N days. N is UNMEASURED: the script prints how many pairs are found at
   N = 0, 1, 2, 3, 5 so the window is chosen from the curve, not from argument.
2. A second function lists the money-out rows whose payee wording says transfer (the words are in
   `measure_categories.py`) but that found no partner (the other side is not in the data: Chase, Fidelity,
   a CD). These are labelled by wording only.
3. Write `private_data/master/transfer_report.csv`: every proposed transfer, its partner (if any), and how it was found.
Run: `~/venvs/finance-tracker/bin/python categorise.py --transfers-only`
Verify (David, 15 minutes): open `private_data/master/transfer_report.csv`, (a) check 20 random pairs are real transfers,
(b) check the 10 largest money-out rows NOT labelled a transfer are real spending, (c) the printed
"money-out excluding transfers" total is plausible against what he knows he spends.
Gate: all three checks pass. If one fails, report the failure and the rows; do not move the bar.

### 1.2 Import the old rules (nothing is categorised yet; two review files are written). BUILT 2026-10-29; gate waiting on David filling in the two files
Why: the old mapping and keyword lists are the only categories David has already decided; they are the starting
rules, and where they disagree a human picks (2 payees, once measured properly: D17).
1. Build `import_rules.py` (one-off, reads only `private_data/reference/`). Inputs: `private_data/reference/Mapping.xlsx` sheet `Sheet2`
   (a row with a `Search Term` gives a contains-rule; a row with only a `Category` gives an exact-payee rule; short terms are kept and reported, D17) and the keyword lists in
   `private_data/reference/config.py`. The script holds an explicit table of list name to category name (for example
   `health_and_wellbeing` to "Health & Wellbeing") so it can be audited by eye.
2. Writes three gitignored files in `private_data/rules/`:
   - `category_rules.csv`: Term (lowercase), Category, Source (mapping or config). Identical term+category pairs
     are merged.
   - `unknown_categories.csv`: every category the old sources use that is NOT in the 38-name list (D12), with
     the number of rules using it, and an empty column `Map To` for David.
   - `conflicts.csv`: every payee in the master matched by rules that give different categories, with the
     matching terms, a `Suggested` category (longest matching term), and an empty column `Chosen` for David.
3. Prints: rules per source, distinct categories, categories outside the list, conflict count.
Run: `~/venvs/finance-tracker/bin/python import_rules.py`
Verify (David, about 30 minutes): fill `Map To` for each unknown category, fill `Chosen` for each conflict.
Gate: both files fully filled in (`Map To`, `Chosen`), and coverage still about 82% of credit-card rows, showing the
import lost nothing (measured 81.9%, D17). Precedence among rules (longest term
wins) is an assumption, tested against the filled-in conflicts in 1.3, not fixed here.

### 1.3 to 1.5 (decision level; detailed when 1.2's gate passes)
- 1.3 Apply the rules (David's `Chosen` answers win) as a dry run; test longest-term-wins against his answers; print coverage by rows and dollars per account type.
- 1.4 Write `private_data/review/uncategorised.csv` (gitignored): unknown payees by dollars, each with a suggested category.
  David edits it in a spreadsheet; the next run reads his answers as rules.
- 1.5 Write `private_data/master/categorised.csv` (Kind, Category added). Tests on made-up data for every rule type.

## Stage 2 onward: not yet planned
Candidates are in ACTION-ITEMS.md (payments and returns, checking, savings, categories, rewards,
charts, stale-data warning). Order and gates to be agreed with David before any is started.
