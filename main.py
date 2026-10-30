"""Personal finance tracker: bank and credit-card export CSVs -> one master CSV.

How it works:
  1. Drop an account's exported CSV into its folder under  private_data/inbox/  (folders are listed in ACCOUNTS below)
  2. Run  python main.py
  3. Each export is converted to the common format, compared with what the master
     already holds for that account, and only the rows the master does not have yet are added.
  4. Once the master file has been written, the export is deleted.
     If anything goes wrong the export is left where it is.

The common format has five columns: Posted Date (YYYY-MM-DD), Payee, Amount, Account, Account Type.
Amount: money LEAVING the account is positive (a charge, a withdrawal), money coming IN is negative
(a refund, a deposit, a payment to a card). The same rule for every account type.
"""
import os
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Where things live. Everything is relative to this file, so the repo can sit anywhere.
# ALL personal financial data lives under private_data/, which is gitignored as a whole:
# exports (inbox/), the merged master (master/), old reference files, rules, review files, test output.
# Nothing outside that folder may hold a real transaction.
# ---------------------------------------------------------------------------
BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'private_data'
INBOX_PATH = DATA_PATH / 'inbox'
MASTER_PATH = DATA_PATH / 'master' / 'master.csv'

# The columns of the master file, in this order.
MASTER_COLUMNS = ['Posted Date', 'Payee', 'Amount', 'Account', 'Account Type']

# A row is "the same row" when all of these match.
DUPLICATE_KEY = ['Posted Date', 'Payee', 'Amount', 'Account']

# Every account the script knows about:
#   (account name written to the master, folder inside private_data/inbox/, account type, export format)
# The format names are the keys of FORMATS below. Add a new account by adding a line here.
ACCOUNTS = [
    ('AMEX Delta',                  'AMEX Delta',                  'Credit Card', 'AMEX'),
    ('BoA Customized Cash Rewards', 'BoA Customized Cash Rewards', 'Credit Card', 'BoA Card'),
    ('BoA Premium Rewards',         'BoA Premium Rewards',         'Credit Card', 'BoA Card'),
    ('CO Savor One',                'CO Savor One',                'Credit Card', 'Capital One'),
    ('Discover',                    'Discover',                    'Credit Card', 'Discover'),
    ('Chase Sapphire Preferred',    'Chase Sapphire Preferred',    'Credit Card', 'Chase Card'),
    ('Chase Amazon Prime',          'Chase Amazon Prime',          'Credit Card', 'Chase Card'),
    ('Ally DA Personal Savings',    'Ally/DA Personal Savings',    'Savings',     'Ally'),
    ('Ally Joint Checking',         'Ally/Joint Checking',         'Checking',    'Ally'),
    ('Ally Joint Savings',          'Ally/Joint Savings',          'Savings',     'Ally'),
    ('BoA Checking',                'BoA/Checking',                'Checking',    'BoA Bank'),
    ('BoA Savings',                 'BoA/Savings',                 'Savings',     'BoA Bank'),
    ('Chase Checking',              'Chase/Checking',              'Checking',    'Chase Bank'),
    ('Chase Savings',               'Chase/Savings',               'Savings',     'Chase Bank'),
]

# Payments to a card are not spending, so they are left out. A row is a payment when its Payee
# contains one of these words. Only cards whose payment wording has been checked against real data
# are listed; the others still load their payments (ACTION-ITEMS #1).
PAYMENT_WORDS = {
    'CO Savor One': ['PYMT'],  # CAPITAL ONE MOBILE PYMT / AUTOPAY PYMT / ONLINE PYMT
    # BoA, checked on 2022-2023 exports of both cards. Refunds (Home Depot, Rover...) are not matched.
    'BoA Customized Cash Rewards': ['PAYMENT - THANK YOU', 'ONLINE PAYMENT FROM', 'PYMT TRANSFER'],
    'BoA Premium Rewards': ['PAYMENT - THANK YOU', 'ONLINE PAYMENT FROM', 'PYMT TRANSFER'],
}


