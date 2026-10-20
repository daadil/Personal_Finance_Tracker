# ACTION-ITEMS

Permanently numbered. A resolved item keeps its number and loses its detail.

1. Card payments are left out for Capital One ("PYMT") and both BoA cards ("PAYMENT - THANK YOU",
   "Online payment from", "PYMT TRANSFER"), checked on real data. Chase, AMEX and Discover still load their
   payments: find each one's wording on its first real export (Chase has a `Type` column that marks them)
   and add it to `PAYMENT_WORDS`. DECIDED 2026-10-19 (David): cash-back credits (CASH AUTO REDEMPTION,
   CASH BACK, CREDIT-CASH BACK REWARD) are KEPT, and so are refunds. Refunds are important to the goal
   (D7). Needs a way to tell them apart later, see #14.
2. Returns: a refund is a negative amount, kept as is. Decide whether it should be linked to the
   original purchase.
3. AMEX and Discover column names are UNVERIFIED (the old script never converted them). Drop one real
   export of each and confirm; a mismatch leaves the file in the inbox with the columns it found.
4. Anticipate each card's next annual fee and create a calendar reminder.
5. Ingest checking accounts (same inbox pattern). Folders exist in `inbox/` (Ally, BoA, Chase); `main.py`
   does not read them yet. See #13 for the export layouts seen in the old script.
6. Ingest savings accounts (same inbox pattern). Same as #5.
7. Categorise transactions (method not chosen).
8. Credit cards only: transaction type and cash-vs-points logic (restaurant = 3% back).
9. Credit cards only: points / cash back earned per purchase.
10. Chart all data, interactive, with filters.
11. Stale-data warning: if the latest Posted Date for a card is more than 45 days old, print
    "possible stale data, please add newest csv".
12. Overlapping exports are de-duplicated by matching rows (date, payee, amount, card), not by date
    range. Identical rows are matched by count, so two real identical purchases survive, but they are
    kept only up to the largest count that any single export shows.
13. Account layouts for checking/savings, from the 2023 script (UNVERIFIED against today's exports):
    Ally: `Date, Time, Amount, Type, Description` (some exports pad the names with a leading space).
    BoA checking and savings: 6 summary lines above the real header, then `Date, Description, Amount, Balance`.
    Chase checking: `Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #`.
    The loader needs a folder-per-account list like `CREDIT_CARD_NAMES` and its own `PAYMENT_WORDS`-style
    rule for transfers between David's own accounts (a transfer is not spending or income).
14. Keep refunds and cash-back visible, not mixed into spending. Add a transaction kind (purchase, refund,
    cash back, fee, transfer) so reports can show or hide each. Refunds net against their category.
15. UPDATE THE FINANCIAL WORKFLOW DIAGRAM. `reference/financial_workflow.pdf` is the 2020 set-up (last
    card info updated 2/27/2023): income sources -> checking -> savings / retirement / CD, plus each card's
    earn rates and annual fee. Redraw it for today's accounts in the SAME STYLE: boxes with logos for
    accounts and cards, yellow sticky notes for rules ("transfer excess $x to maintain $20k-$22k"), diamonds
    for decisions, dashed coloured zones per account type, and one card-detail panel per card with annual
    fee and a "Need Renewal Date" note where it is missing. Drawing tool not chosen (the PDF looks like a
    diagram-editor export); decide with David. Also feeds #4 (annual-fee reminders: renewal dates are blank
    in the old diagram).
16. Rocket Money parity (from general knowledge of the product, not checked against its site): categorised
    spending, recurring bills and subscription detection, per-category budgets, spending trends, net worth
    across accounts, alerts. Pick which of these matter and in what order; this is the Stage 1+ plan.
17. Expense Tracker sheet parity (`Expense Tracker`, Google Sheets). Its tabs: Expenses (form entry),
    CSV Ingest, Date Metrics (savings per year), Monthly Expenses per year (each category by month, a
    total row and a monthly-budget row), MappingTable. The new tool must reproduce the monthly-by-category
    roll-up with budget vs actual, an owner column (whose account), and savings per year.
18. Categories. Source material in `reference/`: `Mapping.xlsx` (about 600 rows: Payee, Search Term, Store,
    Category, Agency) and the keyword lists in `config.py` (about 38 category names). Decide how a payee
    becomes a category (the old way was "payee contains keyword", last match wins) and measure it against
    real data before trusting it (CLAUDE.md: measure, do not reason).
