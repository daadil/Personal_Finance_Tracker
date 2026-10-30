"""Tests for categorise.py (step 1.1). Run:  python test_categorise.py   All data is made up."""
import pandas as pd
import categorise
import import_rules


def make_master(rows):
    """rows: (date, payee, amount, account, account type)"""
    return pd.DataFrame(rows, columns=['Posted Date', 'Payee', 'Amount', 'Account', 'Account Type'])


def test_out_and_in_same_amount_different_accounts_are_a_pair():
    master = make_master([
        ('2026-01-10', 'TO SAVINGS', 500.0, 'Checking A', 'Checking'),
        ('2026-01-11', 'FROM CHECKING', -500.0, 'Savings B', 'Savings'),
    ])
    assert categorise.find_pairs(master, 3) == [(0, 1)]


def test_outside_the_window_is_not_a_pair():
    master = make_master([
        ('2026-01-10', 'x', 500.0, 'Checking A', 'Checking'),
        ('2026-01-20', 'y', -500.0, 'Savings B', 'Savings'),
    ])
    assert categorise.find_pairs(master, 3) == []


def test_same_account_is_not_a_pair():
    master = make_master([
        ('2026-01-10', 'x', 500.0, 'Checking A', 'Checking'),
        ('2026-01-10', 'y', -500.0, 'Checking A', 'Checking'),
    ])
    assert categorise.find_pairs(master, 3) == []


def test_card_refund_is_never_a_transfer():
    # A $20 refund on a card and a $20 withdrawal on the same day are a coincidence, not a transfer.
    master = make_master([
        ('2026-01-10', 'ATM', 20.0, 'Checking A', 'Checking'),
        ('2026-01-10', 'REFUND STORE', -20.0, 'Some Card', 'Credit Card'),
    ])
    assert categorise.find_pairs(master, 3) == []


def test_each_row_is_used_once():
    # Two $500 withdrawals, one $500 deposit: one pair, not two.
    master = make_master([
        ('2026-01-10', 'a', 500.0, 'Checking A', 'Checking'),
        ('2026-01-10', 'b', 500.0, 'Checking A', 'Checking'),
        ('2026-01-10', 'c', -500.0, 'Savings B', 'Savings'),
    ])
    assert len(categorise.find_pairs(master, 3)) == 1


def test_wording_only_transfer_has_no_partner():
    master = make_master([
        ('2026-01-10', 'Internet transfer to Certificate of Deposit', 30000.0, 'Checking A', 'Checking'),
        ('2026-01-11', 'MCDONALDS', 9.0, 'Checking A', 'Checking'),
    ])
    report = categorise.label_transfers(master)
    assert len(report) == 1
    assert report.iloc[0]['How'] == 'wording only'
    assert report.iloc[0]['Amount'] == 30000.0


def test_bill_pay_and_venmo_are_not_labelled_a_transfer():
    master = make_master([
        ('2026-01-10', 'SOMETHING BILL PAY', 137.13, 'Checking A', 'Checking'),
        ('2026-01-10', 'VENMO CASHOUT', -306.0, 'Savings B', 'Savings'),
    ])
    assert len(categorise.label_transfers(master)) == 0


def test_paired_rows_report_both_sides():
    master = make_master([
        ('2026-01-10', 'TO SAVINGS', 500.0, 'Checking A', 'Checking'),
        ('2026-01-10', 'FROM CHECKING', -500.0, 'Savings B', 'Savings'),
    ])
    report = categorise.label_transfers(master)
    assert len(report) == 2 and set(report['How']) == {'paired'}
    assert set(report['Partner Account']) == {'Checking A', 'Savings B'}


RULES = pd.DataFrame([
    ('safeway', 'contains', 'Groceries', 'mapping'),
    ('safeway fuel', 'contains', 'Transportation', 'mapping'),
    ('payment - thank you', 'exact', 'Credit Card Payment', 'mapping'),
], columns=['Term', 'Match', 'Category', 'Source'])


