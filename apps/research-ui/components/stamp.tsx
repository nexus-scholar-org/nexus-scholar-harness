import { localStamp } from "@/lib/local-time";

/** A time on the researcher's clock that keeps the engine's ISO instant in `dateTime` and `title` (H-ui-findings F6). */
export function Stamp({ at }: Readonly<{ at: string | null | undefined }>) {
  if (!at) return null;
  return (
    <time dir="ltr" dateTime={at} title={at}>
      {localStamp(at)}
    </time>
  );
}
