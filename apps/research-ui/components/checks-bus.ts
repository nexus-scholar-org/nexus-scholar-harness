"use client";

import { useEffect, useState } from "react";

/**
 * The discovery checks re-read after a job ends and after a dismissal (02-checks
 * "Data in"): the job stream and the panel announce it on the window, and the
 * panel and the step bar listen. Nothing polls.
 */

const EVENT = "nexus:discovery-checks";

export function notifyDiscoveryChecks(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(EVENT));
}

/** A number that moves each time the discovery checks should be read again. */
export function useDiscoveryChecksVersion(): number {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const bump = () => setVersion((n) => n + 1);
    window.addEventListener(EVENT, bump);
    return () => window.removeEventListener(EVENT, bump);
  }, []);
  return version;
}