def test_pick_category_order_david_then_single_rule_then_longest_term_then_none():
    assert categorise.pick_category('safeway fuel 12', RULES, {'safeway fuel 12': 'Gym'}) == ('Gym', 'david')
    assert categorise.pick_category('safeway 55', RULES, {}) == ('Groceries', 'rule')
    assert categorise.pick_category('safeway fuel 12', RULES, {}) == ('Transportation', 'longest term')
    assert categorise.pick_category('mystery shop', RULES, {}) == ('', 'none')


def test_assign_categories_sets_kind_and_leaves_transfers_uncategorised_and_master_unchanged():
    master = make_master([
        ('2026-01-10', 'SAFEWAY 55', 40.0, 'Card A', 'Credit Card'),
        ('2026-01-11', 'SAFEWAY 55', -5.0, 'Card A', 'Credit Card'),          # a refund: money in, still categorised
        ('2026-01-12', 'Internet transfer to Savings', 500.0, 'Checking A', 'Checking'),
    ])
    before = master.copy()
    result = categorise.assign_categories(master, RULES, {}, {2})
    assert list(result['Kind']) == ['spending', 'money in', 'transfer']
    assert list(result['Category']) == ['Groceries', 'Groceries', '']
    assert master.equals(before)


def test_rules_outside_the_category_list_are_reported():
    category_list = pd.DataFrame({'Category': ['Groceries', 'Transportation']})
    assert categorise.rules_outside_list(RULES, category_list) == ['Credit Card Payment']


def test_review_table_lists_uncategorised_payees_biggest_first_and_skips_transfers():
    master = make_master([
        ('2026-01-10', 'SAFEWAY 55', 40.0, 'Card A', 'Credit Card'),                      # categorised
        ('2026-01-11', 'MYSTERY SHOP ONE 12', 10.0, 'Card A', 'Credit Card'),
        ('2026-01-12', 'BIG UNKNOWN PLACE', 500.0, 'Card A', 'Credit Card'),
        ('2026-01-13', 'Internet transfer to Savings', 900.0, 'Checking A', 'Checking'),   # a transfer: not listed
    ])
    result = categorise.assign_categories(master, RULES, {}, {3})
    table = categorise.build_review_table(result)
    assert list(table['Payee']) == ['BIG UNKNOWN PLACE', 'MYSTERY SHOP ONE 12']
    assert table.iloc[1]['Term'] == 'mystery shop'


def test_apply_review_makes_rules_only_from_answered_rows_and_checks_the_category_list():
    category_list = pd.DataFrame({'Category': ['Groceries', 'Taxes']})
    review = pd.DataFrame({'Payee': ['A SHOP', 'B SHOP', 'C SHOP'], 'Term': ['a shop', 'b shop', ''],
                           'Your Category': ['Taxes', '', 'Taxes']})
    new_rules, problems = categorise.rules_from_review(review, RULES, category_list)
    assert list(new_rules['Term']) == ['a shop'] and new_rules.iloc[0]['Source'] == 'david'
    assert problems == ["'C SHOP': the Term is blank"]
    bad = pd.DataFrame({'Payee': ['D SHOP'], 'Term': ['d shop'], 'Your Category': ['Nonsense']})
    assert 'not in categories.csv' in categorise.rules_from_review(bad, RULES, category_list)[1][0]


def test_apply_review_makes_one_rule_for_many_variants_and_rejects_one_term_two_categories():
    category_list = pd.DataFrame({'Category': ['Groceries', 'Taxes', 'Water']})
    same = pd.DataFrame({'Payee': ['A SHOP 1', 'A SHOP 2', 'A SHOP 3'], 'Term': ['a shop'] * 3,
                         'Your Category': ['Water'] * 3})
    new_rules, problems = categorise.rules_from_review(same, RULES, category_list)
    assert len(new_rules) == 1 and problems == []
    clash = pd.DataFrame({'Payee': ['A SHOP 1', 'A SHOP 2'], 'Term': ['a shop'] * 2,
                          'Your Category': ['Water', 'Taxes']})
    assert categorise.rules_from_review(clash, RULES, category_list)[1] == ["the term 'a shop' was given two different categories"]


if __name__ == '__main__':
    for name, test in list(globals().items()):
        if name.startswith('test_'):
            test()
            print('ok  ', name)
