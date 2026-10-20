"""Stage 1: label transfers (and, in later steps, categories). Reads master/master.csv, never changes it.

Step 1.1 (this file so far): find transfers between David's own accounts.
  python categorise.py --transfers-only
writes master/transfer_report.csv and prints a summary. Nothing else is written.

A transfer is money that moved between his own accounts. It is neither spending nor income, and it
makes up most of the dollars in the master, so it has to be found before any category totals mean anything.
"""
import sys
import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).parent
MASTER_PATH = BASE_PATH / 'master' / 'master.csv'
REPORT_PATH = BASE_PATH / 'master' / 'transfer_report.csv'

# Only checking and savings can be both ends of a transfer. A card has no "other side" in the data:
# card payments are dropped when loading, and a card refund is not a transfer.
TRANSFER_ACCOUNT_TYPES = ['Checking', 'Savings']

# How many days apart the two sides of one transfer may be posted. MEASURED on the 2026-10-19 master
# (pair_curve): 6 pairs at 0 days, 8 at every window from 1 to 30 days, none beyond 1 day apart. So 1 day is
# enough; 3 leaves slack for a weekend. Rerun the curve when more accounts are loaded.
TRANSFER_WINDOW_DAYS = 3

# A payee containing one of these words is treated as a transfer even when the other side is not in
# the data (Fidelity, a CD, an account not loaded). Deliberately short: words that could also mean a
# real payment ("bill pay", Venmo, PayPal, Zelle) are NOT here; those rows stay unlabelled and show up
# in the "largest unlabelled" check for David to judge.
TRANSFER_WORDS = ['transfer', 'trnsfr', 'moneyline', 'booster', 'confirmation#']


def find_pairs(master, window_days):
    """Match money leaving one account with the same amount arriving in a DIFFERENT account.

    Each row is used at most once, so two $500 withdrawals and one $500 deposit make one pair, not two.
    Returns a list of (index of the money-out row, index of the money-in row).
    """
    accounts = master[master['Account Type'].isin(TRANSFER_ACCOUNT_TYPES)].copy()
    accounts['date'] = pd.to_datetime(accounts['Posted Date'])
    money_out = accounts[accounts['Amount'] > 0].sort_values(['Amount', 'date'], ascending=[False, True])
    money_in = accounts[accounts['Amount'] < 0]

    used_in_rows = set()
    pairs = []
    for out_index, out_row in money_out.iterrows():
        # Candidates: same amount (to the cent), different account, not already matched.
        candidates = money_in[(money_in['Amount'].round(2) == round(-out_row['Amount'], 2))
                              & (money_in['Account'] != out_row['Account'])
                              & (~money_in.index.isin(used_in_rows))].copy()
        candidates['gap_days'] = (candidates['date'] - out_row['date']).abs().dt.days
        candidates = candidates[candidates['gap_days'] <= window_days]
        if len(candidates) == 0:
            continue
        # Take the closest date.
        best_index = candidates.sort_values('gap_days').index[0]
        used_in_rows.add(best_index)
        pairs.append((out_index, best_index))
    return pairs


def pair_curve(master, windows=(0, 1, 2, 3, 5, 7)):
    """How many pairs are found at each window. Used to choose TRANSFER_WINDOW_DAYS from data."""
    return {days: len(find_pairs(master, days)) for days in windows}


def has_transfer_word(payee):
    payee = str(payee).lower()
    return any(word in payee for word in TRANSFER_WORDS)


