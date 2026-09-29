import type { EvidenceNode, ProjectSummary } from "./contracts";

export const demoProject: ProjectSummary = {
  slug: "demonstration-review",
  title: "Reliable AI-assisted evidence synthesis",
  researchQuestion: "How can AI-assisted reviews remain reproducible and auditable?",
  lastEvent: "Extraction completed for 18 included studies",
  stages: [
    { id: "protocol", label: "Protocol", description: "Question and criteria sealed", state: "complete" },
    { id: "search", label: "Search", description: "Records discovered and deduplicated", state: "complete", count: 143 },
    { id: "screening", label: "Screening", description: "Transparent inclusion decisions", state: "complete", count: 18 },
    { id: "full-text", label: "Full text", description: "PDFs acquired and verified", state: "complete", count: 18 },
    { id: "evidence", label: "Evidence", description: "Extraction and lineage review", state: "active", count: 18 },
    { id: "synthesis", label: "Synthesis", description: "Grounded report not started", state: "waiting" },
  ],
};

export const demoEvidence: EvidenceNode[] = [
  { kind: "claim", label: "Review claim", detail: "Explicit provenance improves auditability.", status: "accepted" },
  { kind: "chunk", label: "Evidence passage", detail: "Methods, paragraph 4", status: "source" },
  { kind: "document", label: "Extracted document", detail: "Verified text derived from the acquired PDF", status: "source" },
  { kind: "study", label: "Included study", detail: "Study record and bibliographic identity", status: "reviewed" },
  { kind: "decision", label: "Screening decision", detail: "Included against the sealed protocol", status: "reviewed" },
];
