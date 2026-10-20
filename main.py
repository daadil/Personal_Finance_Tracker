"""Personal finance tracker: bank export CSVs -> one master CSV.

How it works:
  1. Drop a card's exported CSV into  inbox/<card name>/
  2. Run  python main.py
  3. Each export is converted to the common format, compared with what the master
     already holds for that card, and only the rows the master does not have yet are added.
  4. Once the master file has been written, the export is deleted.
     If anything goes wrong the export is left where it is.

The common format has four columns: Posted Date (YYYY-MM-DD), Payee, Amount, Credit Card.
A charge is a positive Amount, a refund is negative.
"""
import os
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Where things live. Everything is relative to this file, so the repo can sit anywhere.
# inbox/ and master/ are gitignored (except the .gitkeep files): financial data never goes in git.
# ---------------------------------------------------------------------------
BASE_PATH = Path(__file__).parent
INBOX_PATH = BASE_PATH / 'inbox'
MASTER_PATH = BASE_PATH / 'master' / 'master.csv'

# The four columns of the master file, in this order.
MASTER_COLUMNS = ['Posted Date', 'Payee', 'Amount', 'Credit Card']

# A row is "the same row" when all four of these match.
DUPLICATE_KEY = ['Posted Date', 'Payee', 'Amount', 'Credit Card']

# The inbox folder name for each card. Each folder name is also the value written to the
# 'Credit Card' column. Add a new card by adding a name here, a formatter below, and a line in
# FORMATTERS.
CREDIT_CARD_NAMES = [
    'AMEX Delta',
    'BoA Customized Cash Rewards',
    'BoA Premium Rewards',
    'CO Savor One',
    'Discover',
    'Chase Sapphire Preferred',
    'Chase Amazon Prime',
]


# ---------------------------------------------------------------------------
# Formatters. Each one takes the raw export (as pandas read it) and returns a table with exactly
# Posted Date, Payee, Amount. They pick columns by NAME, not position, so a bank adding a column
# does not silently shift everything. If a column is missing, the check in
# check_columns() stops the file before anything is written.
# ---------------------------------------------------------------------------

# The columns each issuer's export must contain. Checked on a preview of the file's header.
REQUIRED_COLUMNS = {
    # BoA: Posted Date, Reference Number, Payee, Address, Amount  (charges are negative)
    'BoA': ['Posted Date', 'Payee', 'Amount'],
    # Capital One: Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
    'CO': ['Posted Date', 'Description', 'Debit', 'Credit'],
    # Chase: Transaction Date, Post Date, Description, Category, Type, Amount, Memo (charges are negative)
    'Chase': ['Post Date', 'Description', 'Amount'],
    # UNVERIFIED: the old script never converted AMEX or Discover, so these column names are the
    # banks' usual ones, not checked against a real file. If a real export differs, the file is
    # left in the inbox with a message saying which columns it found.
    'AMEX': ['Date', 'Description', 'Amount'],
    'Discover': ['Post Date', 'Description', 'Amount'],
}


