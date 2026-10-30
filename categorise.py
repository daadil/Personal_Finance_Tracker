"""Stage 1: label transfers and categories. Reads private_data/master/master.csv, never changes it.

Step 1.1: find transfers between David's own accounts.
  python categorise.py --transfers-only
writes private_data/master/transfer_report.csv and prints a summary. Nothing else is written.

Step 1.3: apply the category rules as a dry run.
  python categorise.py --categories-preview
writes private_data/test_output/categorised_preview.csv and prints coverage and spot-check rows.

Step 1.4: teach the rules the payees they do not know yet.
  python categorise.py --review-file     lists every uncategorised payee, biggest first, in private_data/review/uncategorised.csv
  (David fills the 'Your Category' column; 'Term' is the text to look for and he can shorten it)
  python categorise.py --apply-review    turns his answers into new rules in private_data/rules/category_rules.csv

A transfer is money that moved between his own accounts. It is neither spending nor income, and it
makes up most of the dollars in the master, so it has to be found before any category totals mean anything.
"""
import sys
import pandas as pd
from pathlib import Path
from import_rules import matching_rules, squeeze   # one definition of 'which rules match a payee'

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'private_data'   # gitignored as a whole: every file written here stays on this Mac
MASTER_PATH = DATA_PATH / 'master' / 'master.csv'
REPORT_PATH = DATA_PATH / 'master' / 'transfer_report.csv'
RULES_PATH = DATA_PATH / 'rules'
PREVIEW_PATH = DATA_PATH / 'test_output' / 'categorised_preview.csv'
REVIEW_PATH = DATA_PATH / 'review' / 'uncategorised.csv'

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


# ---------------------------------------------------------------------------
# Step 1.3: categories
# ---------------------------------------------------------------------------
def rules_outside_list(rules, category_list):
    """Categories that rules use but David's list (categories.csv) does not have."""
    return sorted(set(rules['Category']) - set(category_list['Category']))


def pick_category(payee, rules, chosen, account_type=None):
    """Return (category, how) for one payee, in one type of account.

    Order: David's answer for this exact payee in conflicts.csv; else the one category the rules give; else,
    if rules disagree, the category of the longest matching term; else nothing.
    """
    payee = squeeze(payee)
    if payee in chosen:
        return chosen[payee], 'david'
    hits = matching_rules(rules, payee, account_type)
    if not hits:
        return '', 'none'
    if len({h['Category'] for h in hits}) == 1:
        return hits[0]['Category'], 'rule'
    longest = max(hits, key=lambda h: len(h['Term']))
    return longest['Category'], 'longest term'


def assign_categories(master, rules, chosen, transfer_indexes):
    """Return the master with Kind, Category and How added. The master itself is not changed.

    Kind: 'transfer' (from step 1.1), 'spending' (money out), 'money in' (a refund, a deposit, cash back).
    Transfers get no category: they are neither spending nor income.
    """
    result = master.copy()
    result['Kind'] = ['money in' if amount < 0 else 'spending' for amount in result['Amount']]
    result.loc[result.index.isin(transfer_indexes), 'Kind'] = 'transfer'

    # Work out each distinct payee once; the same payee text repeats many times.
    # The same payee can mean different things in different account types, so the account type is part of the key.
    keys = list(zip(result['Payee'].map(squeeze), result['Account Type']))
    answers = {key: pick_category(key[0], rules, chosen, key[1]) for key in set(keys)}
    result['Category'] = [answers[key][0] for key in keys]
    result['How'] = [answers[key][1] for key in keys]
    result.loc[result['Kind'] == 'transfer', ['Category', 'How']] = ['', 'transfer']
    return result


