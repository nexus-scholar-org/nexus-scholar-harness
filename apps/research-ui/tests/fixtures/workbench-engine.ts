/**
 * A small stateful fake of the query workbench routes (M11a parts A and B), for
 * tests only: the inception and discovery fakes hand it every path under
 * `…/workbench/`. It keeps the engine's shapes, statuses and refusal codes; the
 * engine's real arithmetic is pinned by the Python suite
 * (`tests/console/test_workbench_counts_api.py`, `test_workbench_seeds_comparison_api.py`).
 *
 * Its numbers are its own: a full query counts `total(db, concepts)`, a concept
 * left out counts the same function on the smaller version, so tests can stub
 * values a browser-side sum or ratio would contradict.
 */

type Json = Record<string, unknown>;
type Answer = { status: number; body: unknown };
type Concept = { concept: string; synonyms: string[] };
type Version = { query_key: string; concepts: Concept[]; start_year?: number | null; end_year?: number | null; languages?: string[] };

export interface WorkbenchOptions {
  /** A database's count for a list of concepts (default: a fixed shrink per concept). */
  total?: (db: string, concepts: Concept[]) => number;
  /** A database's row status instead of a count (a refusal, a used-up quota, …), keyed by database. */
  fail?: Record<string, { status: string; error_code?: string; http_status?: number; resets_at?: string; resets_in?: { hours: number; minutes: number } }>;
  /** Refuse every real count with this code (`DISCOVERY_JOB_ACTIVE`, `MAILTO_NOT_SET`, …). */
  refuse?: { status: number; code: string; message?: string; details?: Json } | null;
  /** The budget map in every answer. */
  budget?: Record<string, { limit: number; spent: number; left: number; renews_at: string; low: boolean }>;
  /** What a seed's words are (title), by DOI; missing = not read. */
  seedTitles?: Record<string, string>;
  /** The OpenAlex identifier switch (`NEXUS_WORKBENCH_OPENALEX_IDS`). */
  openalexIds?: boolean;
  /** The records "read what this concept removes" returns. */
  removed?: { title: string; doi: string | null; year: number | null; lacks: string[] }[];
}

const NAMES = ["openalex", "semanticscholar", "arxiv"];
const DEFAULTS = ["openalex", "semanticscholar", "crossref", "arxiv"];
const refuse = (status: number, code: string, message = code.toLowerCase(), details?: Json): Answer => ({ status, body: { detail: { code, message, ...(details ? { details } : {}) } } });
const termsOf = (c: Concept) => [c.concept, ...c.synonyms].filter((t) => t.trim());
const words = (text: string) => text.toLowerCase().replace(/[^0-9a-z]+/g, " ").split(" ").filter(Boolean).map((w) => (w.length > 3 && w.endsWith("s") && !w.endsWith("ss") ? w.slice(0, -1) : w));
const has = (text: string, term: string) => {
  const hay = ` ${words(text).join(" ")} `;
  const needle = words(term).join(" ");
  return needle !== "" && hay.includes(` ${needle} `);
};

