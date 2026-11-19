# M9a-measure report: anthropic/claude-haiku-5-5 (low effort)

Task `screen-v1`, prompt `sha256:3cccd987e5210cf03afdb29a5de8ecb526fff5b267e8bb06664f28ad972dc449`. Scope `frozen`, set `sha256:b051e7e850401ea7b6eba9861be035262ddb08a97a93f8db3bcfe3d3075edfe4`, researcher's decisions verified.
1644 of 1644 records scored; 0 not reached.

## Recall and precision on includes
- Include recall (an Unclear is kept): 98.1%, 95% Wilson lower bound 96.8%; missed includes: 12.
- Same, if failed calls count as misses: 98.1% (lower bound 96.8%).
- Precision on includes: 95.3% of the agent's Includes are the researcher's includes; 39.2% counting its Unclear as an include.
- Excludes caught: 1.9% of the researcher's excludes. Unclear rate: 67.2%.

## Confusion (rows: researcher, columns: agent)
| researcher \ agent | Include | Unclear | Exclude | of which the call failed |
| :-- | --: | --: | --: | --: |
| INCLUDE | 484 | 148 | 12 | 0 |
| EXCLUDE | 24 | 957 | 19 | 5 |

## Draft ladder gates (review-wide)
| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |
| :-- | --: | --: | --: | --: | --: | :-- | :-- |
| L1 | 644 | 35 | 96.8% | 96.8% | 90.0% | yes | yes |
| L2 | 644 | 75 | 96.8% | 96.8% | 95.0% | yes | yes |

## Undecided, truncated and malformed
- Left undecided by the agent (call ok, outcome Unclear): 1100, by reason {'failed_check': 197, 'criterion_not_reported': 902, 'cannot_decide': 1}.
- Driver statuses: {'ok': 1639, 'refusal': 5}; truncated 0, invalid 0, refused 5, error 0.
- Failed checks on answers that parsed: {'quote_in_source': 197}.

## Tokens and cost
- Totals: {'input_tokens': 3941136, 'output_tokens': 701917, 'cache_read_tokens': 3161132, 'cache_write_tokens': 1924}; mean 2824.2 and max 5011 tokens per record.
- Cost: total $0.3726, per record $0.000227, per 1,000 records $0.23 (prices as of 2026-11-11, Batches half price).

## Batches under the draft thresholds
- Under L1's recall (0.9): batch_033, batch_036, batch_065, batch_086, batch_110, batch_135, batch_137, batch_160, batch_185, batch_189, batch_207.
- Under L2's recall (0.95): batch_033, batch_036, batch_065, batch_086, batch_110, batch_135, batch_137, batch_160, batch_185, batch_189, batch_207.
- descriptive: a batch holds few includes; the gates above are the review-wide figures.
