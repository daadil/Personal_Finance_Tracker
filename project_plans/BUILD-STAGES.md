# BUILD-STAGES

The plan: ordered steps, each with a gate that can be observed. What happened: PROGRESS.md.
Later stages stay at decision level until their turn.

## Stage 0: Ingest credit cards into one master (built, gate open)
Progress: Capital One loaded; BoA (both cards) and 2023 Capital One files are in the inbox, dry run clean,
not loaded yet. Chase, AMEX, Discover: no exports yet.
Gate: one real export from each of the 7 cards loads, the rows in `master/master.csv` match the
bank's own statement for that period, and the export is deleted. Needs David's real exports; code
cannot close this gate.

## Stage 1 onward: not yet planned
Candidates are in ACTION-ITEMS.md (payments and returns, checking, savings, categories, rewards,
charts, stale-data warning). Order and gates to be agreed with David before any is started.
