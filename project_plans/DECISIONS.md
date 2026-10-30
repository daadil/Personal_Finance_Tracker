# DECISIONS

Why, including what was rejected and what it cost. (How it works: ARCHITECTURE.md.)

## D1. Rewrite the 2023 script instead of patching it (2026-10-19)
It had hardcoded paths, formatters that changed a copy, a `.strftime` call on a whole column, bare
`try/except` blocks hiding both, and dead code after `exit()`. Cost: the old structure is gone;
the old TODO list was moved to ACTION-ITEMS.md.

## D2. Inbox folder per card, export deleted after load (2026-10-19, David)
The folder name says which bank format to expect, so no guessing from file contents.
Cost: a file in the wrong folder fails its column check and is kept, not loaded.

## D3. Duplicates are matched by row count, not by file or date range (2026-10-19)
Re-dropping a file adds nothing; overlapping exports add only new rows; two real identical purchases
on one day both survive. Rejected: skipping a whole file if its dates overlap the master (loses rows
when exports overlap partly) and plain "drop duplicate rows" (deletes real repeat purchases).
Cost: see ACTION-ITEMS #12.

## D4. Columns picked by name, not position (2026-10-19)
The old script dropped columns by index, so a bank adding a column would silently shift the data.

## D5. Default branch is `main` (2026-10-19)
Renamed from `master` to follow the template.

## D6. Payments are dropped by payee wording, one card at a time (2026-10-19)
A payment is not spending, so it is left out at load and counted in the result line. The wording is
set per card in `PAYMENT_WORDS` only after it has been seen in a real export (Capital One: "PYMT").
Rejected: dropping every negative amount (that would also drop real refunds, 10 of 46 negative rows
in the first Capital One load). Cost: each new card needs a look at its real data first.

## D7. What this project is for (2026-10-19, David)
A local version of Rocket Money plus the `Expense Tracker` Google Sheet: categorised spending, budgets,
monthly roll-ups, with the data staying on this Mac. Refunds matter (so negative amounts are not
discarded), and cash-back credits are kept. Cost: everything Rocket Money does from a bank link (live
sync, bill negotiation) is out of reach; data arrives only as exported CSVs.

## D8. Reference material lives in a gitignored `private_data/reference/` folder (2026-10-19)
The old 2023 script, its config (merchant lists), `Mapping.xlsx` and the workflow PDF are copied there so
any session can find them. They hold personal merchants and account detail, so they are never committed.
Rejected: committing the scripts alone (the merchant lists are personal). Cost: a fresh clone has no
reference folder; the originals are in David's Google Drive.

## D9. One master for every account type; money leaving is positive (2026-10-19)
Checking and savings go in the same master as cards. The column `Credit Card` became `Account` and a new
`Account Type` column (Credit Card, Checking, Savings) was added; the 1,261 existing rows were migrated.
The sign rule is the same for all: money leaving the account is positive, money coming in is negative, so a
card charge and a checking withdrawal read alike and a deposit reads like a refund. Rejected: one file per
account type (the old script) because transfers and net worth need all accounts side by side. Cost: a
transfer shows up twice (out of one account, into another) until ACTION-ITEMS #14 labels it.

