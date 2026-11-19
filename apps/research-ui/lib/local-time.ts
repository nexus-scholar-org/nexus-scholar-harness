/**
 * Engine timestamps in the researcher's own clock (H-ui-findings F6).
 *
 * The engine stores UTC instants (`2026-11-19T06:17:00+00:00`). A screen that
 * printed the first 16 characters showed UTC with no label, an hour or more off
 * the researcher's clock. These print the same instant in the browser's time
 * zone, as `YYYY-MM-DD HH:MM` (24 hours, Latin digits, like the other screens),
 * The ISO string stays available to the caller for a `title` or `dateTime` attribute (`components/stamp.tsx`).
 *
 * Hydration: every caller formats a value read from the engine after the page
 * mounted (a draft, a list, a job), never one in the prerendered HTML, which has
 * no data. The server markup is therefore empty where these print, so the zone
 * the build ran in cannot reach the page.
 */

const ZONE = /(Z|[+-]\d{2}:?\d{2})$/i;

/** The instant as a Date; a timestamp with no zone is read as UTC, as the engine writes them. */
function parse(at: string): Date | null {
  const text = at.trim();
  const date = new Date(/T\d{2}:\d{2}/.test(text) && !ZONE.test(text) ? `${text}Z` : text);
  return Number.isNaN(date.getTime()) ? null : date;
}

const two = (n: number) => String(n).padStart(2, "0");

/** `YYYY-MM-DD HH:MM` in the browser's zone; an unreadable value is shown as it came. */
export function localStamp(at: string | null | undefined): string {
  if (!at) return "";
  const d = parse(at);
  if (!d) return at;
  return `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:${two(d.getMinutes())}`;
}

/** `YYYY-MM-DD` in the browser's zone. */
export function localDate(at: string | null | undefined): string {
  return localStamp(at).slice(0, 10);
}
