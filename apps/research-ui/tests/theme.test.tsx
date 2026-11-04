import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { THEME_BOOT_SCRIPT, THEME_STORAGE_KEY, ThemeToggle } from "@/components/theme-toggle";

/**
 * The design-system pipeline (production plan §3, M0).
 *
 * `app/theme.css` is generated from `docs/ux/brand/tokens.json`; these tests pin
 * that it is current, that every brand colour has a light and a dark value in
 * the output, that no retired UI-01 token name returns, and that the theme
 * selector sets and clears `data-theme` and its stored choice.
 */

const APP = resolve(import.meta.dirname, "..");
const THEME = readFileSync(resolve(APP, "app", "theme.css"), "utf8").replace(/\r\n/g, "\n");
const TOKENS = JSON.parse(
  readFileSync(resolve(APP, "..", "..", "docs", "ux", "brand", "tokens.json"), "utf8"),
) as { color: { tokens: { name: string; value: { light: string; dark: string } }[] } };

describe("generated theme", () => {
  it("is current with the brand tokens", () => {
    const out = execFileSync(process.execPath, [resolve(APP, "scripts", "build-tokens.mjs"), "--check"], {
      encoding: "utf8",
    });
    expect(out).toContain("app/theme.css is current.");
  });

  it("declares every brand colour for light and for dark", () => {
    const [light, rest] = THEME.split("@media (prefers-color-scheme: dark)");
    for (const { name, value } of TOKENS.color.tokens) {
      expect(light).toContain(`--ns-${name}: ${value.light};`);
      expect(rest).toContain(`--ns-${name}: ${value.dark};`);
    }
    expect(THEME).toContain(':root:not([data-theme="light"])');
    expect(THEME).toContain(':root[data-theme="dark"]');
  });

  it("routes every role through a brand variable and keeps retired names out", () => {
    for (const role of ["paper", "leaf", "ink", "ink-muted", "rule", "evidence", "focus", "include", "anchor"]) {
      expect(THEME).toMatch(new RegExp(`--color-${role}: var\\(--ns-[a-z-]+\\);`));
    }
    for (const retired of ["--color-surface", "--color-raised", "--color-accent"]) {
      expect(THEME).not.toContain(retired);
    }
  });
});

describe("theme selector", () => {
  afterEach(() => {
    document.documentElement.removeAttribute("data-theme");
    window.localStorage.clear();
  });

  const labels = { system: "System", light: "Light", dark: "Dark" };

  it("forces dark, then returns to the system preference", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle selectorLabel="Theme" labels={labels} />);

    expect(screen.getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Dark" }));
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(screen.getByRole("button", { name: "Dark" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "System" }));
    expect(document.documentElement).not.toHaveAttribute("data-theme");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBeNull();
  });

  it("restores a stored choice before paint and ignores junk", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "light");
    new Function(THEME_BOOT_SCRIPT)();
    expect(document.documentElement).toHaveAttribute("data-theme", "light");

    document.documentElement.removeAttribute("data-theme");
    window.localStorage.setItem(THEME_STORAGE_KEY, "neon");
    new Function(THEME_BOOT_SCRIPT)();
    expect(document.documentElement).not.toHaveAttribute("data-theme");
  });
});
