"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DataCell } from "@/components/ui/base";
import { inceptionHref, InceptionRefusal, refusalOf, stamp, useLocationParams, type Refusal } from "@/components/inception-frame";
import { createImportedDraft, importDraft, type ImportReport, type ImportSourceRequest } from "@/lib/inception-api";
import { inceptionT } from "@/lib/inception-copy";
import { importLossLines } from "@/lib/inception-import";
import { fileToBase64 } from "@/lib/screening-v1";
import { getWorkspaces, type WorkspaceListing } from "@/lib/workspaces";

/**
 * Start from an existing review (spec 09, M10b). The researcher picks a
 * workspace on this computer or a protocol file; the engine reads it with
 * `dry_run` and answers what comes across, what changes and what they still
 * write. Nothing is stored before "Create the draft from this review", and the
 * source is never written. The browser maps nothing: every line is the engine's.
 */
export function InceptionImport({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const { origin, ready } = useLocationParams();
  const [workspaces, setWorkspaces] = useState<WorkspaceListing | null>(null);
  const [listError, setListError] = useState<Refusal | null>(null);
  const [source, setSource] = useState<ImportSourceRequest | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [reading, setReading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [fileError, setFileError] = useState(false);
  const [fileName, setFileName] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const reportHeading = useRef<HTMLHeadingElement>(null);
  const request = useRef(0);

  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    getWorkspaces(origin, false, controller.signal).then(setWorkspaces, (error) => {
      if (!controller.signal.aborted) setListError(refusalOf(error));
    });
    return () => controller.abort();
  }, [origin, ready]);

  const read = useCallback(
    async (next: ImportSourceRequest) => {
      const mine = ++request.current;
      setSource(next);
      setReport(null);
      setRefusal(null);
      setReading(true);
      try {
        const answer = await importDraft(origin, next);
        if (mine !== request.current) return;
        setReport(answer);
        setTimeout(() => reportHeading.current?.focus(), 0);
      } catch (error) {
        if (mine !== request.current) return;
        setRefusal(refusalOf(error));
        setSource(null);
      } finally {
        if (mine === request.current) setReading(false);
      }
    },
    [origin],
  );

  const pickFile = async (file: File | undefined) => {
    setFileError(false);
    if (!file) return;
    setFileName(file.name);
    try {
      await read({ kind: "file", file_name: file.name, content_base64: await fileToBase64(file) });
    } catch {
      setFileError(true);
    }
  };

  const create = async () => {
    if (!source || !report || creating) return;
    setCreating(true);
    setRefusal(null);
    try {
      const made = await createImportedDraft(origin, source, report.source.protocol_fingerprint);
      window.location.assign(inceptionHref(locale, "scope", made.session_id, origin));
    } catch (error) {
      setRefusal(refusalOf(error));
      setCreating(false);
    }
  };

  const changed = refusal?.code === "IMPORT_SOURCE_CHANGED";
  const items = (workspaces?.items ?? []).filter((item) => item.valid);
  const chosenSlug = source?.kind === "workspace" ? source.slug : null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <nav className="mb-6 text-sm">
        <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "", "", origin)} data-back>
          {t("import.back")}
        </a>
      </nav>
      <header className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("import.eyebrow")}</p>
        <h1 className="mt-2 font-display text-3xl text-ink">{t("import.title")}</h1>
        <p className="mt-2 max-w-2xl text-ink-muted">{t("import.lede")}</p>
      </header>

      {refusal ? (
        <div className="mb-4 space-y-2" data-import-refusal={refusal.code}>
          <InceptionRefusal locale={locale} refusal={refusal} origin={origin} />
          {changed && source ? (
            <Button onClick={() => void read(source)} data-read-again>
              {t("import.readAgain")}
            </Button>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <section aria-labelledby="import-workspace" className="rounded-lg border border-rule bg-leaf p-4" data-source-workspaces>
          <h2 id="import-workspace" className="font-semibold text-ink">
            {t("import.workspace.title")}
          </h2>
          {listError ? (
            <InceptionRefusal locale={locale} refusal={listError} origin={origin} />
          ) : !workspaces ? (
            <p role="status" aria-busy="true" className="mt-2 text-ink-muted">
              {t("loading")}
            </p>
          ) : items.length === 0 ? (
            <p className="mt-2 text-sm text-ink-muted" data-no-workspace>
              {t("import.workspace.empty", { root: workspaces.root })}
            </p>
          ) : (
            <div role="radiogroup" aria-labelledby="import-workspace" className="mt-2 space-y-1">
              {items.map((item) => (
                <label key={item.slug} className="flex min-h-11 cursor-pointer items-start gap-3 rounded-md px-2 py-2 hover:bg-paper" data-workspace={item.slug}>
                  <input
                    type="radio"
                    name="import-workspace"
                    checked={chosenSlug === item.slug}
                    onChange={() => void read({ kind: "workspace", slug: item.slug })}
                    className="mt-1 h-5 w-5 shrink-0"
                  />
                  <span className="min-w-0">
                    <span className="block text-ink" dir="auto">
                      {item.title || item.slug}
                    </span>
                    <span className="block text-xs text-ink-muted">
                      <DataCell>{item.slug}</DataCell>
                      {item.last_event?.at ? <> · {t("import.workspace.last", { date: stamp(item.last_event.at) })}</> : null}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          )}
        </section>

        <section aria-labelledby="import-file" className="rounded-lg border border-rule bg-leaf p-4" data-source-file>
          <h2 id="import-file" className="font-semibold text-ink">
            {t("import.file.title")}
          </h2>
          <p id="import-file-help" className="mt-1 text-sm text-ink-muted">
            {t("import.file.help")}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept=".json,application/json"
            className="sr-only"
            tabIndex={-1}
            onChange={(event) => void pickFile(event.target.files?.[0])}
            data-file-input
          />
          <div className="mt-3">
            <Button onClick={() => fileInput.current?.click()} aria-describedby="import-file-help">
              {t("import.file.choose")}
            </Button>
          </div>
          <p className="mt-2 text-sm text-ink" aria-live="polite">
            {fileName ? t("import.file.chosen", { name: fileName }) : ""}
          </p>
          {fileError ? (
            <p className="mt-1 text-sm text-unclear" role="alert">
              {t("import.file.unreadable")}
            </p>
          ) : null}
        </section>

        <section aria-labelledby="import-text" className="rounded-lg border border-rule bg-leaf p-4 md:col-span-2" data-source-text>
          <h2 id="import-text" className="font-semibold text-ink">
            {t("import.text.title")}
          </h2>
          <p className="mt-1 text-sm text-ink-muted">{t("import.text.note")}</p>
        </section>
      </div>

      {reading ? (
        <p role="status" aria-busy="true" className="mt-6 text-ink-muted" data-reading>
          {t("import.reading")}
        </p>
      ) : null}

      {report ? <ReportCard locale={locale} report={report} headingRef={reportHeading} /> : null}

      <div className="mt-6 flex flex-wrap gap-3">
        {report ? (
          <>
            <Button variant="primary" onClick={() => void create()} disabled={creating} aria-busy={creating || undefined} data-create>
              {creating ? t("import.creating") : t("import.create")}
            </Button>
            <Button
              onClick={() => {
                request.current++;
                setReport(null);
                setSource(null);
                setFileName("");
              }}
              disabled={creating}
            >
              {t("import.change")}
            </Button>
          </>
        ) : null}
      </div>
    </div>
  );
}

function ReportCard({ locale, report, headingRef }: Readonly<{ locale: Locale; report: ImportReport; headingRef: React.RefObject<HTMLHeadingElement | null> }>) {
  const t = inceptionT(locale);
  const d = report.draft;
  const criteria = (d.extra_inclusions?.length ?? 0) + (d.extra_exclusions?.length ?? 0) + (d.proof ? 1 : 0);
  const years = d.start_year ? `${d.start_year} – ${d.end_year ?? t("import.report.noYear")}` : t("import.report.noYear");
  const lossy = importLossLines(locale, report.lost, []);
  const needs = importLossLines(locale, [], report.needs_you);
  const src = report.source;
  return (
    <section aria-labelledby="import-report" className="mt-6 rounded-lg border border-rule bg-leaf p-4" data-report>
      <h2 id="import-report" ref={headingRef} tabIndex={-1} className="font-semibold text-ink">
        {t("import.source", { label: src.label, date: stamp(src.protocol_created_at ?? null), shape: t(src.read === "intent" ? "import.shape.intent" : "import.shape.protocol") })}
      </h2>
      {src.protocol_fingerprint ? (
        <p className="mt-1 text-xs text-ink-muted">
          <DataCell>{src.protocol_fingerprint}</DataCell>
        </p>
      ) : null}
      <h3 className="mt-4 text-sm font-semibold text-ink">{t("import.report.exact")}</h3>
      <p className="text-sm text-ink" data-report-exact>
        {t("import.report.counts", {
          rqs: formatNumber(locale, d.rqs?.length ?? 0),
          criteria: formatNumber(locale, criteria),
          concepts: formatNumber(locale, d.concepts?.length ?? 0),
          columns: formatNumber(locale, (d.custom_matrix_columns?.length ?? 0) + (d.matrix_columns?.length ?? 0)),
          years,
          languages: (d.languages ?? []).join(", "),
        })}
      </p>
      <h3 className="mt-4 text-sm font-semibold text-ink">{t("import.report.lossy")}</h3>
      <ul className="list-disc ps-5 text-sm text-ink" data-report-lossy>
        {lossy.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <h3 className="mt-4 text-sm font-semibold text-ink">{t("import.report.needs")}</h3>
      <ul className="list-disc ps-5 text-sm text-ink" data-report-needs>
        {needs.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {src.collides_with_source ? (
        <p className="mt-3 text-sm text-unclear" data-collides>
          {t("import.report.collides", { slug: src.target_slug })}
        </p>
      ) : null}
    </section>
  );
}
