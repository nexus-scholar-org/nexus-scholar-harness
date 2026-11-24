/**
 * How the engine serving this page was started (M13 Part A).
 *
 * The launch link of `nexus-scholar ui` sets the readable cookie
 * `nexus_started_as`: `terminal` for a start from a terminal, `installed` for
 * the installed app started from an icon. The installed app has no terminal:
 * its words name its own window and settings folder instead of a command or
 * an environment variable. No cookie (the development proxy, `serve`, tests)
 * reads as `terminal`, the words the app had before.
 */

import { useEffect, useState } from "react";

export type StartedAs = "terminal" | "installed";

export const STARTED_AS_COOKIE = "nexus_started_as";

/** The value of the cookie in `cookies` (a `document.cookie` string); `terminal` when absent or unknown. */
export function startedAsFrom(cookies: string): StartedAs {
  for (const part of cookies.split(";")) {
    const [name, ...rest] = part.trim().split("=");
    if (name === STARTED_AS_COOKIE) return rest.join("=") === "installed" ? "installed" : "terminal";
  }
  return "terminal";
}

/** How this page's engine was started; `terminal` outside a browser. */
export function startedAs(): StartedAs {
  return typeof document === "undefined" ? "terminal" : startedAsFrom(document.cookie ?? "");
}

export function isInstalled(): boolean {
  return startedAs() === "installed";
}

/**
 * `isInstalled()` for a component: `false` on the first render (the static export
 * is rendered with no cookie, so the first client render must match it), then the
 * cookie's answer once mounted.
 */
export function useInstalled(): boolean {
  const [installed, setInstalled] = useState(false);
  useEffect(() => {
    setInstalled(isInstalled());
  }, []);
  return installed;
}
