# RUNBOOK

Commands for running the tracker (zsh, MacBook Air).

## One-time setup
1. `cd ~/Documents/GitHub/Personal_Finance_Tracker`
2. `python3 -m venv ~/venvs/finance-tracker`
3. `~/venvs/finance-tracker/bin/pip install -r requirements.txt`

## Load new exports
1. Download the CSV from the bank.
2. Drop it in `inbox/<card name>/` (the folder names match the card names).
3. `~/venvs/finance-tracker/bin/python main.py`
4. Read the result line for each file. "Export deleted" means it is in `master/master.csv`.
   "NOT LOADED, file kept" means nothing changed; the line says why.

## Run the tests (made-up data only)
1. `~/venvs/finance-tracker/bin/python test_main.py`
