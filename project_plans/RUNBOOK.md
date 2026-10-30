# RUNBOOK

Commands for running the tracker (zsh, MacBook Air).

## One-time setup
1. `cd ~/Documents/GitHub/Personal_Finance_Tracker`
2. `python3 -m venv ~/venvs/finance-tracker`
3. `~/venvs/finance-tracker/bin/pip install -r requirements.txt`

## Load new exports
1. Download the CSV from the bank.
2. Drop it in the account's folder in `private_data/inbox/` (cards: `private_data/inbox/<card name>/`; accounts: `private_data/inbox/Ally/Joint Checking/`, `private_data/inbox/BoA/Savings/`, and so on).
3. `~/venvs/finance-tracker/bin/python main.py`
4. Read the result line for each file. "Export deleted" means it is in `private_data/master/master.csv`.
   "NOT LOADED, file kept" means nothing changed; the line says why.

## Run the tests (made-up data only)
1. `~/venvs/finance-tracker/bin/python test_main.py`
2. `~/venvs/finance-tracker/bin/python test_categorise.py`
3. `~/venvs/finance-tracker/bin/python test_import_rules.py`

## Find transfers (Stage 1.1; writes only private_data/master/transfer_report.csv)
1. `~/venvs/finance-tracker/bin/python categorise.py --transfers-only`
2. Read the three checks it prints; open `private_data/master/transfer_report.csv` for every row it labelled.

## Import the old category rules (Stage 1.2; one-off, writes only private_data/rules/; refuses to overwrite once you have edited the rules)
1. `~/venvs/finance-tracker/bin/python import_rules.py`
2. Open `private_data/rules/unknown_categories.csv`, fill the `Map To` column.
3. Open `private_data/rules/conflicts.csv`, fill the `Chosen` column (copy `Suggested` if it is right).
4. To see or edit the list of categories: open `private_data/rules/categories.csv`. After editing rules or the list, refresh the counts: `~/venvs/finance-tracker/bin/python import_rules.py --category-list`

## GitHub: make `main` the default branch and delete the old `master` (one time)
1. Open https://github.com/daadil/Personal_Finance_Tracker/settings (the General page; the Branches page no longer has this setting)
2. Scroll to "Default branch": click the switch icon, choose `main`, click Update, confirm.
3. Open https://github.com/daadil/Personal_Finance_Tracker/branches
4. Click the bin icon on the `master` row, confirm.
5. In the terminal: `cd ~/Documents/GitHub/Personal_Finance_Tracker && git fetch --prune`
