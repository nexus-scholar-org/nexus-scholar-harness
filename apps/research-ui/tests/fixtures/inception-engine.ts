/**
 * A small stateful fake of the inception API (`docs/architecture/inception-api.md`),
 * for tests only: the vitest screens stub `fetch` with it and the Playwright spec
 * answers the console proxy with it. It keeps the engine's shapes and refusal
 * codes; the engine's real behaviour is pinned by the Python suite
 * (`tests/console/test_inception_api.py`, `tests/inception/`).
 *
 * The criteria rules here are a test double of `draft_criteria`: the proof answer
 * becomes a generated inclusion, out-of-scope items and typed criteria are the
 * researcher's own (accepted unless rejected).
 */

import { reconEngine, type ReconOptions } from "./recon-engine";
import { checkRow, digestOf, dismissal, INCEPTION_STEPS, respond, withDismissals, type CheckIn } from "./checks-engine";
import { workbenchEngine, type WorkbenchOptions } from "./workbench-engine";

export const ROOT = "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces";
export const SESSION = "rec_0123456789abcdef0123456789abcdef";

type Json = Record<string, unknown>;
export type Answer = { status: number; body: unknown; sse?: boolean };

export interface FakeOptions {
  /** A workspace already in the target folder; `bound` adds screening decisions. */
  existing?: "none" | "workspace" | "bound" | "folder";
  /** Refuse a route once with this answer, keyed `METHOD path`. */
  refuseOnce?: Record<string, Answer>;
  /** The open route's answer (default: a restart). */
  restarting?: boolean;
  /** The recon routes of the draft (M4d): contact address, keys, what each probe finds. */
  recon?: ReconOptions;
  /** M10b: the workspaces `GET /workspaces` lists, and the protocol each holds for the import. */
  workspaces?: { slug: string; title: string; protocol?: Json }[];
  /**
   * M10b Part B: the checks the fake computes. Default: none, so a screen draws no panel. `true`
   * computes a few of the catalogue's checks from the draft (a test double of `inception/checks.py`);
   * a function gives the rows itself.
   */
  checks?: boolean | ((record: Json) => CheckIn[]);
  /** M10b: the whole answer of `POST …/checks` (a test of what the panel shows, counts included). */
  checksAnswer?: (step: string | undefined) => Json;
  /** M10b: whether a mechanism offered an `accepted_from` value (default: each one). */
  offered?: (entry: Json) => boolean;
  /** M11a: the query workbench routes of a draft (`…/workbench/…`). */
  workbench?: WorkbenchOptions;
  /**
   * M11b part D: `steps/criteria` answers the two method settings and their options, as the
   * engine's `method_choice` does (a test double); `order` replaces the engine's order of the rule's options.
   */
  method?: boolean | { order?: string[] };
}

// --- M10b Part B: proposals (test double of `inception/proposals.py`) -----------------

const STEP_OF_FIELD: Record<string, string> = {
  topic: "scope", start_year: "scope", end_year: "scope", languages: "scope",
  golden_seeds: "direction", grounding: "direction",
  paradigm: "shape", playbook: "shape", secondary_paradigm: "shape", unit_of_analysis: "shape", proof: "shape", rqs: "shape", pool_min: "shape", pool_max: "shape",
  concepts: "criteria", extra_inclusions: "criteria", extra_exclusions: "criteria", out_of_scope: "criteria", out_of_scope_reasons: "criteria",
  default_exclusion_reason: "criteria", criteria_decisions: "criteria", matrix_columns: "criteria", custom_matrix_columns: "criteria", verification_checks: "criteria",
  title: "review", lead_researcher: "review", venue: "review", timeline_weeks: "review",
};
const LIST_FIELDS = new Set(["languages", "rqs", "concepts", "extra_inclusions", "extra_exclusions", "out_of_scope", "matrix_columns", "golden_seeds", "custom_matrix_columns"]);
const SYNONYMS = /^concepts\[(.+)\]\.synonyms$/;

const baseField = (field: string) => (SYNONYMS.test(field) ? "concepts" : field);
export const proposalStep = (field: string) => STEP_OF_FIELD[baseField(field)] ?? "review";

function conceptIndex(draft: Json, name: string): number {
  return ((draft.concepts ?? []) as Json[]).findIndex((c) => String(c?.concept ?? "").toLowerCase() === name.toLowerCase());
}

function targetValue(draft: Json, field: string): unknown {
  const m = field.match(SYNONYMS);
  if (m) {
    const i = conceptIndex(draft, m[1]);
    return i < 0 ? null : [...((((draft.concepts as Json[])[i].synonyms ?? []) as unknown[]))];
  }
  if (field in draft) return draft[field];
  return LIST_FIELDS.has(field) ? [] : null;
}

function shownOf(value: unknown): string {
  const one = (v: unknown): string => (v && typeof v === "object" ? String((v as Json).concept ?? (v as Json).criterion ?? (v as Json).name ?? JSON.stringify(v)) : String(v));
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(one).join(", ");
  return one(value);
}

export interface ProposalIn {
  source?: string;
  field: string;
  op?: "add" | "remove" | "replace";
  value: unknown;
  why?: string;
  evidence?: Json[];
  status?: string;
  /** Made against this value of the target instead of the draft's own (a proposal that is out of date). */
  baseValue?: unknown;
}

