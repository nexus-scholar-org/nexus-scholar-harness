"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DecisionBadge, Hint } from "@/components/ui/base";
import { refusalOf, type Refusal } from "@/components/inception-frame";
import { discoveryT } from "@/lib/discovery-copy";
import type { ConceptReport } from "@/lib/recon-api";
import {
  getSets, postCounts, postRemoved, postReport, postSeeds, postSynonyms, removeSet, stageSet,
  type Cell, type ComparisonSet, type CountsAnswer, type DatabaseRow, type Place, type RemovedAnswer, type ReportAnswer,
  type SeedsAnswer, type Version, type VersionConcept,
} from "@/lib/workbench-api";
import { workbenchT, type WorkbenchCopyKey } from "@/lib/workbench-copy";

/**
 * The query workbench (M11a part C; `docs/ux/phase0-inception/final/10-query-workbench.md`).
 *
 * The concepts block (edit concepts and terms, merge, split; AND between
 * concepts, OR inside) and the evidence column (counts per database and with
 * each concept left out, the size line, the known papers, comparison sets).
 * Edits live in the tab until "Use this version" (Inception) or the caller's
 * own action (Plan, part D). Nothing is sent on a keystroke: the dry call
 * that states the cost goes out when an edit is committed (Enter, Add, a
 * button, leaving the name field); a request to a database only on Count,
 * "What does each synonym add?", "Read what this concept removes", a seed
 * lookup or an OpenAlex check, each after its cost was shown. Every number,
 * gain, ratio, state and string printed is a field of an engine answer.
 */

const DATABASE_NAMES: Record<string, string> = {
  openalex: "OpenAlex", semanticscholar: "Semantic Scholar", crossref: "Crossref", arxiv: "arXiv", pubmed: "PubMed", biorxiv: "bioRxiv",
};
const nameOf = (id: string) => DATABASE_NAMES[id] ?? id;
const MAX_SEEDS = 25;
const SUGGESTIONS_SHOWN = 5;

export type Suggestion = { term: string; source: "pool" | "comparison" | "seed"; concept: number | null; evidence: string; database?: string };

/** What "Use this version" hands the page: the concepts, the seeds and the engine suggestions taken (M10b `accepted_from`). */
export type WorkbenchUse = {
  concepts: VersionConcept[];
  seeds: string[];
  accepted: { mechanism: "pool_synonym" | "suggested_concept"; field: string; value: string }[];
};

/** A concept as the tab holds it: with a stable id for its row (never sent to the engine). */
type Held = VersionConcept & { _id: number };
let NEXT_ID = 1;
const hold = (c: VersionConcept): Held => ({ concept: c.concept, synonyms: [...(c.synonyms ?? [])], _id: NEXT_ID++ });
const bare = (c: Held): VersionConcept => ({ concept: c.concept, synonyms: c.synonyms });

const versionKey = (concepts: VersionConcept[]) => JSON.stringify(concepts.map((c) => [c.concept.trim(), c.synonyms]));
const termsOf = (c: VersionConcept) => [c.concept, ...c.synonyms].filter((t) => t.trim());
const termTotal = (concepts: VersionConcept[]) => concepts.reduce((n, c) => n + termsOf(c).length, 0);
const OFFLINE = new Set(["ENGINE_UNREACHABLE", "CONSOLE_UNREACHABLE"]);

