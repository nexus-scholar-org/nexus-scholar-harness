"use client";

import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

import { formatNumber, type Locale } from "@/i18n";
import type { ChartingCounts, LastExport } from "@/lib/charting-api";
import { cc } from "@/lib/charting-copy";
import { localStamp } from "@/lib/local-time";

/**
 * The last-export line and the open-cell lines (spec 04 "Partial", M12a Part C),
 * shown under the toolbar of `/charting` and beside the downloads of
 * `/charting/report`. Every number is the engine's: `last_export` is what the
 * newest export wrote, `counts.cells_open` and `counts.required_open` are today's.
 * A line with nothing to say is absent, never "never" or "0". None of them
 * stops a download.
 */
export function ExportLines({
  locale,
  numberLocale,
  lastExport,
  counts,
}: Readonly<{ locale: Locale; numberLocale?: Locale; lastExport: LastExport | null; counts: ChartingCounts | null | undefined }>) {
  const n = (value: number) => formatNumber(numberLocale ?? locale, value);
  const cellsOpen = counts?.cells_open ?? 0;
  const requiredOpen = counts?.required_open ?? 0;
  // The file held other open cells than today's: say what it held.
  const fileDiffers =
    lastExport !== null &&
    counts?.cells_open !== undefined &&
    (lastExport.cells_open !== counts.cells_open || lastExport.required_open !== (counts.required_open ?? 0));
  if (!lastExport && cellsOpen === 0 && requiredOpen === 0) return null;
  return (
    <div className="space-y-1 text-sm text-ink" data-export-lines>
      {lastExport ? (
        <p data-last-export>
          {cc(locale, "charting.export.done", {
            when: localStamp(lastExport.at),
            format: cc(locale, lastExport.format === "xlsx" ? "charting.export.format.xlsx" : "charting.export.format.csv"),
            n: n(lastExport.rows),
          }, lastExport.rows)}
          {fileDiffers ? <span data-file-had>{` ${cc(locale, "charting.export.fileHad", { n: n(lastExport.cells_open) }, lastExport.cells_open)}`}</span> : null}
        </p>
      ) : null}
      {cellsOpen > 0 ? <p data-cells-open>{cc(locale, "charting.export.cellsOpen", { n: n(cellsOpen) }, cellsOpen)}</p> : null}
      {requiredOpen > 0 ? (
        <p className="flex items-center gap-1.5 text-unclear" data-role="unclear" data-required-open>
          <ExclamationTriangleIcon aria-hidden="true" className="size-4 shrink-0" data-icon />
          <span>{cc(locale, "charting.export.requiredOpen", { n: n(requiredOpen) }, requiredOpen)}</span>
        </p>
      ) : null}
    </div>
  );
}
