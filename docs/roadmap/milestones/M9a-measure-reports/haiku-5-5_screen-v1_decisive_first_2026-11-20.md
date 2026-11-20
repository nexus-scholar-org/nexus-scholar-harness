# M9a-measure report: anthropic/claude-haiku-5-5 (low effort)

Task `screen-v1`, prompt `sha256:3cccd987e5210cf03afdb29a5de8ecb526fff5b267e8bb06664f28ad972dc449`, outcomes derived under the `decisive_first` not-reported rule. Scope `frozen`, set `sha256:b051e7e850401ea7b6eba9861be035262ddb08a97a93f8db3bcfe3d3075edfe4`, researcher's decisions verified.
1644 of 1644 records scored; 0 not reached.

## Recall and precision on includes
- Include recall (an Unclear is kept): 94.2%, 95% Wilson lower bound 92.2%; missed includes: 37.
- Same, if failed calls count as misses: 94.2% (lower bound 92.2%).
- Precision on includes: 96.5% of the agent's Includes are the researcher's includes; 73.9% counting its Unclear as an include.
- Excludes caught: 78.6% of the researcher's excludes. Unclear rate: 20.8%.

## Confusion (rows: researcher, columns: agent)
| researcher \ agent | Include | Unclear | Exclude | of which the call failed |
| :-- | --: | --: | --: | --: |
| INCLUDE | 462 | 145 | 37 | 0 |
| EXCLUDE | 17 | 197 | 786 | 5 |

## Draft ladder gates (review-wide)
| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |
| :-- | --: | --: | --: | --: | --: | :-- | :-- |
| L1 | 644 | 35 | 92.2% | 92.2% | 90.0% | yes | yes |
| L2 | 644 | 75 | 92.2% | 92.2% | 95.0% | no | no |

## Undecided, truncated and malformed
- Left undecided by the agent (call ok, outcome Unclear): 337, by reason {'failed_check': 196, 'criterion_not_reported': 139, 'cannot_decide': 2}.
- Driver statuses: {'ok': 1639, 'refusal': 5}; truncated 0, invalid 0, refused 5, error 0.
- Failed checks on answers that parsed: {'quote_in_source': 196}.

## Tokens and cost
- Totals: {'input_tokens': 3941136, 'output_tokens': 702225, 'cache_read_tokens': 3161132, 'cache_write_tokens': 1924}; mean 2824.4 and max 5057 tokens per record.
- Cost: total $0.3726, per record $0.000227, per 1,000 records $0.23 (prices as of 2026-11-11, Batches half price).

## Batches under the draft thresholds
- Under L1's recall (0.9): batch_031, batch_049, batch_066, batch_069, batch_086, batch_110, batch_113, batch_123, batch_137, batch_147, batch_168, batch_171, batch_173, batch_175, batch_181, batch_185, batch_186, batch_188, batch_189, batch_197, batch_207, batch_208, batch_210, batch_211, batch_215, batch_221, batch_240, batch_241, batch_243, batch_248, batch_270, batch_275, batch_280, batch_283.
- Under L2's recall (0.95): batch_031, batch_049, batch_066, batch_069, batch_086, batch_110, batch_113, batch_123, batch_137, batch_147, batch_168, batch_171, batch_173, batch_175, batch_181, batch_185, batch_186, batch_188, batch_189, batch_197, batch_207, batch_208, batch_210, batch_211, batch_215, batch_221, batch_240, batch_241, batch_243, batch_248, batch_270, batch_275, batch_280, batch_283.
- descriptive: a batch holds few includes; the gates above are the review-wide figures.
