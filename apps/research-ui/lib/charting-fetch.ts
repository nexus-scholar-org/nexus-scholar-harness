import type { ChartingCopyKey } from "./charting-copy";
import type { DiscardReason, DiscardedFetch, FetchRun, LastLookup, ManifestRequest, ManifestRow, PendingFetch } from "./charting-api";
import { fileSize } from "./charting-logic";

/**
 * The words of a look-up of open-access copies (M12a Part F, spec 03). The
 * engine and the kit record what happened in short codes and English phrases
 * (`ACQUIRED`, `HTTP 403`, `timed out`, `doi found`); this file maps them to
 * the screen's own words, so the kit's text is never shown as the words. Every
 * function returns a copy key with its values: the page fills them in its
 * language and keeps hosts, e-mail and names of settings left to right.
 */

export type Values = Record<string, string | number>;
export type Phrase = { key: ChartingCopyKey; values?: Values };
export type Words = (key: ChartingCopyKey, values?: Values) => string;

// ---------------------------------------------------------------- the waiting file

export type Identity = "doi" | "title" | "notFound" | "notChecked";

/** The kit's check of the first two pages (`scholar_pdf/identity.py`): one of four results. */
export function identityOf(words: string | null | undefined): Identity {
  const said = (words ?? "").trim().toLowerCase();
  if (said.startsWith("doi found")) return "doi";
  if (said.startsWith("title found")) return "title";
  if (said.startsWith("not found")) return "notFound";
  return "notChecked";
}

export const IDENTITY_KEY: Record<Identity, ChartingCopyKey> = {
  doi: "charting.fetch.identity.doi",
  title: "charting.fetch.identity.title",
  notFound: "charting.fetch.identity.notFound",
  notChecked: "charting.fetch.identity.notChecked",
};

/** `C` asks first only when the check did not find the paper in the file, or the same bytes wait or sit on another record (question 3). */
export function confirmAsksFirst(pending: PendingFetch): boolean {
  return identityOf(pending.identity) === "notFound" || (pending.duplicate_of ?? []).length > 0;
}

const SERVICE_KEY: Record<string, ChartingCopyKey> = {
  unpaywall: "charting.fetch.service.unpaywall",
  openalex: "charting.fetch.service.openalex",
  arxiv: "charting.fetch.service.arxiv",
};

/** A service's name; one the screen does not know is shown as the engine names it. */
export function serviceWords(t: Words, name: string | null | undefined): string {
  const key = SERVICE_KEY[(name ?? "").trim().toLowerCase()];
  return key ? t(key) : (name ?? "");
}

/** The service a lookup host belongs to, or null when the host is a PDF host. */
export function serviceOfHost(host: string | null | undefined): string | null {
  const h = (host ?? "").toLowerCase();
  if (h.endsWith("unpaywall.org")) return "unpaywall";
  if (h.endsWith("openalex.org")) return "openalex";
  if (h === "export.arxiv.org") return "arxiv";
  return null;
}

/** The copy's version as words: published, accepted, submitted, an arXiv preprint with its number, or not given. */
export function versionPhrase(copy: { version?: string | null; version_label?: string | null; provider?: string | null; source?: string | null }): Phrase {
  const label = copy.version_label ?? "";
  const arxiv = /arxiv\s+v(\d+)/i.exec(label);
  if (arxiv) return { key: "charting.fetch.version.arxiv", values: { n: arxiv[1] } };
  switch ((copy.version ?? "").trim()) {
    case "publishedVersion":
      return { key: "charting.fetch.version.published" };
    case "acceptedVersion":
      return { key: "charting.fetch.version.accepted" };
    case "submittedVersion":
      return { key: "charting.fetch.version.submitted" };
    default:
      return { key: "charting.fetch.version.unknown" };
  }
}

/** The engine's words for an arXiv copy whose answer names no licence (`fetch.py`, `ARXIV_NO_LICENCE`). */
const NO_LICENCE = new Set(["", "arxiv; licence not given"]);

/** The licence as given, or null when none is given (then the screen says "Licence not given"). */
export function licenceOf(licence: string | null | undefined): string | null {
  const text = (licence ?? "").trim();
  return NO_LICENCE.has(text.toLowerCase()) ? null : text;
}

// ---------------------------------------------------------------- discard

export const DISCARD_REASONS: readonly DiscardReason[] = ["wrong_paper", "not_full_text", "unreadable", "other"];

export const DISCARD_KEY: Record<DiscardReason, ChartingCopyKey> = {
  wrong_paper: "charting.fetch.discard.reason.wrong",
  not_full_text: "charting.fetch.discard.reason.notFull",
  unreadable: "charting.fetch.discard.reason.unreadable",
  other: "charting.fetch.discard.reason.other",
};

