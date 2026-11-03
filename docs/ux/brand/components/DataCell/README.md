# DataCell

One cell of the extraction table in each of its states, so a machine draft is never mistaken for a verified value.

## Use

- Four states, each by background: **draft** on plain `surface` (machine-drafted, unchecked), **verified** on `include-soft`, **edited** on `brand-soft` (a person changed it), **not reported** on `exclude-soft` in `exclude` italic text.
- The selected cell takes a 2px `brand` inset outline.
- Numbers in cells use tabular figures; identifiers use `data` style.
- A table legend repeats the four states with counts, so export can be blocked while any draft remains.

## Don't

- Don't tint a draft cell; its plainness is the signal.
- Don't leave a cell blank: "not reported" is a value and gets its own state.
