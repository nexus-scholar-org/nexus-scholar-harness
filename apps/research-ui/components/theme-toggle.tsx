"use client";

import { useEffect, useState } from "react";

/**
 * The theme selector (production plan §3, M0).
 *
 * Three choices, as buttons with `aria-pressed`: follow the system, or force
 * light or dark. A forced choice sets `data-theme` on `<html>`, which
 * `app/theme.css` reads; "system" removes it, so `prefers-color-scheme`
 * decides. The choice is remembered in `localStorage` under
 * {@link THEME_STORAGE_KEY}; storage can be missing or blocked, so every
 * access is guarded and the page works without it.
 *
 * {@link THEME_BOOT_SCRIPT} applies a remembered choice before first paint
 * (the document component inlines it in `<head>`), so a reader who chose dark
 * never sees a light flash on load.
 */

export type ThemeChoice = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "nexus-scholar-theme";

const CHOICES: readonly ThemeChoice[] = ["system", "light", "dark"];

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
}: Readonly<{ selectorLabel: string; labels: Readonly<Record<ThemeChoice, string>> }>) {
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

  return (
    <div
      role="group"
      aria-label={selectorLabel}
      data-nav-region="theme"
      className="mt-2 flex flex-wrap items-center gap-x-1 gap-y-1"
    >
      {CHOICES.map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={choice === value}
          onClick={() => choose(value)}
          className="block min-h-11 px-2 py-1.5 text-sm font-medium text-ink-muted underline decoration-2 underline-offset-4 decoration-transparent hover:text-ink hover:decoration-rule-strong aria-pressed:text-evidence aria-pressed:decoration-evidence"
        >
          {labels[value]}
        </button>
      ))}
    </div>
  );
}
