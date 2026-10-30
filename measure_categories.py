# Read-only: how much of the master do the old category sources cover? Writes nothing.
# Measured 2026-10-19 (results in project_plans/DECISIONS.md D11). Rerun after the master or the rules change:
#   python measure_categories.py      (needs openpyxl: pip install openpyxl)
import sys, pandas as pd
from pathlib import Path
BASE = Path(__file__).parent
DATA = BASE / 'private_data'
sys.path.insert(0, str(DATA / 'reference'))
import config  # the 2023 keyword lists, in private_data/reference/

m = pd.read_csv(DATA / 'master' / 'master.csv')
m['p'] = m['Payee'].str.lower()
spend = m[(m.Amount > 0)].copy()          # money out; refunds/deposits looked at separately
print('master rows', len(m), '| money-out rows', len(spend), '| money-out $', round(spend.Amount.sum()))

# Source 1: Mapping.xlsx Sheet2 (Payee exact, Search Term substring)
mp = pd.read_excel(DATA / 'reference' / 'Mapping.xlsx', sheet_name='Sheet2').dropna(subset=['Category'])
exact = dict(zip(mp['Payee'].str.lower().str.strip(), mp['Category']))
terms = mp.dropna(subset=['Search Term'])
terms = [(str(t).lower().strip(), c) for t, c in zip(terms['Search Term'], terms['Category']) if len(str(t).strip()) >= 4]
print('mapping rows', len(mp), '| distinct categories', mp['Category'].nunique(), '| search terms', len(terms))

# Source 2: config.py keyword lists
lists = {n: v for n, v in vars(config).items() if isinstance(v, list) and v and all(isinstance(x, str) for x in v)
         and n not in ('file_paths','credit_card','savings_account','checking_account','accountType','transaction_types')}
kw = [(k.lower(), n) for n, v in lists.items() for k in v]
print('config keyword lists', len(lists), '| keywords', len(kw))

def by_exact(p): return exact.get(p.strip())
def by_term(p):
    for t, c in terms:
        if t in p: return c
def by_kw(p):
    for k, n in kw:
        if k in p: return n

for name, fn in [('exact payee (Mapping)', by_exact), ('search term (Mapping)', by_term), ('keywords (config)', by_kw)]:
    hit = spend['p'].map(fn)
    print(f"{name:24s} rows {hit.notna().mean():5.1%}  dollars {spend.Amount[hit.notna()].sum() / spend.Amount.sum():5.1%}")
any_hit = spend['p'].map(lambda p: by_exact(p) or by_term(p) or by_kw(p))
print(f"{'any of the three':24s} rows {any_hit.notna().mean():5.1%}  dollars {spend.Amount[any_hit.notna()].sum() / spend.Amount.sum():5.1%}")

print('\nby account type (any source), share of rows covered:')
print(any_hit.notna().groupby(spend['Account Type']).mean().round(3).to_string())

# how many distinct payees would need a human, and what they cost
un = spend[any_hit.isna()]
g = un.groupby('Payee').Amount.agg(['size', 'sum']).sort_values('sum', ascending=False)
print('\nuncovered: rows', len(un), '| distinct payees', len(g), '| $', round(un.Amount.sum()))
print('top 25 uncovered payees cover', round(g['sum'].head(25).sum() / un.Amount.sum(), 3), 'of uncovered dollars')
print(g.head(12).round(0).to_string())

# do the two sources disagree where both hit?
both = pd.DataFrame({'a': spend['p'].map(by_term), 'b': spend['p'].map(by_kw)}).dropna()
print('\nrows where Mapping search-term and config both hit:', len(both), '| disagree:', int((both.a.str.lower() != both.b.str.lower()).sum()))

print('\n=== transfers ===')
pat = r'transfer|moneyline|confirmation#|trnsfr|billpayment|bill pay|booster|p2p|venmo|paypal|zelle|ecI?heck|check deposit'
spend['xfer'] = spend['p'].str.contains(pat, regex=True)
print('money-out rows that look like transfers:', int(spend.xfer.sum()), 'of', len(spend), '| dollars', round(spend.Amount[spend.xfer].sum()), 'of', round(spend.Amount.sum()))
for t in ['Credit Card', 'Checking', 'Savings']:
    s = spend[spend['Account Type'] == t]
    nx = s[~s.xfer]
    hit = nx['p'].map(lambda p: by_exact(p) or by_term(p) or by_kw(p))
    print(f"{t:12s} money-out $ {s.Amount.sum():9.0f} | transfer-like $ {s.Amount[s.xfer].sum():9.0f} | non-transfer rows {len(nx):4d}, covered {hit.notna().mean():5.1%} rows, {nx.Amount[hit.notna()].sum()/max(nx.Amount.sum(),1):5.1%} dollars")
