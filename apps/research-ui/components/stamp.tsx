import { localStamp } from "@/lib/local-time";

/**
 * A time on the researcher's clock that keeps the engine's ISO instant in `dateTime` (H-ui-findings F6).
 * H-run-small-fixes (finding 5): no `title` any more: assistive technology and page readers
 * announced the raw instant ("2026-11-20T09:45:15.784778+00:00") beside the local time.
 */
export function Stamp({ at }: Readonly<{ at: string | null | undefined }>) {
  if (!at) return null;
  return (
    <time dir="ltr" dateTime={at}>
      {localStamp(at)}
    </time>
  );
}
