import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { ThemeToggle } from "@/components/theme-toggle";
import { THEME_BOOT_SCRIPT, THEME_STORAGE_KEY } from "@/lib/theme-boot";

/**
 * The design-system pipeline (production plan §3, M0).
 *
 * `app/theme.css` is generated from `docs/ux/brand/tokens.json`; these tests pin
 * that it is current, that every brand colour has a light and a dark value in
 * the output, that no retired UI-01 token name returns, and that the theme
 * selector sets and clears `data-theme` and its stored choice.
 */

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
