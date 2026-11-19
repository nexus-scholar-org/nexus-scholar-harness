# M9a-measure report: anthropic/claude-opus-5-5 (low effort)

Task `screen-v1`, prompt `sha256:3cccd987e5210cf03afdb29a5de8ecb526fff5b267e8bb06664f28ad972dc449`. Scope `frozen`, set `sha256:b051e7e850401ea7b6eba9861be035262ddb08a97a93f8db3bcfe3d3075edfe4`, researcher's decisions verified.
1644 of 1644 records scored; 0 not reached.

## Recall and precision on includes
- Include recall (an Unclear is kept): 95.0%, 95% Wilson lower bound 93.1%; missed includes: 32.
- Same, if failed calls count as misses: 95.0% (lower bound 93.1%).
- Precision on includes: 99.3% of the agent's Includes are the researcher's includes; 39.5% counting its Unclear as an include.
- Excludes caught: 6.4% of the researcher's excludes. Unclear rate: 77.1%.

## Confusion (rows: researcher, columns: agent)
| researcher \ agent | Include | Unclear | Exclude | of which the call failed |
| :-- | --: | --: | --: | --: |
| INCLUDE | 278 | 334 | 32 | 0 |
| EXCLUDE | 2 | 934 | 64 | 0 |

## Draft ladder gates (review-wide)
| gate | includes compared | needed | recall lower bound | if failed calls were misses | needed | passes | passes if failed calls were misses |
| :-- | --: | --: | --: | --: | --: | :-- | :-- |
| L1 | 644 | 35 | 93.1% | 93.1% | 90.0% | yes | yes |
| L2 | 644 | 75 | 93.1% | 93.1% | 95.0% | no | no |

## Undecided, truncated and malformed
- Left undecided by the agent (call ok, outcome Unclear): 1268, by reason {'criterion_not_reported': 1250, 'failed_check': 18}.
- Driver statuses: {'ok': 1644}; truncated 0, invalid 0, refused 0, error 0.
- Failed checks on answers that parsed: {'quote_in_source': 12, 'one_answer_per_criterion': 6}.

## Tokens and cost
- Totals: {'input_tokens': 3941136, 'output_tokens': 621803, 'cache_read_tokens': 3159208, 'cache_write_tokens': 3848}; mean 2775.5 and max 4926 tokens per record.
- Cost: total $8.0997, per record $0.004927, per 1,000 records $4.93 (prices as of 2026-11-11, Batches half price).

## Batches under the draft thresholds
- Under L1's recall (0.9): batch_033, batch_035, batch_063, batch_067, batch_073, batch_086, batch_110, batch_161, batch_164, batch_165, batch_168, batch_171, batch_172, batch_173, batch_174, batch_185, batch_187, batch_197, batch_201, batch_202, batch_206, batch_208, batch_220, batch_221, batch_231, batch_232, batch_248, batch_249, batch_262, batch_280, batch_282.
- Under L2's recall (0.95): batch_033, batch_035, batch_063, batch_067, batch_073, batch_086, batch_110, batch_161, batch_164, batch_165, batch_168, batch_171, batch_172, batch_173, batch_174, batch_185, batch_187, batch_197, batch_201, batch_202, batch_206, batch_208, batch_220, batch_221, batch_231, batch_232, batch_248, batch_249, batch_262, batch_280, batch_282.
- descriptive: a batch holds few includes; the gates above are the review-wide figures.
