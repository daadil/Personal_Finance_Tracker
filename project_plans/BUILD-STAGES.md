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
labelled BEFORE categories, or every total is meaningless. `master/master.csv` stays the raw record and is never
edited by this stage; results go to a new derived file, `master/categorised.csv` (gitignored), made by a new
script `categorise.py`. Rules live in `rules/` (gitignored: personal merchants).

### 1.1 Find transfers (read-only report; nothing is written except a report file). BUILT 2026-10-19; gate waiting on David's three checks
Why read-only first: a wrong transfer label hides real spending, and the master is the only copy of the exports.
1. Build `categorise.py` with a function that pairs money-out in one account with money-in in a different
   account: same amount, dates within N days. N is UNMEASURED: the script prints how many pairs are found at
   N = 0, 1, 2, 3, 5 so the window is chosen from the curve, not from argument.
2. A second function lists the money-out rows whose payee wording says transfer (the words are in
   `measure_categories.py`) but that found no partner (the other side is not in the data: Chase, Fidelity,
   a CD). These are labelled by wording only.
3. Write `master/transfer_report.csv`: every proposed transfer, its partner (if any), and how it was found.
Run: `~/venvs/finance-tracker/bin/python categorise.py --transfers-only`
Verify (David, 15 minutes): open `master/transfer_report.csv`, (a) check 20 random pairs are real transfers,
(b) check the 10 largest money-out rows NOT labelled a transfer are real spending, (c) the printed
"money-out excluding transfers" total is plausible against what he knows he spends.
Gate: all three checks pass. If one fails, report the failure and the rows; do not move the bar.

### 1.2 to 1.5 (decision level; detailed when 1.1's gate passes)
- 1.2 Import the old mapping and keyword lists into `rules/category_rules.csv` (term, category, source). Where
  the two sources disagree (72 of 740 rows measured) write the conflicts to a review file; precedence (longest
  term wins) is an assumption to measure against those 72.
- 1.3 Apply the rules as a dry run; print coverage by rows and dollars per account type.
- 1.4 Write `review/uncategorised.csv` (gitignored): unknown payees by dollars, each with a suggested category.
  David edits it in a spreadsheet; the next run reads his answers as rules.
- 1.5 Write `master/categorised.csv` (Kind, Category added). Tests on made-up data for every rule type.

## Stage 2 onward: not yet planned
Candidates are in ACTION-ITEMS.md (payments and returns, checking, savings, categories, rewards,
charts, stale-data warning). Order and gates to be agreed with David before any is started.
