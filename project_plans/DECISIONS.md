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
