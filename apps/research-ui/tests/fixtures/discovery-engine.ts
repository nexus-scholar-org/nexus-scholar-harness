/**
 * A small stateful fake of the discovery routes (`src/scholar_harness/console/api/discovery.py`,
 * packet `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4) and the corpus routes the
 * hand-off uses, for tests only: the vitest screens stub `fetch` with it and the
 * Playwright spec answers the console proxy with it. It keeps the engine's shapes
 * and refusal codes; the engine's behaviour is pinned by the Python suite
 * (`tests/console/test_discovery_api.py`, `tests/console/test_corpus_import_api.py`).
 *
 * Every number here is the fake's own fixed data, the way the engine would have
 * written it (counts, shares, tiers). The screens must print them, never derive them.
 */

type Json = Record<string, unknown>;
export type Answer = { status: number; body: unknown; sse?: boolean };

export const FINGERPRINT = "sha256:" + "cd".repeat(32);
export const QUERY_TEXT = '("weed detection" OR "weed segmentation") AND ("edge device" OR "embedded")';
export const MAILTO_LINE = "SCHOLAR_MAILTO=you@university.edu";

export interface DiscoveryFakeOptions {
  protocol?: "ok" | "missing" | "invalid";
  /** `SCHOLAR_MAILTO` set for the console (default true). */
  mailto?: boolean;
  /** `SCHOLAR_OPENALEX_KEY` set for the console (default true; M3h-providers). */
  openalexKey?: boolean;
  /** `SCHOLAR_S2_KEY` set for the console (default false; M3h-providers). */
  s2Key?: boolean;
  /** Finished browser runs already in the workspace (default 0). */
  runs?: number;
  /** The corpus is frozen already. */
  accepted?: boolean;
  /** Database exports staged for import (a run answers `STAGED_IMPORT_PENDING`). */
  staged?: boolean;
  /** A run is in progress; its stream has no end yet. */
  activeJob?: boolean;
  /** Fail this database in every run, with this typed code. */
  failedLeg?: { provider: string; code: string; error: string };
  /** Cap this database in every run (`cap_hit`, a lower bound). Default: crossref. */
  cappedLeg?: string | null;
  /** The protocol changed after the newest run (the accept answers `PROTOCOL_CHANGED_SINCE_RUN`). */
  protocolChangedSinceRun?: boolean;
  /** A recall check was run already. */
  recall?: boolean;
  /** Refuse a route once with this answer, keyed `METHOD path`. */
  refuseOnce?: Record<string, Answer>;
  /** The protocol's anchor papers kept in inception (`golden_seeds` on the plan, M4d). */
  goldenSeeds?: string[];
}

const PROVIDERS = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"] as const;
const SELECTED = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"];
const FETCHED: Record<string, { reported: number; fetched: number }> = {
  openalex: { reported: 412, fetched: 412 },
  semanticscholar: { reported: 388, fetched: 388 },
  crossref: { reported: 1840, fetched: 500 },
  arxiv: { reported: 57, fetched: 57 },
  pubmed: { reported: 96, fetched: 96 },
};
const EXECUTED: Record<string, string> = {
  openalex: 'title_and_abstract.search:("weed detection" OR "weed segmentation") AND ("edge device" OR "embedded")',
  semanticscholar: '("weed detection" | "weed segmentation") + ("edge device" | "embedded")',
  crossref: "weed detection weed segmentation edge device embedded",
  arxiv: 'abs:"weed detection" OR abs:"weed segmentation"',
  pubmed: '("weed detection"[tiab] OR "weed segmentation"[tiab]) AND ("edge device"[tiab] OR "embedded"[tiab])',
};

export const refuse = (status: number, code: string, message = code.toLowerCase(), details?: unknown): Answer => ({
  status,
  body: { detail: { code, message, ...(details ? { details } : {}) } },
});

function sse(events: { event: string; data: unknown }[]): string {
  return events.map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join("");
}

