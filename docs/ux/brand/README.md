# Nexus Scholar Provenance: brand and design system (2026-11-03)

The visual identity for Nexus Scholar, built fresh from the Phase 0 to Phase 4 wireframes and
their UX reviews (`docs/ux/phase*/`). It replaces the grey wireframe look.

Status: **proposal**, first version, no logo yet. Not yet applied to any canvas or to `apps/research-ui`.

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Design system (brand book, tokens, component previews, cover) | https://claude.ai/artifact/AX9uczVF5he8NDnurHfXDX | [`BRAND_BOOK.md`](BRAND_BOOK.md), [`tokens.json`](tokens.json), [`components/`](components/) |

The live design system is the source of truth; this folder is a snapshot so the brand is findable
in the repo. The Design canvases can install it (the Theme menu then offers its colours and text
styles), and `apps/research-ui` can take `tokens.json` as the basis for its CSS variables.

## The idea in one line

Every number has a source. The interface shows the evidence behind each number, decision and claim.

## Decisions made

- **Neutral-first palette, one hue.** Cool off-white ground, blue-black ink, hairline structure, no
  shadows. `brand` (archive blue) is spent on one primary action per screen.
- **A provenance colour.** `anchor` (burnt ochre) is reserved for evidence: citation anchors,
  verbatim quotes, DOIs. It is the colour that says "this is where the proof is".
- **Four status roles for the whole pipeline.** `include`, `unclear`, `blocked`, `exclude`, each
  with a soft tint, so a researcher learns the colours once. Exclusion is a quiet grey on purpose.
- **Three typefaces, one job each.** Literata for the question each screen asks, Public Sans for
  everything a person reads or fills in, IBM Plex Mono for identifiers only.
- **Machine output looks like a draft.** Plain surface until a person verifies it; only then a tint.
- **Both themes designed**, not inverted; every text colour passes 4.5:1 on its background in both.

## Components (static previews)

`StatusBadge`, `TrustLevel`, `EvidenceQuote`, `GatePanel`, `DataCell`, plus the `Cover`. Each has
a README with use and don't rules and a preview built only from the tokens. There is no component
bundle yet.

## Key screens with the brand applied (2026-11-03)

| Item | Live (private) | Source in this folder |
| :-- | :-- | :-- |
| Canvas, four screens, light and dark | https://claude.ai/artifact/BkEi7opNKhTHMmYoynaNcC | [`key-screens/`](key-screens/) |

Screening triage queue (Phase 2), data extraction table (Phase 3), review and emit (Phase 0) and
trust summary (Phase 4), rebuilt from their wireframes with the design system installed on the
canvas. `key-screens/screens.css` holds the shared patterns (badge, button, card, gate, quote,
table) and is the first draft of what `apps/research-ui` would implement; `ds/nexusscholar/tokens.css`
is the token file compiled by hand from `tokens.json`. Rendered and checked in both themes.

## Next

1. Decide on a logo or wordmark; until then the name in `title` style is the mark.
2. Map `tokens.json` and `screens.css` to `apps/research-ui`.
3. Rebuild the remaining wireframe screens on the brand once these four are approved.
