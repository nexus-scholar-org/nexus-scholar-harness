# Performance & Caching Notes for methodology-copilot

There is no interview or caching runtime in the committed tree: no
`methodology_copilot` Python package (`ParadigmRefractor`,
`SocraticInterviewer`), no `scripts/interview.py`, and no paradigm-template
cache. Do not import, invoke, or document them.

The supported seams are the `scholar-harness inception` wizard (interactive),
`scholar_harness.inception.run_wizard` with an injected responder
(scripted/hermetic), and the `workspace-manager` / `scholar-protocol` CLIs
documented in `SKILL.md`. Refraction, interviewing, and criteria rendering are
conversational + deterministic-CLI work; no bulk-processing or template-cache
machinery exists to tune.

HCM-02 / HCM-05 revisit: if interview or caching runtime lands in the committed
tree, re-derive this note from that implementation. Until then, document current
interfaces only.
