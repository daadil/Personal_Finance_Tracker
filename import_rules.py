"""Stage 1.2: turn the 2023 category lists into starting rules, and list what a human must decide.

One-off. Reads only private_data/reference/ (the old Mapping.xlsx and config.py) and the master
(to find where rules disagree). Writes three files in private_data/rules/ and changes nothing else:
  category_rules.csv      Term, Match, Category, Source
  unknown_categories.csv  categories the old sources use that are not in David's 38-name list, plus 'Map To'
  conflicts.csv           places where rules disagree, plus 'Chosen'

Run:  python import_rules.py                  (first time only: refuses to overwrite David's edited rules)
      python import_rules.py --category-list  (rewrites categories.csv counts from the current rules file)
"""
import sys
import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'private_data'
REFERENCE_PATH = DATA_PATH / 'reference'
RULES_PATH = DATA_PATH / 'rules'
MASTER_PATH = DATA_PATH / 'master' / 'master.csv'

# Which keyword list in the old config.py means which category. Written out by hand so it can be
# checked by eye; a name that is not in the 38-name list would show up in unknown_categories.csv.
CONFIG_LISTS = {
    'auto_maintenance_fees': 'Auto Maintenance/Fees',
    'cash_back': 'Cash Back',
    'clothes': 'Clothes',
    'credit_card_fees': 'Credit Card Fees',
    'education': 'Education',
    'entertainment': 'Entertainment',
    'groceries': 'Groceries',
    'gym': 'Gym',
    'health_and_wellbeing': 'Health & Wellbeing',
    'home_repairs_maintenance': 'Home Repairs/Maintenance',
    'insurance': 'Insurance (Home/Auto/Other)',
    'internet': 'Internet',
    'medical': 'Medical',
    'pet': 'Pet',
    'restaurant': 'Restaurant',
    'shopping': 'Shopping',
    'subscriptions': 'Subscriptions',
    'transportation': 'Transportation',
    'travel': 'Travel',
}

# Terms this short can match inside unrelated words, so the script reports what each one matches.
SHORT_TERM_LENGTH = 4


def build_rules(mapping, config_lists):
    """Combine both old sources into one table of rules: Term, Match, Category, Source.

    Match is 'contains' (the term appears anywhere in the payee) or 'exact' (the whole payee).
    From Mapping.xlsx: a row with a Search Term gives a 'contains' rule. A row with a Category but no
    Search Term only has the full Payee text, so it gives an 'exact' rule. From config.py: every
    keyword gives a 'contains' rule. Identical rules from both sources are merged.
    """
    rules = []
    for _, row in mapping.dropna(subset=['Category']).iterrows():
        category = str(row['Category']).strip()
        if pd.notna(row['Search Term']) and str(row['Search Term']).strip():
            rules.append((str(row['Search Term']).lower().strip(), 'contains', category, 'mapping'))
        elif pd.notna(row['Payee']):
            rules.append((str(row['Payee']).lower().strip(), 'exact', category, 'mapping'))

    for list_name, keywords in config_lists.items():
        for keyword in keywords:
            rules.append((keyword.lower().strip(), 'contains', CONFIG_LISTS[list_name], 'config'))

    table = pd.DataFrame(rules, columns=['Term', 'Match', 'Category', 'Source'])
    # Merge identical (term, match, category) rules; remember every source that had it.
    table = table.groupby(['Term', 'Match', 'Category'], as_index=False)['Source'].agg(lambda s: '+'.join(sorted(set(s))))
    return table.sort_values(['Category', 'Term']).reset_index(drop=True)


def matching_rules(rules, payee):
    """All rules that match one payee (already lowercase and stripped)."""
    hits = []
    for _, rule in rules.iterrows():
        if rule['Match'] == 'contains' and rule['Term'] in payee:
            hits.append(rule)
        elif rule['Match'] == 'exact' and rule['Term'] == payee:
            hits.append(rule)
    return hits


def find_conflicts(rules, master):
    """Where a human must choose: (1) a payee in the master that rules put in different categories,
    (2) one term the sources give two different categories."""
    conflict_rows = []

    payee_counts = master['Payee'].astype(str).str.lower().str.strip().value_counts()
    for payee, count in payee_counts.items():
        hits = matching_rules(rules, payee)
        if len({h['Category'] for h in hits}) > 1:
            candidates = '; '.join(sorted({f"{h['Term']} -> {h['Category']} ({h['Source']})" for h in hits}))
            # A suggestion only: the category of the longest matching term ("safeway fuel" is more specific
            # than "safeway"). David confirms it by copying it into Chosen, or writes a different one.
            longest = max(hits, key=lambda h: len(h['Term']))
            conflict_rows.append({'Kind': 'payee', 'Payee': payee, 'Rows in master': int(count),
                                  'Candidates': candidates, 'Suggested': longest['Category'], 'Chosen': ''})

    for (term, match), group in rules.groupby(['Term', 'Match']):
        if group['Category'].nunique() > 1:
            candidates = '; '.join(f"{c} ({s})" for c, s in zip(group['Category'], group['Source']))
            conflict_rows.append({'Kind': 'term', 'Payee': f"(the term '{term}')", 'Rows in master': 0,
                                  'Candidates': candidates, 'Suggested': '', 'Chosen': ''})
    return pd.DataFrame(conflict_rows, columns=['Kind', 'Payee', 'Rows in master', 'Candidates', 'Suggested', 'Chosen'])


def find_unknown_categories(rules, allowed_categories):
    """Categories the old sources use that are not in David's list. He fills in 'Map To'."""
    unknown = rules[~rules['Category'].isin(allowed_categories)]
    summary = unknown.groupby('Category').agg(**{'Rules using it': ('Term', 'size'), 'Sources': ('Source', lambda s: '+'.join(sorted(set(s))))})
    summary = summary.reset_index()
    summary['Map To'] = ''
    return summary


