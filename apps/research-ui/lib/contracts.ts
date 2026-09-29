export type WorkflowState = "complete" | "active" | "waiting" | "refused";

export interface WorkflowStage {
  id: string;
  label: string;
  description: string;
  state: WorkflowState;
  count?: number;
}

export interface ProjectSummary {
  slug: string;
  title: string;
  researchQuestion: string;
  lastEvent: string;
  stages: WorkflowStage[];
}

export interface EvidenceNode {
  kind: "claim" | "chunk" | "document" | "study" | "decision";
  label: string;
  detail: string;
  status: "accepted" | "source" | "reviewed";
}

// These are view models, not Contract v1 models. The UI never mints contract
// identities or decides acceptance. Future API responses map authoritative
// harness artifacts into these deliberately presentation-only shapes.
