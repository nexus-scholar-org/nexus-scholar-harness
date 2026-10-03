import { expect, test } from "@playwright/test";

import { DESKTOP_VIEWPORT, MOBILE_VIEWPORT, report } from "../tests-browser/helpers";
import { expectNoSidewaysScroll, measureOverflow } from "../tests-browser/overflow-recipe";
import { CATALOGS, type MessageKey } from "../messages";
import type { Locale } from "../i18n";

/**
 * The 30 % expansion gate (packet UI-01d, §13.2, AC-9 and AC-9P).
 *
 * This file exists because the previous version of this gate was **vacuous**
 * (§13.2.1, finding B1): it asked for 30 % inflation and then measured the
 * already-built `.next` tree, which — because `NEXT_PUBLIC_*` is inlined at build
 * time — contained zero inflation. It passed while proving nothing, which is
 * worse than failing.
 *
 * So the precondition comes first and it is unconditional (AC-9P, §13.2.3): the
 * **served response body** is fetched, one catalogued prose sentence is located
 * inside it, and its length is compared with the same string compiled from source
 * before a single clipping assertion runs. A build that did not inflate fails
 * here, loudly, with the numbers printed — so there is no ordering in which a
 * no-clipping assertion can be evaluated against an un-inflated document.
 *
 * Two details of *how* the length is measured, because both would otherwise make
 * the gate lie:
 *
 * 1. **The response body, not the hydrated DOM.** `response.text()` is what
 *    `next start` serves; `page.evaluate` would read a DOM React had already
 *    reconciled, which is a different artifact from the one a reader without
 *    JavaScript receives.
 * 2. **React's text escaping is undone before counting.** React escapes `'` as
 *    `&#x27;` and `"` as `&quot;` in text nodes, and French catalog entries
 *    contain apostrophes. Counting escaped bytes would inflate the *un-inflated*
 *    side of the ratio by however many apostrophes a sentence happens to have,
 *    which could manufacture a 1.30 ratio from a build that expanded nothing.
 */

/** Mirror React's `escapeTextForBrowser`, so the source can be found in the HTML. */
function escapeForHtmlText(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}

/** Undo that escaping so the served run can be compared with a catalogued string. */
function decodeHtmlText(value: string): string {
  return value
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&amp;/g, "&");
}

interface InflationReading {
  locale: Locale;
  key: MessageKey;
  sourceLength: number;
  servedLength: number;
  ratio: number;
}

/**
 * Fetch `/<locale>`'s response body and measure one catalogued sentence inside it.
 *
 * The sentence is located by its *source* text, then the run is read to the next
 * tag boundary and un-escaped: inflation appends, so the source is a prefix of the
 * served run by construction. That is an assumption worth stating rather than
 * hiding, because a rewrite-in-place implementation of `inflate()` would make this
 * measurement meaningless — and it would fail loudly here, which is the point.
 */
async function measureInflation(
  request: import("@playwright/test").APIRequestContext,
  locale: Locale,
  key: MessageKey,
): Promise<InflationReading> {
  const source = CATALOGS[locale][key];
  expect(source, `${locale}/${key} must exist in the catalog`).toBeTruthy();

  const response = await request.get(`/${locale}`);
  expect(response.status(), `/${locale} must serve on the long-strings server`).toBe(200);
  const html = await response.text();

  const escaped = escapeForHtmlText(source);
  const index = html.indexOf(escaped);
  expect(
    index,
    `${locale}/${key} was not found in the served HTML, so the gate cannot measure it`,
  ).toBeGreaterThan(-1);

  const tagEnd = html.indexOf("<", index);
  const served = decodeHtmlText(html.slice(index, tagEnd === -1 ? html.length : tagEnd));
  const ratio = served.length / source.length;

  return {
    locale,
    key,
    sourceLength: source.length,
    servedLength: served.length,
    ratio,
  };
}

function reportInflation(reading: InflationReading): void {
  report(
    `expansion ${reading.locale}/${reading.key}: source=${reading.sourceLength} ` +
      `served=${reading.servedLength} ratio=${reading.ratio.toFixed(4)}`,
  );
}

