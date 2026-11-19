import type { APIRequestContext, Page } from "@playwright/test";

import { DESKTOP_VIEWPORT, expect, HYDRATION_ERROR, test } from "./helpers";

/**
 * React #418 on every full page load (H-hydration-418).
 *
 * `LocaleDocument` took `THEME_BOOT_SCRIPT` from a `"use client"` module, so the page's
 * payload carried `<head>` as `["$","script",null,{"dangerouslySetInnerHTML":{"__html":"$f"}}]`:
 * a reference to that module, not the text. When the module's chunks arrived after
 * hydration began, `<head>` waited for them and was rendered again, React's hydration
 * cursor was left on `<meta charset>`, and the shell's first `<div>` in `<body>` failed
 * to match: #418 with the argument `HTML`, twice per load (the first pass and React's
 * synchronous retry). Whether it happened depended on how fast the chunks came, which is
 * why a warm cache or a fast machine hid it.
 *
 * Two checks per page, in English, French and Arabic:
 * - the payload: `<head>` carries no reference, only literal values (deterministic);
 * - the race: the shell's chunks are held back so hydration starts before they arrive,
 *   and no hydration error may be reported (before the fix this failed on most loads).
 *
 * The `page` fixture in `helpers.ts` also fails any test in this suite on a hydration error.
 */

const LOCALES = ["en", "fr", "ar"] as const;
const PATHS = [
  "workspaces/",
  "inception/scope/?draft=rec_hydration",
  "inception/explore/?draft=rec_hydration",
  "inception/shape/?draft=rec_hydration",
  "discovery/plan/",
  "screening/home/",
] as const;
const HOLD_MS = 800;

/** The page's inline flight payload, decoded (Next writes it as `self.__next_f.push([1, "…"])`). */
function flightPayload(html: string): string {
  const PUSH = /self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)/g;
  let out = "";
  for (const match of html.matchAll(PUSH)) out += JSON.parse(match[1]) as string;
  return out;
}

/** The `<head>` element of the document row: from `["$","head"` to the `["$","body"` that follows it. */
function headModel(payload: string): string {
  const start = payload.indexOf('["$","head"');
  const end = payload.indexOf('["$","body"', start);
  expect(start, "the payload has a <head> element").toBeGreaterThanOrEqual(0);
  expect(end, "the payload has a <body> after <head>").toBeGreaterThan(start);
  return payload.slice(start, end);
}

/** The chunks of the client module that renders the shell (`AppShell`): the ones held back. */
function shellChunks(payload: string): string[] {
  const row = payload.match(/^[0-9a-f]+:I\[\d+,(\[[^\]]*\]),"AppShell"/m);
  expect(row, "the payload references the AppShell module").not.toBeNull();
  return JSON.parse(row![1]) as string[];
}

async function fetchPage(request: APIRequestContext, path: string): Promise<string> {
  const response = await request.get(path);
  expect(response.status(), path).toBe(200);
  return response.text();
}

function collectHydrationErrors(page: Page): () => string[] {
  const seen: string[] = [];
  const onError = (error: Error) => {
    if (HYDRATION_ERROR.test(String(error))) seen.push(String(error).slice(0, 160));
  };
  const onConsole = (message: { type(): string; text(): string }) => {
    if (message.type() === "error" && HYDRATION_ERROR.test(message.text())) seen.push(message.text().slice(0, 160));
  };
  page.on("pageerror", onError);
  page.on("console", onConsole);
  return () => {
    page.off("pageerror", onError);
    page.off("console", onConsole);
    return seen;
  };
}

for (const locale of LOCALES) {
  test.describe(`hydration (${locale})`, () => {
    test.use({ viewport: DESKTOP_VIEWPORT });

    test("the document's <head> reaches the browser as literal values", async ({ request }) => {
      for (const path of PATHS) {
        const head = headModel(flightPayload(await fetchPage(request, `/${locale}/${path}`)));
        // `"$"` alone marks an element. A row reference (`"$f"`), a lazy one (`"$L1"`) or a promise
        // (`"$@2"`) is resolved later and can make `<head>` wait; literal encodings such as
        // `"$undefined"` or `"$S…"` cannot, and are not counted.
        const references = head.match(/"\$(?:L|@)?[0-9a-f]+"/g) ?? [];
        expect(references, `/${locale}/${path}: <head> must not wait for a module`).toEqual([]);
        expect(head).toContain("nexus-scholar-theme");
      }
    });

    test("hydrates with the shell's chunks arriving late", async ({ page, request }) => {
      const held = shellChunks(flightPayload(await fetchPage(request, `/${locale}/workspaces/`)));
      expect(held.length).toBeGreaterThan(0);
      // Routing a request also turns the browser's cache off, so every load fetches the chunks again.
      await page.route(/\/_next\/static\/chunks\/.+\.js$/, async (route) => {
        if (held.some((chunk) => route.request().url().endsWith(chunk))) await new Promise((r) => setTimeout(r, HOLD_MS));
        await route.continue();
      });
      const failures: string[] = [];
      for (const path of PATHS) {
        const stop = collectHydrationErrors(page);
        await page.goto(`/${locale}/${path}`, { waitUntil: "load" });
        await expect(page.locator("main#main-content")).toBeVisible();
        await page.waitForTimeout(HOLD_MS + 700);
        for (const error of stop()) failures.push(`/${locale}/${path}: ${error}`);
      }
      expect(failures).toEqual([]);
    });
  });
}
