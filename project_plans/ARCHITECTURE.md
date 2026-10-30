# ARCHITECTURE

What exists and how it works. (Why it was chosen: DECISIONS.md.)

## Flow
private_data/inbox/<account folder>/*.csv  ->  main.py  ->  private_data/master/master.csv

1. For each account folder (the `ACCOUNTS` table in `main.py`), for each CSV: preview the text to find the
   real header line (some banks put summary lines above it) and check the required columns exist.
2. Read the file and convert it to the common format with that card's formatter.
3. Leave out payments to the card (wording per card, `PAYMENT_WORDS`).
4. Compare with the master for rows already held (match by count).
5. Write the master (temp file, then swap), then delete the export.

## Common format (private_data/master/master.csv)
Posted Date (YYYY-MM-DD), Payee, Amount, Account, Account Type. Money leaving the account is positive,
money coming in is negative, for every account type (D9).

## Files
| file | role |
|---|---|
| `main.py` | the whole pipeline; one formatter per issuer |
| `test_main.py`, `test_categorise.py` | tests on made-up data |
| `categorise.py` | Stage 1: labels transfers (1.1) and applies the category rules as a dry run (1.3). Reads the master, never edits it |
| `import_rules.py` | Stage 1.2, one-off: old mapping and keyword lists to `private_data/rules/` plus two review files |
| `test_import_rules.py` | tests for it, made-up data |
| `measure_categories.py` | read-only: how much of the master the old category sources cover |
| `private_data/master/transfer_report.csv` | every row labelled a transfer and how it was found; gitignored |
| `private_data/inbox/<card>/` | where exports are dropped; contents gitignored |
| `private_data/master/master.csv` | the merged record; gitignored |

## Not built yet
Categories, rewards maths, charts, transfer detection. See BUILD-STAGES.md.

## Reference material (`private_data/reference/`, gitignored)
| file | what it is |
|---|---|
| `Finance_TrackerV1.py` | the 2023 script: loads 14 account folders, categorises by keyword, sums per category, writes xlsx. Never finished; AMEX/Discover/Chase Amazon commented out |
| `config.py` | its settings: account lists and keyword lists per category (about 38 categories) |
| `Mapping.xlsx` | about 600 payees mapped to Store and Category |
| `financial_workflow.pdf` | diagram of the 2020 finance set-up (see ACTION-ITEMS #15) |
| Google Sheet `Expense Tracker` | the spreadsheet this replaces (tabs in ACTION-ITEMS #17) |

## Inbox folders
All accounts are read by `main.py`. Cards: `private_data/inbox/<card name>/`. Accounts: `private_data/inbox/Ally/{DA Personal Savings,
Joint Checking, Joint Savings}`, `private_data/inbox/BoA/{Checking, Savings}`, `private_data/inbox/Chase/{Checking, Savings}`. A CSV in
any other folder is reported and left alone. Everything inside `private_data/inbox/*/*` is gitignored.