def print_categories_preview(result, chosen, rules):
    """What David checks: coverage, whether longest-term agrees with his answers, 20 random rows, biggest gaps."""
    spending = result[result['Kind'] == 'spending']
    print(f"\nRows: {len(result)} | transfers {(result['Kind'] == 'transfer').sum()}, "
          f"spending {len(spending)}, money in {(result['Kind'] == 'money in').sum()}")

    print("\nSpending rows that got a category (transfers excluded):")
    for account_type in ['Credit Card', 'Checking', 'Savings']:
        rows = spending[spending['Account Type'] == account_type]
        if len(rows) == 0:
            continue
        done = rows[rows['Category'] != '']
        print(f"  {account_type:12s} {len(done):4d} of {len(rows):4d} rows ({len(done) / len(rows):5.1%}), "
              f"{done['Amount'].sum() / rows['Amount'].sum():5.1%} of dollars")
    print(f"  How they were decided: {result[result['Kind'] != 'transfer']['How'].value_counts().to_dict()}")

    # Check (c): does 'longest term wins' agree with what David chose?
    agree = [pick_category(payee, rules, {})[0] == category for payee, category in chosen.items()]
    print(f"\nCheck (c): longest-term pick agreed with David's answers: {sum(agree)} of {len(agree)}")

    print("\nCheck (a): 20 random categorised rows")
    done = result[result['Category'] != '']
    for _, row in done.sample(n=min(20, len(done)), random_state=1).iterrows():
        print(f"  {row['Kind']:8s} ${row['Amount']:>9,.2f}  {str(row['Payee'])[:38]:38s} -> {row['Category']} ({row['How']})")

    print("\nCheck (b): 10 largest spending payees with NO category")
    gaps = spending[spending['Category'] == ''].groupby('Payee')['Amount'].agg(['sum', 'size'])
    for payee, row in gaps.sort_values('sum', ascending=False).head(10).iterrows():
        print(f"  ${row['sum']:>9,.2f}  {int(row['size']):3d} rows  {str(payee)[:60]}")


# ---------------------------------------------------------------------------
# Step 1.4: the review loop
# ---------------------------------------------------------------------------
def build_review_table(result):
    """Every payee that got no category (transfers excluded), biggest dollars first, for David to fill in."""
    todo = result[(result['Kind'] != 'transfer') & (result['Category'] == '')]
    table = todo.groupby('Payee').agg(Rows=('Amount', 'size'), Dollars=('Amount', lambda a: round(a.abs().sum(), 2)))
    table = table.sort_values('Dollars', ascending=False).reset_index()
    # A starting guess for the term: the first two words, lowercase. David can shorten or lengthen it.
    table['Term'] = [' '.join(payee.lower().split()[:2]) for payee in table['Payee']]
    table['Suggested'] = ''
    table['Your Category'] = ''
    return table[['Payee', 'Rows', 'Dollars', 'Term', 'Suggested', 'Your Category']]


def rules_from_review(review, rules, category_list):
    """Turn the filled-in rows into new rules. Returns (new rules, list of problems).

    A row counts only when 'Your Category' is filled in. A problem (a category not in the list, or a
    blank term) stops the whole apply, so nothing is half done.
    """
    review = review.fillna('')
    answered = review[review['Your Category'].str.strip() != '']
    problems = []
    new_rules = []
    for _, row in answered.iterrows():
        category, term = row['Your Category'].strip(), row['Term'].strip().lower()
        if category not in set(category_list['Category']):
            problems.append(f"'{row['Payee']}': category '{category}' is not in categories.csv")
        elif term == '':
            problems.append(f"'{row['Payee']}': the Term is blank")
        elif ((rules['Term'] == term) & (rules['Match'] == 'contains') & (rules['Category'] == category)).any():
            continue   # this exact rule already exists
        else:
            new_rules.append({'Term': term, 'Match': 'contains', 'Category': category, 'Source': 'david', 'Account Type': ''})
    new_rules = pd.DataFrame(new_rules, columns=['Term', 'Match', 'Category', 'Source', 'Account Type'])
    # Several payee variants can share one term (one shop, many store numbers): one rule is enough.
    new_rules = new_rules.drop_duplicates(subset=['Term', 'Match', 'Category']).reset_index(drop=True)
    # The same term given two different categories would be a new conflict: stop and say so.
    for term in new_rules[new_rules['Term'].duplicated(keep=False)]['Term'].unique():
        problems.append(f"the term '{term}' was given two different categories")
    return new_rules, problems


def report_new_rules(new_rules, all_rules, master):
    """For each new rule: how many master rows it matches, and whether it now makes any payee ambiguous."""
    payees = master['Payee'].map(squeeze)
    for _, rule in new_rules.iterrows():
        matched = [p for p in payees.unique() if squeeze(rule['Term']) in p]
        clashes = [p for p in matched if len({h['Category'] for h in matching_rules(all_rules, p)}) > 1]
        print(f"  '{rule['Term']}' -> {rule['Category']}: matches {int(payees.str.contains(squeeze(rule['Term']), regex=False).sum())} rows"
              + (f"  (!) {len(clashes)} payees now match two categories, e.g. {clashes[0][:40]}" if clashes else ''))


