# EvidenceQuote

A verbatim passage from a source, with its page, shown wherever a value, decision or claim rests on it.

## Use

- `anchor-soft` background, `radius-sm`, `body` text in `ink`; the locator ("p. 9, Table 3") in `data` style and `anchor` colour before the quote.
- The quote is verbatim; an edit is a new quote. A difference between a claim and its source is marked by a `blocked-soft` span inside the quote and a `blocked` line under it.
- A highlighted criterion word inside an abstract uses the same `anchor-soft` tint as a span.

## Don't

- Don't paraphrase inside the quote block.
- Don't use `unclear-soft` here; ochre means "evidence", amber means "needs you".