def label_transfers(master, window_days=TRANSFER_WINDOW_DAYS):
    """Return the transfer report: one row per row of the master that is a transfer, and how it was found."""
    report_rows = []
    paired = set()

    for out_index, in_index in find_pairs(master, window_days):
        paired.update([out_index, in_index])
        for this_index, other_index in [(out_index, in_index), (in_index, out_index)]:
            this_row, other_row = master.loc[this_index], master.loc[other_index]
            report_rows.append({'Posted Date': this_row['Posted Date'], 'Payee': this_row['Payee'],
                                'Amount': this_row['Amount'], 'Account': this_row['Account'],
                                'How': 'paired', 'Partner Account': other_row['Account'],
                                'Partner Date': other_row['Posted Date'], 'Partner Payee': other_row['Payee'],
                                '_master_index': this_index})

    # No partner in the data, but the wording says transfer.
    for index, row in master.iterrows():
        if index in paired or row['Account Type'] not in TRANSFER_ACCOUNT_TYPES:
            continue
        if has_transfer_word(row['Payee']):
            report_rows.append({'Posted Date': row['Posted Date'], 'Payee': row['Payee'],
                                'Amount': row['Amount'], 'Account': row['Account'],
                                'How': 'wording only', 'Partner Account': '', 'Partner Date': '',
                                'Partner Payee': '', '_master_index': index})

    columns = ['Posted Date', 'Payee', 'Amount', 'Account', 'How', 'Partner Account', 'Partner Date',
               'Partner Payee', '_master_index']
    return pd.DataFrame(report_rows, columns=columns).sort_values(['Posted Date', 'Amount'])


def print_summary(master, report):
    """The three things David checks, printed."""
    money_out = master[master['Amount'] > 0]
    transfer_out = report[report['Amount'] > 0]
    print(f"\nTransfer rows found: {len(report)} "
          f"({(report['How'] == 'paired').sum()} paired, {(report['How'] == 'wording only').sum()} by wording only)")
    print(f"Money out, all accounts:   ${money_out['Amount'].sum():>10,.0f}")
    print(f"  of which transfers:      ${transfer_out['Amount'].sum():>10,.0f}")
    print(f"Money out excluding transfers: ${money_out['Amount'].sum() - transfer_out['Amount'].sum():>10,.0f}   <- check (c)")
    for account_type in ['Credit Card', 'Checking', 'Savings']:
        rows = money_out[money_out['Account Type'] == account_type]
        transfers = transfer_out[transfer_out['Account'].isin(rows['Account'])]
        print(f"  {account_type:12s} out ${rows['Amount'].sum():>9,.0f}, transfers ${transfers['Amount'].sum():>9,.0f}")

    # Check (a): 20 random pairs, same every run.
    pairs = report[(report['How'] == 'paired') & (report['Amount'] > 0)]
    print(f"\nCheck (a): {min(20, len(pairs))} random pairs (out of {len(pairs)})")
    for _, row in pairs.sample(n=min(20, len(pairs)), random_state=1).iterrows():
        print(f"  ${row['Amount']:>9,.2f}  {row['Posted Date']} {row['Account']} -> {row['Partner Date']} "
              f"{row['Partner Account']}  | {str(row['Payee'])[:40]}")

    # Check (b): the biggest money-out rows NOT labelled a transfer.
    unlabelled = money_out[~money_out.index.isin(report['_master_index'])]
    print("\nCheck (b): 10 largest money-out rows NOT labelled a transfer")
    for _, row in unlabelled.sort_values('Amount', ascending=False).head(10).iterrows():
        print(f"  ${row['Amount']:>9,.2f}  {row['Posted Date']} {row['Account']:28s} | {str(row['Payee'])[:50]}")


if __name__ == '__main__':
    if '--transfers-only' not in sys.argv:
        print("Only step 1.1 exists so far. Run:  python categorise.py --transfers-only")
        sys.exit(1)
    master = pd.read_csv(MASTER_PATH)
    master['Amount'] = master['Amount'].astype(float).round(2)

    print("Pairs found by date window (days apart):", pair_curve(master))
    print(f"Using TRANSFER_WINDOW_DAYS = {TRANSFER_WINDOW_DAYS}")
    report = label_transfers(master)
    report.drop(columns=['_master_index']).to_csv(REPORT_PATH, index=False)
    print_summary(master, report)
    print(f"\nReport written to {REPORT_PATH}")
