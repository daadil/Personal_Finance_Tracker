# ARCHITECTURE

What exists and how it works. (Why it was chosen: DECISIONS.md.)

## Flow
inbox/<card name>/*.csv  ->  main.py  ->  master/master.csv

1. For each card folder, for each CSV: preview the header, check the required columns exist.
2. Read the file and convert it to the common format with that card's formatter.
3. Compare with the master for rows already held (match by count).
4. Write the master (temp file, then swap), then delete the export.

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
