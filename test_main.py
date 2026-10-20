"""Tests for main.py. Run:  python test_main.py
All data here is made up. The tests point main.py at a temporary folder, never at the real inbox."""
import tempfile
from pathlib import Path
import pandas as pd
import main

BOA = "Posted Date,Reference Number,Payee,Address,Amount\n" \
      "01/05/2026,1,COFFEE SHOP,SEATTLE WA,-4.50\n" \
      "01/05/2026,2,COFFEE SHOP,SEATTLE WA,-4.50\n" \
      "01/06/2026,3,REFUND STORE,SEATTLE WA,20.00\n"
CAPITAL_ONE = "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit\n" \
              "2026-01-04,2026-01-05,1234,GROCERY,Merchandise,12.5,\n" \
              "2026-01-05,2026-01-06,1234,RETURN,Merchandise,,7.25\n"
CHASE = "Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n" \
        "01/04/2026,01/05/2026,GAS STATION,Gas,Sale,-30.00,\n"


def new_sandbox():
    """Point main.py at an empty temp folder and return it."""
    folder = Path(tempfile.mkdtemp())
    main.INBOX_PATH = folder / 'inbox'
    main.MASTER_PATH = folder / 'master' / 'master.csv'
    return folder


def drop(card, name, text):
    folder = main.INBOX_PATH / card
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text)


def test_load_and_delete():
    new_sandbox()
    drop('BoA Premium Rewards', 'a.csv', BOA)
    drop('CO Savor One', 'b.csv', CAPITAL_ONE)
    drop('Chase Sapphire Preferred', 'c.csv', CHASE)
    main.process_inbox()
    master = pd.read_csv(main.MASTER_PATH)
    assert len(master) == 6, master
    # charges positive, refunds negative, dates Year-Month-Day
    boa = master[master['Credit Card'] == 'BoA Premium Rewards']
    assert sorted(boa['Amount']) == [-20.0, 4.5, 4.5]
    co = master[master['Credit Card'] == 'CO Savor One']
    assert sorted(co['Amount']) == [-7.25, 12.5]
    assert master[master['Payee'] == 'GAS STATION']['Amount'].iloc[0] == 30.0
    assert set(master['Posted Date']) == {'2026-01-05', '2026-01-06'}
    # all three exports deleted
    assert list(main.INBOX_PATH.glob('*/*.csv')) == []


def test_same_file_twice_adds_nothing():
    new_sandbox()
    drop('BoA Premium Rewards', 'a.csv', BOA)
    main.process_inbox()
    drop('BoA Premium Rewards', 'a_again.csv', BOA)
    results = main.process_inbox()
    assert len(pd.read_csv(main.MASTER_PATH)) == 3
    assert '0 new rows' in results[0] and 'Export deleted' in results[0]
    assert list(main.INBOX_PATH.glob('*/*.csv')) == []


def test_overlapping_export_adds_only_new_rows_and_keeps_real_repeats():
    new_sandbox()
    # first export has ONE coffee; the second (overlapping) has two identical coffees plus a refund
    first = BOA.splitlines()[0] + "\n" + BOA.splitlines()[1] + "\n"
    drop('BoA Premium Rewards', 'a.csv', first)
    main.process_inbox()
    drop('BoA Premium Rewards', 'b.csv', BOA)
    main.process_inbox()
    assert len(pd.read_csv(main.MASTER_PATH)) == 3


def test_same_row_on_different_card_is_not_a_duplicate():
    new_sandbox()
    drop('BoA Premium Rewards', 'a.csv', BOA)
    drop('BoA Customized Cash Rewards', 'a.csv', BOA)
    main.process_inbox()
    assert len(pd.read_csv(main.MASTER_PATH)) == 6


def test_bad_file_is_kept_and_master_untouched():
    new_sandbox()
    drop('BoA Premium Rewards', 'bad.csv', "Foo,Bar\n1,2\n")
    results = main.process_inbox()
    assert 'NOT LOADED' in results[0]
    assert (main.INBOX_PATH / 'BoA Premium Rewards' / 'bad.csv').exists()
    assert not main.MASTER_PATH.exists()


def test_stray_csv_in_inbox_root_is_reported_and_kept():
    new_sandbox()
    main.INBOX_PATH.mkdir(parents=True)
    (main.INBOX_PATH / 'oops.csv').write_text(BOA)
    results = main.process_inbox()
    assert any('oops.csv' in r and 'NOT LOADED' in r for r in results)
    assert (main.INBOX_PATH / 'oops.csv').exists()


if __name__ == '__main__':
    for name, test in list(globals().items()):
        if name.startswith('test_'):
            test()
            print('ok  ', name)
