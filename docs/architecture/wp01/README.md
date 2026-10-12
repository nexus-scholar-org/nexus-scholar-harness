# WP-01 packet archive

Dated delivery records for **WP-01** (Contract v1 adoption). WP-01 is closed
(qualified: residual research-validation limits are recorded in the E4 report).
This folder is a historical archive — the normative contract documents remain at
`docs/architecture/contract_v1_baseline.md` and
`docs/architecture/cross_kit_contract_v1.md` (contract-locked), and
`docs/architecture/wp01_contract_adoption_handoff.md` /
`docs/architecture/wp01_packet_c_reference.md` (also contract-locked, not here).

| Packet | Handoff / spec | Completion / closure |
|---|---|---|
| E1 — acquired document | [`wp01_packet_e1_acquired_document_handoff.md`](./wp01_packet_e1_acquired_document_handoff.md) | [`wp01_packet_e1_completion_report.md`](./wp01_packet_e1_completion_report.md) |
| E2 — extracted text | [`wp01_packet_e2_extracted_text_handoff.md`](./wp01_packet_e2_extracted_text_handoff.md) | [`wp01_packet_e2_completion_report.md`](./wp01_packet_e2_completion_report.md) |
| E3 — index/acceptance | [`wp01_packet_e3_implementation_handoff.md`](./wp01_packet_e3_implementation_handoff.md), [`wp01_packet_e3_readiness_baseline.md`](./wp01_packet_e3_readiness_baseline.md) | [`wp01_packet_e3_completion_report.md`](./wp01_packet_e3_completion_report.md), [`e3_residual_repair.md`](./e3_residual_repair.md), [`wp01_e3_adoption_status.md`](./wp01_e3_adoption_status.md) |
| E4 — negative proof | [`wp01_packet_e4_negative_proof_handoff.md`](./wp01_packet_e4_negative_proof_handoff.md) | [`wp01_packet_e4_completion_report.md`](./wp01_packet_e4_completion_report.md) |

The E2 handoff document is read at runtime by
`tests/conformance/test_e2_extraction_boundary.py`; do not move it again without
updating that constant.
