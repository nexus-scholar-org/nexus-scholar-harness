# M9a-measure report: anthropic/claude-sonnet-5-5 (low effort)

Task `screen-v1`, prompt `sha256:3cccd987e5210cf03afdb29a5de8ecb526fff5b267e8bb06664f28ad972dc449`. Scope `frozen`, set `sha256:b051e7e850401ea7b6eba9861be035262ddb08a97a93f8db3bcfe3d3075edfe4`, researcher's decisions verified.
1644 of 1644 records scored; 0 not reached.

## Recall and precision on includes
- Include recall (an Unclear is kept): 95.5%, 95% Wilson lower bound 93.6%; missed includes: 29.
- Same, if failed calls count as misses: 95.5% (lower bound 93.6%).
- Precision on includes: 99.2% of the agent's Includes are the researcher's includes; 38.5% counting its Unclear as an include.
- Excludes caught: 1.7% of the researcher's excludes. Unclear rate: 73.0%.

## Confusion (rows: researcher, columns: agent)
| researcher \ agent | Include | Unclear | Exclude | of which the call failed |
| :-- | --: | --: | --: | --: |
| INCLUDE | 395 | 220 | 29 | 0 |
| EXCLUDE | 3 | 980 | 17 | 0 |

## Draft ladder gates (review-wide)
| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |
| :-- | --: | --: | --: | --: | --: | :-- | :-- |
| L1 | 644 | 35 | 93.6% | 93.6% | 90.0% | yes | yes |
| L2 | 644 | 75 | 93.6% | 93.6% | 95.0% | no | no |

## Undecided, truncated and malformed
- Left undecided by the agent (call ok, outcome Unclear): 1200, by reason {'failed_check': 37, 'criterion_not_reported': 1163}.
- Driver statuses: {'ok': 1644}; truncated 0, invalid 0, refused 0, error 0.
- Failed checks on answers that parsed: {'quote_in_source': 37}.

## Tokens and cost
- Totals: {'input_tokens': 3941136, 'output_tokens': 644003, 'cache_read_tokens': 3161132, 'cache_write_tokens': 1924}; mean 2789.0 and max 4962 tokens per record.
- Cost: total $4.1586, per record $0.00253, per 1,000 records $2.53 (prices as of 2026-11-11, Batches half price).

## Batches under the draft thresholds
- Under L1's recall (0.9): batch_030, batch_033, batch_035, batch_060, batch_067, batch_072, batch_110, batch_141, batch_151, batch_171, batch_172, batch_173, batch_187, batch_188, batch_197, batch_201, batch_202, batch_208, batch_213, batch_220, batch_221, batch_231, batch_241, batch_243, batch_249, batch_262, batch_266, batch_282.
- Under L2's recall (0.95): batch_030, batch_033, batch_035, batch_060, batch_067, batch_072, batch_110, batch_141, batch_151, batch_171, batch_172, batch_173, batch_187, batch_188, batch_197, batch_201, batch_202, batch_208, batch_213, batch_220, batch_221, batch_231, batch_241, batch_243, batch_249, batch_262, batch_266, batch_282.
- descriptive: a batch holds few includes; the gates above are the review-wide figures.
