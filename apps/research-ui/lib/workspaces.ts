import { consoleBase, postJson, readJson } from "./screening-api";

/**
 * The workspaces routes (M5-slim; `docs/architecture/workspaces-api.md` §3).
 * Shapes mirror the engine's answers; every check (validity, busy, the root)
 * is the engine's, and the screen only shows the result.
 */

export interface WorkspaceItem {
  slug: string;
  title: string | null;
  path: string;
  valid: boolean;
  invalid_reason?: string;
  has_corpus?: boolean;
  screening_started?: boolean;
  /** Where the screening stands (M6-beta); older engines omit it. */
  status?: "NEW" | "CORPUS_ACCEPTED" | "SCREENING" | "PUBLISHED" | "PUBLISHED_CHANGED";
  last_event?: { at: string | null; action: string | null } | null;
  is_current: boolean;
  /** H-workspace-format-version: the recorded format (a read); older engines omit it. */
  format?: WorkspaceFormat;
  /** The newest copy saved before a newer version opened the review. */
  last_copy?: WorkspaceCopy | null;
}

export interface WorkspaceFormat {
  recorded: boolean;
  format: number | null;
  written_by: string | null;
  newer: boolean;
  unreadable: boolean;
}

export interface WorkspaceCopy {
  name: string;
  folder: string;
  at: string;
  bytes: number;
}

/**
 * Whether the open workspace is ready, being copied (with progress), or refused
 * (H-workspace-format-version; `GET /api/v1/workspaces/preparation`).
 */
export interface WorkspacePreparation {
  state: "ready" | "preparing" | "refused" | "cancelled";
  slug: string;
  title: string;
  reason: "format" | "build" | null;
  done_bytes: number;
  total_bytes: number;
  refusal?: { code: string; message: string; details?: unknown };
  result?: { copied: boolean; copy: { name: string; folder: string } | null };
}

export interface WorkspaceListing {
  root: string;
  root_source: "flag" | "environment" | "settings" | "default";
  writable: boolean;
  current: { slug: string; path: string } | null;
  busy: { run_active: boolean; pairing_open: boolean };
  skipped_count: number;
  items: WorkspaceItem[];
  /** The open workspace's preparation; `null` with none open, absent from older engines. */
  preparation?: WorkspacePreparation | null;
}

export interface CreatedWorkspace {
  slug: string;
  path: string;
  protocol_fingerprint: string;
}

export interface OpenedWorkspace {
  slug: string;
  path: string;
  restarting: boolean;
}

export function getWorkspaces(origin: string, includeInvalid = false, signal?: AbortSignal): Promise<WorkspaceListing> {
  const query = includeInvalid ? "?include_invalid=true" : "";
  return readJson<WorkspaceListing>(`/api/v1/workspaces${query}`, consoleBase(origin), signal);
}

export function createWorkspace(origin: string, title: string, signal?: AbortSignal): Promise<CreatedWorkspace> {
  return postJson<CreatedWorkspace>("/api/v1/workspaces", origin, { title }, signal);
}

export function openWorkspace(origin: string, slug: string, signal?: AbortSignal): Promise<OpenedWorkspace> {
  return postJson<OpenedWorkspace>("/api/v1/workspaces/open", origin, { slug }, signal);
}

export async function getPreparation(origin: string, signal?: AbortSignal): Promise<WorkspacePreparation | null> {
  const body = await readJson<{ preparation: WorkspacePreparation | null }>("/api/v1/workspaces/preparation", consoleBase(origin), signal);
  return body.preparation ?? null;
}

/** The workspace the engine serves now; `null` while none is open. */
export async function currentWorkspacePath(origin: string, signal?: AbortSignal): Promise<string | null> {
  const meta = await readJson<{ workspace?: string }>("/api/v1/workspace/meta", consoleBase(origin), signal);
  return meta.workspace ?? null;
}

/**
 * The folder name the engine derives from a title, for the live caption only;
 * the engine's own `slugify` decides (a mismatch shows as the created path).
 */
export function previewSlug(title: string): string {
  // `scholar_harness.inception.intent.slugify`: lower-case, drop what is not a
  // word character, space or hyphen (Python's \w keeps Unicode letters), then
  // collapse runs of spaces and hyphens.
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}_\s-]/gu, "")
    .replace(/[-\s]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