export function workbenchEngine(options: WorkbenchOptions = {}, now: () => string = () => "2026-11-21T10:15:00+00:00") {
  const counted = new Set<string>();
  const sets: Json[] = [];
  const total = options.total ?? ((db: string, concepts: Concept[]) => Math.max(1, 900 - 200 * concepts.length - 7 * termsOfAll(concepts)) + ({ openalex: 0, semanticscholar: -50, arxiv: -150, crossref: 5000 } as Record<string, number>)[db]!);
  function termsOfAll(concepts: Concept[]) {
    return concepts.reduce((n, c) => n + termsOf(c).length, 0);
  }
  const budget = () => options.budget ?? {};
  const key = (db: string, concepts: Concept[]) => `${db}|${JSON.stringify(concepts)}`;

  const counts = (body: Json, mode: "counts" | "synonyms"): Answer => {
    const version = body.version as Version;
    const concepts = (version.concepts ?? []).filter((c) => c.concept.trim());
    if (!concepts.length) return refuse(422, "WORKBENCH_VERSION_INVALID", "a version needs at least one concept with a term");
    const dry = !!body.dry_run;
    if (!dry && options.refuse) return refuse(options.refuse.status, options.refuse.code, options.refuse.message, options.refuse.details);
    const names = mode === "synonyms" ? [String(body.provider ?? "openalex")] : ((body.providers as string[] | undefined) ?? DEFAULTS);
    const joined = concepts.length >= 2;
    const at = now();
    const rows = names.map((db) => {
      const base = { name: db, any_words: false, upper_bound: false, error: null, error_code: null, http_status: null, resets_at: null, resets_in: null, last: null, stopped: null };
      if (joined && db === "crossref" && !body.crossref_anyway) return { ...base, status: "not_comparable", string: null, total: null, counted_at: null, from_cache: false, cost: 0, requests: 0, drops: [] };
      const variants: { kind: string; index: number | null; concept: string | null; term: string | null; concepts: Concept[] }[] = [{ kind: "full", index: null, concept: null, term: null, concepts }];
      if (mode === "counts" && joined && db !== "crossref") concepts.forEach((c, i) => variants.push({ kind: "drop", index: i, concept: c.concept, term: null, concepts: concepts.filter((_, j) => j !== i) }));
      if (mode === "synonyms") {
        const i = Number(body.concept_index);
        termsOf(concepts[i]).forEach((term) => {
          const rest = termsOf(concepts[i]).filter((x) => x !== term);
          const smaller = rest.length ? concepts.map((c, j) => (j === i ? { concept: rest[0], synonyms: rest.slice(1) } : c)) : concepts.filter((_, j) => j !== i);
          if (smaller.length) variants.push({ kind: "synonym", index: i, concept: concepts[i].concept, term, concepts: smaller });
        });
      }
      const failure = options.fail?.[db];
      const cells = variants.map((v) => {
        const k = key(db, v.concepts);
        const cached = counted.has(k);
        if (failure && !cached) return { ...v, status: dry ? failure.status : failure.status, total: null, counted_at: null, from_cache: false, cost: dry && failure.status === "to_count" ? 1 : 0, k };
        if (cached) return { ...v, status: "cached", total: total(db, v.concepts), counted_at: "2026-11-21T09:00:00+00:00", from_cache: true, cost: 0, k };
        if (dry) return { ...v, status: "to_count", total: null, counted_at: null, from_cache: false, cost: 1, k };
        counted.add(k);
        return { ...v, status: "counted", total: total(db, v.concepts), counted_at: at, from_cache: false, cost: 1, k };
      });
      const full = cells[0];
      const known = (c: typeof full) => (c.status === "counted" || c.status === "cached" ? c.total : null);
      const rest = cells.slice(1).map((c) => {
        const t = known(c);
        const f = known(full);
        const gain = t !== null && f !== null ? (mode === "synonyms" ? f - t : t - f) : null;
        const ratio = mode === "counts" && t !== null && f !== null && f > 0 ? Math.round((t / f) * 10) / 10 : null;
        return {
          kind: c.kind, concept_index: c.index, concept: c.concept, term: c.term, status: c.status, total: t, string: `${db}:${c.k}`, counted_at: c.counted_at,
          from_cache: c.from_cache, error: null, error_code: null, http_status: null, resets_at: null, gain, ratio,
          note: mode === "counts" && t !== null && f !== null && t >= 2 * f, adds_nothing: gain === 0,
        };
      });
      if (mode === "counts") {
        const best = rest.reduce((b, c, i) => (typeof c.gain === "number" && c.gain > 0 && (b < 0 || c.gain > (rest[b].gain as number)) ? i : b), -1);
        rest.forEach((c, i) => Object.assign(c, { largest: i === best }));
      }
      const status = failure && full.status === failure.status ? failure.status : full.status;
      return {
        ...base, status, any_words: db === "crossref" && joined, string: `${db}:${full.k}`, total: known(full), counted_at: known(full) !== null ? full.counted_at : null,
        from_cache: full.from_cache, error_code: failure?.error_code ?? null, http_status: failure?.http_status ?? null, resets_at: failure?.resets_at ?? null, resets_in: failure?.resets_in ?? null,
        cost: cells.reduce((n, c) => n + (c.status === "to_count" ? 1 : 0), 0), requests: dry ? 0 : cells.filter((c) => c.status === "counted").length,
        ...(mode === "counts" ? { drops: rest } : { synonyms: rest }),
      };
    });
    if (mode === "counts") for (const db of DEFAULTS) if (!names.includes(db)) rows.push({ name: db, status: "not_asked", any_words: false, upper_bound: false, string: null, total: null, counted_at: null, from_cache: false, error: null, error_code: null, http_status: null, resets_at: null, resets_in: null, last: null, stopped: null, cost: 0, requests: 0, drops: [] } as never);
    const byDb = Object.fromEntries(rows.filter((r) => !["not_comparable", "not_asked"].includes(String(r.status)) && !(failure(r))).map((r) => [r.name, Number(r.cost)]));
    function failure(r: { name: string }) {
      return !!options.fail?.[r.name] && options.fail[r.name].status !== "to_count";
    }
    const counted_ = rows.filter((r) => typeof r.total === "number" && !r.any_words).map((r) => r.total as number);
    const sum = counted_.reduce((a, b) => a + b, 0);
    const notes = mode === "counts"
      ? rows.flatMap((r) => ((r as { drops?: Json[] }).drops ?? []).filter((d) => d.note).map((d) => ({ concept_index: d.concept_index, concept: d.concept, database: r.name, total: r.total, without: d.total })))
      : undefined;
    return {
      status: 200,
      body: {
        shape: `workbench.${mode}-v1`, query_key: "main", dry_run: dry, version, concepts: concepts.length, terms: termsOfAll(concepts),
        cost: { total: Object.values(byDb).reduce((a, b) => a + b, 0), by_database: byDb, cached: Object.values(byDb).every((n) => n === 0) && Object.keys(byDb).length > 0 },
        requests: rows.reduce((n, r) => n + Number(r.requests), 0), databases: rows, budget: budget(), mailto_set: true,
        ...(mode === "counts"
          ? {
              notes,
              size: {
                estimate: { counted_all: true, records: { low: sum, high: sum }, works: { low: Math.max(0, ...counted_), high: sum }, assumption: "" },
                effort: { pace_seconds: 30, hours: { low: Math.round((Math.max(0, ...counted_) * 30) / 360) / 10, high: Math.round((sum * 30) / 360) / 10 } },
                warn: { level: "none", threshold_works: 1000, limit: { value: 1000, source: "general" } },
                recommendation: {}, cap: 10000,
              },
              external: { scopus: `TITLE-ABS-KEY(${concepts.map((c) => `(${termsOf(c).map((t) => `"${t}"`).join(" OR ")})`).join(" AND ")})`, wos: `TS=(${concepts.map((c) => `(${termsOf(c).map((t) => `"${t}"`).join(" OR ")})`).join(" AND ")})` },
            }
          : { concept_index: body.concept_index }),
      },
    };
  };

  const seeds = (body: Json, saved: string[]): Answer => {
    const version = body.version as Version;
    const dois = (body.seeds as string[] | undefined) ?? saved;
    const titles = options.seedTitles ?? {};
    const lookedUp = !!body.lookup && !body.dry_run;
    const rows = dois.map((doi) => {
      const title = titles[doi] ?? null;
      const read = title !== null && (lookedUp || !!titles[doi]);
      const concepts = read ? version.concepts.map((c) => ({ concept: c.concept, found: termsOf(c).some((t) => has(title!, t)) })) : [];
      const lacks = concepts.filter((c) => !c.found).map((c) => c.concept);
      return { doi, title, read, concepts, lacks, missed: lacks.length > 0, suggestions: lacks.length ? ["rgb orthophotos"] : [] };
    });
    const read = rows.filter((r) => r.read);
    const untested = version.concepts.filter((_, i) => read.length && read.every((r) => r.concepts[i].found)).map((c) => c.concept);
    const level = !read.length ? null : read.length < 3 ? "few" : untested.length === version.concepts.length ? "all" : untested.length ? "concept" : null;
    const status = !body.openalex ? "not_asked" : !options.openalexIds ? "switch_off" : body.dry_run ? "to_check" : "checked";
    return {
      status: 200,
      body: {
        shape: "workbench.seeds-v1", query_key: "main", dry_run: !!body.dry_run, version, cost: { lookup: body.lookup ? 1 : 0, openalex: status === "to_check" || status === "checked" ? 1 : 0 },
        requests: body.dry_run ? 0 : (body.lookup ? 1 : 0) + (status === "checked" ? 1 : 0), seeds: rows, total: rows.length, read: read.length, not_read: rows.length - read.length,
        use_every_concept: read.filter((r) => !r.missed).length, missed: read.filter((r) => r.missed).length,
        warning: level ? { level, untested } : null,
        databases: [{ name: "openalex", status, found: status === "checked" ? dois.slice(0, -1) : [], not_found: status === "checked" ? dois.slice(-1) : [] }],
        others: "not_checked_here", checked_at: now(), measure: "words",
      },
    };
  };

  const report = (id: string, body: Json): Answer => {
    const set = sets.find((s) => s.id === id);
    if (!set) return refuse(404, "WORKBENCH_COMPARISON_NOT_FOUND");
    const version = body.version as Version;
    const measure = String(body.measure ?? "words");
    const records = set.records as { title: string; doi: string | null; abstract?: string | null }[];
    if (measure === "harvest") return refuse(409, "WORKBENCH_COMPARISON_MEASURE", "There is no harvest or accepted corpus to compare with here.");
    const base = { set: { ...set, records: undefined }, measure, version, total: records.length, no_abstract: records.filter((r) => !r.abstract).length, cost: 0, requests: 0, against: null, not_checked: 0, not_in_database: null };
    if (measure === "openalex" && !options.openalexIds) return { status: 200, body: { ...base, status: "switch_off", missing: [], missing_count: null, page: 1, pages: 0, terms: [] } };
    const text = (r: { title: string; abstract?: string | null }) => `${r.title} ${r.abstract ?? ""}`;
    const missing = records.filter((r) => !version.concepts.every((c) => termsOf(c).some((t) => has(text(r), t))));
    const page = Math.max(1, Number(body.page ?? 1));
    const pages = Math.max(1, Math.ceil(missing.length / 20));
    const shown = missing.slice((page - 1) * 20, page * 20).map((r) => ({ title: r.title, doi: r.doi, year: null, no_abstract: !r.abstract, lacks: version.concepts.filter((c) => !termsOf(c).some((t) => has(text(r), t))).map((c) => c.concept) }));
    const counts = new Map<string, number>();
    for (const r of missing) for (const w of new Set(words(text(r)))) counts.set(w, (counts.get(w) ?? 0) + 1);
    const terms = [...counts.entries()].filter(([w, n]) => n >= 2 && !version.concepts.some((c) => termsOf(c).some((t) => words(t).includes(w)))).slice(0, 15).map(([term, n]) => ({ term, records: n, of: missing.length }));
    return { status: 200, body: { ...base, status: "measured", missing_count: missing.length, page, pages, missing: shown, terms } };
  };

  /** Answer a workbench path (the part after `…/workbench`), or `null` when it is not one. */
  const handle = (method: string, sub: string, body: Json | null, saved: string[] = []): Answer | null => {
    if (method === "POST" && sub === "/counts") return counts(body ?? {}, "counts");
    if (method === "POST" && sub === "/synonyms") return counts(body ?? {}, "synonyms");
    if (method === "POST" && sub === "/removed") {
      if (body?.dry_run) return { status: 200, body: { dry_run: true, database: "openalex", concept_index: body.concept_index, concept: "", string: "openalex:…", cost: 1, requests: 0, status: "to_read", resets_at: null, read: 0, records: [] } };
      const version = body?.version as Version;
      return { status: 200, body: { dry_run: false, database: "openalex", concept_index: body?.concept_index, concept: version.concepts[Number(body?.concept_index)].concept, string: "openalex:…", cost: 1, requests: 1, status: "read", resets_at: null, read: 25, records: options.removed ?? [] } };
    }
    if (method === "POST" && sub === "/seeds") return seeds(body ?? {}, saved);
    if (method === "GET" && sub === "/comparison") return { status: 200, body: { sets: sets.map((s) => ({ ...s, records: undefined })) } };
    if (method === "POST" && sub === "/comparison") {
      if (sets.length >= 5) return refuse(409, "WORKBENCH_COMPARISON_FULL");
      let text = "";
      try {
        text = atob(String(body?.content_base64 ?? ""));
      } catch {
        return refuse(422, "WORKBENCH_COMPARISON_FORMAT");
      }
      const records = text.split(/\nER {2}-.*\n?/).map((block) => ({
        title: (block.match(/TI {2}- (.*)/) ?? [])[1] ?? "",
        doi: (block.match(/DO {2}- (.*)/) ?? [])[1] ?? null,
        abstract: (block.match(/AB {2}- (.*)/) ?? [])[1] ?? null,
      })).filter((r) => r.title);
      if (!records.length) return refuse(422, "WORKBENCH_COMPARISON_FORMAT");
      if (records.length > 5000) return refuse(422, "WORKBENCH_COMPARISON_TOO_LARGE");
      const id = `cmp_${String(sets.length + 1).padStart(3, "0")}`;
      const set = { id, database: body?.database, string: body?.string ?? null, exported_on: body?.exported_on ?? "2026-11-21", staged_at: now(), file_name: body?.file_name, format: "ris", records_count: records.length, no_abstract: records.filter((r) => !r.abstract).length, with_doi: records.filter((r) => r.doi).length, records };
      sets.push(set);
      return { status: 201, body: { ...set, records: undefined } };
    }
    const remove = sub.match(/^\/comparison\/(cmp_\d{3})\/remove$/);
    if (method === "POST" && remove) {
      const at = sets.findIndex((s) => s.id === remove[1]);
      if (at < 0) return refuse(404, "WORKBENCH_COMPARISON_NOT_FOUND");
      sets.splice(at, 1);
      return { status: 200, body: { sets: sets.map((s) => ({ ...s, records: undefined })) } };
    }
    const rep = sub.match(/^\/comparison\/(cmp_\d{3})\/report$/);
    if (method === "POST" && rep) return report(rep[1], body ?? {});
    return null;
  };

  return { handle, counted, sets, options };
}

export const WORKBENCH_NAMES = NAMES;
