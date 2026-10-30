"""Tests for import_rules.py (step 1.2). Run:  python test_import_rules.py   All data is made up."""
import pandas as pd
import import_rules as ir

MAPPING = pd.DataFrame([
    # a search term -> a 'contains' rule
    {'Payee': 'SAFEWAY #1 SEATTLE WA', 'Search Term': 'Safeway', 'Category': 'Groceries'},
    {'Payee': 'SAFEWAY FUEL 12 SEATTLE', 'Search Term': 'Safeway Fuel', 'Category': 'Transportation'},
    # a category but no search term -> an 'exact' rule on the whole payee
    {'Payee': 'PAYMENT - THANK YOU', 'Search Term': None, 'Category': 'Credit Card Payment'},
    # no category -> ignored
    {'Payee': 'MYSTERY SHOP', 'Search Term': None, 'Category': None},
])
CONFIG = {'groceries': ['safeway', 'trader joe'], 'gym': ['otf']}


def make_rules():
    return ir.build_rules(MAPPING, CONFIG)


def test_rules_from_both_sources_are_merged_and_typed():
    rules = make_rules()
    safeway = rules[(rules.Term == 'safeway') & (rules.Category == 'Groceries')]
    assert len(safeway) == 1 and safeway.iloc[0]['Source'] == 'config+mapping'   # same rule from both sources, merged
    exact = rules[rules.Match == 'exact']
    assert list(exact.Term) == ['payment - thank you']
    assert 'mystery shop' not in set(rules.Term)                                 # no category, no rule
    assert 'otf' in set(rules.Term)                                              # short terms are kept


def test_payee_matching_two_categories_is_a_conflict_with_longest_term_suggested():
    rules = make_rules()
    master = pd.DataFrame({'Payee': ['SAFEWAY FUEL 12 SEATTLE', 'SAFEWAY FUEL 12 SEATTLE', 'SAFEWAY #1 SEATTLE WA']})
    conflicts = ir.find_conflicts(rules, master)
    assert len(conflicts) == 1                                                    # the plain Safeway payee has one category
    row = conflicts.iloc[0]
    assert row['Kind'] == 'payee' and row['Rows in master'] == 2
    assert row['Suggested'] == 'Transportation' and row['Chosen'] == ''


def test_same_term_with_two_categories_is_a_term_conflict():
    mapping = pd.DataFrame([{'Payee': 'x', 'Search Term': 'amazon', 'Category': 'Shopping'},
                            {'Payee': 'y', 'Search Term': 'amazon', 'Category': 'Subscriptions'}])
    rules = ir.build_rules(mapping, {})
    conflicts = ir.find_conflicts(rules, pd.DataFrame({'Payee': ['nothing']}))
    assert list(conflicts['Kind']) == ['term']


def test_category_outside_the_list_is_reported():
    unknown = ir.find_unknown_categories(make_rules(), ['Groceries', 'Transportation', 'Gym'])
    assert list(unknown['Category']) == ['Credit Card Payment']
    assert unknown.iloc[0]['Map To'] == ''


def test_exact_rule_matches_only_the_whole_payee():
    rules = make_rules()
    assert len(ir.matching_rules(rules, 'payment - thank you')) == 1
    assert len(ir.matching_rules(rules, 'payment - thank you very much')) == 0


def test_category_list_counts_rules_and_matching_rows_and_keeps_notes():
    rules = make_rules()
    master = pd.DataFrame({'Payee': ['SAFEWAY FUEL 12 SEATTLE', 'TRADER JOES 5', 'TRADER JOES 9']})
    table = ir.build_category_list(rules, master, ['Groceries', 'Transportation', 'Gym', 'Tithe'],
                                   {'Tithe': 'his own note'})
    row = {r['Category']: r for _, r in table.iterrows()}
    assert row['Transportation']['Master rows matching'] == 1
    assert row['Groceries']['Master rows matching'] == 3        # the Safeway Fuel payee also matches 'safeway'
    assert row['Tithe']['Rules using it'] == 0 and row['Tithe']['Note'] == 'his own note'
    assert 'Credit Card Payment' in set(table['Category'])      # used by a rule, so added to the list


if __name__ == '__main__':
    for name, test in list(globals().items()):
        if name.startswith('test_'):
            test()
            print('ok  ', name)