export function makeProposal(draftId: string, draft: Json, p: ProposalIn): Json {
  const source = p.source ?? "check:CONCEPT_TERM_MISSING";
  const op = p.op ?? "add";
  const current = "baseValue" in p ? p.baseValue : targetValue(draft, p.field);
  const base = { hash: digestOf(current), shown: shownOf(current) };
  const target = { kind: "draft", id: draftId, field: p.field };
  return {
    proposal_id: "prop_" + digestOf([source, target, op, p.value, base.hash]).slice(-12).padStart(12, "0"),
    target,
    op,
    value: p.value,
    why: p.why ?? "",
    evidence: p.evidence ?? [],
    source,
    base,
    status: p.status ?? "open",
    decided_at: null,
    decided_value: null,
    step: proposalStep(p.field),
  };
}

function viewProposal(p: Json, draft: Json): Json {
  const field = String((p.target as Json).field);
  const current = targetValue(draft, field);
  const out: Json = { ...p, step: proposalStep(field), current: shownOf(current) };
  if (p.status === "open" && digestOf(current) !== (p.base as Json).hash) out.status = "stale";
  return out;
}

function listingOf(record: Json, step?: string | null): Json {
  const draft = (record.draft ?? {}) as Json;
  const items = ((record.proposals ?? []) as Json[]).map((p) => viewProposal(p, draft));
  const byStep = Object.fromEntries(INCEPTION_STEPS.map((s) => [s, { open: 0, stale: 0 }])) as Record<string, { open: number; stale: number }>;
  for (const item of items) {
    if ((item.status === "open" || item.status === "stale") && byStep[String(item.step)]) byStep[String(item.step)][item.status === "open" ? "open" : "stale"] += 1;
  }
  return { session_id: record.session_id, updated_at: record.updated_at, proposals: step ? items.filter((i) => i.step === step) : items, by_step: byStep };
}

/** `op value` applied to `field`, or the refusal the engine answers. */
function applyOp(draft: Json, field: string, op: string, value: unknown): Json | { refused: Answer } {
  const next = JSON.parse(JSON.stringify(draft)) as Json;
  const m = field.match(SYNONYMS);
  let holder: Json = next;
  let key = field;
  if (m) {
    const i = conceptIndex(next, m[1]);
    if (i < 0) return { refused: refuse(409, "PROPOSAL_STALE", "the concept is no longer in the draft") };
    holder = (next.concepts as Json[])[i];
    key = "synonyms";
  }
  if (op === "replace") {
    holder[key] = value;
    return next;
  }
  const items = [...(((holder[key] ?? []) as unknown[]))];
  const same = (x: unknown) => JSON.stringify(x).toLowerCase() === JSON.stringify(value).toLowerCase() || (!!x && typeof x === "object" && !!value && typeof value === "object" && String((x as Json).concept ?? "").toLowerCase() === String((value as Json).concept ?? "").toLowerCase());
  if (op === "add") {
    if (items.some(same)) return { refused: refuse(409, "PROPOSAL_NOT_OPEN", "the value is already there", { status: "present" }) };
    holder[key] = [...items, value];
  } else {
    holder[key] = items.filter((x) => !same(x));
  }
  return next;
}

/** The checks the fake computes with `checks: true` (a few rows of the catalogue, never the engine's rules). */
function computedChecks(record: Json): CheckIn[] {
  const draft = (record.draft ?? {}) as Json;
  const rows: CheckIn[] = [];
  const empty = (v: unknown) => v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
  if (empty(draft.topic)) rows.push({ check_id: "SCOPE_TOPIC_MISSING", step: "scope", level: "blocker", action: { kind: "field", step: "scope", field: "topic" } });
  if (draft.start_year == null) rows.push({ check_id: "SCOPE_START_YEAR_DEFAULTED", step: "scope", level: "note", params: { year: 2000 }, action: { kind: "field", step: "scope", field: "start_year" } });
  if (!record.grounding) rows.push({ check_id: "DIRECTION_NOT_CHOSEN", step: "direction", level: "note", action: { kind: "step", step: "direction" } });
  if (draft.pool_max == null) rows.push({ check_id: "SHAPE_PLANNED_SIZE_EMPTY", step: "shape", level: "note", action: { kind: "field", step: "shape", field: "pool_max" } });
  const concepts = (draft.concepts ?? []) as { concept: string; synonyms?: string[] }[];
  if (!concepts.length) rows.push({ check_id: "CONCEPTS_NONE", step: "criteria", level: "blocker", action: { kind: "field", step: "criteria", field: "concepts" } });
  const known = concepts.flatMap((c) => [c.concept, ...(c.synonyms ?? [])]);
  const texts = [String(draft.title ?? ""), String(draft.topic ?? ""), ...((draft.rqs ?? []) as string[])];
  const seen: string[] = [];
  for (const text of texts) for (const m of text.matchAll(/\b([A-Z]{2,6})s?\b/g)) if (!seen.includes(m[1])) seen.push(m[1]);
  for (const term of seen.filter((t) => !known.some((k) => new RegExp(`\\b${t}\\b`, "i").test(k))).slice(0, 5)) {
    const initials = concepts.find((c) => {
      const words = c.concept.match(/[A-Za-z0-9]+/g) ?? [];
      return words.length >= 2 && words.map((w) => w[0]).join("").toUpperCase() === term;
    });
    const field = initials ? `concepts[${initials.concept}].synonyms` : "concepts";
    const value = initials ? term : { concept: term, synonyms: [] };
    const proposal = makeProposal(String(record.session_id), draft, { field, value, why: `Your title and questions use ${term}, but no concept or synonym does.`, evidence: [{ kind: "check", check_id: "CONCEPT_TERM_MISSING" }] });
    rows.push({ check_id: "CONCEPT_TERM_MISSING", step: "criteria", level: "warning", subject: term, params: { term }, evidence: [{ kind: "words", name: "term", value: term }], action: { kind: "proposal", proposal_id: proposal.proposal_id }, __proposal: proposal } as CheckIn);
  }
  if (draft.paradigm && (draft.proof || (draft.extra_inclusions as unknown[] | undefined)?.length)) {
    const c = criteriaOf(draft);
    if (c.undecided.length) rows.push({ check_id: "CRITERIA_UNDECIDED", step: "criteria", level: "blocker", params: { n: c.undecided.length }, refusal: "CRITERIA_UNDECIDED", action: { kind: "field", step: "criteria", field: "criteria_decisions", criterion_id: c.undecided[0] } });
    else for (const side of c.missing_sides) rows.push({ check_id: "CRITERIA_SIDE_MISSING", step: "criteria", level: "blocker", subject: side, params: { side }, refusal: "CRITERIA_MISSING", action: { kind: "field", step: "criteria", field: side === "inclusion" ? "extra_inclusions" : "extra_exclusions" } });
  }
  const project = ["title", "lead_researcher"].filter((f) => empty(draft[f]));
  if (project.length) rows.push({ check_id: "REVIEW_PROJECT_MISSING", step: "review", level: "blocker", params: { fields: project.join(", ") }, action: { kind: "field", step: "review", field: project[0] } });
  const open = listingOf(record).proposals as Json[];
  const waiting = open.filter((p) => p.status === "open");
  if (waiting.length) rows.push({ check_id: "REVIEW_PROPOSALS_OPEN", step: "review", level: "note", params: { n: waiting.length }, action: { kind: "step", step: String(waiting[0].step) } });
  return rows;
}

