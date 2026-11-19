/**
 * A small stateful fake of the recon routes of an inception draft (M4c, M4d;
 * `src/scholar_harness/console/api/recon.py`), for tests only. It keeps the
 * engine's shapes and refusal codes; the real behaviour (occurrence counts,
 * directions, staleness) is pinned by `tests/console/test_recon_api.py`.
 * The vitest screens reach it through `inceptionEngine`, the Playwright spec
 * through the console proxy route.
 *
 * As the real session does, every recorded probe (topic or narrower, empty or
 * failed included) overwrites the session's `topic` with the draft's topic,
 * and the scope check compares the draft's question with that topic (the years
 * and languages with the latest usable pool).
 *
 * M10b Part C (sample curation): a pool keeps a small `reserve` (unless
 * `noReserve`), the papers the draft left out are kept on the draft record
 * (`sample_exclusions`, as the engine does), and every read applies them: the
 * effective sample is the first papers of `docs + reserve` that are not left
 * out, as many as the raw sample had (the engine caps at 25). A paper without a
 * DOI is keyed by its pool id. An empty probe's `POOL_EMPTY` carries
 * `details.shorten` by the engine's rule (`says_shorten`).
 */

type Json = Record<string, unknown>;
export type ReconAnswer = { status: number; body: unknown; sse?: boolean };

export type ProbeOutcome = "ok" | "thin" | "partial" | "empty" | "failed" | "noDirections" | "keyRefused" | "someEmpty";

export interface ReconOptions {
  mailto?: boolean;
  keys?: { openalex_key_set: boolean; s2_key_set: boolean };
  /** What successive first-search probes find (default `ok`); a narrower probe finds `narrow` unless listed. */
  outcomes?: (ProbeOutcome | "narrow")[];
  /** The job's stream closes before its end; the job finishes on the next read of the job. */
  holdStream?: boolean;
  /** The OpenAlex topics are missing, so purity is `indeterminate`. */
  noTopics?: boolean;
  /** The ids a probe can ask, in the engine's default order (`databases_available`); default the four. */
  databasesAvailable?: string[];
  /** M10b Part C: the pool was stored before replacements were kept (no `reserve` key). */
  noReserve?: boolean;
  /** M10b Part C: the last paper of a pool has no DOI, so its key is its pool id. */
  noDoiPaper?: boolean;
}

const PROVIDERS = ["openalex", "semanticscholar", "crossref", "arxiv"];
const FLOOR = 12;
/** The longest edited query a probe takes (M10a, `QUERY_MAX` in `recon.py`). */
const QUERY_MAX = 2000;
const PROBE_KEYS = ["refresh", "semantic", "narrower", "databases", "query"];

/**
 * A simple stand-in for the engine's keyword rule (`recon/keywords.py`): a topic
 * that is already a query (a double quote, a standalone AND/OR/NOT) is sent as
 * written; otherwise its words in order without a few English stopwords and
 * one-letter words, each once, at most six.
 */
const STOPWORDS = new Set(["a", "an", "and", "are", "as", "at", "by", "can", "do", "does", "for", "from", "how", "in", "is", "of", "on", "or", "the", "to", "what", "which", "with"]);
export function keywordQuery(topic: string): string {
  const text = topic.normalize("NFC").trim();
  if (text.includes('"') || /(^|\s)(AND|OR|NOT)(\s|$)/.test(text)) return text;
  const seen = new Set<string>();
  const terms: string[] = [];
  for (const word of text.split(/\s+/).map((w) => w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, ""))) {
    const key = word.toLowerCase();
    if (word.length < 2 || seen.has(key) || STOPWORDS.has(key)) continue;
    seen.add(key);
    terms.push(word);
    if (terms.length === 6) break;
  }
  return terms.join(" ") || text;
}

/** What one database received: arXiv joins the terms with AND (M10a, OBS-3); the others take the query as written. */
function executedQuery(provider: string, query: string): string {
  return provider === "arxiv" ? query.split(/\s+/).filter(Boolean).map((w) => `all:${w}`).join(" AND ") : query;
}

interface Doc {
  /** The pool id (`provider|provider_id`), the key of a paper without a DOI. */
  id: string;
  doi: string | null;
  title: string;
  year: number;
  provider: string;
  /** M10b Part C: on a reserve paper in the effective sample, the key of the left-out paper it replaced. */
  added_for?: string | null;
}

interface Pool {
  fingerprint: string;
  created_at: string;
  status: "complete" | "partial" | "empty";
  query: string;
  /** The databases asked, in order (M10a). */
  providers: string[];
  year_min: number | null;
  year_max: number | null;
  languages: string[];
  semantic: boolean;
  docs: Doc[];
  /** M10b Part C: the records fetched beyond the sample, in order; absent on a pool stored before replacements were kept. */
  reserve?: Doc[];
  legs: Json[];
  kind: ProbeOutcome | "narrow";
}

