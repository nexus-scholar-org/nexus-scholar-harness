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
}

export interface WorkspaceListing {
  root: string;
  root_source: "flag" | "environment" | "default";
  writable: boolean;
  current: { slug: string; path: string } | null;
  busy: { run_active: boolean; pairing_open: boolean };
  skipped_count: number;
  items: WorkspaceItem[];
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
