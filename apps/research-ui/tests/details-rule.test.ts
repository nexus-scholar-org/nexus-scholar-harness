import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

/**
 * Rule page 12, rule 3 (M6-beta): every "Details" summary is a target of at
 * least 44 px with a visible focus ring. The screens write `<details>` inline
 * rather than through one component, so the rule is checked on the source:
 * each `<summary` in a component carries the classes.
 */

const COMPONENTS = resolve(process.cwd(), "components");

describe("details.rule", () => {
  it("gives every summary a 44 px target and a focus ring", () => {
    const offenders: string[] = [];
    let seen = 0;
    for (const name of readdirSync(COMPONENTS).filter((f) => f.endsWith(".tsx"))) {
      const text = readFileSync(join(COMPONENTS, name), "utf-8");
      for (const match of text.matchAll(/<summary className="([^"]*)"/g)) {
        seen += 1;
        const classes = match[1].split(/\s+/);
        if (!classes.includes("min-h-11") || !classes.some((c) => c.startsWith("focus-visible:outline"))) offenders.push(`${name}: ${match[1]}`);
      }
      for (const bare of text.matchAll(/<summary(?! className)/g)) offenders.push(`${name}: summary without classes at ${bare.index}`);
    }
    expect(seen).toBeGreaterThan(10); // anti-vacuity: the screens use Details
    expect(offenders).toEqual([]);
  });
});