const DISCARD_DONE_KEY: Record<Exclude<DiscardReason, "other">, ChartingCopyKey> = {
  wrong_paper: "charting.fetch.discard.doneReason.wrong",
  not_full_text: "charting.fetch.discard.doneReason.notFull",
  unreadable: "charting.fetch.discard.doneReason.unreadable",
};

/** "Discarded: wrong paper", or the researcher's own words for Other. */
export function discardedWords(t: Words, discarded: DiscardedFetch): string | null {
  if (!discarded.reason) return null;
  const reason = discarded.reason === "other" ? (discarded.reason_text ?? "").trim() : t(DISCARD_DONE_KEY[discarded.reason]);
  return reason ? t("charting.fetch.discard.done", { reason }) : null;
}

// ---------------------------------------------------------------- errors, checks and answers

export type ErrorClass = "refused" | "notFound" | "gone" | "tryLater" | "server" | "connection" | "timeout" | "certificate" | "tooLarge" | "redirects" | "lookupAny" | "storage" | "other";

/** The class of one of the kit's short failure words (`fetch_failure`, `check_failure`, the run's error kinds). */
export function errorClass(text: string): { cls: ErrorClass; status?: number } {
  const said = text.trim().toLowerCase();
  const http = /^http (\d{3})/.exec(said);
  if (http) {
    const status = Number(http[1]);
    if (status === 429) return { cls: "tryLater", status };
    if (status === 404) return { cls: "notFound", status };
    if (status === 410) return { cls: "gone", status };
    if (status >= 500) return { cls: "server", status };
    return { cls: "refused", status };
  }
  if (said.includes("certificate")) return { cls: "certificate" };
  if (said.startsWith("timed out") || said.includes("timeout")) return { cls: "timeout" };
  if (said.startsWith("network error")) return { cls: "connection" };
  if (said.includes("over the limit")) return { cls: "tooLarge" };
  if (said.includes("too many redirects")) return { cls: "redirects" };
  if (said.startsWith("lookup failed")) return { cls: "lookupAny" };
  if (said.includes("manifest not written") || said.includes("could not be stored")) return { cls: "storage" };
  return { cls: "other" };
}

const ERROR_KEY: Record<ErrorClass, ChartingCopyKey> = {
  refused: "charting.fetch.error.refused",
  notFound: "charting.fetch.error.notFound",
  gone: "charting.fetch.error.gone",
  tryLater: "charting.fetch.error.tryLater",
  server: "charting.fetch.error.server",
  connection: "charting.fetch.error.connection",
  timeout: "charting.fetch.error.timeout",
  certificate: "charting.fetch.error.certificate",
  tooLarge: "charting.fetch.error.tooLarge",
  redirects: "charting.fetch.error.redirects",
  lookupAny: "charting.fetch.error.lookupAny",
  storage: "charting.fetch.error.storage",
  other: "charting.fetch.error.other",
};

/** The run's errors by kind as lines with their numbers, the largest first ("3 × the host refused (HTTP 403)"). */
export function errorPhrases(errors: Record<string, number> | undefined, n: (value: number) => string): Phrase[] {
  const grouped = new Map<string, { cls: ErrorClass; status?: number; count: number }>();
  for (const [kind, count] of Object.entries(errors ?? {})) {
    if (!count) continue;
    const { cls, status } = errorClass(kind);
    const id = `${cls}:${status ?? ""}`;
    const was = grouped.get(id);
    grouped.set(id, { cls, status, count: (was?.count ?? 0) + count });
  }
  return [...grouped.values()]
    .sort((a, b) => b.count - a.count)
    .map((g) => ({ key: ERROR_KEY[g.cls], values: { n: n(g.count), status: g.status ?? "" } }));
}

/** A failed check's words from the kit's failure text (`validator.check_failure`, the size limit, the redirects). */
export function checkFromText(text: string | null | undefined): ChartingCopyKey | null {
  const said = (text ?? "").toLowerCase();
  if (!said) return null;
  if (said.includes("not a complete pdf") || said.includes("pypdf") || said.includes("could not be read")) return "charting.fetch.check.structure";
  if (said.includes("not a pdf")) return "charting.fetch.check.notPdf";
  if (said.includes("size floor")) return "charting.fetch.check.tooSmall";
  if (said.includes("over the limit")) return "charting.fetch.check.tooLarge";
  if (said.includes("too many redirects")) return "charting.fetch.check.redirects";
  return null;
}

/** The checks a manifest row names (`validator.pdf_checks`, the size limit), by the words of a failure. */
const CHECK_NAME_KEY: Record<string, ChartingCopyKey> = {
  pdf_header: "charting.fetch.check.notPdf",
  pdf_trailer: "charting.fetch.check.structure",
  size_floor: "charting.fetch.check.tooSmall",
  size_limit: "charting.fetch.check.tooLarge",
  structure: "charting.fetch.check.structure",
  readable: "charting.fetch.check.structure",
};

