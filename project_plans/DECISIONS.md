# DECISIONS

Why, including what was rejected and what it cost. (How it works: ARCHITECTURE.md.)

## D1. Rewrite the 2023 script instead of patching it (2026-10-19)
It had hardcoded paths, formatters that changed a copy, a `.strftime` call on a whole column, bare
`try/except` blocks hiding both, and dead code after `exit()`. Cost: the old structure is gone;
the old TODO list was moved to ACTION-ITEMS.md.

## D2. Inbox folder per card, export deleted after load (2026-10-19, David)
The folder name says which bank format to expect, so no guessing from file contents.
Cost: a file in the wrong folder fails its column check and is kept, not loaded.

## D3. Duplicates are matched by row count, not by file or date range (2026-10-19)
Re-dropping a file adds nothing; overlapping exports add only new rows; two real identical purchases
on one day both survive. Rejected: skipping a whole file if its dates overlap the master (loses rows
when exports overlap partly) and plain "drop duplicate rows" (deletes real repeat purchases).
Cost: see ACTION-ITEMS #12.

## D4. Columns picked by name, not position (2026-10-19)
The old script dropped columns by index, so a bank adding a column would silently shift the data.

## D5. Default branch is `main` (2026-10-19)
Renamed from `master` to follow the template.

## D6. Payments are dropped by payee wording, one card at a time (2026-10-19)
A payment is not spending, so it is left out at load and counted in the result line. The wording is
set per card in `PAYMENT_WORDS` only after it has been seen in a real export (Capital One: "PYMT").
Rejected: dropping every negative amount (that would also drop real refunds, 10 of 46 negative rows
in the first Capital One load). Cost: each new card needs a look at its real data first.

## D7. What this project is for (2026-10-19, David)
A local version of Rocket Money plus the `Expense Tracker` Google Sheet: categorised spending, budgets,
monthly roll-ups, with the data staying on this Mac. Refunds matter (so negative amounts are not
discarded), and cash-back credits are kept. Cost: everything Rocket Money does from a bank link (live
sync, bill negotiation) is out of reach; data arrives only as exported CSVs.

## D8. Reference material lives in a gitignored `reference/` folder (2026-10-19)
The old 2023 script, its config (merchant lists), `Mapping.xlsx` and the workflow PDF are copied there so
any session can find them. They hold personal merchants and account detail, so they are never committed.
Rejected: committing the scripts alone (the merchant lists are personal). Cost: a fresh clone has no
reference folder; the originals are in David's Google Drive.

## D9. One master for every account type; money leaving is positive (2026-10-19)
Checking and savings go in the same master as cards. The column `Credit Card` became `Account` and a new
`Account Type` column (Credit Card, Checking, Savings) was added; the 1,261 existing rows were migrated.
The sign rule is the same for all: money leaving the account is positive, money coming in is negative, so a
card charge and a checking withdrawal read alike and a deposit reads like a refund. Rejected: one file per
account type (the old script) because transfers and net worth need all accounts side by side. Cost: a
transfer shows up twice (out of one account, into another) until ACTION-ITEMS #14 labels it.

## D10. Order of work after Stage 0 (2026-10-19, David)
Categories first (ACTION-ITEMS #18), because budgets, roll-ups and subscriptions all need them. Diagram tool:
draw.io (#15).
