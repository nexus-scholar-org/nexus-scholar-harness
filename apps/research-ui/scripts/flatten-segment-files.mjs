// Next's packaged export writes each page's prefetch ("segment") files next to the page,
// and the client asks for them by a flat name: `__next.$d$locale.workspaces.__PAGE__.txt`
// (`convertSegmentPathToStaticExportFilename`, which swaps "/" for "."). The exporter
// builds that name from the segment's file path with a regular expression that swaps only
// "/", so on Windows, where the path has "\", it leaves the separators in and writes
// nested folders (`__next.$d$locale\workspaces\__PAGE__.txt`). A build made on Windows
// then answers 404 to every prefetch, on every page, on every load (H-ui-findings F9).
// Linux and macOS builds are already flat, so this finds nothing to do there.
import { existsSync, readdirSync, renameSync, rmSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

function filesUnder(dir) {
  const found = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) found.push(...filesUnder(path));
    else found.push(path);
  }
  return found;
}

/** Rewrites every folder `__next.*` under `root` into the flat files the client asks for; returns how many it moved. */
export function flattenSegmentFiles(root) {
  let moved = 0;
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      if (!statSync(path).isDirectory()) continue;
      if (!name.startsWith("__next.")) {
        walk(path);
        continue;
      }
      for (const file of filesUnder(path)) {
        const flat = join(dir, `${name}.${relative(path, file).split(sep).join(".")}`);
        if (existsSync(flat)) throw new Error(`flattenSegmentFiles: ${flat} already exists`);
        renameSync(file, flat);
        moved += 1;
      }
      rmSync(path, { recursive: true, force: true });
    }
  };
  walk(root);
  return moved;
}
