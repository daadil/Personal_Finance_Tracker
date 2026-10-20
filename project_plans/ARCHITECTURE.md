# ARCHITECTURE

What exists and how it works. (Why it was chosen: DECISIONS.md.)

## Flow
inbox/<card name>/*.csv  ->  main.py  ->  master/master.csv

1. For each card folder, for each CSV: preview the header, check the required columns exist.
2. Read the file and convert it to the common format with that card's formatter.
3. Leave out payments to the card (wording per card, `PAYMENT_WORDS`).
4. Compare with the master for rows already held (match by count).
5. Write the master (temp file, then swap), then delete the export.

## Common format (master/master.csv)
Posted Date (YYYY-MM-DD), Payee, Amount (charge positive, refund negative), Credit Card.

## Files
| file | role |
|---|---|
| `main.py` | the whole pipeline; one formatter per issuer |
| `test_main.py` | tests on made-up data |
| `inbox/<card>/` | where exports are dropped; contents gitignored |
| `master/master.csv` | the merged record; gitignored |

## Not built yet
Checking and savings accounts, categories, rewards maths, charts. See BUILD-STAGES.md.

## Reference material (`reference/`, gitignored)
| file | what it is |
|---|---|
| `Finance_TrackerV1.py` | the 2023 script: loads 14 account folders, categorises by keyword, sums per category, writes xlsx. Never finished; AMEX/Discover/Chase Amazon commented out |
| `config.py` | its settings: account lists and keyword lists per category (about 38 categories) |
| `Mapping.xlsx` | about 600 payees mapped to Store and Category |
| `financial_workflow.pdf` | diagram of the 2020 finance set-up (see ACTION-ITEMS #15) |
| Google Sheet `Expense Tracker` | the spreadsheet this replaces (tabs in ACTION-ITEMS #17) |

## Inbox folders
Credit cards (read by `main.py`): one folder per card in `inbox/`.
Accounts (not read yet, ACTION-ITEMS #5, #6): `inbox/Ally/{DA Personal Savings, Joint Checking, Joint Savings}`,
`inbox/BoA/{Checking, Savings}`, `inbox/Chase/{Checking, Savings}`. Everything inside `inbox/*/*` is gitignored.