/** M10b: the import's test double. It keeps the engine's report shape; the mapping rules are the engine's (Python tests). */
function importReport(protocol: Json, label: string, kind: "workspace" | "file", slug?: string): Json {
  const meta = (protocol.metadata ?? {}) as Json;
  const sc = (protocol.screening_criteria ?? {}) as { inclusion?: Json[]; exclusion?: Json[] };
  const draft: Json = {
    topic: "",
    title: meta.title,
    lead_researcher: meta.lead_researcher,
    paradigm: ((protocol.epistemology ?? {}) as Json).primary_paradigm,
    playbook: protocol.playbook_type,
    rqs: ((protocol.research_questions ?? []) as Json[]).map((rq) => rq.text),
    extra_inclusions: (sc.inclusion ?? []).map((c) => c.criterion),
    extra_exclusions: (sc.exclusion ?? []).map((c) => ({ criterion: c.criterion, reason_category: c.reason_category ?? "OUT_OF_SCOPE" })),
  };
  return {
    source: {
      kind, label, read: "protocol", slug, protocol_created_at: "2026-10-12T14:12:24+00:00",
      protocol_fingerprint: "sha256:" + "ef".repeat(32), target_slug: slugify(String(meta.title ?? "")), collides_with_source: false,
    },
    draft,
    carried: [{ field: "rqs", from: "research_questions[].text", class: "exact" }],
    lost: [{ what: "facets", count: (draft.rqs as unknown[]).length }, { what: "rationale" }, { what: "preset" }],
    needs_you: ["topic"],
    earlier_pool: { min: 0, max: 1000 },
  };
}

const PARADIGMS = [
  { name: "Positivist", goal: "Measure objective, generalizable statistical effects." },
  { name: "Interpretivist", goal: "Understand human meaning, perceptions, and identity." },
  { name: "Design Science", goal: "Engineer a novel artifact that solves an operational utility problem." },
  { name: "Pragmatist / Mixed Methods", goal: "Solve a socio-technical problem by triangulating metrics with narratives." },
];
const PLAYBOOKS = [
  { name: "PRISMA_SLR", framework: "PRISMA 2020" },
  { name: "SCOPING_REVIEW", framework: "JBI Scoping Review Framework" },
  { name: "DESIGN_SCIENCE", framework: "Hevner DSR" },
];

function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^\p{L}\p{N}_\s-]/gu, "")
    .trim()
    .replace(/[-\s]+/g, "-");
}

function idOf(kind: string, source: string, text: string, reason: string | null = null): string {
  let h = 0;
  for (const ch of `${kind}|${source}|${text}|${reason ?? ""}`) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `crit_${h.toString(16).padStart(12, "0").slice(0, 12)}`;
}

/** The engine's `method_choice` and `METHOD_OPTIONS` (M11b part D), as a test double. */
function methodOf(draft: Json, option: true | { order?: string[] }) {
  const rule = (draft.method_not_reported ?? null) as string | null;
  return {
    method: {
      blinding: (draft.method_blinding ?? "reveal_after_decision") as string,
      not_reported: rule,
      chosen: rule !== null,
      started_before_question: !("method_not_reported" in draft),
    },
    method_options: {
      blinding: ["reveal_after_decision", "show"],
      not_reported: option === true || !option.order ? ["unclear", "decisive_first", "exclude"] : option.order,
    },
  };
}

