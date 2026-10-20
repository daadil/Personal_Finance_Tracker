# ACTION-ITEMS

Permanently numbered. A resolved item keeps its number and loses its detail.

1. Payments are not dropped yet (the master still holds card payments as negative amounts).
   Chase has a `Type` column that marks them; BoA and Capital One need checking against real files.
2. Returns: a refund is a negative amount, kept as is. Decide whether it should be linked to the
   original purchase.
3. AMEX and Discover column names are UNVERIFIED (the old script never converted them). Drop one real
   export of each and confirm; a mismatch leaves the file in the inbox with the columns it found.
4. Anticipate each card's next annual fee and create a calendar reminder.
5. Ingest checking accounts (same inbox pattern).
6. Ingest savings accounts (same inbox pattern).
7. Categorise transactions (method not chosen).
8. Credit cards only: transaction type and cash-vs-points logic (restaurant = 3% back).
9. Credit cards only: points / cash back earned per purchase.
10. Chart all data, interactive, with filters.
11. Stale-data warning: if the latest Posted Date for a card is more than 45 days old, print
    "possible stale data, please add newest csv".
12. Overlapping exports are de-duplicated by matching rows (date, payee, amount, card), not by date
    range. Identical rows are matched by count, so two real identical purchases survive, but they are
    kept only up to the largest count that any single export shows.