const refuse = (status: number, code: string, message = code.toLowerCase(), details?: unknown): ReconAnswer => ({
  status,
  body: { detail: { code, message, ...(details ? { details } : {}) } },
});

function docs(prefix: string, title: string, n: number, start = 0): Doc[] {
  return Array.from({ length: n }, (_, i) => {
    const id = `${prefix}${String(start + i).padStart(3, "0")}`;
    return { id: `openalex|W${id}`, doi: `10.1/${id}`, title: `${title} ${start + i}`, year: 2020 + (i % 5), provider: "openalex" };
  });
}

/** The engine's key of a paper (`sample.paper_key`): its DOI, else its pool id. */
const keyOf = (doc: Doc) => doc.doi ?? doc.id;

/** The draft's papers left out (`record.sample_exclusions.items`), in the order they were left out. */
const leftOut = (record: Json): Json[] => (((record.sample_exclusions as Json | undefined)?.items ?? []) as Json[]).filter((i) => !!i && typeof i === "object");

/** A stand-in for the engine's digest of the left-out keys: only compared, never shown. */
const digestOf = (keys: string[]) => `keys:${[...new Set(keys)].sort().join(",")}`;

/** The rule of the engine's `says_shorten`: a keyword query of 3 or more words, no OR, every database answered with nothing. */
function saysShorten(query: string, legs: Json[], semantic: boolean): boolean {
  const words = query.split(/[\s()"]+/).filter(Boolean);
  if (semantic || words.includes("OR") || words.filter((w) => !["AND", "OR", "NOT"].includes(w)).length < 3) return false;
  return legs.length > 0 && legs.every((l) => l.status !== "failed" && !l.fetched);
}

function occurs(term: string, doc: Doc): boolean {
  return doc.title.toLowerCase().includes(term.toLowerCase().trim());
}

function leg(provider: string, fetched: number, failed: string | null = null, extra: Json = {}): Json {
  return {
    provider,
    status: failed ? "failed" : "ok",
    reported_total: failed ? null : fetched * 3,
    fetched: failed ? 0 : fetched,
    cap: 25,
    cap_hit: false,
    error: failed,
    error_code: failed ? "PROVIDER_UNAVAILABLE" : null,
    notes: [`language (en): no language filter is sent to ${provider}`],
    key_set: provider === "openalex" || provider === "semanticscholar" ? true : null,
    ...extra,
  };
}

export function reconEngine(options: ReconOptions, now: () => string) {
  const keys = options.keys ?? { openalex_key_set: true, s2_key_set: false };
  const outcomes = [...(options.outcomes ?? [])];
  const available = [...(options.databasesAvailable ?? PROVIDERS)];
  /** The session's `topic`: the draft's topic at the last recorded probe (`ReconSessions.probe`). */
  let sessionTopic: string | null = null;
  const probes: Json[] = [];
  const pools: Pool[] = [];
  let latest: Pool | null = null;
  let narrowed = 0;
  let poolCount = 0;
  const jobs = new Map<string, { job: Json; events: { event: string; data: unknown }[]; held: boolean; finish: () => void }>();
  let jobCount = 0;

  const makePool = (kind: ProbeOutcome | "narrow", query: string, draft: Json, semantic: boolean, providers: string[]): Pool => {
    poolCount += 1;
    let list: Doc[] = [];
    let legs = providers.map((p) => leg(p, 6));
    if (kind === "ok" || kind === "partial" || kind === "noDirections" || kind === "keyRefused" || kind === "someEmpty") {
      list = [...docs("w", "Real-time weed detection on embedded hardware", 8), ...docs("s", "Lightweight cnn weed segmentation", 6)];
      if (kind === "noDirections") list = list.map((d, i) => ({ ...d, title: `Unrelated paper ${i}` }));
    } else if (kind === "thin") list = docs("t", "Real-time weed detection on embedded hardware", 7);
    else if (kind === "narrow") list = docs("n", "Embedded weed detection on a microcontroller", 10);
    if (options.noDoiPaper && list.length) list[list.length - 1] = { ...list[list.length - 1], doi: null, title: "A paper without a DOI" };
    // M10b Part C: what the databases returned beyond the sample (the engine keeps it from M10b on).
    const reserve = list.length && kind !== "thin" ? docs("r", "Crop row following for field robots", 2) : [];
    // Every database answered and found nothing: 0 of 0.
    if (kind === "empty") legs = providers.map((p) => leg(p, 0));
    // M10d: one database answered with nothing while the others found papers.
    if (kind === "someEmpty") legs = providers.map((p) => (p === "arxiv" ? leg(p, 0) : leg(p, 6)));
    if (kind === "partial") legs = providers.map((p) => (p === "crossref" ? leg(p, 0, "ConnectError: offline") : leg(p, 6)));
    if (kind === "keyRefused")
      legs = providers.map((p) =>
        p === "semanticscholar" ? { ...leg(p, 0, "HTTPStatusError: 403"), error_code: "PROVIDER_REFUSED", notes: ["Semantic Scholar rejected SCHOLAR_S2_KEY (HTTP 403)"] } : leg(p, 6),
      );
    if (kind === "failed") legs = providers.map((p) => leg(p, 0, "ConnectError: offline"));
    const status = list.length === 0 ? "empty" : legs.some((l) => l.status === "failed") ? "partial" : "complete";
    return {
      fingerprint: `sha256:${String(poolCount).padStart(4, "0")}${"ab".repeat(30)}`,
      created_at: now(),
      status,
      query,
      providers,
      year_min: (draft.start_year as number | null | undefined) ?? 2000,
      year_max: (draft.end_year as number | null | undefined) ?? null,
      languages: ((draft.languages as string[] | undefined) ?? ["en"]).slice().sort(),
      semantic,
      docs: list,
      ...(options.noReserve ? {} : { reserve }),
      // Only a database that ran records the query it received.
      legs: legs.map((l) => ({ ...l, executed_query: l.status === "ok" ? executedQuery(String(l.provider), query) : null })),
      kind,
    };
  };

  const summary = (pool: Pool) => ({
    path: `C:\\recon\\pool_${pool.fingerprint.slice(7, 11)}.json`,
    fingerprint: pool.fingerprint,
    created_at: pool.created_at,
    cache_key: `ck_${pool.fingerprint.slice(7, 11)}`,
    status: pool.status,
    query: pool.query,
    providers: pool.providers,
    year_min: pool.year_min,
    year_max: pool.year_max,
    languages: pool.languages,
    semantic: pool.semantic,
    n_docs: pool.docs.length,
    max_docs: 25,
    legs: pool.legs,
  });

  /** The engine's `effective_pool`: the first papers of `docs + reserve` not left out (here as many as the raw sample had). */
  const effective = (pool: Pool, keys: string[]): Pool => {
    const left = new Set(keys);
    const seen = new Set<string>();
    const candidates = [...pool.docs, ...(pool.reserve ?? [])].filter((d) => !seen.has(keyOf(d)) && !!seen.add(keyOf(d)));
    const inSample = new Set(pool.docs.map(keyOf));
    const replaced = pool.docs.map(keyOf).filter((k) => left.has(k));
    const kept = candidates.filter((d) => !left.has(keyOf(d))).slice(0, pool.docs.length);
    return { ...pool, docs: kept.map((d) => (inSample.has(keyOf(d)) ? d : { ...d, added_for: replaced.shift() ?? null })) };
  };

  /** The pool every read of this draft sees: the latest pool after the papers the draft left out. */
  const current = (record: Json): Pool => effective(latest!, leftOut(record).map((i) => String(i.key)));

  /** The `sample` object of `GET`/`POST .../recon/sample` (`sample.view`). */
  const sampleView = (record: Json) => {
    if (!latest) return null;
    const items = leftOut(record);
    const keys = items.map((i) => String(i.key));
    const pool = effective(latest, keys);
    const known = new Set([...latest.docs, ...(latest.reserve ?? [])].map(keyOf));
    const used = new Set(pool.docs.map(keyOf));
    const excluded = items.map((i) => ({ key: i.key, doi: i.doi ?? null, title: i.title ?? null, year: i.year ?? null, provider: i.provider ?? null, excluded_at: i.excluded_at ?? null, in_pool: known.has(String(i.key)) }));
    const n = pool.docs.length;
    const marked = excluded.filter((e) => e.in_pool).length;
    const share = marked + n ? Math.round((marked / (marked + n)) * 10000) / 10000 : 0;
    const reasons = [...(n < FLOOR ? ["BELOW_FLOOR"] : []), ...(marked && share >= 0.5 ? ["MOSTLY_OFF_TOPIC"] : [])];
    return {
      session_id: record.session_id,
      updated_at: record.updated_at,
      pool_fingerprint: latest.fingerprint,
      n_docs: n,
      n_docs_raw: latest.docs.length,
      max_docs: 25,
      reserve_n: [...known].filter((k) => !used.has(k) && !keys.includes(k)).length,
      has_reserve: latest.reserve !== undefined,
      excluded,
      excluded_in_pool: marked,
      recommend: { search: reasons.length > 0, reason: reasons[0] ?? null, reasons, threshold: { floor: FLOOR, share: 0.5 }, marked_share: share },
      exclusions_digest: digestOf(keys),
    };
  };

  const directionsOf = (pool: Pool) => {
    const labels = pool.kind === "noDirections" ? [] : pool.kind === "narrow" ? ["embedded weed detection", "microcontroller"] : ["weed detection", "weed segmentation", "embedded hardware"];
    return labels
      .map((label) => {
        const anchors = pool.docs.filter((d) => d.doi && occurs(label, d)).map((d) => d.doi as string);
        return { label, concept: label, anchor_dois: anchors, observed_in: anchors.length, n_docs: pool.docs.length, detail: `pool term observed in ${anchors.length} papers`, schools: anchors.length ? ["Edge inference"] : [] };
      })
      .filter((d) => d.observed_in >= 2);
  };

  const gates = (pool: Pool) => ({
    pool: { n_docs: pool.docs.length, sufficient: pool.docs.length >= FLOOR, label: pool.docs.length >= FLOOR ? "sufficient" : "thin", threshold: FLOOR },
    purity: options.noTopics
      ? { label: "indeterminate", purity: null, n_topics: 0, top1_share: null, top3_share: null, threshold: 0.5 }
      : { label: "coherent", purity: 0.8, n_topics: 6, top1_share: 0.4, top3_share: 0.71, threshold: 0.5 },
  });

  const conceptRows = (draft: Json): { rows: { concept: string; synonyms: string[] }[]; source: string } => {
    const cs = (draft.concepts as { concept: string; synonyms?: string[] }[] | undefined) ?? [];
    if (cs.length) return { rows: cs.map((c) => ({ concept: c.concept, synonyms: c.synonyms ?? [] })), source: "draft" };
    return { rows: [{ concept: "weed", synonyms: [] }, { concept: "detection", synonyms: [] }], source: "suggested" };
  };

  const POOL_TERMS = ["embedded hardware", "lightweight cnn", "real-time"];

  const conceptReport = (pool: Pool, draft: Json) => {
    const { rows, source } = conceptRows(draft);
    const known = new Set(rows.flatMap((r) => [r.concept, ...r.synonyms].map((t) => t.toLowerCase())));
    // As `concept_report`, over the papers with a DOI only.
    const withDoi = pool.docs.filter((d) => d.doi);
    return rows.map((r) => {
      const terms = [r.concept, ...r.synonyms].map((term) => {
        const anchors = withDoi.filter((d) => occurs(term, d)).map((d) => d.doi as string);
        return { term, observed_in: anchors.length, anchor_dois: anchors };
      });
      const anchoring = withDoi.filter((d) => [r.concept, ...r.synonyms].some((term) => occurs(term, d)));
      const suggestions = POOL_TERMS.filter((t) => !known.has(t))
        .map((term) => ({ term, observed_in: anchoring.filter((d) => occurs(term, d)).length }))
        .filter((s) => s.observed_in >= 2)
        .sort((a, b) => b.observed_in - a.observed_in || a.term.localeCompare(b.term));
      return { concept: r.concept, source, terms, anchored_in: anchoring.length, suggestions };
    });
  };

  type Scope = { topic: string; year_min: number | null; year_max: number | null; languages: string[] };
  const scopeOf = (draft: Json): Scope => ({
    topic: (draft.topic as string | undefined) ?? "",
    year_min: (draft.start_year as number | null | undefined) ?? 2000,
    year_max: (draft.end_year as number | null | undefined) ?? null,
    languages: ((draft.languages as string[] | undefined) ?? ["en"]).slice().sort(),
  });

  const changes = (now: Scope, then: Scope): string[] => {
    const out: string[] = [];
    if (now.topic !== then.topic) out.push("topic");
    if (now.year_min !== then.year_min || now.year_max !== then.year_max) out.push("years");
    if (JSON.stringify(now.languages) !== JSON.stringify(then.languages)) out.push("languages");
    return out;
  };

  const binding = (grounding: Json, record: Json) => {
    const draft = (record.draft ?? {}) as Json;
    const bound = (grounding.pool as Json).fingerprint as string;
    const current = latest?.fingerprint ?? null;
    if (bound !== current) return { stale: true, code: "POOL_CHANGED", reason: "the session searched again after this direction was chosen", bound, current };
    const changed = changes(scopeOf(draft), grounding.scope as Scope);
    if (changed.length) return { stale: true, code: "SCOPE_CHANGED", reason: `the draft's ${changed.join(", ")} changed after this direction was chosen`, changes: changed, bound, current };
    // M10b Part C: a direction bound before the sample changed.
    const digest = digestOf(leftOut(record).map((i) => String(i.key)));
    if ((grounding.sample_exclusions_digest ?? digestOf([])) !== digest) return { stale: true, code: "SAMPLE_CHANGED", reason: "the sample changed after this direction was chosen", bound, current };
    return { stale: false, bound, current };
  };

  const active = () => [...jobs.values()].find((j) => j.job.state === "running")?.job ?? null;

  const handle = (method: string, rest: string, query: URLSearchParams, body: Json | null, record: Json, store: (next: Json) => void): ReconAnswer => {
    const draft = (record.draft ?? {}) as Json;
    const sid = record.session_id as string;
    if (rest === "" && method === "GET") {
      const grounding = (record.grounding as Json | undefined) ?? null;
      // The session's topic sentence, not the pool's query: an edited or keyword query is not a scope change (M10a).
      const scopeChanges = latest ? changes(scopeOf(draft), { topic: sessionTopic ?? "", year_min: latest.year_min, year_max: latest.year_max, languages: latest.languages }) : [];
      return {
        status: 200,
        body: {
          session_id: sid,
          mailto_set: options.mailto ?? true,
          keys,
          topic_changed: scopeChanges.includes("topic"),
          scope_changed: scopeChanges.length > 0,
          scope_changes: scopeChanges,
          session: probes.length ? { session_id: sid, topic: sessionTopic, latest: probes[probes.length - 1], probes, narrower_left: Math.max(0, 1 - narrowed) } : null,
          grounding,
          binding: grounding ? binding(grounding, record) : null,
          active_job: active(),
          derived_query: draft.topic ? keywordQuery(String(draft.topic)) : null,
          databases_available: [...available],
        },
      };
    }
    if (rest === "/probe" && method === "POST") {
      // The body first, as pydantic does (`ProbeBody`, extra="forbid"): 422 BODY_INVALID.
      const invalid = (loc: string, msg: string) => refuse(422, "BODY_INVALID", "The request body is not valid.", { errors: [{ loc: ["body", loc], msg, type: "value_error" }] });
      const narrowerSent = body?.narrower !== undefined && body?.narrower !== null;
      const extra = Object.keys(body ?? {}).find((k) => !PROBE_KEYS.includes(k));
      if (extra) return invalid(extra, "Extra inputs are not permitted");
      let edited: string | null = null;
      if (body?.query !== undefined && body?.query !== null) {
        if (typeof body.query !== "string") return invalid("query", "Input should be a valid string");
        edited = body.query.trim();
        if (edited.length < 1 || [...edited].length > QUERY_MAX) return invalid("query", `String should have 1 to ${QUERY_MAX} characters`);
      }
      const databasesSent = body?.databases !== undefined && body?.databases !== null;
      if (databasesSent && !Array.isArray(body!.databases)) return invalid("databases", "Input should be a valid list");
      // `list[str]`: an item that is not a string is a body error, before the list check.
      if (databasesSent && (body!.databases as unknown[]).some((item) => typeof item !== "string")) return invalid("databases", "Input should be a valid string");
      if (narrowerSent && (edited !== null || databasesSent)) return invalid("narrower", "a narrower search takes no query or databases");
      // Then the database list (M10a): 422 PROVIDER_UNKNOWN for an unknown, empty or repeated list.
      let providers = [...PROVIDERS];
      if (databasesSent) {
        const names = body!.databases as string[];
        const unknown = names.filter((n) => !PROVIDERS.includes(n));
        const repeated = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))].sort();
        if (unknown.length || repeated.length || !names.length)
          return refuse(422, "PROVIDER_UNKNOWN", "Unknown, empty or repeated database list.", { unknown, repeated, known: [...PROVIDERS] });
        providers = names;
      }
      if (!draft.topic) return refuse(422, "DRAFT_INCOMPLETE", "a probe needs the draft's topic", { missing: ["topic"] });
      if (!(options.mailto ?? true)) return refuse(409, "MAILTO_NOT_SET", "A search needs a contact email for the literature databases.");
      // The edited query as written, else the topic's keyword query; the topic itself is kept.
      let queryText = edited ?? keywordQuery(draft.topic as string);
      let purpose = "topic";
      if (narrowerSent) {
        if (!latest) return refuse(409, "RECON_NO_POOL", "Run the first search before a narrower one.");
        if (narrowed >= 1) return refuse(409, "NARROW_BUDGET_SPENT", "The one narrower search of this draft is used.");
        const labels = directionsOf(current(record)).map((d) => d.label);
        if (!labels.includes(String(body!.narrower))) return refuse(422, "DIRECTION_UNKNOWN", "not a direction", { directions: labels });
        // The label as written, on the databases of the latest probe that recorded them.
        queryText = String(body!.narrower);
        purpose = "narrower";
        providers = ([...probes].reverse().find((p) => Array.isArray(p.providers))?.providers as string[] | undefined) ?? [...PROVIDERS];
      }
      const running = active();
      if (running) return refuse(409, "RECON_JOB_ACTIVE", "A search for this draft is already running.", { job: running });
      const semantic = !!body?.semantic;
      let pool: Pool;
      let cached = false;
      // The order of the databases is part of the cache key: another order is another pool.
      const cachedPool =
        purpose === "topic" && !body?.refresh
          ? pools.find((p) => p.query === queryText && p.status === "complete" && p.semantic === semantic && p.kind !== "narrow" && p.providers.join() === providers.join())
          : undefined;
      if (cachedPool) {
        pool = cachedPool;
        cached = true;
      } else {
        // A narrower probe takes the next outcome only when it is one a narrower search can have.
        const next = outcomes[0];
        const kind = purpose === "narrower" ? (next === "empty" || next === "failed" || next === "narrow" ? outcomes.shift()! : "narrow") : (outcomes.shift() ?? "ok");
        pool = makePool(kind, queryText, draft, semantic, providers);
      }
      if (purpose === "narrower") narrowed += 1;
      const probe = {
        purpose,
        query: queryText,
        providers: pool.providers,
        fingerprint: pool.fingerprint,
        created_at: pool.created_at,
        cache_key: `ck_${pool.fingerprint.slice(7, 11)}`,
        status: pool.status,
        n_docs: pool.docs.length,
        served_from_cache: cached,
        year_min: pool.year_min,
        year_max: pool.year_max,
        languages: pool.languages,
        legs: pool.legs,
        at: now(),
      };
      probes.push(probe);
      sessionTopic = (draft.topic as string | undefined) ?? null;
      if (pool.docs.length) {
        if (!pools.includes(pool)) pools.push(pool);
        latest = pool;
      }
      jobCount += 1;
      const jobId = `rjob_${String(jobCount).padStart(16, "0")}`;
      const job: Json = { job_id: jobId, session_id: sid, kind: "probe", state: "running", started_at: now(), finished_at: null, result: null, error: null };
      const events: { event: string; data: unknown }[] = [{ event: "snapshot", data: { job: { ...job } } }];
      for (const l of pool.legs) events.push({ event: "leg", data: { job_id: jobId, provider: l.provider, fetched: l.fetched } });
      const finish = () => {
        job.finished_at = now();
        if (pool.docs.length === 0) {
          const failed = pool.legs.every((l) => l.status === "failed");
          job.state = "failed";
          job.error = failed
            ? { code: "PROVIDERS_FAILED", message: "Every database failed to answer.", details: { legs: pool.legs } }
            : { code: "POOL_EMPTY", message: "The search found no papers.", details: { legs: pool.legs, status: "empty", shorten: saysShorten(pool.query, pool.legs, pool.semantic) } };
          events.push({ event: "failed", data: { job: { ...job } } });
        } else {
          job.state = "succeeded";
          job.result = { session_id: sid, ...probe };
          events.push({ event: "done", data: { job: { ...job } } });
        }
      };
      const entry = { job, events, held: !!options.holdStream, finish };
      if (!entry.held) finish();
      jobs.set(jobId, entry);
      return { status: 202, body: { job: { ...job, state: "running", finished_at: null, result: null, error: null } } };
    }
    const jobMatch = rest.match(/^\/jobs\/([^/]+)(\/events)?$/);
    if (jobMatch && method === "GET") {
      const entry = jobs.get(jobMatch[1]);
      if (!entry) return refuse(404, "RECON_JOB_NOT_FOUND", `no recon job ${jobMatch[1]} for this draft`);
      if (jobMatch[2]) {
        const text = entry.events.map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join("");
        return { status: 200, body: text, sse: true };
      }
      if (entry.held && entry.job.state === "running") {
        entry.held = false;
        entry.finish();
      }
      return { status: 200, body: { job: entry.job } };
    }
    const needPool = (): ReconAnswer | null => {
      if (!probes.length) return refuse(404, "RECON_SESSION_NOT_FOUND", `session not found: ${sid}`);
      if (!latest) return refuse(409, "RECON_NO_POOL", "the session has no pool; run a probe first");
      return null;
    };
    if (rest === "/distill" && method === "POST") {
      const missing = needPool();
      if (missing) return missing;
      const pool = current(record);
      const dirs = directionsOf(pool);
      const counts = new Map<string, number>();
      for (const d of dirs) for (const doi of d.anchor_dois) counts.set(doi, (counts.get(doi) ?? 0) + 1);
      const papers = pool.docs
        .map((d) => ({ key: keyOf(d), doi: d.doi, title: d.title, year: d.year, provider: d.provider, directions_anchored: counts.get(d.doi ?? "") ?? 0, added_for: d.added_for ?? null }))
        .sort((a, b) => b.directions_anchored - a.directions_anchored || a.title.localeCompare(b.title));
      return {
        status: 200,
        body: {
          session_id: sid,
          pool: summary(pool),
          terms_path: "C:\\recon\\distilled.json",
          qei: 0.4,
          gates: gates(pool),
          papers,
          metrics: [{ label: "accuracy", count: 9 }],
          datasets: [{ label: "DeepWeeds", count: 2 }],
          schools: [
            { label: "Edge inference", n: 8, anchor_dois: pool.docs.slice(0, 8).map((d) => d.doi) },
            { label: "Federated learning", n: 1, anchor_dois: pool.docs.slice(0, 1).map((d) => d.doi) },
          ],
          topics: options.noTopics ? [] : ["Weed control", "Edge computing", "Plant detection", "Embedded vision", "Precision farming", "Robotics"].map((label, i) => ({ label, n: 6 - i, score: 0.5 })),
          micro_taxonomy_top: [],
        },
      };
    }
    if (rest === "/directions" && method === "GET") {
      const missing = needPool();
      if (missing) return missing;
      const pool = current(record);
      return { status: 200, body: { session_id: sid, pool: summary(pool), gates: gates(pool), directions: directionsOf(pool), narrower_left: Math.max(0, 1 - narrowed) } };
    }
    if (rest === "/concepts" && method === "GET") {
      const missing = needPool();
      if (missing) return missing;
      const pool = current(record);
      return { status: 200, body: { session_id: sid, fingerprint: latest!.fingerprint, n_docs: pool.docs.length, concepts: conceptReport(pool, draft) } };
    }
    if (rest === "/sample" && method === "GET") {
      const missing = needPool();
      if (missing) return missing;
      return { status: 200, body: sampleView(record) };
    }
    if (rest === "/sample" && method === "POST") {
      // The body first, as pydantic does (`SampleBody`, extra="forbid", at most 25 keys each).
      const extra = Object.keys(body ?? {}).find((k) => !["add", "remove", "base_updated_at"].includes(k));
      const add = (body?.add ?? []) as string[];
      const remove = (body?.remove ?? []) as string[];
      if (extra || !Array.isArray(add) || !Array.isArray(remove) || add.length > 25 || remove.length > 25)
        return refuse(422, "BODY_INVALID", "The request body is not valid.", { errors: [{ loc: ["body", extra ?? "add"], msg: "not valid", type: "value_error" }] });
      const missing = needPool();
      if (missing) return missing;
      if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
      if (body?.base_updated_at && body.base_updated_at !== record.updated_at) return refuse(409, "DRAFT_CONFLICT", "the draft changed since it was read");
      const items = leftOut(record).map((i) => ({ ...i }));
      const have = new Set(items.map((i) => String(i.key)));
      const shown = new Map(current(record).docs.map((d) => [keyOf(d), d]));
      const known = new Set([...latest!.docs, ...(latest!.reserve ?? [])].map(keyOf));
      const unknown = [...new Set([...add.filter((k) => !shown.has(k) && !have.has(k)), ...remove.filter((k) => !have.has(k) && !known.has(k))])].sort();
      if (unknown.length) return refuse(422, "PAPER_UNKNOWN", "That paper is not in this sample.", { keys: unknown });
      const kept = items.filter((i) => !remove.includes(String(i.key)));
      const keys = new Set(kept.map((i) => String(i.key)));
      for (const key of add) {
        if (keys.has(key) || remove.includes(key)) continue;
        const doc = shown.get(key)!;
        kept.push({ key, doi: doc.doi, title: doc.title, year: doc.year, provider: doc.provider, reason: "NOT_RELEVANT", excluded_at: now(), pool_fingerprint: latest!.fingerprint });
        keys.add(key);
      }
      if (kept.length > 200) return refuse(422, "SAMPLE_EXCLUSIONS_FULL", "A draft can record 200 papers left out.", { limit: 200 });
      const stored = { ...record, sample_exclusions: { items: kept }, updated_at: now() };
      store(stored);
      return { status: 200, body: sampleView(stored) };
    }
    if (rest === "/evidence" && method === "GET") {
      const term = query.get("term") ?? "";
      if (!term.trim()) return refuse(422, "TERM_EMPTY", "Type a phrase to check.");
      const missing = needPool();
      if (missing) return missing;
      const pool = current(record);
      const anchors = pool.docs.filter((d) => d.doi && occurs(term, d)).map((d) => d.doi as string);
      return { status: 200, body: { term, hits: anchors.length * 3, observed_in: anchors.length, anchor_dois: anchors, n_docs: pool.docs.length } };
    }
    if (rest === "/seeds" && method === "GET") {
      const missing = needPool();
      if (missing) return missing;
      const pool = current(record);
      const dirs = directionsOf(pool);
      const { rows } = conceptRows(draft);
      // A seed is a DOI; a left-out paper is never offered (the effective pool).
      const papers = pool.docs
        .filter((d): d is Doc & { doi: string } => !!d.doi)
        .map((d) => ({
          doi: d.doi,
          title: d.title,
          year: d.year,
          provider: d.provider,
          anchors: { directions: dirs.filter((x) => x.anchor_dois.includes(d.doi)).map((x) => x.label), concepts: rows.filter((r) => occurs(r.concept, d)).map((r) => r.concept) },
        }))
        .filter((p) => p.anchors.directions.length || p.anchors.concepts.length)
        .sort((a, b) => b.anchors.directions.length + b.anchors.concepts.length - (a.anchors.directions.length + a.anchors.concepts.length) || a.title.localeCompare(b.title));
      return { status: 200, body: { session_id: sid, fingerprint: latest!.fingerprint, papers } };
    }
    if (rest === "/bind" && method === "POST") {
      const picked = [!!body?.direction, !!body?.own, !!body?.skip].filter(Boolean).length;
      if (picked !== 1) return refuse(422, "NO_DIRECTION", "Choose one of the proposed directions, write your own, or go on without one.");
      const missing = needPool();
      if (missing) return missing;
      if (record.emitted) return refuse(409, "DRAFT_EMITTED", "this draft already created a workspace");
      if (body?.base_updated_at && body.base_updated_at !== record.updated_at) return refuse(409, "DRAFT_CONFLICT", "the draft changed since it was read");
      const pool = current(record);
      const n = pool.docs.length;
      if (n < FLOOR && !body?.accept_thin_pool && !body?.skip) return refuse(409, "POOL_TOO_SMALL", `The pool has ${n} papers, under the floor of ${FLOOR}`, { n_docs: n, floor: FLOOR });
      let direction: Json;
      if (body?.direction) {
        const chosen = directionsOf(pool).find((d) => d.label === body.direction);
        if (!chosen) return refuse(422, "DIRECTION_UNKNOWN", "not a direction of the current pool", { directions: directionsOf(pool).map((d) => d.label) });
        direction = { ...chosen, source: "pool", grounded: true };
      } else if (body?.skip) {
        direction = { label: "", concept: "", anchor_dois: [], observed_in: 0, n_docs: n, schools: [], detail: "no direction chosen; the protocol is not grounded", source: "none", grounded: false };
      } else {
        const own = String(body?.own ?? "").trim();
        const anchors = pool.docs.filter((d) => d.doi && occurs(own, d)).map((d) => d.doi as string);
        direction = { label: own, concept: own, anchor_dois: anchors, observed_in: anchors.length, n_docs: n, schools: [], detail: "your direction", source: "researcher", grounded: anchors.length >= 2 };
      }
      const grounding = {
        session_id: sid,
        bound_at: now(),
        pool: { fingerprint: pool.fingerprint, created_at: pool.created_at, cache_key: "ck", path: "C:\\recon\\pool.json", status: pool.status, query: pool.query, providers: pool.providers, n_docs: n, legs: pool.legs },
        direction,
        anchors: [...(direction.anchor_dois as string[])].sort(),
        choice: body?.skip ? "none" : direction.source,
        scope: scopeOf(draft),
        sample_exclusions_digest: digestOf(leftOut(record).map((i) => String(i.key))),
      };
      const stored = { ...record, grounding, updated_at: now() };
      store(stored);
      return { status: 200, body: stored };
    }
    if (rest === "/delta") return refuse(500, "NOT_IN_THE_BROWSER", "the browser never calls the gap check");
    return refuse(404, "NOT_FOUND", rest);
  };

  /** A stale binding refuses the preview and genesis with session (STALE_BINDING). */
  const staleBinding = (record: Json): ReconAnswer | null => {
    const grounding = record.grounding as Json | undefined;
    if (!grounding) return null;
    const state = binding(grounding, record);
    return state.stale ? refuse(409, "STALE_BINDING", `The direction was chosen on a pool that no longer matches (${state.reason}).`, state) : null;
  };

  /** The draft's `sample` object (null before a pool), for a test's own checks rows. */
  const sample = (record: Json) => sampleView(record);

  return { handle, staleBinding, jobs, probes, sample };
}