# ---------------------------------------------------------------------------
# Formatters. Each one takes the raw export (as pandas read it) and returns a table with exactly
# Posted Date, Payee, Amount. They pick columns by NAME, not position, so a bank adding a column
# does not silently shift everything.
# ---------------------------------------------------------------------------
def format_boa_card(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Posted Date']
    out['Payee'] = raw['Payee']
    # BoA shows a charge as negative; the master wants money leaving as positive.
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


def format_chase_card(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Post Date']
    out['Payee'] = raw['Description']
    # Chase shows a charge as negative; the master wants it positive.
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


def format_ally(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Date']
    out['Payee'] = raw['Description']
    # Ally shows a withdrawal as negative and a deposit as positive; the master wants the opposite.
    # The export's own 'Time' and 'Type' columns are not needed: the sign already says which it is.
    out['Amount'] = raw['Amount'] * -1
    return out


def format_boa_bank(raw):
    # The export lists a 'Beginning balance' line with no amount. It is not a transaction.
    raw = raw.dropna(subset=['Amount'])
    out = pd.DataFrame()
    out['Posted Date'] = raw['Date']
    out['Payee'] = raw['Description']
    # BoA shows money out as negative; the master wants it positive.
    out['Amount'] = raw['Amount'] * -1
    return out


def format_chase_bank(raw):
    out = pd.DataFrame()
    out['Posted Date'] = raw['Posting Date']
    out['Payee'] = raw['Description']
    # Chase shows money out as negative; the master wants it positive.
    out['Amount'] = raw['Amount'] * -1
    return out


# For each export format: the columns it must contain, and the formatter. The required columns are
# also how the real header line is found, because some exports have summary lines above it.
FORMATS = {
    # BoA card: Posted Date, Reference Number, Payee, Address, Amount
    'BoA Card': (['Posted Date', 'Payee', 'Amount'], format_boa_card),
    # Capital One: Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
    'Capital One': (['Posted Date', 'Description', 'Debit', 'Credit'], format_capital_one),
    # Chase card: Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    'Chase Card': (['Post Date', 'Description', 'Amount'], format_chase_card),
    # Ally (checking and savings): Date, Time, Amount, Type, Description
    'Ally': (['Date', 'Amount', 'Description'], format_ally),
    # BoA checking/savings: summary lines, a blank line, then Date, Description, Amount, Running Bal.
    'BoA Bank': (['Date', 'Description', 'Amount'], format_boa_bank),
    # UNVERIFIED: no real export of these yet. Column names are from the 2023 script (checking) or
    # the banks' usual ones. If a real export differs, the file is left in the inbox with a message
    # saying which columns it found.
    'AMEX': (['Date', 'Description', 'Amount'], format_amex),
    'Discover': (['Post Date', 'Description', 'Amount'], format_discover),
    # Chase checking/savings: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #
    'Chase Bank': (['Posting Date', 'Description', 'Amount'], format_chase_bank),
}


# ---------------------------------------------------------------------------
# Reading one export
# ---------------------------------------------------------------------------
def find_header_line(csv_path, required_columns):
    """Preview the file (text only) and return the line number of the real header.

    The real header is the first line that holds every required column name. Some banks put
    summary lines above it. Raises ValueError, naming the first line, if no line qualifies.
    """
    with open(csv_path, encoding='utf-8-sig') as file:
        lines = file.read().splitlines()
    for line_number, line in enumerate(lines):
        names = [name.strip().strip('"') for name in line.split(',')]
        if all(column in names for column in required_columns):
            return line_number
    first_line = lines[0] if lines else '(empty file)'
    raise ValueError(f"no header line with columns {required_columns}; the file starts with: {first_line[:100]}")


def read_export(csv_path, account_name):
    """Read one export. Returns (rows in the common format, number of payment rows left out)."""
    _, _, account_type, format_name = next(a for a in ACCOUNTS if a[0] == account_name)
    required_columns, formatter = FORMATS[format_name]

    header_line = find_header_line(csv_path, required_columns)
    # skipinitialspace: Ally pads some column names with a space. thousands: BoA writes "20,000.00".
    raw = pd.read_csv(csv_path, skiprows=header_line, skipinitialspace=True, thousands=',')
    rows = formatter(raw)

    # Dates to Year-Month-Day, so every account sorts and compares the same way.
    rows['Posted Date'] = pd.to_datetime(rows['Posted Date']).dt.strftime('%Y-%m-%d')
    # Two decimals, so 12.5 and 12.50 count as the same amount when comparing rows.
    rows['Amount'] = rows['Amount'].astype(float).round(2)
    rows['Payee'] = rows['Payee'].astype(str).str.strip()
    rows['Account'] = account_name
    rows['Account Type'] = account_type

    # A blank date or amount means the export was cut off or malformed; stop rather than guess.
    if rows['Posted Date'].isna().any() or rows['Amount'].isna().any():
        raise ValueError("some rows have no date or no amount")

    # Leave out payments to the card, and count them so the result line can report it.
    is_payment = pd.Series(False, index=rows.index)
    for word in PAYMENT_WORDS.get(account_name, []):
        is_payment = is_payment | rows['Payee'].str.contains(word, case=False, regex=False)
    return rows[~is_payment][MASTER_COLUMNS].reset_index(drop=True), int(is_payment.sum())


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
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    master = master.sort_values(by=['Posted Date', 'Account'], kind='stable')
    temp_path = MASTER_PATH.with_name('master.csv.tmp')
    master.to_csv(temp_path, index=False)
    os.replace(temp_path, MASTER_PATH)


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def process_inbox():
    """Go through every account folder in the inbox. Returns a list of plain-English result lines."""
    results = []
    for account_name, folder_name, _, _ in ACCOUNTS:
        folder = INBOX_PATH / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        for csv_path in sorted(folder.glob('*.csv')):
            try:
                export_rows, payments_skipped = read_export(csv_path, account_name)
                master = read_master()
                new_rows = find_new_rows(export_rows, master)

                if len(new_rows) > 0:
                    write_master(pd.concat([master, new_rows], ignore_index=True))

                # Reached only after the master was written (or nothing needed writing).
                csv_path.unlink()
                results.append(f"{account_name} / {csv_path.name}: {len(new_rows)} new rows added, "
                               f"{len(export_rows) - len(new_rows)} already in master, "
                               f"{payments_skipped} payments left out. Export deleted.")
            except Exception as error:
                # Leave the file where it is so nothing is lost, and say why.
                results.append(f"{account_name} / {csv_path.name}: NOT LOADED, file kept. {error}")

    # A CSV in a folder that belongs to no account (the inbox root, or a bank folder such as
    # private_data/inbox/Ally/) would otherwise sit there unnoticed.
    known_folders = [INBOX_PATH / folder_name for _, folder_name, _, _ in ACCOUNTS]
    for stray in sorted(INBOX_PATH.rglob('*.csv')):
        if stray.parent not in known_folders:
            results.append(f"{stray.relative_to(INBOX_PATH)}: NOT LOADED. Put it in an account folder inside private_data/inbox/.")
    return results


if __name__ == '__main__':
    lines = process_inbox()
    if not lines:
        print("Inbox is empty. Drop exports into their account folder inside private_data/inbox/ and run again.")
    for line in lines:
        print(line)
