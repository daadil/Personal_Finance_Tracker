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

## Find transfers (Stage 1.1; writes only private_data/master/transfer_report.csv)
1. `~/venvs/finance-tracker/bin/python categorise.py --transfers-only`
2. Read the three checks it prints; open `private_data/master/transfer_report.csv` for every row it labelled.

## GitHub: make `main` the default branch and delete the old `master` (one time)
1. Open https://github.com/daadil/Personal_Finance_Tracker/settings (the General page; the Branches page no longer has this setting)
2. Scroll to "Default branch": click the switch icon, choose `main`, click Update, confirm.
3. Open https://github.com/daadil/Personal_Finance_Tracker/branches
4. Click the bin icon on the `master` row, confirm.
5. In the terminal: `cd ~/Documents/GitHub/Personal_Finance_Tracker && git fetch --prune`
