import { consoleBase, postJson, readJson } from "./screening-api";

/**
 * The query workbench routes (M11a parts A and B; `docs/roadmap/milestones/M11a-query-workbench.md`).
 *
 * Two places share these shapes: a draft at Inception
 * (`/api/v1/inception/drafts/{id}/workbench/…`) and the open workspace on Plan
 * (`/api/v1/discovery/workbench/…`). Every number, gain, ratio, cost, status,
 * reset time and suggested term is the engine's; the screen prints them.
 * Nothing is sent on a keystroke: a real call goes out only on Count, "What
 * does each synonym add?", "Read what this concept removes", the seed check or
 * the comparison, each after a dry run that stated its cost.
 */

export interface VersionConcept {
  concept: string;
  synonyms: string[];
}

export interface Version {
  query_key: string;
  concepts: VersionConcept[];
  start_year?: number | null;
  end_year?: number | null;
  languages?: string[];
}

/** A cell of the counts table: the full query, a concept left out, or a term left out. */
export interface Cell {
  kind: "full" | "drop" | "synonym";
  concept_index: number | null;
  concept: string | null;
  term: string | null;
  status: string;
  total: number | null;
  string: string | null;
  counted_at: string | null;
  from_cache: boolean;
  error: string | null;
  error_code: string | null;
  http_status: number | null;
  resets_at: string | null;
  gain?: number | null;
  ratio?: number | null;
  note?: boolean;
  largest?: boolean;
  adds_nothing?: boolean;
}

export interface Span {
  hours: number;
  minutes: number;
}

export interface DatabaseRow {
  name: string;
  status: string;
  any_words: boolean;
  upper_bound: boolean;
  string: string | null;
  total: number | null;
  counted_at: string | null;
  from_cache: boolean;
  error: string | null;
  error_code: string | null;
  http_status: number | null;
  resets_at: string | null;
  resets_in: Span | null;
  /** The longest one count may take, in seconds (the engine's `COUNT_TIMEOUT`). */
  timeout_seconds?: number;
  cost: number;
  requests: number;
  last: { total: number; counted_at: string } | null;
  stopped?: { status: string; error_code: string | null; http_status: number | null; resets_at: string | null; resets_in: Span | null } | null;
  drops?: Cell[];
  synonyms?: Cell[];
}

export interface Budget {
  limit: number;
  spent: number;
  left: number;
  renews_at: string;
  low: boolean;
}

export interface Note {
  concept_index: number;
  concept: string;
  database: string;
  total: number;
  without: number;
}

export interface SizeLine {
  estimate: { counted_all: boolean; records: { low: number; high: number | null }; works: { low: number; high: number | null }; assumption: string };
  effort: { pace_seconds: number; hours: { low: number | null; high: number | null } };
  warn: { level: "none" | "note" | "warning"; threshold_works: number; limit: { value: number; source: "planned" | "general" } };
  recommendation: Record<string, unknown>;
  cap: number;
}

export interface CountsAnswer {
  shape: string;
  query_key: string;
  dry_run: boolean;
  version: Version;
  concepts: number;
  terms: number;
  cost: { total: number; by_database: Record<string, number>; cached: boolean };
  requests: number;
  databases: DatabaseRow[];
  budget: Record<string, Budget | null>;
  notes?: Note[];
  size?: SizeLine;
  concept_index?: number;
  /** Decision 2026-11-20, M11a item 10: the version written for Scopus and Web of Science, to copy. */
  external?: Record<string, string>;
  mailto_set: boolean;
}

export interface RemovedAnswer {
  dry_run: boolean;
  database: string;
  concept_index: number;
  concept: string;
  string: string | null;
  cost: number;
  requests: number;
  status: string;
  resets_at: string | null;
  read: number;
  records: { title: string; doi: string | null; year: number | null; lacks: string[] }[];
}

export interface SeedRow {
  doi: string;
  title: string | null;
  read: boolean;
  concepts: { concept: string; found: boolean }[];
  lacks: string[];
  missed: boolean;
  suggestions: string[];
}

export interface SeedsAnswer {
  dry_run: boolean;
  cost: { lookup: number; openalex: number };
  requests: number;
  seeds: SeedRow[];
  total: number;
  read: number;
  not_read: number;
  use_every_concept: number;
  missed: number;
  warning: { level: "all" | "concept" | "few"; untested: string[] } | null;
  databases: { name: string; status: string; found: string[]; not_found: string[] }[];
  checked_at: string;
}

export interface ComparisonSet {
  id: string;
  database: string;
  string: string | null;
  exported_on: string;
  staged_at: string;
  file_name: string;
  format: string;
  records_count: number;
  no_abstract: number;
  with_doi: number;
}

export interface ReportAnswer {
  set: ComparisonSet;
  measure: "harvest" | "openalex" | "words";
  version: Version;
  total: number;
  no_abstract: number;
  cost: number;
  requests: number;
  status: string;
  against: { label: string; records: number } | null;
  not_checked: number;
  not_in_database: number | null;
  missing_count: number | null;
  page: number;
  pages: number;
  missing: { title: string | null; doi: string | null; year: number | null; lacks: string[]; no_abstract: boolean }[];
  terms: { term: string; records: number; of: number }[];
}

/** Where the workbench reads and writes: a draft (Inception) or the open workspace (Plan). */
export type Place = { kind: "draft"; id: string } | { kind: "workspace" };

export function workbenchBase(place: Place): string {
  return place.kind === "draft" ? `/api/v1/inception/drafts/${encodeURIComponent(place.id)}/workbench` : "/api/v1/discovery/workbench";
}

export function postCounts(origin: string, place: Place, body: { version: Version; providers?: string[]; dry_run: boolean; crossref_anyway?: boolean }, signal?: AbortSignal) {
  return postJson<CountsAnswer>(`${workbenchBase(place)}/counts`, origin, body, signal);
}

export function postSynonyms(origin: string, place: Place, body: { version: Version; concept_index: number; provider: string; dry_run: boolean }, signal?: AbortSignal) {
  return postJson<CountsAnswer>(`${workbenchBase(place)}/synonyms`, origin, body, signal);
}

export function postRemoved(origin: string, place: Place, body: { version: Version; concept_index: number; dry_run: boolean }, signal?: AbortSignal) {
  return postJson<RemovedAnswer>(`${workbenchBase(place)}/removed`, origin, body, signal);
}

export function postSeeds(origin: string, place: Place, body: { version: Version; seeds?: string[]; lookup: boolean; openalex: boolean; dry_run: boolean }, signal?: AbortSignal) {
  return postJson<SeedsAnswer>(`${workbenchBase(place)}/seeds`, origin, body, signal);
}

export function getSets(origin: string, place: Place, signal?: AbortSignal) {
  return readJson<{ sets: ComparisonSet[] }>(`${workbenchBase(place)}/comparison`, consoleBase(origin), signal);
}

export function stageSet(origin: string, place: Place, body: { file_name: string; content_base64: string; database: string; string?: string | null; exported_on?: string | null }) {
  return postJson<ComparisonSet>(`${workbenchBase(place)}/comparison`, origin, body);
}

export function removeSet(origin: string, place: Place, id: string) {
  return postJson<{ sets: ComparisonSet[] }>(`${workbenchBase(place)}/comparison/${encodeURIComponent(id)}/remove`, origin, {});
}

export function postReport(origin: string, place: Place, id: string, body: { version: Version; measure: string; page: number; run?: string; dry_run: boolean }, signal?: AbortSignal) {
  return postJson<ReportAnswer>(`${workbenchBase(place)}/comparison/${encodeURIComponent(id)}/report`, origin, body, signal);
}
