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

export const ROOT = "C:\\Users\\r\\Documents\\Nexus Scholar\\workspaces";
export const SESSION = "rec_0123456789abcdef0123456789abcdef";

type Json = Record<string, unknown>;
export type Answer = { status: number; body: unknown };

export interface FakeOptions {
  /** A workspace already in the target folder; `bound` adds screening decisions. */
  existing?: "none" | "workspace" | "bound" | "folder";
  /** Refuse a route once with this answer, keyed `METHOD path`. */
  refuseOnce?: Record<string, Answer>;
  /** The open route's answer (default: a restart). */
  restarting?: boolean;
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

function idOf(kind: string, source: string, text: string): string {
  let h = 0;
  for (const ch of `${kind}|${source}|${text}`) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `crit_${h.toString(16).padStart(12, "0").slice(0, 12)}`;
}

function criteriaOf(draft: Json) {
  const decisions = (draft.criteria_decisions ?? {}) as Record<string, boolean>;
  const items: Json[] = [];
  const push = (kind: string, text: string, source: string, generated: boolean, reason: string | null, label: string) => {
    const id = idOf(kind, source, text);
    const d = decisions[id];
    const status = d === undefined ? (generated ? "undecided" : "accepted") : d ? "accepted" : "rejected";
    items.push({ id, kind, criterion: text, reason_category: reason, source, source_label: label, generated, status });
  };
  if (draft.proof) push("inclusion", `Reports the gold-standard proof — ${String(draft.proof)}`, "proof", true, null, "written by the wizard from your proof answer");
  for (const c of (draft.extra_inclusions ?? []) as string[]) push("inclusion", c, "manual", false, null, "typed by you");
  for (const c of (draft.out_of_scope ?? []) as string[]) push("exclusion", c, "out_of_scope", false, "OUT_OF_SCOPE", "your out-of-scope answer");
  for (const c of (draft.extra_exclusions ?? []) as { criterion: string; reason_category?: string }[]) push("exclusion", c.criterion, "manual", false, c.reason_category ?? "OUT_OF_SCOPE", "typed by you");
  const accepted = new Set(items.filter((i) => i.status === "accepted").map((i) => i.kind));
  return {
    criteria: items,
    undecided: items.filter((i) => i.status === "undecided").map((i) => i.id),
    missing_sides: ["inclusion", "exclusion"].filter((k) => !accepted.has(k)),
  };
}

const refuse = (status: number, code: string, message = code.toLowerCase(), details?: unknown): Answer => ({
  status,
  body: { detail: { code, message, ...(details ? { details } : {}) } },
});

export function inceptionEngine(options: FakeOptions = {}) {
  let clock = 0;
  const now = () => `2026-11-09T10:${String(clock++).padStart(2, "0")}:00+00:00`;
  const drafts = new Map<string, Json>();
  const calls: { method: string; path: string; body: Json | null }[] = [];
  const refuseOnce = { ...(options.refuseOnce ?? {}) };
  let existing = options.existing ?? "none";
  let current: string | null = null;
  let nextId = 0;

  const seed = (draft: Json = {}, emitted: Json | null = null, id = SESSION): string => {
    const at = now();
    drafts.set(id, { session_id: id, created_at: at, updated_at: at, draft, emitted });
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
    if (c.missing_sides.length) return refuse(422, "CRITERIA_MISSING", "a protocol needs at least one inclusion and one exclusion criterion", { missing_sides: c.missing_sides });
    const slug = slugify(String(draft.title));
    const exists = existing !== "none";
    return {
      status: 200,
      body: {
        intent: { project_slug: slug },
        protocol: {},
        protocol_fingerprint: "sha256:" + "ab".repeat(32),
        screening_criteria: "# Screening criteria\n",
        criteria: c.criteria.filter((i) => i.status === "accepted"),
        files: ["intent.json", "protocol.json", "SCREENING_CRITERIA.md", "audit/journal.jsonl"],
        written: [],
        target: {
          slug,
          path: `${ROOT}\\${slug}`,
          exists,
          screening: exists ? { bound: existing === "bound", decision_events: existing === "bound" ? 4 : 0, decision_files: 0, published: false } : null,
        },
      },
    };
  };

  const handle = (method: string, path: string, body: Json | null): Answer => {
    calls.push({ method, path, body });
    const once = refuseOnce[`${method} ${path}`];
    if (once) {
      delete refuseOnce[`${method} ${path}`];
      return once;
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
      }));
      return { status: 200, body: { root: ROOT, items } };
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
        const stored = { ...record, draft: body?.draft ?? {}, updated_at: now() };
        drafts.set(one[1], stored);
        return { status: 200, body: stored };
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
          body: { step: "shape", recommended_playbook: "DESIGN_SCIENCE", playbooks: PLAYBOOKS, trustworthiness_framework: "Hevner DSR", rq_draft: `Can a novel ${String(draft.topic)} artifact achieve its goal?`, lexicon: "Use DSR rigor vocabulary.", lexicon_warnings: [] },
        };
      }
      if (step[1] === "criteria") {
        const lacking = need(draft, ["paradigm", "proof"]);
        return lacking ?? { status: 200, body: { step: "criteria", ...criteriaOf(draft) } };
      }
      if (step[1] === "matrix") {
        const lacking = need(draft, ["playbook"]);
        const columns = [{ id: "performance", name: "Performance Metric", description: "Primary accuracy metric" }];
        return lacking ?? { status: 200, body: { step: "matrix", columns, selected: columns.map((c) => c.name).filter((n) => ((draft.matrix_columns ?? []) as string[]).includes(n)) } };
      }
      return refuse(404, "STEP_UNKNOWN");
    }
    if (path === "/api/v1/inception/preview" && method === "POST") return previewOf((body?.draft ?? {}) as Json);
    const gen = path.match(/^\/api\/v1\/inception\/drafts\/([^/]+)\/genesis$/);
    if (gen && method === "POST") {
      const record = drafts.get(gen[1]);
      if (!record) return refuse(404, "DRAFT_NOT_FOUND");
      if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
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
        ...(replaced ? { previous_fingerprint: "sha256:" + "cd".repeat(32), backup_dir: `${target}\\audit\\replaced\\20261109T100000Z` } : {}),
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
    return refuse(404, "NOT_FOUND", path);
  };

  return { handle, calls, drafts, seed };
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

/** Stub `fetch` (vitest) with the fake; returns the engine for assertions. */
export function stubFetch(engine: ReturnType<typeof inceptionEngine>, stub: (fn: (url: string, init?: RequestInit) => Promise<Response>) => void) {
  stub(async (url: string, init?: RequestInit) => {
    const parsed = new URL(url, "http://localhost");
    const path = parsed.pathname.replace("/api/console", "");
    const method = (init?.method ?? "GET").toUpperCase();
    const body = init?.body ? (JSON.parse(String(init.body)) as Json) : null;
    const answer = engine.handle(method, path, body);
    return new Response(JSON.stringify(answer.body), { status: answer.status, headers: { "content-type": "application/json" } });
  });
}
