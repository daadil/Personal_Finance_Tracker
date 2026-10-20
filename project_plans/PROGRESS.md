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