def format_boa(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Posted Date']
    out['Payee'] = raw['Payee']
    # BoA shows a charge as negative; the master wants a charge as positive.
    out['Amount'] = raw['Amount'] * -1
    return out


def format_capital_one(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Posted Date']
    out['Payee'] = raw['Description']
    # Capital One puts charges in 'Debit' and refunds/payments in 'Credit', leaving the other blank.
    # Charge = Debit as is. Refund = Credit made negative. A blank cell reads as 0.
    out['Amount'] = raw['Debit'].fillna(0) - raw['Credit'].fillna(0)
    return out


def format_chase(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Post Date']
    out['Payee'] = raw['Description']
    # Chase shows a charge as negative; the master wants a charge as positive.
    out['Amount'] = raw['Amount'] * -1
    return out


def format_amex(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Date']
    out['Payee'] = raw['Description']
    # AMEX already shows a charge as positive.
    out['Amount'] = raw['Amount']
    return out


def format_discover(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Post Date']
    out['Payee'] = raw['Description']
    # Discover already shows a charge as positive.
    out['Amount'] = raw['Amount']
    return out


# For each card: which column check to run and which formatter to use.
FORMATTERS = {
    'AMEX Delta': ('AMEX', format_amex),
    'BoA Customized Cash Rewards': ('BoA', format_boa),
    'BoA Premium Rewards': ('BoA', format_boa),
    'CO Savor One': ('CO', format_capital_one),
    'Discover': ('Discover', format_discover),
    'Chase Sapphire Preferred': ('Chase', format_chase),
    'Chase Amazon Prime': ('Chase', format_chase),
}


# ---------------------------------------------------------------------------
# Reading one export
# ---------------------------------------------------------------------------
def check_columns(csv_path, card_name):
    """Preview only the header row. Raises ValueError if a required column is missing."""
    issuer, _ = FORMATTERS[card_name]
    header = pd.read_csv(csv_path, nrows=0)
    missing = [c for c in REQUIRED_COLUMNS[issuer] if c not in header.columns]
    if missing:
        raise ValueError(f"missing column(s) {missing}; the file has {list(header.columns)}")


def read_export(csv_path, card_name):
    """Read one export and return it in the common format (Posted Date, Payee, Amount, Credit Card)."""
    check_columns(csv_path, card_name)
    _, formatter = FORMATTERS[card_name]
    raw = pd.read_csv(csv_path)
    rows = formatter(raw)

    # Dates to Year-Month-Day, so every card sorts and compares the same way.
    rows['Posted Date'] = pd.to_datetime(rows['Posted Date']).dt.strftime('%Y-%m-%d')
    # Two decimals, so 12.5 and 12.50 count as the same amount when comparing rows.
    rows['Amount'] = rows['Amount'].astype(float).round(2)
    rows['Payee'] = rows['Payee'].astype(str).str.strip()
    rows['Credit Card'] = card_name

    # A blank date or amount means the export was cut off or malformed; stop rather than guess.
    if rows['Posted Date'].isna().any() or rows['Amount'].isna().any():
        raise ValueError("some rows have no date or no amount")
    return rows[MASTER_COLUMNS]


# ---------------------------------------------------------------------------
# Comparing with the master
# ---------------------------------------------------------------------------
def read_master():
    """Return the master table, or an empty one if the master does not exist yet."""
    if not MASTER_PATH.exists():
        return pd.DataFrame(columns=MASTER_COLUMNS)
    master = pd.read_csv(MASTER_PATH)
    master['Amount'] = master['Amount'].astype(float).round(2)
    return master


def find_new_rows(export_rows, master):
    """Return only the rows of the export that the master does not already have.

    Rows are matched on DUPLICATE_KEY. Matching is by COUNT, not just by presence: if the export
    has two identical $4.50 coffees on one day and the master has one, one is new. That keeps a
    real repeat purchase, and still drops a re-dropped file (every count already matches).
    """
    # Number the identical rows within each group: 0, 1, 2, ...
    export_rows = export_rows.copy()
    export_rows['_n'] = export_rows.groupby(DUPLICATE_KEY).cumcount()

    # Count how many of each the master already has.
    master_counts = master.groupby(DUPLICATE_KEY).size().rename('_have').reset_index()
    export_rows = export_rows.merge(master_counts, on=DUPLICATE_KEY, how='left')
    export_rows['_have'] = export_rows['_have'].fillna(0)

    # The k-th identical row (counting from 0) is new only if the master has k or fewer of them.
    new_rows = export_rows[export_rows['_n'] >= export_rows['_have']]
    return new_rows[MASTER_COLUMNS]


def write_master(master):
    """Write the master to a temp file, then swap it in, so a crash cannot leave half a master."""
    MASTER_PATH.parent.mkdir(exist_ok=True)
    master = master.sort_values(by=['Posted Date', 'Credit Card'], kind='stable')
    temp_path = MASTER_PATH.with_name('master.csv.tmp')
    master.to_csv(temp_path, index=False)
    os.replace(temp_path, MASTER_PATH)


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def process_inbox():
    """Go through every card folder in the inbox. Returns a list of plain-English result lines."""
    results = []
    for card_name in CREDIT_CARD_NAMES:
        card_folder = INBOX_PATH / card_name
        card_folder.mkdir(parents=True, exist_ok=True)

        for csv_path in sorted(card_folder.glob('*.csv')):
            try:
                export_rows = read_export(csv_path, card_name)
                master = read_master()
                new_rows = find_new_rows(export_rows, master)

                if len(new_rows) > 0:
                    write_master(pd.concat([master, new_rows], ignore_index=True))

                # Reached only after the master was written (or nothing needed writing).
                csv_path.unlink()
                results.append(f"{card_name} / {csv_path.name}: {len(new_rows)} new rows added, "
                               f"{len(export_rows) - len(new_rows)} already in master. Export deleted.")
            except Exception as error:
                # Leave the file where it is so nothing is lost, and say why.
                results.append(f"{card_name} / {csv_path.name}: NOT LOADED, file kept. {error}")

    # A CSV dropped in the wrong place would otherwise sit there unnoticed.
    for stray in INBOX_PATH.glob('*.csv'):
        results.append(f"{stray.name}: NOT LOADED. Put it in a card folder inside inbox/.")
    return results


if __name__ == '__main__':
    lines = process_inbox()
    if not lines:
        print("Inbox is empty. Drop exports into inbox/<card name>/ and run again.")
    for line in lines:
        print(line)
