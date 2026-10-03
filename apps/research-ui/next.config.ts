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
const nextConfig: NextConfig = {
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