export function discoveryEngine(options: DiscoveryFakeOptions = {}) {
  let clock = 0;
  const now = () => `2026-11-10T09:${String(clock++).padStart(2, "0")}:00+00:00`;
  const calls: { method: string; path: string; body: Json | null }[] = [];
  const refuseOnce = { ...(options.refuseOnce ?? {}) };
  const capped = options.cappedLeg === undefined ? "crossref" : options.cappedLeg;
  let protocol = options.protocol ?? "ok";
  let mailto = options.mailto ?? true;
  let openalexKey = options.openalexKey ?? true;
  const s2Key = options.s2Key ?? false;
  let accepted = options.accepted ?? false;
  let staged = options.staged ?? false;
  let protocolChanged = options.protocolChangedSinceRun ?? false;
  const runs: Json[] = [];
  const jobs = new Map<string, { job: Json; events: { event: string; data: unknown }[]; open: boolean }>();
  let recall: Json | null = null;
  let methods: Record<string, Json> = {};
  let nextJob = 0;

  const legsOf = (capOverride: number | null): Json[] =>
    SELECTED.map((provider) => {
      const failed = options.failedLeg?.provider === provider;
      const base = FETCHED[provider];
      const cap = capOverride ?? (provider === capped ? 500 : 10000);
      const hit = !failed && provider === capped;
      const at = now();
      return {
        provider, query_id: "Q1", executed_query: EXECUTED[provider], request: {},
        reported_total: failed ? null : base.reported, fetched: failed ? 0 : hit ? cap : base.fetched, pages: 1,
        cap, cap_source: capOverride ? "run_override" : provider === capped ? "protocol" : "engine_ceiling", cap_hit: hit,
        status: failed ? "failed" : "ok", error: failed ? options.failedLeg!.error : null, error_code: failed ? options.failedLeg!.code : null,
        notes: [], mailto_set: true, started_at: at, finished_at: at,
      };
    });

  const addRun = (capOverride: number | null = null, status = "PENDING_CORPUS_ACCEPT"): Json => {
    const legs = legsOf(capOverride);
    const run = {
      run: `run_${String(runs.length + 1).padStart(3, "0")}`, status, query_id: "Q1", query_text: QUERY_TEXT,
      year_min: 2018, year_max: 2026, raw_published: true, corpus_published: true, cap_override: capOverride, notes: [], legs,
    };
    runs.unshift(run);
    return run;
  };
  for (let i = 0; i < (options.runs ?? 0); i++) addRun();

  const fetchedTotal = (run: Json) => (run.legs as Json[]).reduce((n, l) => n + Number(l.fetched), 0);
  const summaries = () =>
    runs.map((run, index) => ({
      run: run.run, status: run.status, started_at: (run.legs as Json[])[0]?.started_at ?? null,
      finished_at: (run.legs as Json[]).at(-1)?.finished_at ?? null, legs_total: (run.legs as Json[]).length,
      fetched_total: fetchedTotal(run), raw_published: true, cap_override: run.cap_override, stale: index > 0,
    }));
  const activeJob = () => [...jobs.values()].find((j) => j.job.state === "running")?.job ?? null;
  const runsPayload = () => ({ shape: "discovery.runs-v1", runs: summaries(), active_job: activeJob() });

  const dedup = () => {
    const run = runs[0];
    if (!run) return null;
    const input = fetchedTotal(run);
    const tiers = { identifier: 301, exact_title: 74, fuzzy_title: 18 };
    const removed = tiers.identifier + tiers.exact_title + tiers.fuzzy_title;
    return {
      shape: "discovery.dedup-v1", run: run.run, input_records: input, unique_works: input - removed, removed,
      removed_rate: Math.round((removed / input) * 10000) / 10000, tiers,
      method: { title_similarity: 0.97, year_tolerance: 1, first_author: true, source: "default" }, near_twins: null,
    };
  };

  const corpus = () => {
    const d = dedup();
    const fromDiscovery = runs.length > 0;
    return {
      shape: "screening.corpus-v1",
      state: accepted ? "ACCEPTED" : fromDiscovery || staged ? "STAGED" : "EMPTY",
      sources: staged ? [{ id: "src_1", label: "Scopus", file_name: "scopus.ris", format: "ris", records: 120, searched_on: "2026-11-01", query: null, limits: null, rejected: [] }] : [],
      databases: [],
      preview: { identified: 0, duplicates: 0, unique_studies: 0 },
      accepted: accepted ? { artifact_id: "ART-corpus-" + "1".repeat(12), accepted_at: now(), records: d?.input_records ?? 0, studies: d?.unique_works ?? 0, duplicates: d?.removed ?? 0 } : null,
      from_discovery: fromDiscovery && !staged,
      limits: { max_source_bytes: 52428800, label_max_length: 40 },
      staging_refused: accepted
        ? { code: "CORPUS_ALREADY_ACCEPTED", message: "the corpus is already accepted; its sources can no longer change" }
        : fromDiscovery
          ? { code: "VERIFIED_EXISTS", message: "literature/verified.json already exists and holds the corpus of a search run; database exports are imported only before any search run" }
          : null,
    };
  };

  const plan = () => ({
    shape: "discovery.plan-v1", protocol_fingerprint: FINGERPRINT,
    query: { id: "Q1", text: QUERY_TEXT, year_min: 2018, year_max: 2026, language: "en" },
    cap: { value: 500, source: "protocol", ceiling: 10000 }, mailto_set: mailto, openalex_key_set: openalexKey, s2_key_set: s2Key, golden_seeds: options.goldenSeeds ?? [],
    providers: PROVIDERS.map((name) => {
      const selected = SELECTED.includes(name);
      return {
        name, selected, executed_query: selected ? EXECUTED[name] : null, request: selected ? { q: EXECUTED[name] } : null,
        cannot_express: selected ? (name === "arxiv" ? ["language en", "year window 2018-2026"] : ["language en"]) : [],
        notes: [], status: selected ? "translated" : name === "biorxiv" ? "off_by_default" : "not_selected",
      };
    }),
    imports_hint: ["scopus", "wos"],
  });

  const startJob = (kind: "run" | "recall", events: { event: string; data: unknown }[], result: Json | null, open = false, state = "succeeded", error: Json | null = null): Json => {
    const id = `djob_${String(nextJob++).padStart(16, "0")}`;
    const started = now();
    const running = { job_id: id, kind, state: "running", started_at: started, finished_at: null, result: null, error: null };
    const all: { event: string; data: unknown }[] = [{ event: "snapshot", data: { job: running } }, ...events.map((e) => ({ ...e, data: { job_id: id, ...(e.data as Json) } }))];
    let job: Json = running;
    if (!open) {
      job = { ...running, state, finished_at: now(), result, error };
      all.push({ event: state === "succeeded" ? "done" : "failed", data: { job } });
    }
    jobs.set(id, { job, events: all, open });
    return running;
  };

  if (options.activeJob) {
    startJob("run", [{ event: "leg", data: { provider: "openalex", fetched: 25, reported_total: 412, cap: 10000, cap_hit: false, status: "running", error_code: null } }], null, true);
  }

  const handoff = () => {
    const d = dedup();
    const total = d?.unique_works ?? 0;
    return {
      shape: "discovery.handoff-v1", corpus: corpus(), run: runs[0]?.run ?? null,
      provider_mix: [
        { provider: "openalex", records: 402, share: 0.3561 }, { provider: "semanticscholar", records: 371, share: 0.3286 },
        { provider: "crossref", records: 480, share: 0.4252 }, { provider: "pubmed", records: 90, share: 0.0797 }, { provider: "arxiv", records: 55, share: 0.0487 },
      ],
      abstracts: { with_abstract: total - 84, title_only: 84, share_with_abstract: total ? Math.round(((total - 84) / total) * 10000) / 10000 : 0 },
      outside_year_window: 6, near_twins_undecided: null,
      lower_bound_databases: capped && runs.length ? [capped] : [], protocol_fingerprint: FINGERPRINT,
    };
  };

  const report = (name: string | null): Answer => {
    const run = name ? runs.find((r) => r.run === name) : runs[0];
    if (!run) return refuse(404, "RUN_NOT_FOUND", name ? `No search run ${name} in this workspace.` : "No search run yet in this workspace.");
    const legs = run.legs as Json[];
    const newest = run === runs[0];
    const d = dedup();
    const stored = methods[String(run.run)];
    return {
      status: 200,
      body: {
        shape: "discovery.report-v1", run: run.run, status: run.status, cap_override: run.cap_override,
        identification: legs.map((l) => ({
          database: l.provider, kind: "search", executed_query: l.executed_query, reported_total: l.reported_total, fetched: l.fetched,
          completeness: l.status === "failed" ? "failed" : l.status === "stopped" ? "stopped" : l.cap_hit ? "lower_bound" : "full",
          no_abstract_rate: l.status === "failed" ? null : 0.0712, cache: null, error_code: l.error_code, searched_at: l.started_at, notes: l.notes,
        })),
        not_searched: [{ database: "biorxiv", reason: "off by default" }],
        imports: [],
        dedup: newest && d ? { removed: d.removed, by_tier: d.tiers, near_twins: null, unique_works: d.unique_works } : { removed: null, by_tier: null, near_twins: null, unique_works: null },
        outside_year_window: 6,
        prisma: null,
        methods_text: stored
          ? { ...stored, built_from: run.run, earlier_reviewed: null }
          : {
              text: `We searched OpenAlex, Semantic Scholar, Crossref, arXiv and PubMed on 2026-11-10 with the query ${QUERY_TEXT}, limited to 2018–2026. Crossref returned 1840 records, of which the first 500 were retrieved (the protocol's cap).`,
              built_from: run.run, reviewed: false, reviewed_at: null, earlier_reviewed: null,
            },
        runs: runsPayload(),
      },
    };
  };

  function handle(method: string, path: string, body: Json | null): Answer {
    calls.push({ method, path, body });
    const key = `${method} ${path.split("?")[0]}`;
    if (refuseOnce[key]) {
      const answer = refuseOnce[key];
      delete refuseOnce[key];
      return answer;
    }
    const [route, query = ""] = path.split("?");
    const params = new URLSearchParams(query);
    const needProtocol = (): Answer | null =>
      protocol === "missing"
        ? refuse(409, "PROTOCOL_MISSING", "This workspace has no protocol.json; finish inception first.")
        : protocol === "invalid"
          ? refuse(422, "PROTOCOL_INVALID", "protocol.json is not a valid protocol: method.retrieval_cap must be positive")
          : null;
    const mailtoRefusal = refuse(409, "MAILTO_NOT_SET", "A search needs a contact email for the literature databases. Set SCHOLAR_MAILTO for the console (environment or .env) and start it again.");
    const busy = (): Answer | null => {
      const active = activeJob();
      return active ? refuse(409, "DISCOVERY_JOB_ACTIVE", "A discovery job is already running for this workspace.", { job: active }) : null;
    };

    if (method === "GET" && route === "/api/v1/discovery/plan") return needProtocol() ?? { status: 200, body: plan() };
    if (method === "GET" && route === "/api/v1/discovery/runs") return { status: 200, body: runsPayload() };
    const runMatch = /^\/api\/v1\/discovery\/runs\/(run_\d{3,})(\/report)?$/.exec(route);
    if (method === "GET" && runMatch) {
      const run = runs.find((r) => r.run === runMatch[1]);
      if (!run) return refuse(404, "RUN_NOT_FOUND", `No search run ${runMatch[1]} in this workspace.`);
      if (runMatch[2]) return { status: 200, body: `# Search report ${run.run}\n` };
      return { status: 200, body: { ...run, report_path: `literature/search_runs/${run.run}/search_report.md`, recall_check: recall ? { check: "check_001", checked_at: recall.checked_at, found: recall.found, total: recall.total, missed_everywhere: recall.missed_everywhere } : null } };
    }
    if (method === "POST" && route === "/api/v1/discovery/runs") {
      const cap = body?.cap_override as number | undefined;
      const refused =
        needProtocol() ??
        (cap !== undefined && cap !== null && !(cap >= 1 && cap <= 10000) ? refuse(422, "CAP_INVALID", "A run cap must be 1 to 10000 records per database.") : null) ??
        (!mailto ? mailtoRefusal : null) ??
        (!openalexKey && ((body?.providers as string[] | undefined) ?? SELECTED).includes("openalex")
          ? refuse(409, "OPENALEX_KEY_NOT_SET", "OpenAlex needs an API key. Set SCHOLAR_OPENALEX_KEY for the console (environment or .env) and start it again, or leave OpenAlex out of this run.")
          : null) ??
        (accepted ? refuse(409, "CORPUS_ALREADY_ACCEPTED", "The corpus snapshot is accepted; a frozen corpus is never searched again from the browser.") : null) ??
        (staged ? refuse(409, "STAGED_IMPORT_PENDING", "Database exports are staged for import; accept or remove them before a search run.") : null) ??
        busy();
      if (refused) return refused;
      const run = addRun(cap ?? null);
      protocolChanged = false;
      const legs = run.legs as Json[];
      const events = [
        ...legs.flatMap((l) => [
          { event: "leg", data: { provider: l.provider, fetched: 1, reported_total: l.reported_total, cap: l.cap, cap_hit: false, status: "running", error_code: null } },
          { event: "leg", data: { provider: l.provider, fetched: l.fetched, reported_total: l.reported_total, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code } },
        ]),
        // The engine's own stage statuses (`pipeline/coordinator.py`: discovery SUCCESS or PARTIAL, deduplication and hydration DONE, verification the outcome status).
        { event: "stage", data: { stage: "discovery", status: options.failedLeg ? "PARTIAL" : "SUCCESS", detail: { count: fetchedTotal(run) } } },
        { event: "stage", data: { stage: "deduplication", status: "DONE", detail: {} } },
        { event: "stage", data: { stage: "hydration", status: "DONE", detail: null } },
        { event: "stage", data: { stage: "verification", status: "SUCCESS", detail: {} } },
        { event: "stage", data: { stage: "corpus_snapshot", status: "NOT_ACCEPTED", detail: { reason: "awaiting the hand-off accept" } } },
      ];
      const job = startJob("run", events, {
        run: run.run, status: "PENDING_CORPUS_ACCEPT",
        stages: { corpus_snapshot: { status: "NOT_ACCEPTED", reason: "awaiting the hand-off accept" } },
      });
      return { status: 202, body: { job } };
    }
    if (method === "POST" && route === "/api/v1/discovery/recall") {
      const seeds = (body?.seeds ?? []) as { id: string; kind: string; source: string }[];
      const refused =
        needProtocol() ??
        (!seeds.length || seeds.length > 25 ? refuse(422, "SEEDS_INVALID", seeds.length ? `a recall check takes at most 25 seeds, not ${seeds.length}` : "a recall check needs at least one seed") : null) ??
        (seeds.find((s) => !/^10\.\d{4,9}\/\S+$|^\d{4}\.\d{4,5}(v\d+)?$/i.test(s.id))
          ? refuse(422, "SEEDS_INVALID", `seed ${seeds.find((s) => !/^10\.\d{4,9}\/\S+$|^\d{4}\.\d{4,5}(v\d+)?$/i.test(s.id))!.id} is not a well-formed identifier`)
          : null) ??
        (!mailto ? mailtoRefusal : null) ??
        busy();
      if (refused) return refused;
      const rows = seeds.map((s, i) => ({
        ...s, title: `Seed paper ${i + 1}`, title_check: "ok",
        per_provider: Object.fromEntries(SELECTED.map((p) => [p, i === seeds.length - 1 && seeds.length > 1 ? "not_found" : p === "arxiv" && s.kind === "doi" ? "n/a" : "found"])),
      }));
      const missed = rows.filter((r) => !Object.values(r.per_provider).includes("found")).map((r) => r.id);
      recall = { shape: "discovery.recall-v1", protocol_fingerprint: FINGERPRINT, checked_at: now(), query_text: QUERY_TEXT, seeds: rows, found: rows.length - missed.length, total: rows.length, missed_everywhere: missed, legs: legsOf(null) };
      const job = startJob("recall", (recall.legs as Json[]).map((l) => ({ event: "leg", data: { provider: l.provider, fetched: l.fetched, reported_total: l.reported_total, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code } })), { check: "check_001", found: recall.found, total: recall.total });
      return { status: 202, body: { job } };
    }
    if (method === "GET" && route === "/api/v1/discovery/recall") return recall ? { status: 200, body: recall } : refuse(404, "RECALL_NOT_RUN", "No recall check has been run in this workspace.");
    const jobMatch = /^\/api\/v1\/discovery\/jobs\/([A-Za-z0-9_-]+)(\/events|\/cancel)?$/.exec(route);
    if (jobMatch) {
      const entry = jobs.get(jobMatch[1]);
      if (!entry) return refuse(404, "DISCOVERY_JOB_NOT_FOUND", `No discovery job ${jobMatch[1]} in this workspace.`);
      if (method === "GET" && jobMatch[2] === "/events") return { status: 200, body: sse(entry.events), sse: true };
      if (method === "POST" && jobMatch[2] === "/cancel") {
        if (entry.job.state === "running") {
          entry.job = { ...entry.job, state: "cancelled", finished_at: now() };
          entry.events.push({ event: "failed", data: { job: entry.job } });
          entry.open = false;
          if (entry.job.kind === "run") addRun(null, "PARTIAL");
        }
        return { status: 200, body: { job: entry.job } };
      }
      if (method === "GET" && !jobMatch[2]) return { status: 200, body: { job: entry.job } };
    }
    if (method === "GET" && route === "/api/v1/discovery/dedup") return dedup() ? { status: 200, body: dedup() } : refuse(404, "DEDUP_NOT_RUN", "No deduplication has run in this workspace yet.");
    if (method === "GET" && route === "/api/v1/discovery/report") return needProtocol() ?? report(params.get("run"));
    if (method === "PUT" && route === "/api/v1/discovery/report/methods") {
      const run = body?.run ? runs.find((r) => r.run === body.run) : runs[0];
      if (!run) return refuse(404, "RUN_NOT_FOUND", "No search run yet in this workspace.");
      const at = now();
      const saved = { text: String(body?.text ?? "").trim(), built_from: run.run, reviewed: Boolean(body?.reviewed), reviewed_at: body?.reviewed ? at : null };
      methods = { ...methods, [String(run.run)]: saved };
      return { status: 200, body: saved };
    }
    if (method === "GET" && route === "/api/v1/discovery/handoff") return needProtocol() ?? { status: 200, body: handoff() };
    if (method === "GET" && route === "/api/v1/screening/corpus") return { status: 200, body: corpus() };
    if (method === "POST" && route === "/api/v1/screening/corpus/accept") {
      if (accepted) return refuse(409, "CORPUS_ALREADY_ACCEPTED", "the corpus is already accepted");
      if (!runs.length && !staged) return refuse(409, "NOTHING_STAGED", "add at least one database export first");
      if (protocolChanged) return refuse(409, "PROTOCOL_CHANGED_SINCE_RUN", `${runs[0]?.run ?? "the search run"} searched a query or year window the protocol no longer has; run the search again before accepting its corpus`);
      accepted = true;
      return { status: 200, body: corpus() };
    }
    return refuse(404, "NOT_FOUND", `the fake has no ${method} ${route}`);
  }

  return {
    calls,
    handle,
    runs,
    setMailto: (value: boolean) => (mailto = value),
    setOpenalexKey: (value: boolean) => (openalexKey = value),
    setProtocol: (value: "ok" | "missing" | "invalid") => (protocol = value),
    setStaged: (value: boolean) => (staged = value),
    get accepted() {
      return accepted;
    },
  };
}

export type DiscoveryFake = ReturnType<typeof discoveryEngine>;

/** Answer `fetch` from the fake: the console proxy prefix is dropped, SSE answers come back as streams. */
export function stubDiscoveryFetch(engine: DiscoveryFake, install: (fn: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) => void): void {
  install(async (input, init) => {
    const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url, "http://ui.test");
    const path = url.pathname.replace(/^\/api\/console/, "") + url.search;
    const raw = init?.body ? (JSON.parse(String(init.body)) as Json) : null;
    const answer = engine.handle(init?.method ?? "GET", path, raw);
    if (answer.sse) return new Response(String(answer.body), { status: answer.status, headers: { "content-type": "text/event-stream" } });
    if (typeof answer.body === "string") return new Response(answer.body, { status: answer.status, headers: { "content-type": "text/markdown" } });
    return new Response(JSON.stringify(answer.body), { status: answer.status, headers: { "content-type": "application/json" } });
  });
}
