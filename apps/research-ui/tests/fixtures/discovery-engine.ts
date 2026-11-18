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
  /** Review F3: what the hand-off says changed in the protocol since the corpus run, before any click. */
  handoffProtocolChange?: "search" | "other" | null;
  /** A recall check was run already. */
  recall?: boolean;
  /** Refuse a route once with this answer, keyed `METHOD path`. */
  refuseOnce?: Record<string, Answer>;
  /** The protocol's anchor papers kept in inception (`golden_seeds` on the plan, M4d). */
  goldenSeeds?: string[];
  /** M3g: the screening is published and current (the chase's seeds are its includes; default false). */
  published?: boolean;
  /** M3g: finished chase runs already in the workspace (default 0). */
  chaseRuns?: number;
  /** M3g: fail this database and direction in every chase, with this typed code. */
  chaseFailedLeg?: { provider: string; direction: "forward" | "backward"; code: string; error: string };
  /** M3g: the forward OpenAlex leg reaches its cap in every chase (a lower bound). Default false. */
  chaseCapped?: boolean;
  /** M3g: every chase finds nothing new (EMPTY_RESULT). */
  chaseNothingNew?: boolean;
  /** M3g: the published includes carry no identifier (no chaseable seed). */
  chaseNoSeeds?: boolean;
  /** M3g: a chase is in progress; its stream has no end yet. */
  activeChase?: boolean;
  /** M10a: the protocol's own database list, in its order (`protocol_providers`; default the five defaults). */
  protocolProviders?: string[];
  /** M10a: a started run stays running (its stream sends each database's first event and no end). */
  holdRun?: boolean;
  /**
   * M3i: how the steps after the search ended for the newest run already in the workspace, and for
   * every run started (its job then ends `failed` after the search). Default: they ended (`ready`).
   */
  preparation?: "failed" | "stopped" | "interrupted";
  /** M3i: the step it failed in or stopped before (default `verification`); `null` with `legacyRun`. */
  preparationStage?: "deduplication" | "hydration" | "verification";
  /** M3i: the newest run was made before the stage marker existed (`marker: false`, no stage). */
  legacyRun?: boolean;
  /** M3i: the newest run's saved records are gone (`can_finish: false`). */
  recordsMissing?: boolean;
  /** M3i: a started run stays running after its search, in the abstracts step (no end). */
  holdAfterSearch?: boolean;
  /** M3i: a started "finish preparing" job stays running, in the abstracts step (no end). */
  holdPrepare?: boolean;
  /**
   * M10b Part D: the answer of `POST /discovery/estimate`, as a body or built from the request body.
   * Absent: the fake counts `FETCHED`'s reported totals with the engine's arithmetic.
   */
  estimate?: object | ((body: Json | null) => object);
  /** M10b Part D: databases whose count fails (the row is `failed` with this code). */
  estimateFails?: Record<string, string>;
  /** M10b Part D: the planned maximum stated in `intent.json` (default none: the general limit of 1,000). */
  plannedMax?: number;
}

const PROVIDERS = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"] as const;
const SELECTED = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"];
const FETCHED: Record<string, { reported: number; fetched: number }> = {
  openalex: { reported: 412, fetched: 412 },
  semanticscholar: { reported: 388, fetched: 388 },
  crossref: { reported: 1840, fetched: 500 },
  arxiv: { reported: 57, fetched: 57 },
  pubmed: { reported: 96, fetched: 96 },
  biorxiv: { reported: 12, fetched: 12 },
};
const EXECUTED: Record<string, string> = {
  openalex: 'title_and_abstract.search:("weed detection" OR "weed segmentation") AND ("edge device" OR "embedded")',
  semanticscholar: '("weed detection" | "weed segmentation") + ("edge device" | "embedded")',
  crossref: "weed detection weed segmentation edge device embedded",
  arxiv: 'abs:"weed detection" OR abs:"weed segmentation"',
  pubmed: '("weed detection"[tiab] OR "weed segmentation"[tiab]) AND ("edge device"[tiab] OR "embedded"[tiab])',
};
/** bioRxiv has no dry run (the plan says `selected` with a note); its leg still records what it sent. */
const BIORXIV_LEG_QUERY = "weed detection weed segmentation edge device embedded";

/** The engine's `_canonical`: case, spaces and dashes folded, `semantic_scholar` is `semanticscholar`. */
const canonical = (name: string): string => {
  const key = name.toLowerCase().trim().replace(/[- ]/g, "_");
  return key === "semantic_scholar" ? "semanticscholar" : key;
};

/** The engine's `_check_providers`: `null` when absent, else the canonical list or a `PROVIDER_UNKNOWN` answer. */
function checkProviders(names: string[] | null | undefined): { names: string[] | null } | { refused: Answer } {
  if (names === null || names === undefined) return { names: null };
  const unknown = names.filter((n) => !(PROVIDERS as readonly string[]).includes(canonical(n)));
  if (unknown.length || !names.length) {
    return { refused: refuse(422, "PROVIDER_UNKNOWN", "Unknown or empty database list.", { unknown, known: [...PROVIDERS] }) };
  }
  // A name given twice is kept once, at its first place (M10a).
  return { names: [...new Set(names.map(canonical))] };
}