/** The first failed check of a manifest row, as a copy key; null when none failed. */
export function failedCheck(row: ManifestRow): ChartingCopyKey | null {
  for (const [name, result] of Object.entries(row.checks ?? {})) {
    if (name !== "identity" && result === "fail") return CHECK_NAME_KEY[name] ?? "charting.fetch.check.structure";
  }
  return null;
}

const ANSWER_KEY: Partial<Record<ErrorClass, ChartingCopyKey>> = {
  refused: "charting.fetch.answer.refused",
  notFound: "charting.fetch.answer.notFound",
  gone: "charting.fetch.answer.gone",
  tryLater: "charting.fetch.answer.tryLater",
  server: "charting.fetch.answer.server",
  connection: "charting.fetch.answer.connection",
  timeout: "charting.fetch.answer.timeout",
  certificate: "charting.fetch.answer.certificate",
  tooLarge: "charting.fetch.answer.tooLarge",
  redirects: "charting.fetch.answer.redirects",
};

/** What one failure text means for one address, as words ("HTTP 403: the host refused", "the file failed the checks: …"). */
function failureWords(t: Words, text: string): string {
  const check = checkFromText(text);
  if (check && check !== "charting.fetch.check.redirects" && check !== "charting.fetch.check.tooLarge") {
    return t("charting.fetch.answer.checkFailed", { check: t(check) });
  }
  const { cls, status } = errorClass(text);
  const key = ANSWER_KEY[cls];
  return key ? t(key, { status: status ?? "" }) : t("charting.fetch.answer.other");
}

/** What one address answered, from its manifest request ("a PDF, 1.2 MB", "HTTP 403: the host refused · redirected 2 times"). */
export function requestAnswer(t: Words, request: ManifestRequest, row: ManifestRow): string {
  const stored = row.outcome === "ACQUIRED" && request.url === row.address && !request.error;
  let words: string;
  if (stored) words = row.size ? t("charting.fetch.answer.pdf", { size: fileSize(row.size) }) : t("charting.fetch.answer.pdfPlain");
  else if (request.error) words = failureWords(t, request.error);
  else if (request.http_status) words = t("charting.fetch.answer.status", { status: request.http_status });
  else words = t("charting.fetch.answer.other");
  const hops = request.redirects?.length ?? 0;
  return hops > 0 ? `${words} · ${t("charting.fetch.answer.redirected", { n: hops })}` : words;
}

/** One of the run's last requests (`FetchAttempt.answer`: "stored", the failure, or the status) as words. */
export function recentAnswer(t: Words, answer: string): string {
  const said = answer.trim();
  if (said === "stored") return t("charting.fetch.answer.pdfPlain");
  if (said === "answered") return t("charting.fetch.tried.serviceAnswer.answered");
  if (/^HTTP \d{3}$/.test(said)) {
    const status = Number(said.slice(5));
    return status < 400 ? t("charting.fetch.answer.status", { status }) : failureWords(t, said);
  }
  return failureWords(t, said);
}

// ---------------------------------------------------------------- one record

/** The last look-up of a row as words ("no open copy listed"), or null when there is nothing to say (a file was found). */
export function outcomePhrase(t: Words, last: LastLookup): Phrase | null {
  if (last.same_as_discarded) return { key: "charting.fetch.outcome.sameAsDiscarded" };
  switch (last.outcome) {
    case "ACQUIRED":
      return null;
    case "NO_OPEN_COPY_LISTED":
      return { key: "charting.fetch.outcome.noCopy" };
    case "OPEN_NO_DIRECT_PDF":
      return { key: "charting.fetch.outcome.noPdf" };
    case "LOOKUP_FAILED":
      return { key: "charting.fetch.outcome.lookupFailed" };
    case "SKIPPED_NO_ID":
      return { key: "charting.fetch.outcome.skipped" };
    case "PDF_NOT_FETCHED": {
      if (last.try_later) return { key: "charting.fetch.outcome.lookupFailed" };
      const check = checkFromText(last.message);
      return check ? { key: "charting.fetch.outcome.checkFailed", values: { check: t(check) } } : { key: "charting.fetch.outcome.downloadFailed" };
    }
    default:
      return { key: "charting.fetch.outcome.downloadFailed" };
  }
}