if __name__ == '__main__':
    modes = ['--transfers-only', '--categories-preview', '--review-file', '--apply-review']
    if not any(mode in sys.argv for mode in modes):
        print("Run one of:  python categorise.py " + "   |   python categorise.py ".join(modes))
        sys.exit(1)
    master = pd.read_csv(MASTER_PATH)
    master['Amount'] = master['Amount'].astype(float).round(2)

    if '--review-file' in sys.argv or '--apply-review' in sys.argv:
        rules = pd.read_csv(RULES_PATH / 'category_rules.csv')
        if 'Account Type' not in rules.columns:
            rules['Account Type'] = ''
        category_list = pd.read_csv(RULES_PATH / 'categories.csv')
        conflicts = pd.read_csv(RULES_PATH / 'conflicts.csv').fillna('')
        conflicts = conflicts[(conflicts['Kind'] == 'payee') & (conflicts['Chosen'] != '')]
        chosen = dict(zip(conflicts['Payee'], conflicts['Chosen']))

        if '--review-file' in sys.argv:
            if REVIEW_PATH.exists():
                print(f"{REVIEW_PATH} already exists and may hold answers not yet applied. Run --apply-review first.")
                sys.exit(1)
            result = assign_categories(master, rules, chosen, set(label_transfers(master)['_master_index']))
            table = build_review_table(result)
            REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
            table.to_csv(REVIEW_PATH, index=False)
            print(f"{len(table)} uncategorised payees -> {REVIEW_PATH}")
            sys.exit(0)

        review = pd.read_csv(REVIEW_PATH)
        new_rules, problems = rules_from_review(review, rules, category_list)
        if problems:
            print("Stopped, nothing changed:"); [print("  " + p) for p in problems]
            sys.exit(1)
        all_rules = pd.concat([rules, new_rules], ignore_index=True)
        print(f"{len(new_rules)} new rules:"); report_new_rules(new_rules, all_rules, master)
        (RULES_PATH / 'category_rules.csv.bak').write_text((RULES_PATH / 'category_rules.csv').read_text())
        all_rules.to_csv(RULES_PATH / 'category_rules.csv', index=False)
        # Keep the answered file as a record, so --review-file can make a fresh list of what is left.
        REVIEW_PATH.rename(REVIEW_PATH.with_name('uncategorised_applied.csv'))
        print(f"Rules saved (backup: category_rules.csv.bak). Answered file kept as uncategorised_applied.csv.")
        sys.exit(0)

    if '--categories-preview' in sys.argv:
        rules = pd.read_csv(RULES_PATH / 'category_rules.csv')
        if 'Account Type' not in rules.columns:
            rules['Account Type'] = ''
        category_list = pd.read_csv(RULES_PATH / 'categories.csv')
        outside = rules_outside_list(rules, category_list)
        if outside:
            print(f"Stopped: rules use categories that are not in categories.csv: {outside}")
            sys.exit(1)
        conflicts = pd.read_csv(RULES_PATH / 'conflicts.csv').fillna('')
        conflicts = conflicts[(conflicts['Kind'] == 'payee') & (conflicts['Chosen'] != '')]
        chosen = dict(zip(conflicts['Payee'], conflicts['Chosen']))

        transfers = label_transfers(master)
        result = assign_categories(master, rules, chosen, set(transfers['_master_index']))
        PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(PREVIEW_PATH, index=False)
        print_categories_preview(result, chosen, rules)
        print(f"\nPreview written to {PREVIEW_PATH}  (the master was not changed)")
        sys.exit(0)

    print("Pairs found by date window (days apart):", pair_curve(master))
    print(f"Using TRANSFER_WINDOW_DAYS = {TRANSFER_WINDOW_DAYS}")
    report = label_transfers(master)
    report.drop(columns=['_master_index']).to_csv(REPORT_PATH, index=False)
    print_summary(master, report)
    print(f"\nReport written to {REPORT_PATH}")
