# Multi-Agent Screening Consensus Report

This report documents the scientific multi-rater screening workflow executed for the `ai-research-harnesses-trust` workspace.

## Screeners
A total of four independent AI screeners evaluated the literature batches:
1. **Screener 1**: Gemini Flash 3.8
2. **Screener 2**: Big Picle (Open Code)
3. **Screener 3**: Gemini 3.1 Pro (Antigravity subagent)
4. **Screener 4**: Gemini 3.1 Pro (Antigravity subagent)

## Methodology
- **Majority Voting**: For the 239 screened documents, a 4-way vote was collected. Any paper with 3 or 4 votes for a specific outcome was automatically assigned that consensus decision.
- **Tie-breaking (Adjudication)**: Any paper deadlocked at 2-vs-2 (2 INCLUDEs, 2 EXCLUDEs) was flagged for adjudication. A dedicated Senior Adjudicator Agent was spawned to evaluate and definitively break the ties.

## Voting Results & Agreement
- **Screener 1 (Gemini Flash 3.8)**: 84 INCLUDES
- **Screener 2 (Big Picle)**: 71 INCLUDES
- **Screener 3 (Gemini 3.1 Pro)**: 60 INCLUDES
- **Screener 4 (Gemini 3.1 Pro)**: 19 INCLUDES
- **Fleiss' Kappa (across all 4)**: 0.408 (Fair/Moderate agreement)

## Final Reconciled Outcomes
Out of 239 total documents:
- **Clear Consensus (3+ votes)**: 48 INCLUDE, 165 EXCLUDE
- **Deadlocks (2-vs-2 ties)**: 26 papers (Resolved by Senior Adjudicator)

### Definitive Final Results
- **Total INCLUDE**: 58
- **Total EXCLUDE**: 181

The fully reconciled decisions for all 239 papers have been saved to:
`literature/screening/final_reconciled_decisions.json`

