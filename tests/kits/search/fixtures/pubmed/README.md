# PubMed ESearch responses (M3h-providers, F11)

Recorded once on 2026-11-10 from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
with `retmode=json`, no `email`, `tool` or `api_key`. Saved unchanged.

- `esearch_ab_field_not_found.json`: `term=weed[ab] AND drone[ti]`. PubMed has
  no `[ab]` tag: it searched `"weed"[All Fields]`. The XML answer to the same
  request carries `<ErrorList><FieldNotFound>ab</FieldNotFound></ErrorList>`,
  but the JSON `errorlist.fieldsnotfound` is empty, so the provider compares
  the tags it sent with the ones PubMed is known to apply (`[ti]`, `[tiab]`,
  `[au]`, `[pdat]`) whenever PubMed returns a `querytranslation`.
- `esearch_tiab_ok.json`: `term="weed mapping"[tiab] AND drone[ti] AND smith[au] AND 2020:2026[pdat]`;
  every tag is applied (`[Title/Abstract]`, `[Title]`, `[Author]`, `[Date - Publication]`).
- `esearch_golden_uav_warnings.json`: the ESearch answer inside the golden UAV
  cassette (`tests/fixtures/cassettes/golden_uav_search.yaml`, recorded
  2026-11-08), trimmed to `count`, `retmax`, `retstart`, `querytranslation`,
  `errorlist` (absent in this answer) and `warninglist`, with an empty `idlist`. Its `warninglist`
  reports `quotedphrasesnotfound: ['"herbicide prescription"']`, and its
  `querytranslation` shows the words searched separately and ANDed, not dropped.