function criteriaOf(draft: Json) {
  const decisions = (draft.criteria_decisions ?? {}) as Record<string, boolean>;
  const items: Json[] = [];
  const push = (kind: string, text: string, source: string, generated: boolean, reason: string | null, label: string) => {
    const id = idOf(kind, source, text, kind === "exclusion" ? reason : null);
    const d = decisions[id];
    const status = d === undefined ? (generated || source === "out_of_scope" ? "undecided" : "accepted") : d ? "accepted" : "rejected";
    const extra = kind === "exclusion" ? { reason_valid: /^[A-Z][A-Z0-9_]{2,39}$/.test(reason ?? "") } : {};
    items.push({ id, kind, criterion: text, reason_category: reason, source, source_label: label, generated, status, ...extra });
  };
  const oosReasons = (draft.out_of_scope_reasons ?? {}) as Record<string, string>;
  // H-run-small-fixes (finding 1): the proof writes its criterion only when no typed inclusion is left.
  const typedLeft = ((draft.extra_inclusions ?? []) as string[]).some((c) => c.trim() && decisions[idOf("inclusion", "manual", c)] !== false);
  if (draft.proof && String(draft.proof).trim() && !typedLeft) push("inclusion", `Reports the gold-standard proof — ${String(draft.proof)}`, "proof", true, null, "written by the wizard from your proof answer");
  for (const c of (draft.extra_inclusions ?? []) as string[]) push("inclusion", c, "manual", false, null, "typed by you");
  // H-run-small-fixes (finding 2): one candidate per item; semicolons and line breaks separate items.
  const items_ = [...new Set(((draft.out_of_scope ?? []) as string[]).flatMap((c) => c.split(/[;\n]/)).map((c) => c.trim()).filter(Boolean))];
  for (const c of items_) push("exclusion", c, "out_of_scope", false, oosReasons[c] ?? "OUT_OF_SCOPE", "your out-of-scope answer");
  for (const c of (draft.extra_exclusions ?? []) as { criterion: string; reason_category?: string }[]) push("exclusion", c.criterion, "manual", false, c.reason_category ?? "OUT_OF_SCOPE", "typed by you");
  if (!items.some((i) => i.kind === "exclusion") && draft.paradigm) {
    push("exclusion", "Opinion pieces without data.", "paradigm_default", true, (draft.default_exclusion_reason as string | null) ?? "OUT_OF_SCOPE", "the {paradigm} paradigm's default exclusion, written by the wizard");
  }
  const accepted = new Set(items.filter((i) => i.status === "accepted").map((i) => i.kind));
  const used = [...new Set(items.filter((i) => i.kind === "exclusion").map((i) => String(i.reason_category)))];
  return {
    criteria: items,
    undecided: items.filter((i) => i.status === "undecided").map((i) => i.id),
    missing_sides: ["inclusion", "exclusion"].filter((k) => !accepted.has(k)),
    reason_suggestions: [
      ...used.map((code) => ({ code, source: "used", phrases: code === "NO_EMPIRICAL_EVALUATION" })),
      ...["OUT_OF_SCOPE", "WRONG_POPULATION", "NO_EMPIRICAL_EVALUATION"].filter((c) => !used.includes(c)).map((code) => ({ code, source: "default", phrases: code === "NO_EMPIRICAL_EVALUATION" })),
    ],
  };
}

/** The engine's `proof_required` (M10b): an undropped typed inclusion makes the proof optional. */
export function proofRequired(draft: Json): boolean {
  const decisions = (draft.criteria_decisions ?? {}) as Record<string, boolean>;
  return !((draft.extra_inclusions ?? []) as string[]).some((c) => decisions[idOf("inclusion", "manual", c)] !== false);
}

const refuse = (status: number, code: string, message = code.toLowerCase(), details?: unknown): Answer => ({
  status,
  body: { detail: { code, message, ...(details ? { details } : {}) } },
});