/** Each service asked for this record and what it answered ("Unpaywall: no open copy listed"). */
export function servicePhrases(t: Words, row: ManifestRow): { service: string; answer: string }[] {
  const provider = (row.provider ?? "").toLowerCase();
  return (row.lookups ?? []).map((lookup) => {
    const name = (lookup.service ?? "").toLowerCase();
    let answer: string;
    if (lookup.state === "NOT_ASKED") answer = t("charting.fetch.tried.serviceAnswer.notAsked", { why: t("charting.fetch.tried.notAskedKey") });
    else if (lookup.state === "FAILED") {
      const why = lookup.http_status ? t("charting.fetch.answer.status", { status: lookup.http_status }) : t("charting.fetch.answer.connection");
      answer = t("charting.fetch.tried.serviceAnswer.failed", { why });
    } else if (lookup.state === "NOT_FOUND") answer = t("charting.fetch.tried.serviceAnswer.none");
    else if (name && name === provider) {
      answer = name === "arxiv" && row.arxiv_version
        ? t("charting.fetch.tried.serviceAnswer.found", { version: row.arxiv_version })
        : t("charting.fetch.tried.serviceAnswer.open");
    } else if (row.outcome === "NO_OPEN_COPY_LISTED") answer = t("charting.fetch.tried.serviceAnswer.none");
    else if (row.outcome === "OPEN_NO_DIRECT_PDF" && !provider) answer = t("charting.fetch.tried.serviceAnswer.open");
    else answer = t("charting.fetch.tried.serviceAnswer.answered");
    return { service: serviceWords(t, lookup.service), answer };
  });
}

/** Each address tried, at most three, in the order asked; the copy's version and licence go with its own address. */
export function addressPhrases(t: Words, row: ManifestRow): Phrase[] {
  const last = new Map<string, ManifestRequest>();
  for (const request of row.requests ?? []) last.set(request.url, request);
  return [...last.values()].slice(0, 3).map((request): Phrase => {
    const answer = requestAnswer(t, request, row);
    if (request.url !== row.address) return { key: "charting.fetch.tried.addressShort", values: { host: request.host, answer } };
    const version = versionPhrase(row);
    const licence = licenceOf(row.license);
    return {
      key: "charting.fetch.tried.address",
      values: { host: request.host, version: t(version.key, version.values), licence: licence ? t("charting.fetch.licence", { licence }) : t("charting.fetch.licenceNone"), answer },
    };
  });
}

/** The row's checks as one list: each failed check by its words (or "every file check passed"), then the identity result. */
export function checksWords(t: Words, row: ManifestRow): string | null {
  const named = Object.entries(row.checks ?? {}).filter(([name]) => name !== "identity");
  const parts: string[] = [];
  if (named.length) {
    const failed = named.filter(([, result]) => result === "fail").map(([name]) => t(CHECK_NAME_KEY[name] ?? "charting.fetch.check.structure"));
    parts.push(...(failed.length ? [...new Set(failed)] : [t("charting.fetch.check.allPassed")]));
  }
  if (row.checks?.identity) parts.push(t(IDENTITY_KEY[identityOf(row.checks.identity)]));
  return parts.length ? t("charting.fetch.tried.checks", { list: parts.join(", ") }) : null;
}

/** Whether PubMed Central (its NCBI host) was asked for the PDF and gave none (spec 03, "What was tried"). */
export function pmcGaveNoPdf(row: ManifestRow): boolean {
  return (row.requests ?? []).some((request) => {
    const host = (request.host ?? "").toLowerCase();
    const pmc = host.includes("ncbi.nlm.nih.gov") || /(^|\.)pmc\./.test(host);
    const stored = row.outcome === "ACQUIRED" && request.url === row.address && !request.error;
    return pmc && !stored;
  });
}

// ---------------------------------------------------------------- the run

export const ACTIVE_STATES = new Set(["running", "cancelling"]);
export const ENDED_STATES = new Set(["finished", "cancelled", "failed"]);

/** What the run does now, as a phrase ("Asking Unpaywall", "Downloading from europepmc.org"), or null. */
export function nowPhrase(t: Words, run: FetchRun): Phrase | null {
  const now = run.now;
  if (!now || !now.host) return null;
  if (now.phase === "asking") {
    const service = serviceOfHost(now.host);
    return { key: "charting.fetch.run.now.lookup", values: { service: service ? serviceWords(t, service) : now.host } };
  }
  if (now.phase === "downloading") return { key: "charting.fetch.run.now.download", values: { host: now.host } };
  if (now.phase === "waiting") return { key: "charting.fetch.run.now.wait", values: { s: Math.max(1, Math.round(now.seconds ?? 0)), host: now.host } };
  return null;
}

/** The sum of the run's errors (the counts line and the summary's "errors"). */
export function errorCount(run: FetchRun): number {
  return Object.values(run.errors ?? {}).reduce((sum, count) => sum + (count || 0), 0);
}

/** How many records a run reached, as the live region announces it: once every 25 records. */
export const ANNOUNCE_EVERY = 25;

/** Whether OpenAlex was left out of a run (its key not set). */
export function openalexNotAsked(run: FetchRun): boolean {
  return run.openalex_key_set === false || (Array.isArray(run.providers) && !run.providers.includes("openalex"));
}