## D10. Order of work after Stage 0 (2026-10-19, David)
Categories first (ACTION-ITEMS #18), because budgets, roll-ups and subscriptions all need them. Diagram tool:
draw.io (#15).

## D11. Transfers come before categories (2026-10-19, measured)
`measure_categories.py` on the 1,496-row master: about 70% of the money-out dollars are transfer-like
(moves between his own accounts, brokerage, CD). Checking is 97% transfers by dollars and Savings is 100%.
On credit cards alone (no transfers) the old Mapping.xlsx and keyword lists cover 82% of rows and 71% of
dollars. Overall, before separating transfers, they cover 79% of rows but only 22% of dollars: the number that
looked fine was the wrong one. (The 72-of-740 "disagreement" first reported here was an artefact of comparing first matches; see D17.)
Rejected: categorising first (every total would be dominated by transfers).

## D12. Category list and new payees (2026-10-19, David)
Use the old 38-name list from config.py (it matches the Expense Tracker sheet's monthly tabs). Payees the old
mapping does not know are proposed by Claude into a gitignored review CSV that David edits; his answers
become rules. Rejected: asking in the terminal each run (200+ distinct payees now) and leaving them blank.

## D13. Derived data goes in a separate file; the master stays raw (2026-10-19)
Kind and Category are written to `private_data/master/categorised.csv`, rebuilt from the master and the rules. Rejected:
adding category columns to `master.csv`, because the loader's duplicate check and the deleted exports make
the master the only copy of the raw data, and a rules mistake would then be permanent.

## D14. Transfer matching: 3-day window, wording rules kept short (2026-10-19, measured)
Pair count by days apart on the 1,496-row master: 6 at 0 days, 8 at every window from 1 to 30. No pair
is more than 1 day apart, so 3 days (slack for a weekend) finds everything a wider window does. Pairing
is limited to checking and savings, one-to-one, different accounts: a card refund must never be read as a
transfer. Only 8 pairs exist because the other side of most transfers is not in the data (BoA Checking,
Chase, Fidelity and a CD are not loaded), so 106 rows are labelled by payee wording alone.
Rejected: wording that could also be a real payment ("bill pay", Venmo, PayPal, Zelle). Those rows stay
unlabelled and show up in the check for David. Cost: some true transfers (P2P cash-outs) stay unlabelled
until he says so.

## D15. Card payments and the cards that are not loaded (2026-10-29, David and measured)
Step 1.1's gate passed. David's answers to check (b): the large unlabelled rows are real spending or payments
on cards or real spending; one was a payment on a closed store card whose purchases are not in the data, one was taxes.
Measured on the 63 non-transfer Ally Checking rows: no payment to a LOADED card (Capital One, BoA) appears in
Ally Checking, so nothing is double counted today. The only card payments there are to that closed store card, a card whose own
purchases are not in the data, so the payment is the only record of that spending and counts as spending.
Rule: a payment to a card whose purchases ARE loaded is not spending; a payment to a card whose purchases are
NOT loaded is spending. Risk: when BoA Checking is loaded, its payments to the loaded cards would double count
(ACTION-ITEMS #19).

## D16. One gitignored folder for everything personal (2026-10-29, David)
`private_data/` holds the actuals (`inbox/`, `master/`), the training data (`reference/`, `rules/`, `review/`)
and all outputs (`test_output/`); the .gitignore names that one folder, with the earlier file-type patterns
kept as a second layer. Before this the data folders sat at the repo root, each with its own ignore line.
Audited at the same time: no data file has ever been committed on any branch. The docs had carried real
totals and two named transactions; those are removed from the files but remain in the history of two pushed
commits (rewriting pushed history is against David's rule, so the choice is his). Cost: a fresh clone has no
`private_data/` and `main.py` creates the inbox folders on its first run; the reference files come from Drive.

## D17. Importing the old rules: what the measurement changed (2026-10-29)
Three corrections to the step 1.2 spec, all from running it on the real data:
1. Conflicts: 2 payees (one "safeway" vs "safeway fuel" pattern), not 72. The 72 compared the first match of
   each old source, so ordering looked like disagreement. Counting every matching rule per payee gives 2.
   The longest-term-wins assumption fits both: the file suggests it, David confirms.
2. Short terms: the spec skipped terms under 4 characters. That was a guess; it would have dropped real stores
   (a gym, a grocer). They are kept, and the script prints what each short term matches in the master. All 9
   matched what was intended.
3. 97 Mapping rows have a category but no search term, only the full payee text. They are imported as exact-match
   rules instead of being lost.
Result: 302 rules (198 from the mapping, 32 from config, 72 from both), 23 categories used of the 38. One category
outside the list: "Credit Card Payment" (6 rules); these are the same payment wording the loader already drops,
so they never reach the master. Coverage of credit-card money-out rows with the rules: 81.9% (82.1% measured
before; the denominators differ slightly), so nothing was lost in the import.

## D18. "Credit Card Payment" is its own category; the category list is a file David owns (2026-10-29, David)
He answered the 1.2 review files: the unknown category "Credit Card Payment" becomes a category of its own (39
names now, not 38), and both Safeway-fuel payees are Transportation (longest term won, as suggested). He also
edited four rules (two Kohl's rules and Quince from Shopping to Clothes; rover.com from Travel to Pet).
`private_data/rules/categories.csv` is now the list of allowed categories, with rule counts and his notes; he
edits it, and `import_rules.py --category-list` refreshes the counts without losing his names or notes.
`import_rules.py` refuses to overwrite `category_rules.csv` (it would wipe his edits) unless `--force` is given.
Payments on cards that are loaded stay dropped at load (D6); David decided not to keep them for a cross-check
("let's not overcomplicate", ACTION-ITEMS #21), so the category has no rows. Rejected: keeping payments to
reconcile card spend, and giving payments a Kind instead of a category.

## D19. How the review loop works (2026-10-29)
David gave categories for the ten largest gaps; they went in through the same review file the rest will use.
Choices, all from running it on the real data: (1) `Term` is prefilled with the first two words of the payee and
the apply step prints how many master rows each new rule matches, so a term that is too broad shows itself;
(2) one rule per distinct term, because seven variants of one bill had been written as seven identical rules (a
defect found on the first real apply and fixed, with a test); (3) any problem stops the whole apply, so it is
never half done; (4) the file is archived, not deleted, after applying. Suggestions are never applied without
David copying them into `Your Category`: he asked not to overcomplicate, and wrong category rules cost more
than a copy and paste. Rejected: an accept-all-suggestions switch. "Taxes" was added as a new category at his
request, separate from Property Tax. Anything he calls a store card payment (a card not loaded) is categorised
"Credit Card Payment" and still counts as spending (D15).

## D20. Second review batch: what was held, fixed and found (2026-10-29)
David filled in 169 of 182 rows. Applied 163 rules with no payee matching two categories. Three judgment calls:
1. "Subscription" was not in his list; read as the typo it is and applied as "Subscriptions" (said so to him).
2. His category for the bank's "Interest Paid" lines (Credit Card Fees) was held back, not applied: all 37 rows
   are money coming in on savings and checking, which is interest earned (Income). Card interest he pays is a
   different payee and already has a rule. Held pending his word (settled in D21).
3. His "eCheck deposit" is categorised Taxes (he said that is what he sees when paying property tax) although
   the one row is money in. Applied as told.
Found by running it: two new rules matched 0 rows because the bank writes payees with irregular double spaces.
Matching now ignores capitals and extra spaces on both sides (test added). Also: four rows (two credits, an
adjustment, a rebill of the same amount) net to zero, so leaving them uncategorised changes no total.

## D21. A rule may depend on the account type (2026-10-29, David)
David's rule: "Interest Paid" means different things by account: on checking or savings it is money earned
(Income); on a credit card it is money spent. Rules gained an optional `Account Type` column (blank = every
account; several types separated by `|`), and matching now takes the account type of each row. Two rules were
added: "interest paid" for Checking|Savings is Income, for Credit Card is Credit Card Fees. In the current data
every "Interest Paid" row is on a savings or checking account (37 rows), so today only the Income rule is used;
the card rule is for later exports. Rejected: a separate payee wording per bank (David's point is that the same
words flip meaning, so the account type has to be an input). Cost: one more column in the rules file, and
`import_rules.find_conflicts` does not yet consider it (it is a one-off and its files are already answered).
