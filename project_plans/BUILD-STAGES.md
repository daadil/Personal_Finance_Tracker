# BUILD-STAGES

The plan: ordered steps, each with a gate that can be observed. What happened: PROGRESS.md.
Later stages stay at decision level until their turn.

## Stage 0: Ingest every account into one master (built, gate open)
Progress (2026-10-19): loaded for real: Capital One, both BoA cards, Ally (3 accounts), BoA Savings: 1,496
rows in the master. No export yet: AMEX, Discover, both Chase cards, BoA Checking, Chase Checking and Savings.
Gate: one real export from each of the 14 accounts loads, the rows in `master/master.csv` match the
bank's own statement for that period, and the export is deleted. Needs David's real exports; code
cannot close this gate.

## Stage 1 (next, not started): categories
Decided by David (D10). Not planned in detail until Stage 0's gate closes (ACTION-ITEMS #18 holds the inputs).

## Stage 2 onward: not yet planned
Candidates are in ACTION-ITEMS.md (payments and returns, checking, savings, categories, rewards,
charts, stale-data warning). Order and gates to be agreed with David before any is started.