/** `scholar_search.plan.run_providers`: canonical, known only, the first of each repeat; none known is the default suite. */
function runProviders(names: string[]): string[] {
  const known = [...new Set(names.map(canonical).filter((n) => (PROVIDERS as readonly string[]).includes(n)))];
  return known.length ? known : [...SELECTED];
}

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
  // M3g: the citation chase. The screening is published or not; the chase runs, newest first.
  let published = options.published ?? false;
  let round = 1;
  const chases: Json[] = [];
  const SEED = "STU-" + "a".repeat(32);
  const SEED_TITLE = "Edge weed detection on UAV imagery with a quantised network";
  const UNCHASEABLE = { study_id: "STU-" + "b".repeat(32), title: "A record published without a DOI", reason: "no DOI, OpenAlex id or Semantic Scholar id" };
  const chaseLegsOf = (providers: string[], directions: string[], cap: number): Json[] =>
    providers.flatMap((provider) =>
      directions.map((direction) => {
        const failed = options.chaseFailedLeg?.provider === provider && options.chaseFailedLeg.direction === direction;
        const hit = !!options.chaseCapped && provider === "openalex" && direction === "forward";
        const fetched = failed ? 0 : hit ? cap : provider === "openalex" ? (direction === "forward" ? 7 : 31) : direction === "forward" ? 5 : 0;
        const at = now();
        return {
          seed: SEED, provider, direction, fetched, cap: direction === "forward" ? cap : null, cap_hit: hit,
          status: failed ? "failed" : "ok", error: failed ? options.chaseFailedLeg!.error : null, error_code: failed ? options.chaseFailedLeg!.code : null,
          notes: hit ? [`stopped at the cap of ${cap}: the count is a lower bound`] : [], started_at: at, finished_at: at,
        };
      }),
    );
  const legsSummary = (legs: Json[]): Json[] => {
    const rows = new Map<string, Json>();
    for (const leg of legs) {
      const key = `${leg.provider}|${leg.direction}`;
      const row = rows.get(key) ?? { provider: leg.provider, direction: leg.direction, legs: 0, ok: 0, failed: 0, skipped: 0, fetched: 0, cap_hits: 0 };
      row.legs = Number(row.legs) + 1;
      row[String(leg.status)] = Number(row[String(leg.status)] ?? 0) + 1;
      row.fetched = Number(row.fetched) + Number(leg.fetched);
      row.cap_hits = Number(row.cap_hits) + (leg.cap_hit ? 1 : 0);
      rows.set(key, row);
    }
    return [...rows.values()];
  };
  const addChase = (request: Json | null, cancelled = false): Json => {
    const providers = ((request?.providers as string[] | undefined) ?? ["openalex", "semanticscholar"]);
    const directions = ((request?.directions as string[] | undefined) ?? ["forward", "backward"]);
    const cap = (request?.cap_per_seed as number | undefined) ?? 500;
    const ceiling = (request?.ceiling as number | undefined) ?? 5000;
    const legs = chaseLegsOf(providers, directions, cap);
    const raw = legs.reduce((n, l) => n + Number(l.fetched), 0);
    const failed = legs.filter((l) => l.status === "failed").length;
    const nothing = !!options.chaseNothingNew;
    const counts = nothing
      ? { raw, duplicates_within_chase: 0, already_in_corpus: raw, outside_year_window: 0, over_ceiling: 0, new: 0 }
      : { raw, duplicates_within_chase: Math.min(6, raw), already_in_corpus: Math.min(9, Math.max(0, raw - 6)), outside_year_window: Math.min(11, Math.max(0, raw - 15)), over_ceiling: 0, new: Math.max(0, raw - 26) };
    const status = cancelled ? "PARTIAL" : failed === legs.length && legs.length ? "FAILED" : failed ? "PARTIAL" : counts.new === 0 ? "EMPTY_RESULT" : "SUCCESS";
    const reason = cancelled
      ? `cancelled by the researcher: ${raw} record(s) fetched before the stop; not published`
      : status === "FAILED" ? "every database leg failed" : status === "PARTIAL" ? `${failed} of ${legs.length} legs failed`
        : status === "EMPTY_RESULT" ? "nothing new: every chased record is in the corpus, a duplicate or outside the year window" : `${counts.new} new record(s) from 1 seed(s)`;
    const at = now();
    const chase = {
      schema: "nexus.citation-chase.v1", chase: `chase_${String(chases.length + 1).padStart(3, "0")}`, status, reason, started_at: at, finished_at: now(),
      seed_source: (request?.seeds as string | undefined) ?? "included", generation_id: "GEN-" + "7".repeat(12), parent_corpus: { artifact_id: "ART-corpus-" + "1".repeat(12), sha256: "sha256:" + "ab".repeat(32) },
      providers, directions, forward_cap: cap, run_ceiling: ceiling, year_min: 2018, year_max: 2026,
      seeds: [
        { study_id: SEED, title: SEED_TITLE, decision: "INCLUDE", doi: "10.1000/seed", openalex_id: "W1", s2_id: null, chaseable: true, reason: null },
        { ...UNCHASEABLE, decision: "INCLUDE", doi: null, openalex_id: null, s2_id: null, chaseable: false },
      ],
      legs, legs_summary: legsSummary(legs), counts,
      already_in_corpus: counts.already_in_corpus ? [{ record: "doi:10.1000/known", title: "A work already in your corpus", study_id: "STU-" + "c".repeat(32) }] : [],
      published: status !== "FAILED" && !cancelled, cancelled, notes: request?.note ? [String(request.note)] : cancelled ? ["cancelled by the researcher"] : [], accepted: null,
    };
    chases.unshift(chase);
    return chase;
  };
  for (let i = 0; i < (options.chaseRuns ?? 0); i++) addChase(null);
  const chaseSummaries = () =>
    chases.map((c) => ({
      chase: c.chase, status: c.status, reason: c.reason, started_at: c.started_at, finished_at: c.finished_at, seeds: (c.seeds as Json[]).length,
      chaseable_seeds: (c.seeds as Json[]).filter((x) => x.chaseable).length, providers: c.providers, directions: c.directions, counts: c.counts, published: c.published, accepted: c.accepted,
    }));
  const chaseState = () => ({
    shape: "discovery.chase-v1",
    screening: { published, generation_id: published ? "GEN-" + "7".repeat(12) : null, round, arm: round > 1 ? "citation_searching" : "databases" },
    seeds: !published
      ? { source: "included", total: 0, chaseable: 0, not_chaseable: [] }
      : options.chaseNoSeeds
        ? { source: "included", total: 1, chaseable: 0, not_chaseable: [UNCHASEABLE] }
        : { source: "included", total: 2, chaseable: 1, not_chaseable: [UNCHASEABLE] },
    keys: { openalex_key_set: openalexKey, s2_key_set: s2Key },
    defaults: { directions: ["forward", "backward"], providers: ["openalex", "semanticscholar"], forward_cap: 500, run_ceiling: 5000 },
    runs: chaseSummaries(), latest: chases[0] ?? null, active_job: activeJob(),
  });

  // M10a: `protocol_providers`, the list a run sent no `providers` searches; an edit of the protocol
  // (`setProtocolProviders`) changes it and the protocol's fingerprint, as the engine would.
  let protocolProviders = runProviders(options.protocolProviders ?? SELECTED);
  let fingerprint = FINGERPRINT;
  // M10a: the legs run and are listed in the order asked, else in the protocol's order.
  const legsOf = (capOverride: number | null, requested: string[] | null = null): Json[] =>
    (requested ?? protocolProviders).map((provider) => {
      const failed = options.failedLeg?.provider === provider;
      const base = FETCHED[provider];
      const cap = capOverride ?? (provider === capped ? 500 : 10000);
      const hit = !failed && provider === capped;
      const at = now();
      return {
        provider, query_id: "Q1", executed_query: EXECUTED[provider] ?? BIORXIV_LEG_QUERY, request: {},
        reported_total: failed ? null : base.reported, fetched: failed ? 0 : hit ? cap : base.fetched, pages: 1,
        cap, cap_source: capOverride ? "run_override" : provider === capped ? "protocol" : "engine_ceiling", cap_hit: hit,
        status: failed ? "failed" : "ok", error: failed ? options.failedLeg!.error : null, error_code: failed ? options.failedLeg!.code : null,
        notes: [], mailto_set: true, started_at: at, finished_at: at,
      };
    });

  const addRun = (capOverride: number | null = null, status = "PENDING_CORPUS_ACCEPT", requested: string[] | null = null): Json => {
    const legs = legsOf(capOverride, requested);
    const run = {
      run: `run_${String(runs.length + 1).padStart(3, "0")}`, status, query_id: "Q1", query_text: QUERY_TEXT,
      year_min: 2018, year_max: 2026, raw_published: true, corpus_published: true, cap_override: capOverride, notes: [],
      // M10a: the databases asked for, in order; null when the protocol's list was used.
      requested_providers: requested, legs,
    };
    runs.unshift(run);
    return run;
  };
  for (let i = 0; i < (options.runs ?? 0); i++) addRun();

  const fetchedTotal = (run: Json) => (run.legs as Json[]).reduce((n, l) => n + Number(l.fetched), 0);
  const activeJob = () => [...jobs.values()].find((j) => j.job.state === "running")?.job ?? null;

  // M3i: the steps after the search, per run, as the engine reads them from the run's stage marker
  // (`literature/search_runs/run_NNN/pipeline.json`). A run not listed here ended them (`ready`).
  type Prep = { state: "failed" | "stopped" | "interrupted" | "none"; stage: string | null; message: string | null; marker: boolean };
  const prep = new Map<string, Prep>();
  /** The engine's corpus run: the newest run whose search was kept as the corpus (a stopped search is not). */
  const corpusRun = (): Json | undefined => runs.find((r) => prep.get(String(r.run))?.state !== "none");
  const STAGES = ["deduplication", "hydration", "verification"];
  const stageAt = "2026-11-10T09:30:00+00:00";
  const unfinishedPrep = (): Prep => ({
    state: options.preparation ?? "failed",
    stage: options.legacyRun ? null : (options.preparationStage ?? "verification"),
    message: (options.preparation ?? "failed") === "failed" ? "RuntimeError: verifier down" : null,
    marker: !options.legacyRun,
  });
  const stagesDone = (stage: string | null, all = false): Json =>
    Object.fromEntries(
      STAGES.slice(0, all ? STAGES.length : stage ? STAGES.indexOf(stage) : 0).map((name) => [name, { status: name === "verification" ? "SUCCESS" : "DONE", at: stageAt }]),
    );
  /** The run's `preparation`, as `GET /discovery/runs`, `/runs/{run}` and `/handoff` carry it. */
  const preparationOf = (run: Json): Json => {
    const view = (state: string, stage: string | null, extra: Json = {}): Json => ({
      state, stage, stages: stagesDone(stage, state === "ready" || state === "superseded"), ended_at: state === "running" ? null : stageAt,
      message: null, marker: true, can_finish: false, cannot_finish: null, job_id: null, ...extra,
    });
    const stored = prep.get(String(run.run));
    // A search that was stopped is not the corpus: it has nothing to prepare, and it supersedes nothing.
    if (stored?.state === "none") return view("none", null, { stages: {}, marker: false });
    if (run !== corpusRun()) return view("superseded", null);
    const active = activeJob();
    if (active && (active.kind === "prepare" || (active.kind === "run" && active.preparing_run === run.run))) {
      return view("running", "hydration", { job_id: active.job_id });
    }
    if (!stored) return view("ready", null);
    const reason = accepted ? "corpus_accepted" : options.recordsMissing ? "records_missing" : null;
    return view(stored.state, stored.stage, {
      message: stored.message, marker: stored.marker, stages: stored.marker ? stagesDone(stored.stage) : {},
      can_finish: reason === null, cannot_finish: reason,
    });
  };
  /** The corpus run's steps after the search have not ended: its works are not a corpus yet. */
  const pending = (): Json | null => {
    const run = corpusRun();
    if (!run) return null;
    const view = preparationOf(run);
    return view.state === "ready" ? null : view;
  };
  if (runs.length && (options.preparation || options.legacyRun)) prep.set(String(runs[0].run), unfinishedPrep());

  const summaries = () =>
    runs.map((run, index) => ({
      run: run.run, status: run.status, started_at: (run.legs as Json[])[0]?.started_at ?? null,
      finished_at: (run.legs as Json[]).at(-1)?.finished_at ?? null, legs_total: (run.legs as Json[]).length,
      fetched_total: fetchedTotal(run), raw_published: true, cap_override: run.cap_override,
      requested_providers: run.requested_providers ?? null, stale: index > 0, preparation: preparationOf(run),
    }));
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
    // M3i: while the newest run's steps after the search have not ended, no discovery corpus is waiting.
    const fromDiscovery = !!corpusRun() && (accepted || !pending());
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

  // M10a: `?providers=` lists the chosen databases first, in order, as the selected rows; the others follow in the known order.
  const plan = (requested: string[] | null = null) => {
    const chosen = requested ? [...new Set(requested)] : protocolProviders;
    const names = requested ? [...chosen, ...PROVIDERS.filter((n) => !chosen.includes(n))] : [...PROVIDERS];
    return {
      shape: "discovery.plan-v1", protocol_fingerprint: fingerprint,
      query: { id: "Q1", text: QUERY_TEXT, year_min: 2018, year_max: 2026, language: "en" },
      cap: { value: 500, source: "protocol", ceiling: 10000 }, mailto_set: mailto, openalex_key_set: openalexKey, s2_key_set: s2Key, golden_seeds: options.goldenSeeds ?? [],
      providers: names.map((name) => {
        const selected = chosen.includes(name);
        const translated = selected && name in EXECUTED;
        return {
          name, selected, executed_query: translated ? EXECUTED[name] : null, request: translated ? { q: EXECUTED[name] } : null,
          cannot_express: translated ? (name === "arxiv" ? ["language en", "year window 2018-2026"] : ["language en"]) : [],
          notes: selected && !translated ? [`${name} has no dry-run translation`] : [],
          status: translated ? "translated" : selected ? "selected" : name === "biorxiv" ? "off_by_default" : "not_selected",
        };
      }),
      protocol_providers: [...protocolProviders],
      requested_providers: requested,
      imports_hint: ["scopus", "wos"],
    };
  };

  const startJob = (kind: "run" | "recall" | "chase" | "prepare", events: { event: string; data: unknown }[], result: Json | null, open = false, state = "succeeded", error: Json | null = null): Json => {
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

  if (options.activeChase) {
    startJob("chase", [{ event: "leg", data: { seed: SEED, provider: "openalex", direction: "forward", fetched: 7, cap: 500, cap_hit: false, status: "ok", error_code: null, notes: [] } }], null, true);
  }
  if (options.activeJob) {
    startJob("run", [{ event: "leg", data: { provider: "openalex", fetched: 25, reported_total: 412, cap: 10000, cap_hit: false, status: "running", error_code: null } }], null, true);
  }

  const handoff = () => {
    const d = dedup();
    // M3i: an unfinished preparation counts none of verified.json's rows (unless exports are staged or the corpus is frozen).
    const unfinished = !!pending() && !accepted && !staged;
    const total = unfinished ? 0 : (d?.unique_works ?? 0);
    return {
      shape: "discovery.handoff-v1", corpus: corpus(), run: corpusRun()?.run ?? null,
      preparation: corpusRun() ? preparationOf(corpusRun()!) : null,
      provider_mix: unfinished ? [] : [
        { provider: "openalex", records: 402, share: 0.3561 }, { provider: "semanticscholar", records: 371, share: 0.3286 },
        { provider: "crossref", records: 480, share: 0.4252 }, { provider: "pubmed", records: 90, share: 0.0797 }, { provider: "arxiv", records: 55, share: 0.0487 },
      ],
      abstracts: unfinished
        ? { with_abstract: 0, title_only: 0, share_with_abstract: 0 }
        : { with_abstract: total - 84, title_only: 84, share_with_abstract: total ? Math.round(((total - 84) / total) * 10000) / 10000 : 0 },
      outside_year_window: 6, near_twins_undecided: null,
      lower_bound_databases: capped && runs.length ? [capped] : [], protocol_fingerprint: FINGERPRINT,
      run_protocol_fingerprint: runs.length ? FINGERPRINT : null,
      protocol_changed: runs.length ? !!options.handoffProtocolChange : null,
      search_changed: runs.length ? options.handoffProtocolChange === "search" : null,
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
        // M10a: a protocol database the run's requested_providers left out is "not_selected_for_run".
        not_searched: PROVIDERS.filter((name) => !legs.some((l) => l.provider === name)).map((name) => {
          const requested = run.requested_providers as string[] | null | undefined;
          const leftOut = Array.isArray(requested) && protocolProviders.includes(name) && !requested.includes(name);
          return { database: name, reason: leftOut ? "not_selected_for_run" : name === "biorxiv" ? "off by default" : "not selected in the protocol" };
        }),
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

  /** M10b Part D: the engine's estimate arithmetic (`scholar_search.estimate.summarize`) over `FETCHED`'s totals. */
  const estimateOf = (names: string[], whatIf: number | null, pace: number): Json => {
    const cap = whatIf ?? 500;
    const limit = options.plannedMax ?? 1000;
    const fails = options.estimateFails ?? {};
    const rows: Json[] = names.map((name) => {
      if (name === "biorxiv") return { name, status: "not_countable", reported_total: null, fetch_estimate: null, fetch_is_upper_bound: false, cap_binds: null, not_fetched: null, error: null, error_code: null, notes: [] };
      if (fails[name]) return { name, status: "failed", reported_total: null, fetch_estimate: null, fetch_is_upper_bound: false, cap_binds: null, not_fetched: null, error: `[${name}] the count failed`, error_code: fails[name], notes: [] };
      const total = FETCHED[name].reported;
      return { name, status: "counted", reported_total: total, fetch_estimate: Math.min(total, cap), fetch_is_upper_bound: name === "arxiv", cap_binds: total > cap, not_fetched: total - Math.min(total, cap), error: null, error_code: null, notes: [] };
    });
    for (const name of PROVIDERS) {
      if (!names.includes(name)) rows.push({ name, status: name === "biorxiv" ? "off_by_default" : "not_selected", reported_total: null, fetch_estimate: null, fetch_is_upper_bound: false, cap_binds: null, not_fetched: null, error: null, error_code: null, notes: [] });
    }
    const counted = rows.filter((r) => r.fetch_estimate !== null) as { fetch_estimate: number; fetch_is_upper_bound: boolean; reported_total: number }[];
    const all = rows.every((r) => r.status === "counted" || r.status === "not_selected" || r.status === "off_by_default");
    const exact = counted.filter((r) => !r.fetch_is_upper_bound).map((r) => r.fetch_estimate);
    const sum = (list: number[]) => list.reduce((a, b) => a + b, 0);
    const low = Math.max(0, ...exact);
    const high = all ? sum(counted.map((r) => r.fetch_estimate)) : null;
    const level = low > limit ? "warning" : high === null || high > limit ? "note" : "none";
    const totals = counted.map((r) => r.reported_total);
    let best = 0;
    for (let c = 0; c <= cap; c++) if (sum(totals.map((t) => Math.min(t, c))) <= limit) best = c;
    const recommendation =
      level === "none"
        ? { kind: null, cap: null, expected_works: null, cuts: null }
        : all && best >= 100
          ? {
              kind: "cap", cap: best, cuts: totals.filter((t) => t > best).length,
              expected_works: { low: Math.max(0, ...counted.filter((r) => !r.fetch_is_upper_bound).map((r) => Math.min(r.reported_total, best))), high: sum(totals.map((t) => Math.min(t, best))) },
            }
          : { kind: "narrow", cap: null, expected_works: null, cuts: null };
    const hours = (works: number | null) => (works === null ? null : Math.round((works * pace) / 360) / 10);
    return {
      shape: "discovery.estimate-v1", protocol_fingerprint: fingerprint, counted_at: now(), served_from_cache: false, recall_check: null,
      cap: { value: cap, source: whatIf === null ? "protocol" : "run_override", ceiling: 10000 },
      providers: rows,
      estimate: { counted_all: all, records: { low: sum(exact), high }, works: { low, high }, assumption: "low: every record of a smaller database is a duplicate of the largest; high: no duplicate" },
      effort: { pace_seconds: pace, hours: { low: hours(low), high: hours(high) } },
      warn: { level, threshold_works: limit, limit: { value: limit, source: options.plannedMax ? "planned" : "general" } },
      recommendation,
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

    if (method === "GET" && route === "/api/v1/discovery/plan") {
      const refused = needProtocol();
      if (refused) return refused;
      const raw = params.get("providers");
      const checked = checkProviders(raw === null ? null : raw.split(",").map((s) => s.trim()));
      if ("refused" in checked) return checked.refused;
      return { status: 200, body: plan(checked.names) };
    }
    if (method === "GET" && route === "/api/v1/discovery/runs") return { status: 200, body: runsPayload() };
    const runMatch = /^\/api\/v1\/discovery\/runs\/(run_\d{3,})(\/report)?$/.exec(route);
    if (method === "GET" && runMatch) {
      const run = runs.find((r) => r.run === runMatch[1]);
      if (!run) return refuse(404, "RUN_NOT_FOUND", `No search run ${runMatch[1]} in this workspace.`);
      if (runMatch[2]) return { status: 200, body: `# Search report ${run.run}\n` };
      return { status: 200, body: { ...run, preparation: preparationOf(run), report_path: `literature/search_runs/${run.run}/search_report.md`, recall_check: recall ? { check: "check_001", checked_at: recall.checked_at, found: recall.found, total: recall.total, missed_everywhere: recall.missed_everywhere } : null } };
    }
    if (method === "POST" && route === "/api/v1/discovery/runs") {
      const cap = body?.cap_override as number | undefined;
      const checked = checkProviders(body?.providers as string[] | null | undefined);
      const requested = "names" in checked ? checked.names : null;
      const refused =
        needProtocol() ??
        (cap !== undefined && cap !== null && !(cap >= 1 && cap <= 10000) ? refuse(422, "CAP_INVALID", "A run cap must be 1 to 10000 records per database.") : null) ??
        ("refused" in checked ? checked.refused : null) ??
        (!mailto ? mailtoRefusal : null) ??
        (!openalexKey && (requested ?? protocolProviders).includes("openalex")
          ? refuse(409, "OPENALEX_KEY_NOT_SET", "OpenAlex needs an API key. Set SCHOLAR_OPENALEX_KEY for the console (environment or .env) and start it again, or leave OpenAlex out of this run.")
          : null) ??
        (accepted ? refuse(409, "CORPUS_ALREADY_ACCEPTED", "The corpus snapshot is accepted; a frozen corpus is never searched again from the browser.") : null) ??
        (staged ? refuse(409, "STAGED_IMPORT_PENDING", "Database exports are staged for import; accept or remove them before a search run.") : null) ??
        busy();
      if (refused) return refused;
      if (options.holdRun) {
        // The run is still fetching: each database's first event, no stage and no end.
        const held = legsOf(cap ?? null, requested).map((l) => ({ event: "leg", data: { provider: l.provider, fetched: 1, reported_total: l.reported_total, cap: l.cap, cap_hit: false, status: "running", error_code: null } }));
        return { status: 202, body: { job: startJob("run", held, null, true) } };
      }
      const run = addRun(cap ?? null, "PENDING_CORPUS_ACCEPT", requested);
      protocolChanged = false;
      const legs = run.legs as Json[];
      const searched = [
        ...legs.flatMap((l) => [
          { event: "leg", data: { provider: l.provider, fetched: 1, reported_total: l.reported_total, cap: l.cap, cap_hit: false, status: "running", error_code: null } },
          { event: "leg", data: { provider: l.provider, fetched: l.fetched, reported_total: l.reported_total, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code } },
        ]),
        { event: "stage", data: { stage: "discovery", status: options.failedLeg ? "PARTIAL" : "SUCCESS", detail: { count: fetchedTotal(run) } } },
      ];
      if (options.holdAfterSearch) {
        // M3i: the search ended and was published; the job is now adding abstracts and has no end yet.
        const held = startJob("run", [...searched, { event: "stage", data: { stage: "deduplication", status: "DONE", detail: {} } }], null, true);
        const entry = jobs.get(String(held.job_id))!;
        entry.job = { ...entry.job, preparing_run: run.run };
        return { status: 202, body: { job: held } };
      }
      if (options.preparation === "failed") {
        // M3i: a step after the search raised: the job fails, the run keeps its records and its marker says where.
        const failure = unfinishedPrep();
        prep.set(String(run.run), failure);
        const done = STAGES.slice(0, STAGES.indexOf(failure.stage ?? "deduplication")).map((stage) => ({ event: "stage", data: { stage, status: "DONE", detail: null } }));
        const job = startJob("run", [...searched, ...done], null, false, "failed", { code: "DISCOVERY_FAILED", message: String(failure.message) });
        return { status: 202, body: { job } };
      }
      const events = [
        ...searched,
        // The engine's own stage statuses (`pipeline/coordinator.py`: discovery SUCCESS or PARTIAL, deduplication and hydration DONE, verification the outcome status).
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
    // M3i: finish the steps after a search from the run's saved records; nothing is searched again.
    const prepareMatch = /^\/api\/v1\/discovery\/runs\/(run_\d{3,})\/prepare$/.exec(route);
    if (method === "POST" && prepareMatch) {
      const run = runs.find((r) => r.run === prepareMatch[1]);
      if (!run) return refuse(404, "RUN_NOT_FOUND", `No search run ${prepareMatch[1]} in this workspace.`);
      const stored = prep.get(String(run.run));
      const unavailable = (reason: string, message: string) => refuse(409, "PREPARATION_NOT_AVAILABLE", message, { run: run.run, reason });
      const refused =
        needProtocol() ??
        (accepted ? refuse(409, "CORPUS_ALREADY_ACCEPTED", "The corpus snapshot is accepted; a frozen corpus is never prepared again from the browser.") : null) ??
        (staged ? refuse(409, "STAGED_IMPORT_PENDING", "Database exports are staged for import; accept or remove them before finishing a harvest.") : null) ??
        busy() ??
        (stored?.state === "none" ? unavailable("not_published", `The search of ${run.run} was stopped or failed, so it was not kept as the corpus; search again.`) : null) ??
        (run !== corpusRun() ? unavailable("superseded", `A later search run is the corpus now; ${run.run} is kept as a record only.`) : null) ??
        (!stored ? unavailable("already_prepared", `The corpus of ${run.run} is already prepared.`) : null) ??
        (options.recordsMissing ? unavailable("records_missing", `The saved records of ${run.run} (raw.json) cannot be read; search again.`) : null) ??
        (!mailto ? mailtoRefusal : null);
      if (refused) return refused;
      const from = stored!.stage && stored!.stage !== "deduplication" ? "hydration" : "deduplication";
      if (options.holdPrepare) {
        return { status: 202, body: { job: startJob("prepare", from === "deduplication" ? [{ event: "stage", data: { stage: "deduplication", status: "DONE", detail: {} } }] : [], null, true) } };
      }
      prep.delete(String(run.run));
      const events = [
        ...(from === "deduplication" ? [{ event: "stage", data: { stage: "deduplication", status: "DONE", detail: {} } }] : []),
        { event: "stage", data: { stage: "hydration", status: "DONE", detail: null } },
        { event: "stage", data: { stage: "verification", status: "SUCCESS", detail: {} } },
        { event: "stage", data: { stage: "corpus_snapshot", status: "NOT_ACCEPTED", detail: { reason: "awaiting the hand-off accept" } } },
      ];
      const job = startJob("prepare", events, {
        run: run.run, status: "PENDING_CORPUS_ACCEPT", resumed_from: from,
        stages: { corpus_snapshot: { status: "NOT_ACCEPTED", reason: "awaiting the hand-off accept" } },
      });
      return { status: 202, body: { job } };
    }
    if (method === "POST" && route === "/api/v1/discovery/estimate") {
      const cap = body?.cap as number | undefined;
      const pace = body?.pace_seconds as number | undefined;
      const checked = checkProviders(body?.providers as string[] | null | undefined);
      const requested = "names" in checked ? checked.names : null;
      const refused =
        needProtocol() ??
        (cap !== undefined && cap !== null && !(cap >= 1 && cap <= 10000) ? refuse(422, "CAP_INVALID", "A cap must be 1 to 10000 records per database.") : null) ??
        (pace !== undefined && pace !== null && !(Number.isInteger(pace) && pace >= 5 && pace <= 600) ? refuse(422, "PACE_INVALID", "The pace must be a whole number of seconds from 5 to 600.") : null) ??
        ("refused" in checked ? checked.refused : null) ??
        (!mailto ? mailtoRefusal : null) ??
        (!openalexKey && (requested ?? protocolProviders).includes("openalex")
          ? refuse(409, "OPENALEX_KEY_NOT_SET", "OpenAlex needs an API key. Set SCHOLAR_OPENALEX_KEY for the console (environment or .env) and start it again, or leave OpenAlex out of this run.")
          : null) ??
        (accepted ? refuse(409, "CORPUS_ALREADY_ACCEPTED", "The corpus snapshot is accepted; a frozen corpus is never searched again from the browser.") : null) ??
        busy();
      if (refused) return refused;
      const stub = options.estimate;
      if (stub) return { status: 200, body: typeof stub === "function" ? (stub as (b: Json | null) => object)(body) : stub };
      return { status: 200, body: estimateOf(requested ?? protocolProviders, cap ?? null, pace ?? 30) };
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
        per_provider: Object.fromEntries(protocolProviders.map((p) => [p, i === seeds.length - 1 && seeds.length > 1 ? "not_found" : p === "arxiv" && s.kind === "doi" ? "n/a" : "found"])),
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
          // M3i: a stop after the search is read before the next step: the step that is running
          // (abstracts) ends, the job ends cancelled, and the run's marker says it stopped before verification.
          const preparing = entry.job.kind === "prepare" || (entry.job.kind === "run" && !!entry.job.preparing_run);
          const run = preparing ? (entry.job.kind === "prepare" ? corpusRun() : runs.find((r) => r.run === entry.job.preparing_run)) : null;
          if (run) {
            entry.events.push({ event: "stage", data: { job_id: entry.job.job_id, stage: "hydration", status: "DONE", detail: null } });
            prep.set(String(run.run), { state: "stopped", stage: "verification", message: null, marker: true });
          }
          entry.job = { ...entry.job, state: "cancelled", finished_at: now(), ...(run ? { result: { run: run.run, status: "CANCELLED" } } : {}) };
          entry.events.push({ event: "failed", data: { job: entry.job } });
          entry.open = false;
          if (entry.job.kind === "run" && !run) prep.set(String(addRun(null, "PARTIAL").run), { state: "none", stage: null, message: null, marker: false });
          if (entry.job.kind === "chase") addChase(null, true);
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
      // M3i: an unfinished preparation is named before "nothing staged", and only when no export is staged.
      const waiting = staged ? null : pending();
      if (waiting) {
        const state = waiting.state === "running" ? "interrupted" : waiting.state;
        const run = corpusRun()!.run;
        return refuse(409, "PREPARATION_UNFINISHED", `the corpus of ${run} is not prepared yet (${state}${waiting.stage ? ` at ${waiting.stage}` : ""}); finish preparing it on the Harvest screen, or search again`, { run, state, stage: waiting.stage });
      }
      if (!corpusRun() && !staged) return refuse(409, "NOTHING_STAGED", "add at least one database export first");
      if (protocolChanged) return refuse(409, "PROTOCOL_CHANGED_SINCE_RUN", `${runs[0]?.run ?? "the search run"} searched a query or year window the protocol no longer has; run the search again before accepting its corpus`);
      accepted = true;
      return { status: 200, body: corpus() };
    }
    // M3g: citation chasing.
    if (method === "GET" && route === "/api/v1/discovery/chase") return { status: 200, body: chaseState() };
    const chaseMatch = /^\/api\/v1\/discovery\/chase\/runs\/(chase_\d{3,})$/.exec(route);
    if (method === "GET" && chaseMatch) {
      const chase = chases.find((c) => c.chase === chaseMatch[1]);
      return chase ? { status: 200, body: chase } : refuse(404, "CHASE_NOT_RUN", `no chase run '${chaseMatch[1]}' in this workspace`);
    }
    if (method === "POST" && route === "/api/v1/discovery/chase/runs") {
      const directions = body?.directions as string[] | undefined;
      const providers = (body?.providers as string[] | undefined) ?? ["openalex", "semanticscholar"];
      const refused =
        needProtocol() ??
        (!published ? refuse(409, "SCREENING_NOT_PUBLISHED", "literature/included.json is missing: publish the screening before chasing citations") : null) ??
        (providers.some((p) => !PROVIDERS.includes(p as (typeof PROVIDERS)[number])) ? refuse(422, "PROVIDER_UNKNOWN", "Unknown or empty database list.") : null) ??
        (directions && (!directions.length || directions.some((d) => d !== "forward" && d !== "backward")) ? refuse(422, "CHASE_DIRECTION_INVALID", "directions must be among ['forward', 'backward']") : null) ??
        (body?.seeds && body.seeds !== "included" && body.seeds !== "included+unclear" ? refuse(422, "CHASE_SEEDS_INVALID", "seed source must be one of ['included', 'included+unclear']") : null) ??
        (!openalexKey && providers.includes("openalex")
          ? refuse(409, "OPENALEX_KEY_NOT_SET", "OpenAlex needs an API key. Set SCHOLAR_OPENALEX_KEY for the console (environment or .env) and start it again, or leave OpenAlex out of this run.")
          : null) ??
        busy();
      if (refused) return refused;
      const chase = addChase(body);
      const legs = chase.legs as Json[];
      const events = legs.map((l) => ({ event: "leg", data: { seed: l.seed, provider: l.provider, direction: l.direction, fetched: l.fetched, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code, notes: l.notes } }));
      const result = { chase: chase.chase, status: chase.status, reason: chase.reason, counts: chase.counts, published: chase.published, cancelled: false, legs_summary: chase.legs_summary };
      const job = chase.status === "FAILED"
        ? startJob("chase", events, result, false, "failed", { code: "PROVIDERS_FAILED", message: chase.reason })
        : startJob("chase", events, result);
      return { status: 202, body: { job } };
    }
    if (method === "POST" && route === "/api/v1/discovery/chase/accept") {
      const wanted = body?.chase as string | undefined;
      const chase = wanted ? chases.find((c) => c.chase === wanted) : chases.find((c) => c.published);
      if (!chase) return refuse(409, "CHASE_NOT_RUN", "no published chase run in this workspace; run `chase run` first");
      if (chase.accepted) return refuse(409, "CHASE_ALREADY_ACCEPTED", `${chase.chase} was already sent to screening (round ${(chase.accepted as Json).round})`);
      if (!chase.published) return refuse(409, "CHASE_NOT_RUN", `${chase.chase} was not published (${chase.status}): nothing to send`);
      if (!published) return refuse(409, "SCREENING_NOT_PUBLISHED", "the screening is not published and current");
      if (protocolChanged) return refuse(409, "PROTOCOL_CHANGED_SINCE_PUBLISH", "protocol.json changed after the screening was published; screening must be redone and published under the current protocol before a chase is sent");
      const counts = chase.counts as Json;
      if (!Number(counts.new)) return refuse(409, "CHASE_NOTHING_NEW", `${chase.chase} found nothing new to screen`);
      const active = activeJob();
      if (active) return refuse(409, "WORKSPACE_JOB_ACTIVE", "A discovery job is running in this workspace; nothing was moved.", { job: active });
      round += 1;
      published = false;
      chase.accepted = { round, artifact_id: "ART-corpus-" + "2".repeat(12), accepted_at: now(), records: counts.new, studies: counts.new };
      return {
        status: 200,
        body: {
          shape: "discovery.chase-accept-v1", chase: chase.chase, round, corpus: { artifact_id: "ART-corpus-" + "2".repeat(12), studies: counts.new, records: counts.new, outcome_status: "SUCCESS" },
          parent_corpus: "ART-corpus-" + "1".repeat(12), archived: ["screening/", "included.json", "excluded.json", "conflicts.json", "prisma_report.json", "prisma_screening_report.md", "verified.json"],
          archive_path: `literature/screening_rounds/round_${String(round - 1).padStart(3, "0")}`,
        },
      };
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
    /** M10a: the protocol's database list is edited (a new list and a new fingerprint). */
    setProtocolProviders: (value: string[]) => {
      protocolProviders = runProviders(value);
      fingerprint = "sha256:" + "ef".repeat(32);
    },
    /**
     * M10a: a run stopped by the researcher after `done` databases of the `requested` list: its legs
     * are a strict prefix of `requested_providers`, the last one `stopped`.
     */
    addStoppedRun: (requested: string[], done: number) => {
      const run = addRun(null, "PARTIAL", requested);
      const legs = (run.legs as Json[]).slice(0, done);
      if (legs.length) legs[legs.length - 1] = { ...legs[legs.length - 1], status: "stopped" };
      run.legs = legs;
      return run;
    },
    get accepted() {
      return accepted;
    },
    chases,
    setPublished: (value: boolean) => (published = value),
    get round() {
      return round;
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
