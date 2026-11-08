import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import type { NextConfig } from "next";

/**
 * Two settings, both recorded as written scope-extension requests in
 * `UI-01D_WORK_PACKET.md` §13.2.4 (row H8). Neither is a preference; each one
 * is the only place its requirement can be expressed.
 *
 * 1. `redirects()` — the root has no overview of its own, because the overview
 *    lives under a locale. `GET /` is answered with a permanent-visible 307 to
 *    `/en`. `permanent: true` would be wrong: a 308 is cached by browsers and
 *    proxies indefinitely, so pinning the root to English forever would make the
 *    redirect unchangeable without users clearing caches. A 307 asks the server
 *    each time, which is what a "there is no content here, try here" answer
 *    should do. `middleware.ts` could also express it, and is rejected on the
 *    merits: it adds a runtime layer, it is framework-version-sensitive, and a
 *    redirect table declared here does not need a request interceptor.
 *
 * 2. `distDir` — the long-string gate builds the same application twice: once
 *    normally, and once with translation expansion switched on. Next inlines
 *    `NEXT_PUBLIC_*` variables at build time, so the inflated variant has to be
 *    a genuinely separate compilation, and a separate compilation needs its own
 *    output directory. Without this line the second build would overwrite the
 *    first, the gate would measure the wrong tree, and "30 % expansion" would
 *    pass while measuring nothing. The normal build is unaffected: no variable,
 *    default value.
 */
const staticExport = process.env.NEXT_STATIC_EXPORT === "1";

/**
 * 3. The version the footer shows (M6-beta): read from the root
 *    `pyproject.toml`, the one place it lives, at build time. The app is built
 *    together with the wheel from the same commit, so the two always agree.
 */
function projectVersion(): string {
  try {
    const text = readFileSync(resolve(__dirname, "..", "..", "pyproject.toml"), "utf-8");
    const found = /^version\s*=\s*"([^"]+)"/m.exec(text)?.[1] ?? "";
    if (!found) console.warn("next.config: no version in pyproject.toml; the footer will show none");
    return found;
  } catch (error) {
    console.warn(`next.config: pyproject.toml not readable (${String(error)}); the footer will show no version`);
    return "";
  }
}
const env = { NEXT_PUBLIC_NEXUS_VERSION: projectVersion() };

const nextConfig: NextConfig = staticExport
  ? {
      env,
      output: "export",
      distDir: process.env.NEXT_DIST_DIR ?? ".next-export",
      trailingSlash: true,
      pageExtensions: ["tsx"],
      images: { unoptimized: true },
    }
  : {
      env,
      output: "standalone",
      distDir: process.env.NEXT_DIST_DIR ?? ".next",
      async redirects() {
        return [
          {
            source: "/",
            destination: "/en",
            permanent: false,
          },
        ];
      },
    };

export default nextConfig;