function hhmm(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

function dayOf(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "";
}

export function QueryWorkbench({
  locale,
  origin,
  place,
  saved,
  startYear,
  endYear,
  languages,
  seeds: savedSeeds,
  providers,
  pool,
  editableSeeds,
  primary,
  onDirty,
  onCounted,
  onUse,
  using,
  topicConcepts,
  bindUse,
}: Readonly<{
  locale: Locale;
  origin: string;
  place: Place;
  /** The concepts last used (the draft's, or the protocol's on Plan). */
  saved: VersionConcept[];
  startYear?: number | null;
  endYear?: number | null;
  languages?: string[];
  seeds: string[];
  /** The databases to count (Explore's ticked list, or Plan's choice); the engine's default when absent. */
  providers?: string[] | null;
  /** The first search's per-concept counts and suggestions, when a pool exists (Inception only). */
  pool?: ConceptReport | null;
  /** Inception: a known paper can be added by DOI (decision 2026-11-21, item 2). */
  editableSeeds?: boolean;
  /** The caller's own primary action (Plan, part D); Inception uses "Use this version". */
  primary?: (state: { version: Version; changed: boolean }) => ReactNode;
  onDirty?: (dirty: boolean) => void;
  onCounted?: () => void;
  onUse?: (use: WorkbenchUse) => Promise<boolean>;
  using?: boolean;
  /** Inception: the engine's concepts for the topic (`default_concepts`), offered as drafts. */
  topicConcepts?: string[];
  /** The page's "Use it" in its leave prompt runs the same use. */
  bindUse?: (use: () => Promise<boolean>) => void;
}>) {
  const t = workbenchT(locale);
  const dt = discoveryT(locale);
  const [concepts, setConcepts] = useState<Held[]>(() => saved.map(hold));
  const [seeds, setSeeds] = useState<string[]>(savedSeeds);
  const [usedKey, setUsedKey] = useState(() => versionKey(saved));
  const [poolTerms, setPoolTerms] = useState<{ concept: string; term: string }[]>([]);
  const [topicTaken, setTopicTaken] = useState<string[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [mergeName, setMergeName] = useState<string | null>(null);
  const [dry, setDry] = useState<CountsAnswer | null>(null);
  const [answer, setAnswer] = useState<CountsAnswer | null>(null);
  const [answerKey, setAnswerKey] = useState<string | null>(null);
  const [prior, setPrior] = useState<{ answer: CountsAnswer; key: string } | null>(null);
  const [counting, setCounting] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [offline, setOffline] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [usedNote, setUsedNote] = useState(false);

  const version: Version = useMemo(
    () => ({ query_key: "main", concepts: concepts.filter((c) => c.concept.trim()).map(bare), start_year: startYear ?? null, end_year: endYear ?? null, languages: languages ?? ["en"] }),
    [concepts, startYear, endYear, languages],
  );
  const key = versionKey(version.concepts);
  const savedKey = versionKey(saved);
  useEffect(() => {
    // The saved search moved (an assistant's proposal applied, another save): an untouched workbench follows it.
    if (savedKey === usedKey) return;
    if (key === usedKey) {
      setConcepts(saved.map(hold));
      commit();
    }
    setUsedKey(savedKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedKey]);
  const changed = key !== usedKey || seeds.join("|") !== savedSeeds.join("|");
  const stale = answer !== null && answerKey !== key;
  useEffect(() => onDirty?.(changed), [changed, onDirty]);

  const fail = useCallback((error: unknown) => {
    const r = refusalOf(error);
    if (OFFLINE.has(r.code)) setOffline(true);
    else setRefusal(r);
  }, []);

  // The dry call: re-read after every committed edit (never on a keystroke); it sends nothing.
  const [committed, setCommitted] = useState(0);
  const commit = () => setCommitted((n) => n + 1);
  const providersKey = (providers ?? []).join(",");
  useEffect(() => {
    if (!version.concepts.length) return setDry(null);
    const controller = new AbortController();
    postCounts(origin, place, { version, providers: providers ?? undefined, dry_run: true }, controller.signal).then(
      (read) => {
        setDry(read);
        setOffline(false);
      },
      (error) => {
        if (!controller.signal.aborted) fail(error);
      },
    );
    return () => controller.abort();
    // `committed` is the trigger: the dry call follows committed edits only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [committed, origin, providersKey]);

  /** Focus an element of the region once it is drawn (the spec's focus moves after Merge, Split, Remove, Apply). */
  const focusSoon = (selector: string) => {
    if (typeof window === "undefined") return;
    window.setTimeout(() => (document.querySelector(selector) as HTMLElement | null)?.focus(), 0);
  };

  const edit = (next: Held[]) => {
    // A change of the concept list's indices clears the merge selection (review C2: a stale index crashed Merge).
    if (next.length !== concepts.length) {
      setSelected([]);
      setMergeName(null);
    }
    setConcepts(next);
    setUsedNote(false);
    commit();
  };

  const count = async (extra: { crossref_anyway?: boolean; providers?: string[] } = {}) => {
    setRefusal(null);
    setCounting(true);
    setAnnounce(dry ? t("workbench.announce.counting", { n: formatNumber(locale, dry.cost.total) }) : t("workbench.counting"));
    try {
      const read = await postCounts(origin, place, { version, providers: extra.providers ?? providers ?? undefined, dry_run: false, crossref_anyway: extra.crossref_anyway });
      if (extra.crossref_anyway && answer && answerKey === key) {
        // "Count anyway" asks Crossref alone; its row joins the answer already shown.
        const row = read.databases.find((r) => r.name === "crossref");
        setAnswer({ ...answer, databases: answer.databases.map((r) => (r.name === "crossref" && row ? row : r)) });
      } else {
        if (answer && answerKey && answerKey !== key) setPrior({ answer, key: answerKey });
        setAnswer(read);
        setAnswerKey(key);
      }
      setOffline(false);
      const summary = read.databases.filter((r) => typeof r.total === "number").map((r) => `${nameOf(r.name)} ${formatNumber(locale, r.total as number)}`).join(", ");
      setAnnounce(t("workbench.announce.counted", { summary }));
      onCounted?.();
      commit();
    } catch (error) {
      fail(error);
      setAnnounce("");
    } finally {
      setCounting(false);
    }
  };

  const use = async (): Promise<boolean> => {
    if (!onUse) return false;
    const accepted: WorkbenchUse["accepted"] = [
      ...poolTerms.map((p) => ({ mechanism: "pool_synonym" as const, field: `concepts[${p.concept}].synonyms`, value: p.term })),
      ...topicTaken.map((word) => ({ mechanism: "suggested_concept" as const, field: "concepts", value: word })),
    ];
    const ok = await onUse({ concepts: version.concepts, seeds, accepted });
    if (ok) {
      setUsedKey(key);
      setPoolTerms([]);
      setTopicTaken([]);
      setUsedNote(true);
    }
    return ok;
  };
  useEffect(() => bindUse?.(use));

  const discard = () => {
    setConcepts(saved.map(hold));
    setSeeds(savedSeeds);
    setPoolTerms([]);
    setTopicTaken([]);
    setSelected([]);
    setMergeName(null);
    commit();
  };

  const addTerm = (index: number, term: string, from?: Suggestion) => {
    const text = term.trim();
    if (!text) return;
    const c = concepts[index];
    if (termsOf(c).some((x) => x.toLowerCase() === text.toLowerCase())) return;
    edit(concepts.map((x, i) => (i === index ? { ...x, synonyms: [...x.synonyms, text] } : x)));
    if (from?.source === "pool") setPoolTerms((list) => [...list, { concept: c.concept.trim(), term: text }]);
    setAnnounce(t("workbench.announce.added", { term: text, concept: c.concept }));
  };

  const removeTerm = (index: number, term: string) => {
    const c = concepts[index];
    if (term === c.concept) {
      const [first, ...rest] = c.synonyms;
      if (first === undefined) return edit(concepts.filter((_, i) => i !== index));
      return edit(concepts.map((x, i) => (i === index ? { ...x, concept: first, synonyms: rest } : x)));
    }
    edit(concepts.map((x, i) => (i === index ? { ...x, synonyms: x.synonyms.filter((s) => s !== term) } : x)));
    focusSoon(`#wb-term-${index}`);
  };

  const splitTerm = (index: number, term: string) => {
    const without = concepts.map((x, i) => (i === index ? { ...x, synonyms: x.synonyms.filter((s) => s !== term) } : x));
    edit([...without, hold({ concept: term, synonyms: [] })]);
    setAnnounce(t("workbench.announce.split", { term }));
    focusSoon(`#wb-concept-${without.length}`);
  };

  const merge = () => {
    if (selected.length !== 2 || mergeName === null) return;
    const [a, b] = [...selected].sort((x, y) => x - y);
    if (!concepts[a] || !concepts[b]) return setSelected([]);
    const terms = [...termsOf(concepts[a]), ...termsOf(concepts[b])];
    const name = mergeName.trim() || concepts[a].concept;
    const rest = terms.filter((x, i) => x.toLowerCase() !== name.toLowerCase() && terms.findIndex((y) => y.toLowerCase() === x.toLowerCase()) === i);
    const merged = { ...concepts[a], concept: name, synonyms: rest };
    edit(concepts.flatMap((c, i) => (i === a ? [merged] : i === b ? [] : [c])));
    setSelected([]);
    setMergeName(null);
    setAnnounce(t("workbench.announce.merged", { name }));
    focusSoon(`#wb-concept-${a}`);
  };

  // Pool suggestions (D5): the first search's co-occurring terms, per concept.
  const poolSuggestions = (index: number): Suggestion[] => {
    if (!pool) return [];
    const row = pool.concepts.find((r) => r.source === "draft" && r.concept === concepts[index].concept.trim());
    const have = new Set(termsOf(concepts[index]).map((x) => x.toLowerCase()));
    return (row?.suggestions ?? [])
      .filter((s) => !have.has(s.term.toLowerCase()) && !rejected.includes(`pool:${concepts[index].concept}:${s.term}`))
      .map((s) => ({ term: s.term, source: "pool", concept: index, evidence: t("workbench.suggest.evidence.pool", { term: s.term, n: formatNumber(locale, s.observed_in) }) }));
  };

  const primaryKind = changed ? "use" : "count";
  const onRegionKey = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" && event.ctrlKey) {
      event.preventDefault();
      if (primaryKind === "use" && onUse) void use();
      else if (version.concepts.length && !counting) void count();
    }
  };

  const costLine = (() => {
    if (!version.concepts.length) return t("workbench.needConcept");
    if (!dry) return t("workbench.cost.reading");
    if (dry.cost.total === 0) return t("workbench.cost.cached");
    const parts = Object.entries(dry.cost.by_database).filter(([, n]) => n > 0).map(([db, n]) => t("workbench.cost.part", { database: nameOf(db), n: formatNumber(locale, n) })).join(", ");
    return t("workbench.cost", { n: formatNumber(locale, dry.cost.total), parts });
  })();

  return (
    <section aria-labelledby="workbench-title" className="rounded-lg border border-rule bg-leaf p-4" data-workbench onKeyDown={onRegionKey}>
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 id="workbench-title" className="font-semibold text-ink">
          {t("workbench.title")}
        </h2>
        <span className="text-xs text-ink-muted" data-query-key>
          {t("workbench.queryKey", { key: "main" })}
        </span>
        <Hint locale={locale} label={t("workbench.title")} text={t("workbench.keys")} textKey="workbench.keys" />
        <span className="text-xs text-ink-muted" data-written>
          {t("workbench.written", { n: formatNumber(locale, version.concepts.length), t: formatNumber(locale, termTotal(version.concepts)) })}
        </span>
      </div>
      <div className="mt-3 grid gap-4 xl:grid-cols-12">
        {/* The concepts block (direction A's block). */}
        <div className="min-w-0 space-y-3 xl:col-span-5" data-concepts-block>
          {concepts.length === 0 ? <p className="text-sm text-ink-muted" data-no-concepts>{t("workbench.needConcept")}</p> : null}
          {(topicConcepts ?? []).filter((w) => !concepts.some((c) => c.concept.trim().toLowerCase() === w.toLowerCase())).length ? (
            <div className="rounded-md border border-dashed border-ink-muted p-2" data-topic-concepts>
              <p className="text-xs font-semibold text-ink-muted">{t("workbench.suggest.label", { source: t("workbench.suggest.source.topic") })}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {(topicConcepts ?? [])
                  .filter((w) => !concepts.some((c) => c.concept.trim().toLowerCase() === w.toLowerCase()))
                  .map((word) => (
                    <Button
                      key={word}
                      variant="secondary"
                      className="border-dashed"
                      onClick={() => {
                        edit([...concepts, hold({ concept: word, synonyms: [] })]);
                        setTopicTaken((list) => [...list, word]);
                      }}
                      data-topic-concept={word}
                    >
                      {t("workbench.topic.add", { word })}
                    </Button>
                  ))}
              </div>
            </div>
          ) : null}
          <ol className="space-y-3">
            {concepts.map((c, index) => (
              <li key={c._id} data-concept-row={index}>
                {index > 0 ? (
                  <p className="mb-2 text-xs font-semibold text-ink-muted" data-op="and">
                    {t("workbench.op.and")}
                  </p>
                ) : null}
                <ConceptRow
                  locale={locale}
                  index={index}
                  concept={c}
                  note={answer && !stale ? (answer.notes ?? []).find((n) => n.concept_index === index) ?? null : null}
                  selected={selected.includes(index)}
                  onSelect={(on) => setSelected((list) => (on ? [...list, index].slice(-2) : list.filter((i) => i !== index)))}
                  onRename={(name) => edit(concepts.map((x, i) => (i === index ? { ...x, concept: name } : x)))}
                  onAddTerm={(term) => addTerm(index, term)}
                  onRemoveTerm={(term) => removeTerm(index, term)}
                  onSplit={(term) => splitTerm(index, term)}
                  onRemove={() => edit(concepts.filter((_, i) => i !== index))}
                  suggestions={poolSuggestions(index)}
                  onApply={(s) => addTerm(index, s.term, s)}
                  onReject={(s) => setRejected((list) => [...list, `pool:${c.concept}:${s.term}`])}
                  pool={pool ?? null}
                />
              </li>
            ))}
          </ol>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => edit([...concepts, hold({ concept: t("workbench.concept.newName"), synonyms: [] })])} data-add-concept>
              {t("workbench.concept.add")}
            </Button>
            <Button onClick={() => setMergeName(concepts[Math.min(...selected)]?.concept ?? "")} disabled={selected.length !== 2} data-merge>
              {t("workbench.concept.merge")}
            </Button>
          </div>
          {mergeName !== null ? (
            <div className="flex flex-wrap items-end gap-2" data-merge-form>
              <div>
                <label htmlFor="workbench-merge-name" className="block text-xs text-ink-muted">
                  {t("workbench.concept.mergeName")}
                </label>
                {/* A concept's name is also searched (the protocol's first term), so the merged name is one of its terms. */}
                <select
                  id="workbench-merge-name"
                  value={mergeName}
                  autoFocus
                  onChange={(event) => setMergeName(event.target.value)}
                  className="mt-1 block min-h-11 max-w-full rounded-md border border-rule bg-paper px-2 text-ink"
                >
                  {selected
                    .slice()
                    .sort((x, y) => x - y)
                    .flatMap((i) => termsOf(concepts[i]))
                    .map((term, i) => (
                      <option key={`${i}:${term}`} value={term}>
                        {term}
                      </option>
                    ))}
                </select>
                <Hint locale={locale} label={t("workbench.concept.mergeName")} text={t("workbench.concept.mergeNameHelp")} textKey="workbench.concept.mergeNameHelp" />
              </div>
              <Button onClick={merge} data-merge-do>
                {t("workbench.concept.mergeDo")}
              </Button>
              <Button variant="quiet" onClick={() => setMergeName(null)}>
                {t("workbench.concept.cancel")}
              </Button>
            </div>
          ) : null}
          <p className="text-sm text-ink" data-cost aria-live="off">
            {costLine}
          </p>
          {providers?.length ? (
            <p className="text-xs text-ink-muted" data-databases>
              {t("workbench.databases", { names: providers.map(nameOf).join(", ") })}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2" data-decision-bar>
            {/* One brand button per screen: on Inception it is "Use this version" while edits are unused, else the page's own;
                on Plan (no "Use"), Count is the region's primary action until the caller's own action takes over. */}
            <Button
              variant={!onUse && !changed ? "primary" : "secondary"}
              onClick={() => void count()}
              disabled={counting || offline || !version.concepts.length}
              data-count
            >
              {counting ? t("workbench.counting") : t("workbench.count")}
            </Button>
            {onUse ? (
              <Button variant={primaryKind === "use" ? "primary" : "secondary"} onClick={() => void use()} disabled={!changed || using || offline || !version.concepts.length} data-use>
                {t("workbench.use")}
              </Button>
            ) : null}
            {primary ? primary({ version, changed }) : null}
            <Button variant="quiet" onClick={discard} disabled={!changed} data-discard>
              {t("workbench.discard")}
            </Button>
          </div>
          {offline ? (
            <p className="text-sm text-unclear" data-offline>
              {t("workbench.offline")}
              {answer ? ` · ${t("workbench.asOf", { time: `${hhmm(answer.databases.find((r) => r.counted_at)?.counted_at ?? null)} UTC` })}` : ""}{" "}
              <Button variant="quiet" className="px-0" onClick={commit} data-offline-retry>
                {t("workbench.err.checkAgain")}
              </Button>
            </p>
          ) : null}
          {usedNote && !changed ? (
            <p role="status" className="text-sm text-ink" data-used>
              {t("workbench.used")}
            </p>
          ) : null}
          {changed ? (
            <p className="text-xs text-ink-muted" data-unused>
              {t("workbench.unused")}
            </p>
          ) : null}
          {refusal ? <WorkbenchRefusal locale={locale} refusal={refusal} onRetry={() => setRefusal(null)} /> : null}
          <p className="sr-only" role="status" aria-live="polite" data-announce>
            {announce}
          </p>
        </div>

        {/* The evidence column. */}
        <div className="min-w-0 space-y-3 xl:col-span-7" data-evidence>
          <CountsSection
            locale={locale}
            origin={origin}
            place={place}
            version={version}
            answer={answer}
            prior={prior}
            stale={stale}
            counting={counting}
            providers={providers ?? null}
            onCountAnyway={() => void count({ crossref_anyway: true, providers: ["crossref"] })}
            dt={dt}
            offline={offline}
            refresh={committed}
          />
          <SeedsSection
            locale={locale}
            origin={origin}
            place={place}
            version={version}
            seeds={seeds}
            editable={!!editableSeeds}
            refresh={committed}
            onAdd={(doi) => setSeeds((list) => (list.length >= MAX_SEEDS || list.includes(doi) ? list : [...list, doi]))}
            onApply={(index, term) => addTerm(index, term)}
            onFail={fail}
            offline={offline}
          />
          <ComparisonSection locale={locale} origin={origin} place={place} version={version} onApply={(index, term) => addTerm(index, term)} onFail={fail} offline={offline} />
          {answer?.external ? <ExternalStrings locale={locale} strings={answer.external} /> : dry?.external ? <ExternalStrings locale={locale} strings={dry.external} /> : null}
        </div>
      </div>
    </section>
  );
}

/** One concept: its name, its terms as wrapping chips (OR), its actions and its suggestions. */
function ConceptRow({
  locale, index, concept, note, selected, onSelect, onRename, onAddTerm, onRemoveTerm, onSplit, onRemove, suggestions, onApply, onReject, pool,
}: Readonly<{
  locale: Locale;
  index: number;
  concept: VersionConcept;
  note: { concept: string; database: string; total: number; without: number } | null;
  selected: boolean;
  onSelect: (on: boolean) => void;
  onRename: (name: string) => void;
  onAddTerm: (term: string) => void;
  onRemoveTerm: (term: string) => void;
  onSplit: (term: string) => void;
  onRemove: () => void;
  suggestions: Suggestion[];
  onApply: (s: Suggestion) => void;
  onReject: (s: Suggestion) => void;
  pool: ConceptReport | null;
}>) {
  const t = workbenchT(locale);
  const [name, setName] = useState(concept.concept);
  const [term, setTerm] = useState("");
  const [all, setAll] = useState(false);
  useEffect(() => setName(concept.concept), [concept.concept]);
  const terms = termsOf(concept);
  const poolRow = pool?.concepts.find((r) => r.source === "draft" && r.concept === concept.concept.trim());
  const shown = all ? suggestions : suggestions.slice(0, SUGGESTIONS_SHOWN);
  return (
    <div className="rounded-md border border-rule bg-paper p-3" data-concept={index}>
      <div className="flex flex-wrap items-end gap-2">
        <div className="w-full min-w-0">
          <label htmlFor={`wb-concept-${index}`} className="block text-xs text-ink-muted">
            {t("workbench.concept.label", { n: formatNumber(locale, index + 1) })}
          </label>
          <input
            id={`wb-concept-${index}`}
            value={name}
            dir="auto"
            onChange={(event) => setName(event.target.value)}
            onBlur={() => name.trim() && name !== concept.concept && onRename(name.trim())}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                if (name.trim() && name !== concept.concept) onRename(name.trim());
              }
              if (event.key === "Escape") setName(concept.concept);
            }}
            className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
          />
        </div>
        <label className="flex min-h-11 cursor-pointer items-center gap-2 text-xs text-ink">
          <input type="checkbox" checked={selected} onChange={(event) => onSelect(event.target.checked)} className="h-5 w-5" data-select={index} />
          <span>{t("workbench.concept.select", { concept: concept.concept })}</span>
        </label>
        <Button variant="quiet" onClick={onRemove} data-remove-concept={index}>
          {t("workbench.concept.remove")}
        </Button>
      </div>
      <ul className="mt-2 flex flex-wrap items-center gap-1" data-chips={index}>
        {terms.map((x, i) => {
          const observed = poolRow?.terms.find((p) => p.term === x)?.observed_in;
          return (
            <li key={x} className="flex flex-wrap items-center gap-1" data-chip={x}>
              {i > 0 ? (
                <span className="text-xs text-ink-muted" data-op="or">
                  {t("workbench.op.or")}
                </span>
              ) : null}
              <span className="inline-flex flex-wrap items-center gap-x-1 rounded-sm border border-rule ps-2 text-sm">
                <bdi dir="auto" className="text-ink">
                  {x}
                </bdi>
                {pool && observed !== undefined ? (
                  observed === 0 ? (
                    <DecisionBadge role="unclear">{t("workbench.pool.none")}</DecisionBadge>
                  ) : (
                    <span className="text-xs text-ink-muted" data-in-pool>
                      {t("workbench.term.inPool", { n: formatNumber(locale, observed), m: formatNumber(locale, pool.n_docs) })}
                    </span>
                  )
                ) : null}
                <Button variant="quiet" className="min-h-11 px-1 text-xs" onClick={() => onRemoveTerm(x)} aria-label={t("workbench.term.remove", { term: x })}>
                  ×
                </Button>
                {i > 0 ? (
                  <>
                    <Button variant="quiet" className="min-h-11 px-1 text-xs" onClick={() => onSplit(x)} aria-describedby={`wb-split-${index}-${i}`} data-split={x}>
                      {t("workbench.term.splitShort")}
                    </Button>
                    <span id={`wb-split-${index}-${i}`} className="sr-only">
                      {t("workbench.term.split", { term: x })}
                    </span>
                  </>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
      <div className="mt-2 flex items-end gap-2">
        <div className="min-w-0 flex-1">
          <label htmlFor={`wb-term-${index}`} className="block text-xs text-ink-muted">
            {t("workbench.term.add")}
          </label>
          <input
            id={`wb-term-${index}`}
            value={term}
            dir="auto"
            onChange={(event) => setTerm(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                onAddTerm(term);
                setTerm("");
              }
            }}
            className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
          />
        </div>
        <Button
          onClick={() => {
            onAddTerm(term);
            setTerm("");
          }}
          disabled={!term.trim()}
          data-add-term={index}
        >
          {t("workbench.term.addButton")}
        </Button>
      </div>
      {note ? (
        <p className="mt-2 text-sm text-unclear" data-note={index}>
          {t("workbench.note", { concept: note.concept, database: nameOf(note.database), n: formatNumber(locale, note.without), m: formatNumber(locale, note.total) })}
        </p>
      ) : null}
      {suggestions.length ? (
        <SuggestionList
          locale={locale}
          label={t("workbench.suggest.label", { source: t("workbench.suggest.source.pool") })}
          items={shown}
          onApply={onApply}
          onReject={onReject}
          more={suggestions.length > SUGGESTIONS_SHOWN && !all ? () => setAll(true) : undefined}
          total={suggestions.length}
        />
      ) : null}
    </div>
  );
}

/** D5 suggestions: dashed, "Suggested by … · not yet yours", Apply and Reject per term, keys J/K/A/R on a focused row. */
function SuggestionList({
  locale, label, items, onApply, onReject, more, total, concepts,
}: Readonly<{
  locale: Locale;
  label: string;
  items: Suggestion[];
  onApply: (s: Suggestion, concept?: number) => void;
  onReject: (s: Suggestion) => void;
  more?: () => void;
  total: number;
  /** When the term has no concept yet (a comparison term), the researcher chooses one. */
  concepts?: VersionConcept[];
}>) {
  const t = workbenchT(locale);
  const list = useRef<HTMLUListElement>(null);
  const [choice, setChoice] = useState<Record<string, number>>({});
  const move = (event: KeyboardEvent<HTMLLIElement>, s: Suggestion) => {
    const target = event.target as HTMLElement;
    if (["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)) return;
    const rows = [...(list.current?.querySelectorAll<HTMLElement>("[data-suggestion-row]") ?? [])];
    const at = rows.indexOf(event.currentTarget);
    if (event.key === "j" || event.key === "J") rows[Math.min(rows.length - 1, at + 1)]?.focus();
    else if (event.key === "k" || event.key === "K") rows[Math.max(0, at - 1)]?.focus();
    else if (event.key === "a" || event.key === "A") {
      apply(s);
      next(at);
    } else if (event.key === "r" || event.key === "R") {
      onReject(s);
      next(at);
    }
    else return;
    event.preventDefault();
  };
  /** After Apply or Reject the list redraws; focus goes to the row now at the same place, or the list's label. */
  const next = (at: number) =>
    window.setTimeout(() => {
      const rows = [...(list.current?.querySelectorAll<HTMLElement>("[data-suggestion-row]") ?? [])];
      (rows[Math.min(at, rows.length - 1)] ?? list.current?.parentElement?.querySelector<HTMLElement>("p"))?.focus();
    }, 0);
  const apply = (s: Suggestion) => {
    const concept = s.concept ?? choice[s.term];
    if (concept === undefined) return;
    onApply(s, concept);
  };
  return (
    <div className="mt-2 rounded-md border border-dashed border-ink-muted p-2" data-suggestions>
      <p className="text-xs font-semibold text-ink-muted">{label}</p>
      <ul ref={list} className="mt-1 space-y-1">
        {items.map((s) => (
          <li key={`${s.source}:${s.term}`} tabIndex={0} onKeyDown={(event) => move(event, s)} className="flex flex-wrap items-center gap-2 rounded-sm focus-visible:outline-2 focus-visible:outline-focus" data-suggestion-row={s.term}>
            <bdi dir="auto" className="text-sm text-ink">
              {s.evidence}
            </bdi>
            {s.concept === null && concepts ? (
              <span className="flex items-center gap-1">
                <label className="text-xs text-ink-muted" htmlFor={`wb-as-${s.source}-${s.term}`}>
                  {t("workbench.suggest.addAs")}
                </label>
                <select
                  id={`wb-as-${s.source}-${s.term}`}
                  value={choice[s.term] ?? ""}
                  onChange={(event) => setChoice((c) => ({ ...c, [s.term]: Number(event.target.value) }))}
                  className="min-h-11 rounded-md border border-rule bg-paper px-1 text-sm text-ink"
                >
                  <option value="">{t("workbench.suggest.chooseConcept")}</option>
                  {concepts.map((c, i) => (
                    <option key={i} value={i}>
                      {c.concept}
                    </option>
                  ))}
                </select>
              </span>
            ) : null}
            <Button onClick={() => apply(s)} disabled={s.concept === null && choice[s.term] === undefined} data-apply={s.term}>
              {t("workbench.suggest.apply")}
            </Button>
            <Button variant="quiet" onClick={() => onReject(s)} data-reject={s.term}>
              {t("workbench.suggest.reject")}
            </Button>
          </li>
        ))}
      </ul>
      {more ? (
        <Button variant="quiet" className="px-0" onClick={more}>
          {t("workbench.suggest.more", { n: formatNumber(locale, total) })}
        </Button>
      ) : null}
    </div>
  );
}

/** The words of a row's state, from the engine's fields. */
function rowWords(locale: Locale, row: DatabaseRow, stale: boolean, budget?: { limit: number; renews_at: string } | null): { text: string; role: "include" | "unclear" | "exclude" | "blocked" } {
  const t = workbenchT(locale);
  const n = (v: number | null) => (v === null ? "" : formatNumber(locale, v));
  const db = nameOf(row.name);
  const when = (iso: string | null) => {
    if (!iso) return "";
    return dayOf(iso) === new Date().toISOString().slice(0, 10) ? t("workbench.today", { time: hhmm(iso) }) : t("workbench.onDay", { day: dayOf(iso), time: hhmm(iso) });
  };
  const left = row.resets_in ? t("workbench.span", { h: formatNumber(locale, row.resets_in.hours), m: formatNumber(locale, row.resets_in.minutes) }) : "";
  if (stale && typeof row.total === "number") return { text: t("workbench.row.stale", { n: n(row.total) }), role: "unclear" };
  switch (row.status) {
    case "counted":
      if (row.any_words) return { text: t("workbench.row.crossrefCounted", { n: n(row.total) }), role: "unclear" };
      if (row.upper_bound) return { text: t("workbench.row.upperBound", { n: n(row.total) }), role: "unclear" };
      return { text: t("workbench.row.counted", { n: n(row.total), time: hhmm(row.counted_at) }), role: "include" };
    case "cached":
      if (row.any_words) return { text: t("workbench.row.crossrefCounted", { n: n(row.total) }), role: "unclear" };
      return { text: t("workbench.row.cached", { n: n(row.total), when: when(row.counted_at) }), role: "include" };
    case "quota_used_up":
      return row.last
        ? { text: t("workbench.row.quota", { database: db, time: hhmm(row.resets_at), left, n: n(row.last.total), when: when(row.last.counted_at) }), role: "blocked" }
        : { text: t("workbench.row.quota.none", { database: db, time: hhmm(row.resets_at), left }), role: "blocked" };
    case "budget_spent":
      return { text: t("workbench.row.budget", { database: db, n: formatNumber(locale, budget?.limit ?? 0), time: hhmm(budget?.renews_at ?? null) }), role: "blocked" };
    case "rate_limited":
      return { text: t("workbench.row.busy", { database: db }), role: "blocked" };
    case "refused":
      return { text: t("workbench.row.refused", { database: db, status: String(row.http_status ?? "") }), role: "blocked" };
    case "unavailable":
      return { text: t("workbench.row.unavailable", { database: db }), role: "blocked" };
    case "timeout":
      return row.timeout_seconds
        ? { text: t("workbench.row.timeout", { database: db, seconds: formatNumber(locale, row.timeout_seconds) }), role: "blocked" }
        : { text: t("workbench.row.unavailable", { database: db }), role: "blocked" };
    case "key_missing":
      return { text: t("workbench.row.keyMissing"), role: "blocked" };
    case "not_comparable":
      return { text: t("workbench.row.crossref"), role: "unclear" };
    case "not_countable":
      return { text: t("workbench.row.notCountable"), role: "exclude" };
    case "not_asked":
      return { text: t("workbench.row.notAsked"), role: "exclude" };
    case "to_count":
      return { text: t("workbench.row.toCount"), role: "exclude" };
    default:
      return { text: t("workbench.row.failed", { database: db }), role: "blocked" };
  }
}

function cellText(locale: Locale, cell: Cell): string {
  const t = workbenchT(locale);
  if (typeof cell.total !== "number") return t("workbench.cell.state", { state: t(stateKey(cell.status)) });
  if (typeof cell.gain !== "number") return formatNumber(locale, cell.total);
  const values = { count: formatNumber(locale, cell.total), gain: formatNumber(locale, cell.gain) };
  return typeof cell.ratio === "number" ? t("workbench.cell.gain", { ...values, ratio: formatNumber(locale, cell.ratio) }) : t("workbench.cell.gainNoRatio", values);
}

function stateKey(status: string): WorkbenchCopyKey {
  const known = ["rate_limited", "refused", "unavailable", "timeout", "quota_used_up", "budget_spent", "key_missing", "not_countable", "to_count"];
  return (known.includes(status) ? `workbench.state.${status}` : "workbench.state.failed") as WorkbenchCopyKey;
}

function CountsSection({
  locale, origin, place, version, answer, prior, stale, counting, providers, onCountAnyway, dt, offline, refresh,
}: Readonly<{
  locale: Locale;
  origin: string;
  place: Place;
  version: Version;
  answer: CountsAnswer | null;
  prior: { answer: CountsAnswer; key: string } | null;
  stale: boolean;
  counting: boolean;
  providers: string[] | null;
  onCountAnyway: () => void;
  dt: ReturnType<typeof discoveryT>;
  offline: boolean;
  refresh: number;
}>) {
  const t = workbenchT(locale);
  const concepts = answer?.version.concepts ?? version.concepts;
  const rows = answer?.databases ?? [];
  const budgets = Object.entries(answer?.budget ?? {}).filter(([, b]) => b?.low);
  return (
    <details open className="rounded-md border border-rule bg-paper p-3" data-section="counts">
      <summary className="min-h-11 cursor-pointer py-2 font-semibold text-ink rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("workbench.section.counts")}</summary>
      {counting ? (
        <p role="status" aria-busy="true" className="text-sm text-ink-muted" data-counting>
          {t("workbench.row.counting")}
        </p>
      ) : null}
      {!answer ? (
        <p className="text-sm text-ink-muted" data-counts-empty>
          {t("workbench.empty")}
        </p>
      ) : (
        <div data-stale={stale ? "true" : undefined}>
          {/* No dimming: at opacity-80 the muted and "unclear" words fell below 4.5:1 in light (axe, M11a part D). The badge and the row words say the counts are for the previous version. */}
          {stale ? <DecisionBadge role="unclear">{t("workbench.badge.previous")}</DecisionBadge> : null}
          {concepts.length === 1 ? (
            <p className="mt-1 text-sm text-ink-muted" data-one-concept>
              {t("workbench.oneConcept")}
            </p>
          ) : null}
          {/* Narrow windows (mobile layout): one card per database, the same words. */}
          <ul className="mt-2 space-y-2 sm:hidden" data-counts-cards>
            {rows.map((row) => {
              const words = rowWords(locale, row, stale, answer.budget?.[row.name] ?? null);
              const drops = concepts.length > 1 && !row.any_words ? row.drops ?? [] : [];
              return (
                <li key={row.name} className="rounded-sm border border-rule p-2 text-sm" data-card={row.name}>
                  <p className="font-medium text-ink" dir="ltr">
                    {nameOf(row.name)}
                  </p>
                  <p className={words.role === "blocked" ? "text-blocked" : words.role === "unclear" ? "text-unclear" : "text-ink"}>
                    <bdi dir="auto">{words.text}</bdi>
                  </p>
                  {drops.map((cell) => (
                    <p key={cell.concept_index ?? 0} className="text-ink">
                      <bdi dir="auto">{t("workbench.col.without", { concept: cell.concept ?? "" })}</bdi>: {cellText(locale, cell)}
                      {cell.largest ? <span className="ms-1 text-xs font-semibold">{t("workbench.largest")}</span> : null}
                    </p>
                  ))}
                  {row.status === "not_comparable" && !stale ? (
                    <Button className="mt-1" onClick={onCountAnyway}>
                      {t("workbench.crossref.anyway")}
                    </Button>
                  ) : null}
                  {row.string ? (
                    <details className="mt-1 text-xs">
                      <summary className="min-h-11 cursor-pointer py-3 text-ink-muted rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("workbench.string.show")}</summary>
                      <code dir="ltr" className="block whitespace-pre-wrap break-all select-all text-ink">
                        {row.string}
                      </code>
                    </details>
                  ) : null}
                </li>
              );
            })}
          </ul>
          <div className="mt-2 hidden max-w-full overflow-x-auto sm:block" data-counts-scroll>
            <table className="min-w-full text-sm" data-counts>
              <caption className="sr-only">{t("workbench.caption")}</caption>
              <thead>
                <tr>
                  <th scope="col" className="sticky start-0 bg-paper p-2 text-start">
                    {t("workbench.col.database")}
                  </th>
                  <th scope="col" className="p-2 text-start">
                    {t("workbench.col.query")}
                  </th>
                  {concepts.length > 1
                    ? concepts.map((c, i) => (
                        <th key={i} scope="col" className="p-2 text-start">
                          <bdi dir="auto">{t("workbench.col.without", { concept: c.concept })}</bdi>
                        </th>
                      ))
                    : null}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const words = rowWords(locale, row, stale, answer.budget?.[row.name] ?? null);
                  const drops = row.drops ?? [];
                  const showDrops = concepts.length > 1 && drops.length > 0 && !row.any_words;
                  return (
                    <tr key={row.name} data-row={row.name} data-status={row.status} className="border-t border-rule align-top">
                      <th scope="row" className="sticky start-0 bg-paper p-2 text-start font-medium" dir="ltr">
                        {nameOf(row.name)}
                      </th>
                      <td className="p-2" data-cell="query" colSpan={row.status === "not_comparable" || row.any_words ? 1 + (concepts.length > 1 ? concepts.length : 0) : 1}>
                        <span className={`block ${words.role === "blocked" ? "text-blocked" : words.role === "unclear" ? "text-unclear" : "text-ink"}`}>
                          <bdi dir="auto">{words.text}</bdi>
                        </span>
                        {row.status === "not_comparable" && !stale ? (
                          <Button className="mt-1" onClick={onCountAnyway} data-count-anyway>
                            {t("workbench.crossref.anyway")}
                          </Button>
                        ) : null}
                        {row.stopped ? (
                          <span className="mt-1 block text-xs text-unclear" data-stopped>
                            {t("workbench.row.stopped", { state: t(stateKey(row.stopped.status)) })}
                          </span>
                        ) : null}
                        {row.error_code && words.role === "blocked" ? (
                          <span className="block font-mono text-xs text-ink-muted" dir="ltr">
                            {row.error_code}
                          </span>
                        ) : null}
                        {row.string ? (
                          <details className="mt-1 text-xs">
                            <summary className="min-h-11 cursor-pointer py-3 text-ink-muted rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("workbench.string.show")}</summary>
                            <code dir="ltr" className="block whitespace-pre-wrap break-all select-all text-ink" data-string>
                              {row.string}
                            </code>
                          </details>
                        ) : null}
                      </td>
                      {concepts.length > 1 && !(row.status === "not_comparable" || row.any_words)
                        ? concepts.map((_, i) => {
                            const cell = drops.find((d) => d.concept_index === i);
                            return (
                              <td key={i} className="p-2" data-cell={`drop-${i}`}>
                                {showDrops && cell ? (
                                  <>
                                    <span className="block text-ink" aria-label={typeof cell.total === "number" && typeof cell.gain === "number" && typeof cell.ratio === "number" ? t("workbench.cell.gainSpoken", { count: formatNumber(locale, cell.total), gain: formatNumber(locale, cell.gain), ratio: formatNumber(locale, cell.ratio) }) : undefined}>
                                      {cellText(locale, cell)}
                                    </span>
                                    {cell.largest ? (
                                      <span className="text-xs font-semibold text-ink" data-largest>
                                        {t("workbench.largest")}
                                      </span>
                                    ) : null}
                                  </>
                                ) : null}
                              </td>
                            );
                          })
                        : null}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {budgets.map(([name, b]) =>
            b ? (
              <p key={name} className="mt-1 text-xs text-ink-muted" data-budget-low={name}>
                {t("workbench.budget.low", { database: nameOf(name), n: formatNumber(locale, b.left), m: formatNumber(locale, b.limit) })}
              </p>
            ) : null,
          )}
          {answer.size ? <SizeLine locale={locale} size={answer.size} rows={rows} dt={dt} /> : null}
        </div>
      )}
      <Versions locale={locale} answer={answer} prior={prior} stale={stale} version={version} />
      {answer && !stale && version.concepts.length ? (
        <ConceptTools locale={locale} origin={origin} place={place} version={version} providers={providers} offline={offline} refresh={refresh} />
      ) : null}
    </details>
  );
}

function SizeLine({ locale, size, rows, dt }: Readonly<{ locale: Locale; size: NonNullable<CountsAnswer["size"]>; rows: DatabaseRow[]; dt: ReturnType<typeof discoveryT> }>) {
  const n = (v: number | null) => (v === null ? "" : formatNumber(locale, v));
  const records = size.estimate.records;
  const works = size.estimate.works;
  const hours = size.effort.hours;
  const failed = rows.filter((r) => !["counted", "cached", "not_comparable", "not_asked"].includes(r.status) && !r.any_words).map((r) => nameOf(r.name));
  const warn = size.warn;
  return (
    <div className="mt-3 space-y-1 text-sm text-ink" data-size-line>
      <p>{records.high === null ? dt("estimate.records.atLeast", { low: n(records.low) }) : dt("estimate.records", { high: n(records.high) })}</p>
      <p>{works.high === null ? dt("estimate.works.atLeast", { low: n(works.low) }) : dt("estimate.works", { low: n(works.low), high: n(works.high) })}</p>
      <p>
        {hours.high === null ? dt("estimate.effort.atLeast", { low: n(hours.low) }) : dt("estimate.effort", { low: n(hours.low), high: n(hours.high) })}{" "}
        <span className="text-ink-muted">{dt("estimate.effort.basis", { pace: n(size.effort.pace_seconds) })}</span>
      </p>
      {warn.level === "warning" ? <p className="text-unclear" data-size-warn>{dt("estimate.warn.warning", { low: n(works.low), threshold: n(warn.threshold_works) })}</p> : null}
      {warn.level === "note" && works.high !== null ? <p className="text-unclear" data-size-warn>{dt("estimate.warn.note", { high: n(works.high), threshold: n(warn.threshold_works) })}</p> : null}
      {warn.level === "note" && works.high === null && failed.length ? <p className="text-unclear" data-size-warn>{dt("estimate.warn.unbounded", { names: failed.join(", ") })}</p> : null}
    </div>
  );
}

function Versions({ locale, answer, prior, stale, version }: Readonly<{ locale: Locale; answer: CountsAnswer | null; prior: { answer: CountsAnswer; key: string } | null; stale: boolean; version: Version }>) {
  const t = workbenchT(locale);
  if (!answer || (!stale && !prior)) return null;
  const left = stale ? answer : prior!.answer;
  const right = stale ? null : answer;
  const label = (a: CountsAnswer | null, v: Version) =>
    a
      ? t("workbench.versions.label", { n: formatNumber(locale, a.concepts), t: formatNumber(locale, a.terms), time: hhmm(a.databases.find((r) => r.counted_at)?.counted_at ?? null) })
      : t("workbench.versions.notCounted", { n: formatNumber(locale, v.concepts.length), t: formatNumber(locale, termTotal(v.concepts)) });
  const totals = (a: CountsAnswer | null) =>
    (a?.databases ?? []).filter((r) => typeof r.total === "number" && !r.any_words).map((r) => (
      <li key={r.name} dir="ltr">
        {nameOf(r.name)} {formatNumber(locale, r.total as number)}
      </li>
    ));
  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2" data-versions>
      <div role="group" aria-labelledby="wb-versions-last" className="rounded-md border border-rule p-2" data-version="last">
        <p id="wb-versions-last" className="text-xs font-semibold text-ink">
          {t("workbench.versions.last")}
        </p>
        <p className="text-xs text-ink-muted">{label(left, left.version)}</p>
        <ul className="text-sm">{totals(left)}</ul>
      </div>
      <div role="group" aria-labelledby="wb-versions-now" className="rounded-md border border-rule p-2" data-version="now">
        <p id="wb-versions-now" className="text-xs font-semibold text-ink">
          {t("workbench.versions.now")}
        </p>
        <p className="text-xs text-ink-muted">{label(right, version)}</p>
        <ul className="text-sm">{totals(right)}</ul>
      </div>
    </div>
  );
}

/** "What does each synonym add?" and "Read what this concept removes", on one concept at a time. */
function ConceptTools({ locale, origin, place, version, providers, offline, refresh }: Readonly<{ locale: Locale; origin: string; place: Place; version: Version; providers: string[] | null; offline: boolean; refresh: number }>) {
  const t = workbenchT(locale);
  const [index, setIndex] = useState(0);
  const [database, setDatabase] = useState("openalex");
  const [synDry, setSynDry] = useState<CountsAnswer | null>(null);
  const [syn, setSyn] = useState<CountsAnswer | null>(null);
  const [removed, setRemoved] = useState<RemovedAnswer | null>(null);
  const [removedDry, setRemovedDry] = useState<RemovedAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Refusal | null>(null);
  const [costError, setCostError] = useState<Refusal | null>(null);
  const [retry, setRetry] = useState(0);
  const names = (providers?.length ? providers : ["openalex", "semanticscholar", "arxiv"]).filter((n) => n !== "crossref");
  const concept = version.concepts[Math.min(index, version.concepts.length - 1)];
  const toolsKey = `${index}|${JSON.stringify(version.concepts)}`;
  useEffect(() => {
    if (version.concepts.length < 2) return setRemovedDry(null);
    const controller = new AbortController();
    postRemoved(origin, place, { version, concept_index: index, dry_run: true }, controller.signal).then(
      (read) => {
        setRemovedDry(read);
        setCostError(null);
      },
      (e) => {
        if (controller.signal.aborted) return;
        setRemovedDry(null);
        setCostError(refusalOf(e));
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toolsKey, origin, refresh, retry]);
  const run = async <T,>(fn: () => Promise<T>, done: (v: T) => void) => {
    setBusy(true);
    setError(null);
    try {
      done(await fn());
    } catch (e) {
      setError(refusalOf(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="mt-3 space-y-2 border-t border-rule pt-3" data-concept-tools>
      <div className="flex flex-wrap items-end gap-2">
        <div>
          <label htmlFor="wb-tools-concept" className="block text-xs text-ink-muted">
            {t("workbench.tools.concept")}
          </label>
          <select id="wb-tools-concept" value={index} onChange={(e) => { setIndex(Number(e.target.value)); setSynDry(null); setSyn(null); setRemoved(null); }} className="mt-1 min-h-11 max-w-full rounded-md border border-rule bg-paper px-2 text-ink">
            {version.concepts.map((c, i) => (
              <option key={i} value={i}>
                {c.concept}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="wb-tools-db" className="block text-xs text-ink-muted">
            {t("workbench.syn.database")}
          </label>
          <select id="wb-tools-db" value={database} onChange={(e) => { setDatabase(e.target.value); setSynDry(null); }} className="mt-1 min-h-11 rounded-md border border-rule bg-paper px-2 text-ink">
            {names.map((n) => (
              <option key={n} value={n}>
                {nameOf(n)}
              </option>
            ))}
          </select>
        </div>
        <Button
          disabled={busy || offline}
          onClick={() => void run(() => postSynonyms(origin, place, { version, concept_index: index, provider: database, dry_run: true }), setSynDry)}
          aria-describedby="wb-tools-concept"
          data-syn
        >
          {t("workbench.syn.button")}
        </Button>
        {version.concepts.length > 1 ? (
          <Button disabled={busy || offline || !removedDry} onClick={() => void run(() => postRemoved(origin, place, { version, concept_index: index, dry_run: false }), setRemoved)} data-removed>
            {t("workbench.removed.button")}
            {removedDry ? ` (${t("workbench.removed.cost", { n: formatNumber(locale, removedDry.cost) })})` : ""}
          </Button>
        ) : null}
      </div>
      {synDry && !syn ? (
        <p className="flex flex-wrap items-center gap-2 text-sm text-ink" data-syn-cost>
          {synDry.cost.total === 0 ? t("workbench.syn.cost.cached") : t("workbench.syn.cost", { n: formatNumber(locale, synDry.cost.total) })}
          <Button disabled={busy || offline} onClick={() => void run(() => postSynonyms(origin, place, { version, concept_index: index, provider: database, dry_run: false }), setSyn)} data-syn-confirm>
            {t("workbench.syn.confirm")}
          </Button>
        </p>
      ) : null}
      {syn ? (
        <div data-syn-result>
          <p className="text-sm font-semibold text-ink">{t("workbench.syn.title", { concept: concept.concept, database: nameOf(database) })}</p>
          <ul className="text-sm">
            {(syn.databases.find((r) => r.name === database)?.synonyms ?? []).map((cell) => (
              <li key={cell.term ?? ""} data-syn-term={cell.term}>
                <bdi dir="auto">
                  {cell.adds_nothing
                    ? `${cell.term}: ${t("workbench.syn.none", { database: nameOf(database) })}`
                    : typeof cell.total === "number" && typeof cell.gain === "number"
                      ? t("workbench.syn.add", { term: cell.term ?? "", count: formatNumber(locale, cell.total), gain: formatNumber(locale, cell.gain) })
                      : `${cell.term}: ${t("workbench.cell.state", { state: t(stateKey(cell.status)) })}`}
                </bdi>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {removed ? (
        <div data-removed-result>
          <p className="text-sm font-semibold text-ink">{t("workbench.removed.title", { concept: removed.concept })}</p>
          {removed.status !== "read" ? (
            <p className="text-sm text-blocked">{t("workbench.cell.state", { state: t(stateKey(removed.status)) })}</p>
          ) : removed.records.length === 0 ? (
            <p className="text-sm text-ink-muted">{t("workbench.removed.none")}</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {removed.records.map((r, i) => (
                <li key={`${r.doi}-${i}`} data-removed-record>
                  <bdi dir="auto" className="text-ink">
                    {r.title}
                  </bdi>{" "}
                  <span className="text-xs text-ink-muted">{t("workbench.removed.absent", { concept: removed.concept })}</span>{" "}
                  {r.doi ? (
                    <a href={`https://doi.org/${r.doi}`} target="_blank" rel="noreferrer" dir="ltr" className="text-xs text-brand underline">
                      {r.doi}
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
      {error ? <WorkbenchRefusal locale={locale} refusal={error} onRetry={() => setError(null)} /> : null}
      {costError ? <WorkbenchRefusal locale={locale} refusal={costError} onRetry={() => setRetry((n) => n + 1)} /> : null}
    </div>
  );
}

function SeedsSection({
  locale, origin, place, version, seeds, editable, onAdd, onApply, onFail, offline, refresh,
}: Readonly<{
  locale: Locale;
  origin: string;
  place: Place;
  version: Version;
  seeds: string[];
  editable: boolean;
  onAdd: (doi: string) => void;
  onApply: (concept: number, term: string) => void;
  onFail: (error: unknown) => void;
  offline: boolean;
  refresh: number;
}>) {
  const t = workbenchT(locale);
  const [check, setCheck] = useState<SeedsAnswer | null>(null);
  const [costs, setCosts] = useState<SeedsAnswer["cost"] | null>(null);
  const [sent, setSent] = useState(0);
  /** The seeds and version the last real check was for (review C round 3). */
  const realKey = useRef<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [doi, setDoi] = useState("");
  const [rejected, setRejected] = useState<string[]>([]);
  const seedKey = seeds.join("|") + JSON.stringify(version.concepts);
  useEffect(() => {
    if (!version.concepts.length) return;
    const controller = new AbortController();
    postSeeds(origin, place, { version, seeds, lookup: true, openalex: true, dry_run: true }, controller.signal).then(
      (read) => {
        setCosts(read.cost);
        // After a real check its answer stays shown; the dry call only renews the costs.
        setCheck((current) => (current && !current.dry_run && realKey.current === seedKey ? current : read));
      },
      (e) => {
        if (!controller.signal.aborted) onFail(e);
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seedKey, origin, refresh, sent]);
  const send = async (opts: { lookup: boolean; openalex: boolean }) => {
    setBusy(true);
    try {
      setCheck(await postSeeds(origin, place, { version, seeds, ...opts, dry_run: false }));
      realKey.current = seedKey;
      setSent((n) => n + 1);
    } catch (e) {
      onFail(e);
    } finally {
      setBusy(false);
    }
  };
  const summary = check && check.read ? t("workbench.seeds.summary", { n: formatNumber(locale, check.use_every_concept), m: formatNumber(locale, check.read) }) : t("workbench.seeds.summary.none");
  const warning = check?.warning;
  const oa = check?.databases.find((d) => d.name === "openalex");
  const seedSuggestions: Suggestion[] = (check?.seeds ?? [])
    .filter((s) => s.missed)
    .flatMap((s) => s.suggestions.map((term) => ({ term, source: "seed" as const, concept: null, evidence: term })))
    .filter((s, i, all) => !rejected.includes(s.term) && all.findIndex((x) => x.term === s.term) === i);
  return (
    <details className="rounded-md border border-rule bg-paper p-3" data-section="seeds">
      <summary className="min-h-11 cursor-pointer py-2 font-semibold text-ink rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
        {t("workbench.seeds.title")} · <span className="font-normal text-ink-muted" data-seeds-summary>{summary}</span>
      </summary>
      {seeds.length === 0 ? <p className="text-sm text-ink-muted">{t("workbench.seeds.none")}</p> : null}
      {warning ? (
        <p role="note" className="mt-2 rounded-md border border-unclear p-2 text-sm text-unclear" data-seeds-warning={warning.level}>
          {warning.level === "all"
            ? t("workbench.seeds.warn.all", { n: formatNumber(locale, check!.read), concept: warning.untested[0] ?? "" })
            : warning.level === "concept"
              ? warning.untested.map((c) => t("workbench.seeds.warn.concept", { concept: c })).join(" ")
              : t("workbench.seeds.warn.few")}
        </p>
      ) : null}
      {check && check.total > 0 && check.read === 0 ? <p className="mt-2 text-sm text-ink-muted">{t("workbench.seeds.notReadAll")}</p> : null}
      <div className="mt-2 flex flex-wrap gap-2">
        {costs && costs.lookup > 0 ? (
          <Button disabled={busy || offline} onClick={() => void send({ lookup: true, openalex: false })} data-seeds-lookup>
            {t("workbench.seeds.lookup", { n: formatNumber(locale, costs.lookup) })}
          </Button>
        ) : null}
        {seeds.length ? (
          <Button disabled={busy || offline || oa?.status === "switch_off"} onClick={() => void send({ lookup: false, openalex: true })} data-seeds-openalex>
            {t("workbench.seeds.check")}
            {costs?.openalex ? ` (${t("workbench.removed.cost", { n: formatNumber(locale, costs.openalex) })})` : ""}
          </Button>
        ) : null}
      </div>
      <ul className="mt-2 space-y-2 text-sm">
        {(check?.seeds ?? []).map((s) => (
          <li key={s.doi} className="rounded-sm border border-rule p-2" data-seed={s.doi} data-missed={s.missed}>
            <bdi dir="auto" className="text-ink">{s.title ?? s.doi}</bdi>
            {!s.read ? (
              <span className="ms-2"><DecisionBadge role="unclear">{t("workbench.seeds.notRead")}</DecisionBadge></span>
            ) : (
              <span className="mt-1 flex flex-wrap gap-2 text-xs">
                {s.concepts.map((c) => (
                  <span key={c.concept} className={c.found ? "text-ink" : "text-unclear"}>
                    <bdi dir="auto">{t(c.found ? "workbench.seeds.found" : "workbench.seeds.lacks", { concept: c.concept })}</bdi>
                  </span>
                ))}
              </span>
            )}
            {s.missed ? (
              <span className="block text-xs text-unclear">
                {t("workbench.seeds.missed")}: {t("workbench.seeds.missed.why", { concept: s.lacks[0] ?? "" })}
              </span>
            ) : null}
            {oa && oa.status === "checked" ? (
              <span className="block text-xs text-ink-muted" dir="ltr">
                {t(oa.found.includes(s.doi) ? "workbench.seeds.db.found" : "workbench.seeds.db.notFound", { database: "OpenAlex" })}
              </span>
            ) : null}
          </li>
        ))}
      </ul>
      {seeds.length ? (
        <p className="mt-2 text-xs text-ink-muted" data-seeds-db>
          {oa?.status === "switch_off" ? t("workbench.seeds.db.switchOff") : null} {t("workbench.seeds.db.notChecked")}
        </p>
      ) : null}
      <Hint locale={locale} label={t("workbench.seeds.title")} text={t("workbench.seeds.measure")} textKey="workbench.seeds.measure" />
      {seedSuggestions.length ? (
        <SuggestionList
          locale={locale}
          label={t("workbench.suggest.label", { source: t("workbench.suggest.source.seed") })}
          items={seedSuggestions}
          concepts={version.concepts}
          onApply={(s, concept) => concept !== undefined && onApply(concept, s.term)}
          onReject={(s) => setRejected((list) => [...list, s.term])}
          total={seedSuggestions.length}
        />
      ) : null}
      {editable ? (
        <div className="mt-2 flex items-end gap-2">
          <div className="min-w-0 flex-1">
            <label htmlFor="wb-seed-doi" className="block text-xs text-ink-muted">
              {t("workbench.seeds.add")}
            </label>
            <input id="wb-seed-doi" value={doi} dir="ltr" onChange={(e) => setDoi(e.target.value)} className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 font-mono text-ink" />
          </div>
          <Button
            disabled={!doi.trim() || seeds.length >= MAX_SEEDS}
            onClick={() => {
              onAdd(doi.trim());
              setDoi("");
            }}
            data-seed-add
          >
            {t("workbench.seeds.addButton")}
          </Button>
        </div>
      ) : null}
      {editable && seeds.length >= MAX_SEEDS ? <p className="text-xs text-ink-muted">{t("workbench.seeds.full")}</p> : null}
    </details>
  );
}

function ComparisonSection({
  locale, origin, place, version, onApply, onFail, offline,
}: Readonly<{ locale: Locale; origin: string; place: Place; version: Version; onApply: (concept: number, term: string) => void; onFail: (error: unknown) => void; offline: boolean }>) {
  const t = workbenchT(locale);
  const [sets, setSets] = useState<ComparisonSet[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [database, setDatabase] = useState("");
  const [string, setString] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<Refusal | null>(null);
  const [reports, setReports] = useState<Record<string, ReportAnswer>>({});
  const [reportKey, setReportKey] = useState<Record<string, string>>({});
  const [measure, setMeasure] = useState<Record<string, string>>({});
  const [rejected, setRejected] = useState<string[]>([]);
  const vKey = JSON.stringify(version.concepts);
  useEffect(() => {
    const controller = new AbortController();
    getSets(origin, place, controller.signal).then((read) => setSets(read.sets), (e) => {
      if (!controller.signal.aborted) onFail(e);
    });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [origin]);
  const stage = async () => {
    if (!file || !database.trim()) return;
    setError(null);
    try {
      const buffer = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (const byte of buffer) binary += String.fromCharCode(byte);
      const added = await stageSet(origin, place, { file_name: file.name, content_base64: btoa(binary), database: database.trim(), string: string.trim() || null, exported_on: date || null });
      setSets((list) => [...list, added]);
      setFile(null);
      setFileKey((n) => n + 1);
      setDatabase("");
      setString("");
    } catch (e) {
      setError(refusalOf(e));
    }
  };
  const report = async (id: string, page = 1) => {
    setError(null);
    try {
      const read = await postReport(origin, place, id, { version, measure: measure[id] ?? "words", page, dry_run: false });
      setReports((r) => ({ ...r, [id]: read }));
      setReportKey((k) => ({ ...k, [id]: vKey }));
    } catch (e) {
      setError(refusalOf(e));
    }
  };
  const errorText = (r: Refusal) =>
    r.code === "WORKBENCH_COMPARISON_FORMAT" ? t("workbench.cmp.err.format") : r.code === "WORKBENCH_COMPARISON_TOO_LARGE" ? t("workbench.cmp.err.size") : r.code === "WORKBENCH_COMPARISON_FULL" ? t("workbench.cmp.err.count") : t("workbench.err.other", { message: r.message || r.code });
  const summary = sets.length
    ? sets.map((s) => (reports[s.id]?.missing_count != null ? t("workbench.cmp.summary", { database: s.database, m: formatNumber(locale, s.records_count), n: formatNumber(locale, reports[s.id].missing_count as number) }) : t("workbench.cmp.summary.staged", { database: s.database, m: formatNumber(locale, s.records_count) }))).join("; ")
    : t("workbench.cmp.summary.none");
  return (
    <details className="rounded-md border border-rule bg-paper p-3" data-section="comparison">
      <summary className="min-h-11 cursor-pointer py-2 font-semibold text-ink rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
        {t("workbench.cmp.title")} · <bdi dir="auto" className="font-normal text-ink-muted" data-cmp-summary>{summary}</bdi>
      </summary>
      {sets.length === 0 ? <p className="text-sm text-ink-muted">{t("workbench.cmp.empty")}</p> : null}
      <ul className="mt-2 space-y-3">
        {sets.map((s) => {
          const r = reports[s.id];
          const terms: Suggestion[] = (r?.terms ?? [])
            .filter((x) => !rejected.includes(`${s.id}:${x.term}`))
            .map((x) => ({ term: x.term, source: "comparison", concept: null, database: s.database, evidence: `${x.term} · ${t("workbench.suggest.evidence.cmp", { n: formatNumber(locale, x.records), m: formatNumber(locale, x.of) })}` }));
          return (
            <li key={s.id} className="rounded-sm border border-rule p-2 text-sm" data-set={s.id}>
              <p className="text-ink">
                <bdi dir="auto">{t("workbench.cmp.staged", { database: s.database, m: formatNumber(locale, s.records_count), date: s.exported_on })}</bdi>
              </p>
              {s.string ? <code dir="ltr" className="block break-all text-xs text-ink-muted">{s.string}</code> : null}
              <div className="mt-2 flex flex-wrap items-end gap-2">
                <div className="min-w-0 max-w-full">
                  <label htmlFor={`wb-measure-${s.id}`} className="block text-xs text-ink-muted">
                    {t("workbench.cmp.measureChoice")}
                  </label>
                  <select id={`wb-measure-${s.id}`} value={measure[s.id] ?? "words"} onChange={(e) => setMeasure((m) => ({ ...m, [s.id]: e.target.value }))} className="mt-1 min-h-11 w-full max-w-full rounded-md border border-rule bg-paper px-2 text-ink">
                    <option value="words">{t("workbench.cmp.measure.words")}</option>
                    <option value="openalex">{t("workbench.cmp.measure.openalex")}</option>
                    {place.kind === "workspace" ? <option value="harvest">{t("workbench.cmp.measure.harvest")}</option> : null}
                  </select>
                </div>
                <Button disabled={offline} onClick={() => void report(s.id)} data-compare={s.id}>
                  {t("workbench.cmp.compare")}
                </Button>
                <Button
                  variant="quiet"
                  onClick={async () => {
                    try {
                      const read = await removeSet(origin, place, s.id);
                      setSets(read.sets);
                    } catch (e) {
                      setError(refusalOf(e));
                    }
                  }}
                  data-remove-set={s.id}
                >
                  {t("workbench.cmp.remove")}
                </Button>
              </div>
              {r ? (
                <div className="mt-2 space-y-1" data-report={s.id}>
                  {reportKey[s.id] !== vKey ? <DecisionBadge role="unclear">{t("workbench.cmp.stale")}</DecisionBadge> : null}
                  <p className="text-xs text-ink-muted" data-measure={r.measure}>
                    {t("workbench.cmp.measure", { name: t(`workbench.cmp.measure.${r.measure}` as WorkbenchCopyKey) })}
                  </p>
                  {r.measure === "words" ? <Hint locale={locale} label={t("workbench.cmp.measureChoice")} text={t("workbench.cmp.measure.words.help")} textKey="workbench.cmp.measure.words.help" /> : null}
                  {r.status === "switch_off" ? <p className="text-sm text-ink-muted">{t("workbench.cmp.measure.openalex.off")}</p> : null}
                  {r.missing_count === null ? null : r.missing_count === 0 ? (
                    <p className="text-ink">{t("workbench.cmp.none", { database: s.database })}</p>
                  ) : (
                    <p className="font-semibold text-ink" data-report-line>
                      <bdi dir="auto">{t("workbench.cmp.report", { n: formatNumber(locale, r.missing_count), m: formatNumber(locale, r.total), database: s.database })}</bdi>
                    </p>
                  )}
                  {r.no_abstract ? <p className="text-xs text-ink-muted">{t("workbench.cmp.noAbstract", { n: formatNumber(locale, r.no_abstract) })}</p> : null}
                  {r.not_checked ? <p className="text-xs text-ink-muted">{t("workbench.cmp.noDoi", { n: formatNumber(locale, r.not_checked) })}</p> : null}
                  {r.not_in_database ? <p className="text-xs text-ink-muted">{t("workbench.cmp.notInDatabase", { n: formatNumber(locale, r.not_in_database) })}</p> : null}
                  {r.missing.length ? (
                    <>
                      <p className="text-xs font-semibold text-ink">{t("workbench.cmp.missing")}</p>
                      <ul className="space-y-1" data-missing>
                        {r.missing.map((m, i) => (
                          <li key={`${m.doi}-${i}`} data-missing-record>
                            <bdi dir="auto" className="text-ink">{m.title}</bdi>{" "}
                            {m.lacks.length ? <span className="text-xs text-unclear"><bdi dir="auto">{t("workbench.cmp.missing.lacks", { concepts: m.lacks.join(", ") })}</bdi></span> : null}{" "}
                            {m.doi ? (
                              <a href={`https://doi.org/${m.doi}`} target="_blank" rel="noreferrer" dir="ltr" className="text-xs text-brand underline">
                                {m.doi}
                              </a>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                      {r.pages > 1 ? (
                        <div className="flex items-center gap-2">
                          <Button disabled={r.page <= 1} onClick={() => void report(s.id, r.page - 1)}>{t("workbench.cmp.prev")}</Button>
                          <span className="text-xs text-ink-muted">{t("workbench.cmp.page", { p: formatNumber(locale, r.page), total: formatNumber(locale, r.pages) })}</span>
                          <Button disabled={r.page >= r.pages} onClick={() => void report(s.id, r.page + 1)}>{t("workbench.cmp.next")}</Button>
                        </div>
                      ) : null}
                    </>
                  ) : null}
                  <p className="text-xs font-semibold text-ink">{t("workbench.cmp.terms")}</p>
                  {terms.length ? (
                    <SuggestionList
                      locale={locale}
                      label={t("workbench.suggest.label", { source: t("workbench.suggest.source.comparison", { database: s.database }) })}
                      items={terms}
                      concepts={version.concepts}
                      onApply={(x, concept) => concept !== undefined && onApply(concept, x.term)}
                      onReject={(x) => setRejected((list) => [...list, `${s.id}:${x.term}`])}
                      total={terms.length}
                    />
                  ) : (
                    <p className="text-xs text-ink-muted">{t("workbench.cmp.terms.none")}</p>
                  )}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
      <fieldset className="mt-3 grid min-w-0 grid-cols-1 gap-2 sm:grid-cols-2" data-cmp-form>
        <legend className="text-sm font-semibold text-ink">{t("workbench.cmp.add")}</legend>
        <div className="sm:col-span-2">
          <label htmlFor="wb-cmp-file" className="block text-xs text-ink-muted">{t("workbench.cmp.file")}</label>
          <input key={fileKey} id="wb-cmp-file" type="file" accept=".ris,.nbib,.txt" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="mt-1 block min-h-11 w-full max-w-full text-sm text-ink" />
        </div>
        <div>
          <label htmlFor="wb-cmp-db" className="block text-xs text-ink-muted">{t("workbench.cmp.database")}</label>
          <input id="wb-cmp-db" list="wb-cmp-db-list" value={database} onChange={(e) => setDatabase(e.target.value)} className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink" />
          <datalist id="wb-cmp-db-list">
            <option value="Scopus" />
            <option value="Web of Science" />
            <option value="IEEE Xplore" />
          </datalist>
        </div>
        <div>
          <label htmlFor="wb-cmp-date" className="block text-xs text-ink-muted">{t("workbench.cmp.date")}</label>
          <input id="wb-cmp-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink" />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="wb-cmp-string" className="block text-xs text-ink-muted">{t("workbench.cmp.string")}</label>
          <textarea id="wb-cmp-string" rows={2} dir="ltr" value={string} onChange={(e) => setString(e.target.value)} className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 font-mono text-xs text-ink" />
        </div>
        <div className="sm:col-span-2">
          <Button onClick={() => void stage()} disabled={offline || !file || !database.trim()} data-cmp-stage>{t("workbench.cmp.stage")}</Button>
        </div>
      </fieldset>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-blocked" data-cmp-error={error.code}>
          {errorText(error)}
        </p>
      ) : null}
    </details>
  );
}

function ExternalStrings({ locale, strings }: Readonly<{ locale: Locale; strings: Record<string, string> }>) {
  const t = workbenchT(locale);
  return (
    <details className="rounded-md border border-rule bg-paper p-3" data-section="external">
      <summary className="min-h-11 cursor-pointer py-2 font-semibold text-ink rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("workbench.external.title")}</summary>
      <p className="text-xs text-unclear">{t("workbench.external.check")}</p>
      {Object.entries(strings).map(([db, text]) => (
        <div key={db} className="mt-2">
          <p className="text-xs font-semibold text-ink" dir="ltr">{db === "wos" ? "Web of Science" : "Scopus"}</p>
          <code dir="ltr" className="block whitespace-pre-wrap break-all select-all text-xs text-ink" data-external={db}>
            {text}
          </code>
        </div>
      ))}
    </details>
  );
}

function WorkbenchRefusal({ locale, refusal, onRetry }: Readonly<{ locale: Locale; refusal: Refusal; onRetry: () => void }>) {
  const t = workbenchT(locale);
  const text =
    refusal.code === "DISCOVERY_JOB_ACTIVE" ? t("workbench.err.jobActive")
      : refusal.code === "MAILTO_NOT_SET" ? t("workbench.err.mailto")
        : refusal.code === "OPENALEX_KEY_NOT_SET" ? t("workbench.err.key")
          : refusal.code === "DRAFT_CONFLICT" ? t("workbench.err.conflict")
            : refusal.code === "WORKBENCH_STATE_UNREADABLE" ? t("workbench.err.state")
              : refusal.code === "WORKBENCH_VERSION_INVALID" ? t("workbench.err.invalid", { error: refusal.message })
                : refusal.code === "WORKBENCH_BUDGET_SPENT" ? t("workbench.err.other", { message: refusal.message })
                  : t("workbench.err.other", { message: refusal.message || refusal.code });
  return (
    <div role="alert" className="rounded-md border border-blocked p-2 text-sm text-ink" data-workbench-refusal={refusal.code}>
      <p>{text}</p>
      {refusal.code === "MAILTO_NOT_SET" ? <code dir="ltr" className="block text-xs">SCHOLAR_MAILTO=&lt;your email&gt;</code> : null}
      {refusal.code === "OPENALEX_KEY_NOT_SET" ? <code dir="ltr" className="block text-xs">SCHOLAR_OPENALEX_KEY=&lt;your key&gt;</code> : null}
      <Button variant="quiet" className="mt-1 px-0" onClick={onRetry}>
        {t("workbench.err.checkAgain")}
      </Button>
      <p className="font-mono text-xs text-ink-muted" dir="ltr">
        {refusal.code}
      </p>
    </div>
  );
}