def build_category_list(rules, master, allowed_categories, old_notes):
    """One row per category: how many rules use it, how many master rows match a rule of that category.

    The 'Master rows matching' count can add up to more than the master when a payee matches rules from
    two categories (a conflict). 'Note' keeps whatever David wrote in the file before.
    """
    rows_per_category = {}
    for payee in master['Payee'].astype(str).str.lower().str.strip():
        for category in {h['Category'] for h in matching_rules(rules, payee)}:
            rows_per_category[category] = rows_per_category.get(category, 0) + 1
    rules_per_category = rules['Category'].value_counts()

    names = list(allowed_categories) + sorted(set(rules['Category']) - set(allowed_categories))
    table = pd.DataFrame({'Category': names})
    table['Rules using it'] = table['Category'].map(rules_per_category).fillna(0).astype(int)
    table['Master rows matching'] = table['Category'].map(rows_per_category).fillna(0).astype(int)
    table['Note'] = table['Category'].map(old_notes).fillna('')
    return table


def report_short_terms(rules, master):
    """Print what each very short term matches in the master, so false matches can be seen."""
    payees = master['Payee'].astype(str).str.lower().str.strip().drop_duplicates()
    short = rules[(rules['Match'] == 'contains') & (rules['Term'].str.len() <= SHORT_TERM_LENGTH)]
    print(f"\nShort terms ({SHORT_TERM_LENGTH} characters or fewer): what each matches in the master")
    for _, rule in short.iterrows():
        matches = [p for p in payees if rule['Term'] in p]
        print(f"  '{rule['Term']}' -> {rule['Category']}: {len(matches)} distinct payees"
              + (f", e.g. {matches[0][:40]} | {matches[-1][:40]}" if matches else ''))


if __name__ == '__main__':
    sys.path.insert(0, str(REFERENCE_PATH))
    import config  # the old 2023 settings, in private_data/reference/
    RULES_PATH.mkdir(parents=True, exist_ok=True)
    CATEGORY_LIST_PATH = RULES_PATH / 'categories.csv'

    if '--category-list' in sys.argv:
        # The category list is David's: if the file exists its names are kept, and he can add or rename rows.
        rules = pd.read_csv(RULES_PATH / 'category_rules.csv')
        master = pd.read_csv(MASTER_PATH)
        if CATEGORY_LIST_PATH.exists():
            old = pd.read_csv(CATEGORY_LIST_PATH).fillna('')
            allowed, old_notes = list(old['Category']), dict(zip(old['Category'], old['Note']))
        else:
            # First time: his 38 names from the old config, plus the one he added on 2026-10-29.
            allowed = list(config.transaction_types) + ['Credit Card Payment']
            old_notes = {'Credit Card Payment': 'Added 2026-10-29 by David. Own category; a card payment is not new spending.'}
        table = build_category_list(rules, master, allowed, old_notes)
        table.to_csv(CATEGORY_LIST_PATH, index=False)
        print(table.to_string(index=False))
        print(f"\n{len(table)} categories -> {CATEGORY_LIST_PATH}")
        sys.exit(0)

    if (RULES_PATH / 'category_rules.csv').exists() and '--force' not in sys.argv:
        print("private_data/rules/category_rules.csv already exists and may hold David's edits. Not overwriting.")
        print("Use  --category-list  to refresh the category list, or  --force  to start over from the old files.")
        sys.exit(1)

    mapping = pd.read_excel(REFERENCE_PATH / 'Mapping.xlsx', sheet_name='Sheet2')
    config_lists = {name: getattr(config, name) for name in CONFIG_LISTS}
    master = pd.read_csv(MASTER_PATH)

    rules = build_rules(mapping, config_lists)
    unknown = find_unknown_categories(rules, config.transaction_types)
    conflicts = find_conflicts(rules, master)

    rules.to_csv(RULES_PATH / 'category_rules.csv', index=False)
    unknown.to_csv(RULES_PATH / 'unknown_categories.csv', index=False)
    conflicts.to_csv(RULES_PATH / 'conflicts.csv', index=False)

    in_both = rules['Source'].str.contains('+', regex=False).sum()
    print(f"Rules: {len(rules)} ({(rules['Source'] == 'mapping').sum()} mapping only, "
          f"{(rules['Source'] == 'config').sum()} config only, {in_both} in both)")
    print(f"  contains: {(rules['Match'] == 'contains').sum()}, exact: {(rules['Match'] == 'exact').sum()}")
    print(f"Distinct categories used: {rules['Category'].nunique()} of the {len(config.transaction_types)} in the list")
    print(f"Categories outside the list: {len(unknown)}  -> {RULES_PATH / 'unknown_categories.csv'}")
    print(f"Conflicts to resolve: {len(conflicts)} ({(conflicts['Kind'] == 'payee').sum()} payees, "
          f"{(conflicts['Kind'] == 'term').sum()} terms)  -> {RULES_PATH / 'conflicts.csv'}")

    # The sanity number from step 1.1's measurement: credit-card money-out rows covered by any rule.
    cards = master[(master['Account Type'] == 'Credit Card') & (master['Amount'] > 0)]
    covered = cards['Payee'].astype(str).str.lower().str.strip().map(lambda p: len(matching_rules(rules, p)) > 0)
    print(f"Credit-card money-out rows covered by any rule: {covered.mean():.1%} of {len(cards)} "
          f"(2026-10-19 measurement with the old sources: 82.1% of non-transfer rows)")
    report_short_terms(rules, master)
