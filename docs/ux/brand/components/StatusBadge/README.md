# StatusBadge

A small word in one of the four status roles, so the state of a record, cell or claim is readable at a glance and never by colour alone.

## Use

- One badge per row or cell; it carries a word ("Included", "Unclear", "Retracted", "Not reported"), never an icon alone.
- Role colours: `include`, `unclear`, `blocked`, `exclude`, each on its `-soft` tint. Text is the full role colour; never ink on a tint.
- `label` type style, `radius-sm`, padding `space-1` by `space-2`.
- A count may follow the word inside the badge ("Disagree 131"). Keep tabular numbers.

## Don't

- Don't invent a fifth colour for a new state; map it to one of the four roles.
- Don't use a full status colour as a fill behind the word.
- Don't make a badge clickable; put the action in a button beside it.
