"use client";

import { ComputerDesktopIcon, MoonIcon, SunIcon } from "@heroicons/react/24/outline";
import { useEffect, useState, type ComponentType, type SVGProps } from "react";

/**
 * The light/dark selector (production plan §3, M0).
 *
 * `system` follows `prefers-color-scheme`; `light` and `dark` set
 * `data-theme` on `<html>`, which the generated `app/theme.css` honours. The
 * choice is stored in `localStorage` and restored before paint by
 * {@link THEME_BOOT_SCRIPT}, so a forced theme never flashes the other one.
 *
 * Two presentations of the same three buttons: `compact` is the header's
 * icon toolbar (each button named by `aria-label`, as the brand book allows in
 * a toolbar), `full` is the mobile menu's labelled row with 44px targets.
 */

export type ThemeChoice = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "nexus-scholar-theme";

const CHOICES: readonly ThemeChoice[] = ["system", "light", "dark"];

const ICONS: Readonly<Record<ThemeChoice, ComponentType<SVGProps<SVGSVGElement>>>> = {
  system: ComputerDesktopIcon,
  light: SunIcon,
  dark: MoonIcon,
};

/** Runs in `<head>` before the body paints. */
export const THEME_BOOT_SCRIPT = `(function(){try{var t=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY,
)});if(t==="light"||t==="dark"){document.documentElement.setAttribute("data-theme",t);}}catch(e){}})();`;

function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", choice);
}

function storedTheme(): ThemeChoice {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

export function ThemeToggle({
  selectorLabel,
  labels,
  variant = "compact",
}: Readonly<{
  selectorLabel: string;
  labels: Readonly<Record<ThemeChoice, string>>;
  variant?: "compact" | "full";
}>) {
  const [choice, setChoice] = useState<ThemeChoice>("system");

  useEffect(() => {
    setChoice(storedTheme());
  }, []);

  function choose(next: ThemeChoice): void {
    setChoice(next);
    applyTheme(next);
    try {
      if (next === "system") window.localStorage.removeItem(THEME_STORAGE_KEY);
      else window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Storage unavailable: the choice holds for this page only.
    }
  }

  const compact = variant === "compact";
  return (
    <div
      role="group"
      aria-label={selectorLabel}
      data-nav-region="theme"
      className={
        compact
          ? "flex items-center gap-0.5 rounded-md border border-rule bg-paper p-0.5"
          : "grid grid-cols-3 gap-1 rounded-md border border-rule bg-paper p-1"
      }
    >
      {CHOICES.map((value) => {
        const Icon = ICONS[value];
        return (
          <button
            key={value}
            type="button"
            aria-pressed={choice === value}
            aria-label={compact ? labels[value] : undefined}
            title={compact ? labels[value] : undefined}
            onClick={() => choose(value)}
            className={
              compact
                ? "inline-flex size-8 items-center justify-center rounded-sm text-ink-muted hover:text-ink aria-pressed:bg-leaf aria-pressed:text-ink aria-pressed:shadow-[0_0_0_1px_var(--color-rule)]"
                : "inline-flex min-h-11 items-center justify-center gap-2 rounded-sm text-sm font-medium text-ink-muted hover:text-ink aria-pressed:bg-leaf aria-pressed:text-ink aria-pressed:shadow-[0_0_0_1px_var(--color-rule)]"
            }
          >
            <Icon aria-hidden="true" className="size-4" />
            {compact ? null : labels[value]}
          </button>
        );
      })}
    </div>
  );
}
