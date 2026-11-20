# M9a-measure report: anthropic/claude-haiku-5-5 (low effort)

Task `screen-v2`, prompt `sha256:4a026b9f9eb06536e124c10fbb88f914cebafeea308787314a3c838a8278a11a`, outcomes derived under the `decisive_first` not-reported rule. Scope `frozen`, set `sha256:b051e7e850401ea7b6eba9861be035262ddb08a97a93f8db3bcfe3d3075edfe4`, researcher's decisions verified.
1644 of 1644 records scored; 0 not reached.

## Recall and precision on includes
- Include recall (an Unclear is kept): 94.6%, 95% Wilson lower bound 92.5%; missed includes: 35.
- Same, if failed calls count as misses: 94.6% (lower bound 92.5%).
- Precision on includes: 95.9% of the agent's Includes are the researcher's includes; 68.6% counting its Unclear as an include.
- Excludes caught: 72.1% of the researcher's excludes. Unclear rate: 22.9%.

## Confusion (rows: researcher, columns: agent)
| researcher \ agent | Include | Unclear | Exclude | of which the call failed |
| :-- | --: | --: | --: | --: |
| INCLUDE | 490 | 119 | 35 | 0 |
| EXCLUDE | 21 | 258 | 721 | 5 |

## Draft ladder gates (review-wide)
| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |
| :-- | --: | --: | --: | --: | --: | :-- | :-- |
| L1 | 644 | 35 | 92.5% | 92.5% | 90.0% | yes | yes |
| L2 | 644 | 75 | 92.5% | 92.5% | 95.0% | no | no |

## Undecided, truncated and malformed
- Left undecided by the agent (call ok, outcome Unclear): 372, by reason {'failed_check': 283, 'criterion_not_reported': 89}.
- Driver statuses: {'ok': 1639, 'refusal': 5}; truncated 0, invalid 0, refused 5, error 0.
- Failed checks on answers that parsed: {'quote_in_source': 283}.

## Tokens and cost
- Totals: {'input_tokens': 4292952, 'output_tokens': 697452, 'cache_read_tokens': 3508458, 'cache_write_tokens': 6414}; mean 3035.5 and max 5127 tokens per record.
- Cost: total $0.3891, per record $0.000237, per 1,000 records $0.24 (prices as of 2026-11-11, Batches half price).

## Batches under the draft thresholds
- Under L1's recall (0.9): batch_031, batch_049, batch_065, batch_066, batch_067, batch_074, batch_083, batch_110, batch_112, batch_113, batch_123, batch_136, batch_137, batch_168, batch_171, batch_173, batch_174, batch_175, batch_187, batch_188, batch_194, batch_197, batch_200, batch_208, batch_211, batch_221, batch_232, batch_243, batch_248, batch_280.
- Under L2's recall (0.95): batch_031, batch_049, batch_065, batch_066, batch_067, batch_074, batch_083, batch_110, batch_112, batch_113, batch_123, batch_136, batch_137, batch_168, batch_171, batch_173, batch_174, batch_175, batch_187, batch_188, batch_194, batch_197, batch_200, batch_208, batch_211, batch_221, batch_232, batch_243, batch_248, batch_280.
- descriptive: a batch holds few includes; the gates above are the review-wide figures.
