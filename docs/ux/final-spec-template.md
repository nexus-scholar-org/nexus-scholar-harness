# Final screen spec template

One page per screen at `docs/ux/<phase>/final/NN-<screen>.md`. The canvas boards
stay as design history; a spec cites them and never redraws them. UI work on a
screen starts only when its spec says `Status: FINAL`, and a spec is FINAL only
when it has no open questions. Example:
[`phase2-screening/final/03-triage-desktop.md`](phase2-screening/final/03-triage-desktop.md).

Mark every backend call as existing (✓) or new (✗ plus the milestone that adds
it). Name contract types and refusal codes exactly as the API contract and
[`../architecture/refusals.md`](../architecture/refusals.md) spell them.

Copy the block below.

```markdown
# NN Screen name    Status: DRAFT | Phase N Name | Route `/path` | Milestone Mx (what) + My (what)

Boards: `BoardName` (id, state). Contract: `docs/architecture/<contract>.md` §n.

**Purpose.** One sentence: the researcher's job on this screen.

**Changed from the canvas.**
- Each place the spec overrides the board, and why (decision or contract section).

## Entry / exit
- Entry: where from (screen, link, shortcut).
- Exit: where to, and the gate that must hold.

## Data in
| Field | Source |
| :-- | :-- |
| fields shown | `GET /path` ✓ or ✗ Mx; contract type |

## Data out
Writes: endpoint, payload fields, per-item results, journal event emitted.

## Backend calls
| Call | Status |
| :-- | :-- |
| `METHOD /api/v1/...` | ✓ / ✗ Mx |

## States
- **Default**:
- **Empty**:
- **Loading** (skeleton):
- **Error** (typed refusal code → copy):
- **Partial**:
- **Offline**:
- **Stale / protocol changed**:

## Desktop layout
Reference to the board or brand key-screen; regions and their order.

## Mobile layout (≤ 640 px)
Layout, touch targets ≥ 44 px, gestures.

## Keyboard
Shortcuts and focus order.

## Copy
i18n keys and en master strings (fr/ar fall back to en, plan §7).

## Accessibility
Contrast pairs, RTL notes, screen-reader labels.

## Acceptance tests
vitest and Playwright spec names, one line each on what they prove.

## Open questions
Must be empty to mark FINAL. Once answered, rename this section to
"Decisions" and record each answer with its date and source.
```