test.describe("30 % long-string expansion (AC-9P precondition, then AC-9)", () => {
  test("AC-9P: /en serves prose at least 30 % longer than the catalog source", async ({
    request,
  }) => {
    // `overview.traceLede` is body prose (packet §13.2.3 step 2), not a short
    // label, so the 30 % filler dominates any incidental whitespace
    // normalisation.
    const reading = await measureInflation(request, "en", "overview.traceLede");
    reportInflation(reading);

    expect(reading.servedLength, "strictly longer, not merely equal").toBeGreaterThan(
      reading.sourceLength,
    );
    expect(reading.ratio).toBeGreaterThanOrEqual(1.3);
  });

  test("AC-9P: /ar serves Arabic prose at least 30 % longer than the catalog source", async ({
    request,
  }) => {
    // The Arabic path is proved separately on purpose: a Latin-only measurement
    // would not establish that the Arabic filler is applied, and Arabic filler is
    // the one that exercises the script's real glyph metrics (D-I18N-15).
    const reading = await measureInflation(request, "ar", "overview.asideBody");
    reportInflation(reading);

    expect(reading.servedLength).toBeGreaterThan(reading.sourceLength);
    expect(reading.ratio).toBeGreaterThanOrEqual(1.3);
  });

  test("AC-9P: /fr serves prose at least 30 % longer than the catalog source", async ({ request }) => {
    // French is not named in §13.2.3, but it is the longest of the three by
    // volume and it is the locale whose punctuation would otherwise distort the
    // ratio above, so it is measured rather than assumed.
    const reading = await measureInflation(request, "fr", "overview.asideBody");
    reportInflation(reading);

    expect(reading.servedLength).toBeGreaterThan(reading.sourceLength);
    expect(reading.ratio).toBeGreaterThanOrEqual(1.3);
  });

  for (const locale of ["en", "fr", "ar"] as const) {
    for (const [name, viewport] of [
      ["375px", MOBILE_VIEWPORT],
      ["1440px", DESKTOP_VIEWPORT],
    ] as const) {
      test(`AC-9: ${name}/${locale} does not scroll sideways with the strings inflated`, async ({
        page,
      }) => {
        await page.setViewportSize(viewport);
        await page.goto(`/${locale}`);

        // The same recipe the browser suite runs, imported rather than copied —
        // see `tests-browser/overflow-recipe.ts`.
        const measured = await measureOverflow(page);
        report(`long-strings ${name}/${locale}: ${JSON.stringify(measured)}`);
        expectNoSidewaysScroll(measured, `long-strings ${name}/${locale}`);
      });
    }
  }

  test("AC-9: no inflated string is truncated rather than wrapped", async ({ page }) => {
    // Wrapping is the intended behaviour at 30 % expansion; silently clipping is
    // not. The predicate is `text-overflow: ellipsis`, and it is deliberately
    // *only* that.
    //
    // The first draft of this check also flagged `overflow-x: hidden|clip`, and it
    // failed on the skip link and its inner span — correctly, because those two
    // clip their box on purpose (the clip-reveal technique the focus-visibility
    // gate asserts), and a clipped box is not evidence of truncated *text*.
    // Widening the predicate to "clips its overflow" therefore flags the
    // accessibility mechanism this application is proud of, and the fix for that
    // failure would have been to weaken a real rule. `text-overflow: ellipsis` is
    // the only CSS value that renders a truncation marker in place of the missing
    // text, so it is the only one that can prove a string was cut rather than
    // wrapped. `line-clamp` is reported alongside it because `-webkit-line-clamp`
    // truncates by line count without touching `text-overflow`.
    for (const locale of ["en", "fr", "ar"] as const) {
      await page.setViewportSize(MOBILE_VIEWPORT);
      await page.goto(`/${locale}`);

      const truncated = await page.evaluate(() => {
        const offenders: string[] = [];
        for (const node of Array.from(document.querySelectorAll("body *"))) {
          if ((node.textContent ?? "").trim() === "") continue;
          const style = getComputedStyle(node);
          const lineClamped =
            style.webkitLineClamp !== "none" && Number(style.webkitLineClamp) > 0;
          if (style.textOverflow === "ellipsis" || lineClamped) {
            offenders.push(
              `${node.tagName.toLowerCase()}: text-overflow=${style.textOverflow}` +
                ` line-clamp=${style.webkitLineClamp} "${(node.textContent ?? "").slice(0, 40)}"`,
            );
          }
        }
        return offenders;
      });
      report(`long-strings ${locale} truncating elements = ${JSON.stringify(truncated)}`);

      expect(truncated).toEqual([]);
    }
  });
});