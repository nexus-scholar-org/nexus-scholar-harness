// The packaged app's prerendered export (M5-slim). `next build` with
// NEXT_STATIC_EXPORT=1 writes every page as HTML to `.next-export/`, which the
// console serves (`nexus-scholar ui`) and the wheel bundles (`hatch_build.py`).
// A script rather than `NEXT_STATIC_EXPORT=1 next build` in package.json, so it
// runs the same way on Windows.
import { spawnSync } from "node:child_process";

const env = { ...process.env, NEXT_STATIC_EXPORT: "1" };
const steps = [
  ["node", ["scripts/build-tokens.mjs", "--check"]],
  ["npx", ["next", "build"]],
];
for (const [command, args] of steps) {
  const result = spawnSync(command, args, { stdio: "inherit", env, shell: process.platform === "win32" });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