export function inceptionEngine(options: FakeOptions = {}) {
  let clock = 0;
  const now = () => `2026-11-09T10:${String(clock++).padStart(2, "0")}:00+00:00`;
  const drafts = new Map<string, Json>();
  const calls: { method: string; path: string; body: Json | null; search?: string }[] = [];
  const refuseOnce = options.refuseOnce ?? {}; // the caller's object, so a test can add a refusal after the first read
  let existing = options.existing ?? "none";
  let current: string | null = null;
  let nextId = 0;
  const recon = reconEngine(options.recon ?? {}, () => now());
  const workbench = workbenchEngine(options.workbench ?? {});

  const seed = (draft: Json = {}, emitted: Json | null = null, id = SESSION, extra: Json = {}): string => {
    const at = now();
    drafts.set(id, { session_id: id, created_at: at, updated_at: at, draft, emitted, ...extra });
    return id;
  };

  const need = (draft: Json, fields: string[]): Answer | null => {
    const missing = fields.filter((f) => {
      const v = draft[f];
      return v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
    });
    return missing.length ? refuse(422, "DRAFT_INCOMPLETE", `this step needs: ${missing.join(", ")}`, { missing }) : null;
  };

  const previewOf = (draft: Json): Answer => {
    const lacking = need(draft, ["topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher"]);
    if (lacking) return lacking;
    const c = criteriaOf(draft);
    if (c.undecided.length) return refuse(422, "CRITERIA_UNDECIDED", "accept or reject every criterion the wizard wrote", { undecided: c.undecided });
    if (options.method && (draft.method_not_reported ?? null) === null) return refuse(422, "METHOD_RULE_UNCHOSEN", "choose the not-reported rule");
    if (c.missing_sides.length) return refuse(422, "CRITERIA_MISSING", "a protocol needs at least one inclusion and one exclusion criterion", { missing_sides: c.missing_sides });
    const slug = slugify(String(draft.title));
    const exists = existing !== "none";
    return {
      status: 200,
      body: {
        intent: { project_slug: slug },
        protocol: { search_strategy: { target_candidate_pool_size: draft.pool_max != null ? { min: draft.pool_min ?? 0, max: draft.pool_max } : { min: 50, max: 200 } } },
        protocol_fingerprint: "sha256:" + "ab".repeat(32),
        screening_criteria: "# Screening criteria\n",
        criteria: c.criteria.filter((i) => i.status === "accepted"),
        files: ["intent.json", "protocol.json", "SCREENING_CRITERIA.md", "audit/journal.jsonl"],
        written: [],
        target: {
          slug,
          path: `${ROOT}\\${slug}`,
          exists,
          workspace: exists && existing !== "folder",
          screening: exists && existing !== "folder" ? { bound: existing === "bound", decision_events: existing === "bound" ? 4 : 0, decision_files: 0, published: false } : null,
          archive: exists && existing !== "folder" ? ["literature/", "artifacts/"] : [],
        },
      },
    };
  };

  const handle = (method: string, fullPath: string, body: Json | null): Answer => {
    const [path, search = ""] = fullPath.split("?");
    calls.push({ method, path, body, ...(search ? { search } : {}) });
    const once = refuseOnce[`${method} ${path}`];
    if (once) {
      delete refuseOnce[`${method} ${path}`];
      return once;
    }
    // ---- M10b Part C (next-step bar): `GET /drafts/{id}/next-step`, rows 2 to 5 from this fake's draft, simplest reading. ----
    const nextStepPath = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/next-step$/);
    if (nextStepPath && method === "GET") {
      const record = drafts.get(nextStepPath[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      const draft = (record.draft ?? {}) as Json;
      const sid = String(record.session_id);
      const at = new Date().toISOString();
      const answer = (state: string, params: Json, key: string, screen: string): Answer => ({
        status: 200,
        body: {
          shape: "review.next-step-v1", scope: "draft", phase: "inception", round: 1, state, params, waiting: null,
          action: { key, to: { screen, query: { draft: sid } } }, also: [], unknown: [], protocol_fingerprint: null, computed_at: at,
        },
      });
      const emitted = record.emitted as Json | null;
      if (emitted) return answer("DRAFT_CREATED", { title: draft.title ?? emitted.slug, slug: emitted.slug }, "goToDone", "inception.done");
      const blank = (v: unknown) => v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
      if (blank(draft.topic)) return answer("DRAFT_STARTED", { step: "scope" }, "goToStep", "inception.scope");
      const stepOf: Record<string, string> = { topic: "scope", paradigm: "shape", playbook: "shape", unit_of_analysis: "shape", proof: "shape", rqs: "shape", concepts: "criteria", criteria_decisions: "criteria", title: "review", lead_researcher: "review" };
      const order = ["scope", "explore", "direction", "shape", "criteria", "review"];
      const fields = ["paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher"].filter((f) => (f !== "proof" || proofRequired(draft)) && blank(draft[f]));
      if (!fields.length && draft.paradigm && criteriaOf(draft).undecided.length) fields.push("criteria_decisions");
      if (fields.length) {
        const step = fields.map((f) => stepOf[f]).sort((a, b) => order.indexOf(a) - order.indexOf(b))[0];
        return answer("DRAFT_INCOMPLETE", { fields, step }, "goToStep", `inception.${step}`);
      }
      return answer("DRAFT_READY", {}, "goToReview", "inception.review");
    }
    // ---- end of the M10b Part C block ----
    // M10b Part B: checks, dismissals and proposals on the draft record.
    const checksPath = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/checks(?:\/([A-Z_]+)\/(dismiss|restore))?$/);
    if (checksPath && method === "POST") {
      const record = drafts.get(checksPath[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      const step = checksPath[2] ? undefined : ((body?.step as string | undefined) ?? undefined);
      if (step && !(INCEPTION_STEPS as readonly string[]).includes(step)) return refuse(404, "STEP_UNKNOWN", `unknown step '${step}'`, { steps: INCEPTION_STEPS });
      const rowsIn = options.checks === true ? computedChecks(record) : typeof options.checks === "function" ? options.checks(record) : [];
      // The checks that recommend a change record their proposal once (a side write: `updated_at` stays).
      const made = rowsIn.map((r) => (r as unknown as Json).__proposal as Json | undefined).filter(Boolean) as Json[];
      const known = new Set(((record.proposals ?? []) as Json[]).map((p) => p.proposal_id));
      if (!checksPath[2] && !record.emitted && made.some((p) => !known.has(p.proposal_id))) {
        record.proposals = [...((record.proposals ?? []) as Json[]), ...made.filter((p) => !known.has(p.proposal_id))];
      }
      const rows = withDismissals(rowsIn.map((r) => checkRow(r)), (record.check_dismissals ?? []) as Json[]);
      if (checksPath[2]) {
        if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
        const action = checksPath[3] === "dismiss" ? "dismissed" : "restored";
        const { entry, refused } = dismissal(rows, (record.check_dismissals ?? []) as Json[], checksPath[2], action, body, now());
        if (refused) return refused;
        record.check_dismissals = [...((record.check_dismissals ?? []) as Json[]), entry!];
        const again = withDismissals(rowsIn.map((r) => checkRow(r)), record.check_dismissals as Json[]);
        const owner = String(rows.find((r) => r.check_id === checksPath[2])?.step ?? "");
        return { status: 200, body: respond(again, { step: owner, steps: INCEPTION_STEPS, scope: { kind: "draft", id: record.session_id, updated_at: record.updated_at }, at: now(), ready: !again.some((r) => r.level === "blocker" && r.status === "open") }) };
      }
      if (options.checksAnswer) return { status: 200, body: options.checksAnswer(step) };
      return { status: 200, body: respond(rows, { step, steps: INCEPTION_STEPS, scope: { kind: "draft", id: record.session_id, updated_at: record.updated_at }, at: now(), ready: !rows.some((r) => r.level === "blocker" && r.status === "open") }) };
    }
    const proposalsPath = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/proposals(?:\/([^/]+)\/(apply|apply-edited|reject|restore))?$/);
    if (proposalsPath) {
      const record = drafts.get(proposalsPath[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      if (!proposalsPath[2] && method === "GET") {
        const step = new URLSearchParams(search).get("step");
        if (step && !(INCEPTION_STEPS as readonly string[]).includes(step)) return refuse(404, "STEP_UNKNOWN");
        return { status: 200, body: listingOf(record, step) };
      }
      if (proposalsPath[2] && method === "POST") {
        const action = proposalsPath[3];
        const list = (record.proposals ?? []) as Json[];
        const stored = list.find((p) => p.proposal_id === proposalsPath[2]);
        if (!stored) return refuse(404, "PROPOSAL_NOT_FOUND", "no such proposal", { proposal_id: proposalsPath[2] });
        if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
        const draft = (record.draft ?? {}) as Json;
        const seen = viewProposal(stored, draft);
        const answer = action === "apply" || action === "apply-edited";
        if (answer && body?.base_updated_at !== record.updated_at) return refuse(409, "DRAFT_CONFLICT", "the draft changed since it was read");
        if (action === "restore") {
          if (stored.status !== "rejected") return refuse(409, "PROPOSAL_NOT_OPEN", "only a rejected proposal is restored", { status: stored.status });
          Object.assign(stored, { status: "open", decided_at: null, decided_value: null });
        } else {
          if (stored.status !== "open") return refuse(409, "PROPOSAL_NOT_OPEN", "this proposal is decided", { status: stored.status });
          if (seen.status === "stale" && answer) return refuse(409, "PROPOSAL_STALE", "the field changed", { base: (stored.base as Json).shown, current: seen.current });
          if (action === "reject") Object.assign(stored, { status: "rejected", decided_at: now(), reason: body?.reason ?? null });
          else {
            const value = action === "apply" ? stored.value : body?.value;
            const next = applyOp(draft, String((stored.target as Json).field), String(stored.op), value);
            if ("refused" in next) return next.refused as Answer;
            record.draft = next;
            record.updated_at = now();
            Object.assign(stored, { status: action === "apply" ? "applied" : "applied_edited", decided_at: now(), decided_value: value });
          }
        }
        const listing = listingOf(record);
        return { status: 200, body: { session_id: record.session_id, draft: record.draft, updated_at: record.updated_at, proposals: listing.proposals, by_step: listing.by_step } };
      }
    }
    const reconPath = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/recon(.*)$/);
    if (reconPath) {
      const record = drafts.get(reconPath[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      return recon.handle(method, reconPath[2], new URLSearchParams(search), body, record, (next) => drafts.set(reconPath[1], next));
    }
    if (path === "/api/v1/inception/drafts" && method === "GET") {
      const items = [...drafts.values()].map((r) => ({
        session_id: r.session_id,
        readable: true,
        title: (r.draft as Json).title ?? null,
        topic: (r.draft as Json).topic ?? null,
        created_at: r.created_at,
        updated_at: r.updated_at,
        emitted: r.emitted,
        origin_label: ((r.origin as Json | undefined)?.source as Json | undefined)?.label ?? null,
      }));
      return { status: 200, body: { root: ROOT, items } };
    }
    if (path === "/api/v1/inception/drafts/import" && method === "POST") {
      const src = (body?.source ?? {}) as Json;
      let protocol: Json | undefined;
      let label = "";
      if (src.kind === "workspace") {
        const ws = (options.workspaces ?? []).find((w) => w.slug === src.slug);
        if (!ws?.protocol) return refuse(404, "IMPORT_SOURCE_NOT_FOUND", "no protocol.json", { slug: src.slug });
        protocol = ws.protocol;
        label = String(src.slug);
      } else {
        try {
          protocol = JSON.parse(Buffer.from(String(src.content_base64 ?? ""), "base64").toString("utf-8")) as Json;
        } catch {
          return refuse(422, "IMPORT_SOURCE_UNREADABLE", "not JSON", { reason: "not_json" });
        }
        if (!protocol.screening_criteria) return refuse(422, "IMPORT_NOT_A_PROTOCOL", "neither", { missing: ["screening_criteria"] });
        label = String(src.file_name);
      }
      const report = importReport(protocol, label, src.kind === "workspace" ? "workspace" : "file", src.kind === "workspace" ? String(src.slug) : undefined);
      if (body?.dry_run !== false) return { status: 200, body: report };
      if (body.expect_fingerprint !== (report.source as Json).protocol_fingerprint) return refuse(409, "IMPORT_SOURCE_CHANGED", "changed");
      nextId += 1;
      const id = `rec_${String(nextId).padStart(32, "0")}`;
      const checked = { scope: false, direction: false, shape: false, criteria: false, review: false };
      seed(report.draft as Json, null, id, { origin: { kind: "import", source: report.source, imported_at: now(), checked, report: { carried: report.carried, lost: report.lost, needs_you: report.needs_you }, earlier_pool: report.earlier_pool } });
      return { status: 201, body: drafts.get(id) };
    }
    const checkedPath = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/origin\/checked$/);
    if (checkedPath && method === "POST") {
      const record = drafts.get(checkedPath[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      const originRec = record.origin as Json | undefined;
      if (originRec) drafts.set(checkedPath[1], { ...record, origin: { ...originRec, checked: { ...(originRec.checked as Json), [String(body?.step)]: true } } });
      return { status: 200, body: { session_id: checkedPath[1], origin: drafts.get(checkedPath[1])?.origin ?? null } };
    }
    if (path === "/api/v1/workspaces" && method === "GET") {
      const items = (options.workspaces ?? []).map((w) => ({ slug: w.slug, title: w.title, path: `${ROOT}\\${w.slug}`, valid: true, last_event: { at: "2026-11-10T10:00:00+00:00", action: "GENESIS" } }));
      return { status: 200, body: { root: ROOT, items, current: null } };
    }
    if (path === "/api/v1/inception/drafts" && method === "POST") {
      nextId += 1;
      const id = `rec_${String(nextId).padStart(32, "0")}`;
      seed((body?.draft as Json) ?? {}, null, id);
      return { status: 201, body: drafts.get(id) };
    }
    const one = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)$/);
    if (one) {
      const record = drafts.get(one[1]);
      if (!/^rec_[0-9a-f]{32}$/.test(one[1])) return refuse(422, "DRAFT_ID_INVALID");
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      if (method === "GET") return { status: 200, body: record };
      if (method === "PUT") {
        if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
        if (body?.base_updated_at && body.base_updated_at !== record.updated_at) return refuse(409, "DRAFT_CONFLICT", "the draft changed since it was read");
        const seeds = ((body?.draft ?? {}) as Json).golden_seeds as unknown[] | undefined;
        if (seeds && (seeds.length > 25 || seeds.some((d) => !/^10\./.test(String(d))))) return refuse(422, "DRAFT_INVALID", "golden_seeds: at most 25 DOIs", { errors: ["golden_seeds"] });
        // M10b: accepted engine suggestions are recorded decided, judged on the stored draft.
        const accepted = (body?.accepted_from ?? []) as Json[];
        const notRecorded: Json[] = [];
        const proposals = [...((record.proposals ?? []) as Json[])];
        for (const entry of accepted) {
          if (entry.mechanism === "direction" || (options.offered && !options.offered(entry))) {
            notRecorded.push(entry);
            continue;
          }
          const made = makeProposal(one[1], (record.draft ?? {}) as Json, { source: `engine:${String(entry.mechanism)}`, field: String(entry.field), value: entry.value });
          if (!proposals.some((p) => p.proposal_id === made.proposal_id)) proposals.push({ ...made, status: "applied", decided_at: now(), decided_value: entry.value });
        }
        const stored = { ...record, draft: body?.draft ?? {}, updated_at: now(), proposals };
        drafts.set(one[1], stored);
        return { status: 200, body: accepted.length ? { ...stored, not_recorded: notRecorded } : stored };
      }
    }
    const step = path.match(/^\/api\/v1\/inception\/steps\/(\w+)$/);
    if (step && method === "POST") {
      const draft = (body?.draft ?? {}) as Json;
      if (step[1] === "scope") {
        const lacking = need(draft, ["topic"]);
        if (lacking) return lacking;
        return {
          status: 200,
          body: { step: "scope", leanings: [{ paradigm: "Design Science", score: 3 }], recommended_paradigm: "Design Science", paradigms: PARADIGMS, refraction: [], default_concepts: ["weed", "detection"] },
        };
      }
      if (step[1] === "shape") {
        const lacking = need(draft, ["topic", "paradigm"]);
        if (lacking) return lacking;
        return {
          status: 200,
          body: {
            step: "shape",
            recommended_playbook: "DESIGN_SCIENCE",
            playbooks: PLAYBOOKS,
            trustworthiness_framework: "Hevner DSR",
            rq_draft: draft.proof ? `Can a novel ${String(draft.topic)} artifact achieve ${String(draft.proof)} for ${String(draft.unit_of_analysis ?? "its users")}?` : null,
            lexicon: "Use DSR rigor vocabulary.",
            lexicon_warnings: [],
            proof_required: proofRequired(draft),
            pool_preset: { min: 50, max: 200 },
          },
        };
      }
      if (step[1] === "criteria") {
        const lacking = need(draft, proofRequired(draft) ? ["paradigm", "proof"] : ["paradigm"]);
        return lacking ?? { status: 200, body: { step: "criteria", ...criteriaOf(draft), ...(options.method ? methodOf(draft, options.method) : {}) } };
      }
      if (step[1] === "matrix") {
        const lacking = need(draft, ["playbook"]);
        const columns = [{ id: "performance", name: "Performance Metric", description: "Primary accuracy metric" }];
        const own = ((draft.custom_matrix_columns ?? []) as { name: string; description?: string; data_type?: string; required?: boolean }[]).map((c) => ({
          id: c.name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, ""),
          name: c.name,
          description: c.description ?? "",
          data_type: c.data_type ?? "free_text",
          required: !!c.required,
          fallback_value: "Not Reported",
          target_section_category: null,
        }));
        return (
          lacking ?? {
            status: 200,
            body: {
              step: "matrix",
              columns,
              custom_columns: own,
              selected: [...columns.map((c) => c.name).filter((n) => ((draft.matrix_columns ?? []) as string[]).includes(n)), ...own.map((c) => c.name)],
            },
          }
        );
      }
      return refuse(404, "STEP_UNKNOWN");
    }
    if (path === "/api/v1/inception/preview" && method === "POST") {
      const bound = body?.session_id ? drafts.get(String(body.session_id)) : undefined;
      const stale = bound ? recon.staleBinding({ ...bound, draft: body?.draft ?? {} }) : null;
      return stale ?? previewOf((body?.draft ?? {}) as Json);
    }
    const gen = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/genesis$/);
    if (gen && method === "POST") {
      const record = drafts.get(gen[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
      const stale = recon.staleBinding(record);
      if (stale) return stale;
      const compiled = previewOf(record.draft as Json);
      if (compiled.status !== 200) return compiled;
      const slug = slugify(String((record.draft as Json).title));
      const target = `${ROOT}\\${slug}`;
      const typed = body?.confirm_discard_screening_binding as string | undefined;
      if (typed !== undefined && typed !== slug) return refuse(422, "CONFIRMATION_MISMATCH", `type the workspace name '${slug}' to confirm`, { expected: slug });
      if (existing === "folder") return refuse(409, "WORKSPACE_EXISTS", `${target} already exists and is not a workspace`, { path: target });
      if (existing !== "none" && !body?.replace) return refuse(409, "WORKSPACE_EXISTS", `${target} already holds a Nexus Scholar workspace`, { path: target, markers: ["protocol.json"] });
      if (existing === "bound" && typed !== slug) {
        return refuse(409, "SCREENING_BOUND", "screening was done under the current protocol", { path: target, bound: true, decision_events: 4, decision_files: 1, published: false });
      }
      const replaced = existing !== "none";
      const result = {
        slug,
        path: target,
        protocol_fingerprint: "sha256:" + "ab".repeat(32),
        replaced,
        ...(replaced ? { previous_fingerprint: "sha256:" + "cd".repeat(32), backup_dir: `${target}\\audit\\replaced\\20261109T100000Z`, archived: ["literature/", "artifacts/"] } : {}),
      };
      drafts.set(gen[1], { ...record, emitted: { slug, path: target, protocol_fingerprint: result.protocol_fingerprint, replaced } });
      existing = "workspace";
      return { status: 201, body: { session_id: gen[1], ...result } };
    }
    if (path === "/api/v1/workspaces/open" && method === "POST") {
      const slug = String(body?.slug ?? "");
      current = `${ROOT}\\${slug}`;
      return { status: 202, body: { slug, path: current, restarting: options.restarting ?? false } };
    }
    if (path === "/api/v1/workspace/meta") return { status: 200, body: { workspace: current } };
    // M11a: the query workbench of a draft.
    const bench = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/workbench(\/.*)$/);
    if (bench) {
      const record = drafts.get(bench[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
      const seeds = (((record.draft ?? {}) as Json).golden_seeds ?? []) as string[];
      const answer = workbench.handle(method, bench[2], body, seeds);
      if (answer) return answer;
    }
    return refuse(404, "NOT_FOUND", path);
  };

  /** Refuse the next call of `METHOD path` with this answer. */
  const refuseNext = (key: string, answer: Answer) => {
    refuseOnce[key] = answer;
  };

  /** M10b: put a proposal on a draft record as the engine would have made it; answers it. */
  const addProposal = (p: ProposalIn, id = SESSION): Json => {
    const record = drafts.get(id)!;
    const made = makeProposal(id, (record.draft ?? {}) as Json, p);
    record.proposals = [...((record.proposals ?? []) as Json[]), made];
    return made;
  };

  return { handle, calls, drafts, seed, recon, refuseNext, addProposal, workbench };
}

/** A complete draft: every answer preview needs, the generated criterion still undecided. */
export function completeDraft(overrides: Json = {}): Json {
  return {
    topic: "on-device weed detection",
    paradigm: "Design Science",
    playbook: "DESIGN_SCIENCE",
    unit_of_analysis: "embedded cameras",
    proof: "mIoU and FPS on a public benchmark",
    out_of_scope: ["closed-source models"],
    rqs: ["Can on-device weed detection run in real time?"],
    concepts: [{ concept: "weed detection", synonyms: [] }],
    title: "On-Device Weed Detection",
    lead_researcher: "Dr. R",
    ...overrides,
  };
}

/** The id the fake gives the proof criterion of {@link completeDraft}. */
export function proofId(proof = "mIoU and FPS on a public benchmark"): string {
  return idOf("inclusion", "proof", `Reports the gold-standard proof — ${proof}`);
}

/** The id the fake gives an out-of-scope item of {@link completeDraft} (H-run-small-fixes: each waits for Accept). */
export function outOfScopeId(text = "closed-source models", reason = "OUT_OF_SCOPE"): string {
  return idOf("exclusion", "out_of_scope", text, reason);
}

/** Stub `fetch` (vitest) with the fake; returns the engine for assertions. */
export function stubFetch(engine: ReturnType<typeof inceptionEngine>, stub: (fn: (url: string, init?: RequestInit) => Promise<Response>) => void) {
  stub(async (url: string, init?: RequestInit) => {
    const parsed = new URL(url, "http://localhost");
    const path = parsed.pathname.replace("/api/console", "") + parsed.search;
    const method = (init?.method ?? "GET").toUpperCase();
    const body = init?.body ? (JSON.parse(String(init.body)) as Json) : null;
    const answer = engine.handle(method, path, body);
    if (answer.sse) return new Response(String(answer.body), { status: answer.status, headers: { "content-type": "text/event-stream" } });
    return new Response(JSON.stringify(answer.body), { status: answer.status, headers: { "content-type": "application/json" } });
  });
}
