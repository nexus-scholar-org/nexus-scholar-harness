import { mkdirSync, mkdtempSync, readdirSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

import { afterEach, describe, expect, it } from "vitest";

/**
 * H-ui-findings F9: an export built on Windows nests the prefetch files
 * (`__next.$d$locale/workspaces/__PAGE__.txt`) where the client asks for the flat
 * name (`__next.$d$locale.workspaces.__PAGE__.txt`) and every request is a 404.
 */

const made: string[] = [];
afterEach(() => {
  for (const dir of made.splice(0)) rmSync(dir, { recursive: true, force: true });
});

async function flatten(): Promise<(root: string) => number> {
  const module = (await import(pathToFileURL(join(__dirname, "..", "scripts", "flatten-segment-files.mjs")).href)) as { flattenSegmentFiles: (root: string) => number };
  return module.flattenSegmentFiles;
}

function nestedExport(): string {
  const root = mkdtempSync(join(tmpdir(), "export-"));
  made.push(root);
  const page = join(root, "en", "screening", "home");
  mkdirSync(join(page, "__next.$d$locale", "screening", "home"), { recursive: true });
  writeFileSync(join(page, "__next.$d$locale", "screening", "home", "__PAGE__.txt"), "page");
  writeFileSync(join(page, "__next._tree.txt"), "tree");
  writeFileSync(join(page, "index.html"), "<html></html>");
  const top = join(root, "en", "workspaces");
  mkdirSync(join(top, "__next.$d$locale", "workspaces"), { recursive: true });
  writeFileSync(join(top, "__next.$d$locale", "workspaces", "__PAGE__.txt"), "page");
  return root;
}

describe("export prefetch files", () => {
  it("turns nested segment folders into the flat names the client requests", async () => {
    const root = nestedExport();
    const moved = (await flatten())(root);
    expect(moved).toBe(2);
    expect(readdirSync(join(root, "en", "screening", "home")).sort()).toEqual(["__next.$d$locale.screening.home.__PAGE__.txt", "__next._tree.txt", "index.html"]);
    expect(readdirSync(join(root, "en", "workspaces"))).toEqual(["__next.$d$locale.workspaces.__PAGE__.txt"]);
    expect(existsSync(join(root, "en", "workspaces", "__next.$d$locale"))).toBe(false);
  });

  it("leaves an export that is already flat as it is", async () => {
    const root = nestedExport();
    const fn = await flatten();
    fn(root);
    expect(fn(root)).toBe(0);
    expect(readdirSync(join(root, "en", "workspaces"))).toEqual(["__next.$d$locale.workspaces.__PAGE__.txt"]);
  });
});
