/**
 * Whether the one-time notice about a review's copy was dismissed
 * (H-workspace-format-version). Remembered per copy, in this browser only: a
 * convenience, never a record. Storage may be unavailable (a private window);
 * the notice then shows again on the next page load, which is harmless.
 */

const NOTICE_KEY = "nexus.copy-notice.";

export function copyNoticeSeen(copyName: string): boolean {
  try {
    return window.localStorage.getItem(NOTICE_KEY + copyName) === "1";
  } catch {
    return false;
  }
}

export function markCopyNoticeSeen(copyName: string): void {
  try {
    window.localStorage.setItem(NOTICE_KEY + copyName, "1");
  } catch {
    // nothing to do: see above
  }
}
