# ARCHITECTURE

What exists and how it works. (Why it was chosen: DECISIONS.md.)

## Flow
inbox/<account folder>/*.csv  ->  main.py  ->  master/master.csv

1. For each account folder (the `ACCOUNTS` table in `main.py`), for each CSV: preview the text to find the
   real header line (some banks put summary lines above it) and check the required columns exist.
2. Read the file and convert it to the common format with that card's formatter.
3. Leave out payments to the card (wording per card, `PAYMENT_WORDS`).
4. Compare with the master for rows already held (match by count).
5. Write the master (temp file, then swap), then delete the export.

## Common format (master/master.csv)
Posted Date (YYYY-MM-DD), Payee, Amount, Account, Account Type. Money leaving the account is positive,
money coming in is negative, for every account type (D9).

## Files
| file | role |
|---|---|
| `main.py` | the whole pipeline; one formatter per issuer |
| `test_main.py`, `test_categorise.py` | tests on made-up data |
| `categorise.py` | Stage 1: labels transfers (step 1.1); later categories. Reads the master, never edits it |
| `measure_categories.py` | read-only: how much of the master the old category sources cover |
| `master/transfer_report.csv` | every row labelled a transfer and how it was found; gitignored |
| `inbox/<card>/` | where exports are dropped; contents gitignored |
| `master/master.csv` | the merged record; gitignored |

## Not built yet
Categories, rewards maths, charts, transfer detection. See BUILD-STAGES.md.

## Reference material (`reference/`, gitignored)
| file | what it is |
|---|---|
| `Finance_TrackerV1.py` | the 2023 script: loads 14 account folders, categorises by keyword, sums per category, writes xlsx. Never finished; AMEX/Discover/Chase Amazon commented out |
| `config.py` | its settings: account lists and keyword lists per category (about 38 categories) |
| `Mapping.xlsx` | about 600 payees mapped to Store and Category |
| `financial_workflow.pdf` | diagram of the 2020 finance set-up (see ACTION-ITEMS #15) |
| Google Sheet `Expense Tracker` | the spreadsheet this replaces (tabs in ACTION-ITEMS #17) |

## Inbox folders
All accounts are read by `main.py`. Cards: `inbox/<card name>/`. Accounts: `inbox/Ally/{DA Personal Savings,
Joint Checking, Joint Savings}`, `inbox/BoA/{Checking, Savings}`, `inbox/Chase/{Checking, Savings}`. A CSV in
any other folder is reported and left alone. Everything inside `inbox/*/*` is gitignored.
