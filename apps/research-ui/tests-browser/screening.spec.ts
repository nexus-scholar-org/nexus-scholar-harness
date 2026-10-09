import {
  DESKTOP_VIEWPORT,
  expect,
  MOBILE_VIEWPORT,
  PRIMARY_NAV,
  report,
  test,
} from "./helpers";
import { CATALOGS } from "../messages";
import { SUPPORTED_LOCALES, formatNumber, swapLocale } from "../i18n";

/**
 * The screening workspace, in a real browser (packet UI-04).
 *
 * The in-process suite (`tests/screening-form.test.tsx`) proves the structure
 * and the attributes; this file proves the same claims survive hydration, real
 * clicks and a real layout engine — plus the four things only a browser can
 * answer:
 *
 * 1. **The navigation actually gets there.** The nav link is derived from the
 *    declared route table, so clicking it and landing on the workspace, with
 *    `aria-current` moved to it, is the end-to-end statement that the route
 *    exists and the shell knows it.
 * 2. **No decision is preselected after hydration.** The in-process run checks
 *    the initial render; a client component that re-rendered with a default
 *    would pass there and fail here.
 * 3. **The form still submits nowhere.** A forced `requestSubmit()` in a real
 *    document is what `preventDefault` actually has to stop — and the base
 *    `test` fixture fails any run that reaches a non-localhost origin, so "no
 *    API" is enforced for this file by the harness itself, not by an assertion
 *    that could be forgotten.
 * 4. **The demonstration marker stays visible.** Mock data without the visible
 *    label is forbidden outright by `AGENTS.md`; the marker is shell chrome, so
 *    it has to be shown on this route too, not just the overview.
 */

const DEMO_MARKER = "safety.demoDataLabel";

test.describe("screening workspace", () => {
  test("the primary navigation reaches it, and moves aria-current onto the screening link", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en");

    // Before: the overview is the current surface.
    await expect(
      page.locator(`${PRIMARY_NAV} a[aria-current="page"]`),
    ).toHaveText(CATALOGS.en["nav.overview"]);

    await page.locator(`${PRIMARY_NAV} a[href="/en/screening"]`).click();
    await page.waitForURL("**/en/screening");

    expect(new URL(page.url()).pathname).toBe("/en/screening");
    await expect(page.locator("h1")).toHaveText(CATALOGS.en["screening.heading"]);

    // After: exactly one current surface, and it is the workspace — the
    // pathname-derived `currentItemId` is what made this possible at all.
    const current = page.locator(`${PRIMARY_NAV} a[aria-current="page"]`);
    await expect(current).toHaveCount(1);
    await expect(current).toHaveText(CATALOGS.en["nav.screening"]);
    report(`aria-current after navigation = ${await current.getAttribute("href")}`);
  });

  test("the demonstration marker is visible on this route", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/screening");

    // `AGENTS.md`: presenting mock data without the visible label is forbidden.
    // The record here IS mock data, so the marker must render on this route —
    // a shell that only showed it on the overview would be a silent gap.
    await expect(page.getByText(CATALOGS.en[DEMO_MARKER])).toBeVisible();
  });

  for (const locale of SUPPORTED_LOCALES) {
    test(`no decision is preselected after hydration (${locale})`, async ({ page }) => {
      await page.setViewportSize(MOBILE_VIEWPORT);
      await page.goto(`/${locale}/screening`);
      await page.waitForLoadState("networkidle");

      const radios = page.locator('input[type="radio"][name="screening-decision"]');
      await expect(radios).toHaveCount(3);
      for (let index = 0; index < 3; index += 1) {
        await expect(radios.nth(index)).not.toBeChecked();
      }

      // The disabled submit and its explanation are on screen from the start —
      // the absence of an API is stated, not discovered by pressing the button.
      const submit = page.getByRole("button", {
        name: CATALOGS[locale]["screening.submit"],
      });
      await expect(submit).toBeDisabled();
      await expect(
        page.getByText(CATALOGS[locale]["screening.submitDisabledExplanation"]),
      ).toBeVisible();
      await expect(page.getByText(CATALOGS[locale]["screening.noPersistence"])).toBeVisible();
    });
  }

  test("the reason requirement appears only for exclude, and is never a live region", async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/screening");

    const reason = page.getByLabel(CATALOGS.en["screening.reasonLabel"]);
    const requirement = page.getByText(CATALOGS.en["screening.reasonRequired"]);
    const exclude = page.getByLabel(CATALOGS.en["screening.decision.exclude"]);
    const include = page.getByLabel(CATALOGS.en["screening.decision.include"]);

    // Nothing is required for an undecided form.
    await expect(requirement).toHaveCount(0);

    await exclude.check();
    await expect(requirement).toBeVisible();
    // Real text, and NOT announced: no live region, no role. The reader made
    // the choice a moment ago; interrupting them to repeat it would be noise.
    const attributes = await requirement.evaluate((el) => ({
      ariaLive: el.getAttribute("aria-live"),
      ariaAtomic: el.getAttribute("aria-atomic"),
      role: el.getAttribute("role"),
    }));
    report(`requirement element attributes = ${JSON.stringify(attributes)}`);
    expect(attributes).toEqual({ ariaLive: null, ariaAtomic: null, role: null });
    await expect(reason).toHaveAttribute(
      "aria-describedby",
      "screening-reason-hint screening-reason-required",
    );

    // Filling the field satisfies it; another decision withdraws it.
    await reason.fill("No comparator arm.");
    await expect(requirement).toHaveCount(0);
    await reason.fill("");
    await expect(requirement).toBeVisible();
    await include.check();
    await expect(requirement).toHaveCount(0);
  });

  test("a forced submit goes nowhere: same URL, no storage write, no request", async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT);
    await page.goto("/en/screening");

    // Give the form everything a reader could give it, so the disabled button
    // cannot be excused by an incomplete form.
    await page.getByLabel(CATALOGS.en["screening.decision.exclude"]).check();
    await page.getByLabel(CATALOGS.en["screening.reasonLabel"]).fill("No comparator arm.");

    const before = new URL(page.url()).pathname;
    const requests: string[] = [];
    page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));

    // A real document, a real submit event: `preventDefault` is the only thing
    // standing between this and a navigation. (A reader cannot press the
    // disabled button — that is the point — so the event is fired the way a
    // stray Enter in a control or a script would fire it.)
    await page.evaluate(() => {
      const form = document.querySelector("form");
      if (form === null) throw new Error("the screening form is missing");
      form.requestSubmit();
    });
    await page.waitForTimeout(250);

    const after = new URL(page.url()).pathname;
    report(`forced submit: ${before} -> ${after}; requests = ${JSON.stringify(requests)}`);
    expect(after, "a submit must not navigate anywhere").toBe(before);

    // Nothing was written anywhere the browser keeps state. (`localStorage`
    // here is about the *form*, not the locale — the locale's own absence from
    // storage is asserted in `locale-switch.spec.ts`.)
    const stored = await page.evaluate(() => ({
      local: Object.keys(localStorage),
      session: Object.keys(sessionStorage),
      cookies: document.cookie,
    }));
    expect(stored).toEqual({ local: [], session: [], cookies: "" });

    // Every request this interaction made stayed on localhost — the base
    // fixture independently fails the run on any non-localhost origin, and
    // this assertion additionally rules out a same-origin POST to some API
    // route the demonstration is not supposed to have.
    const nonGet = requests.filter((line) => !line.startsWith("GET "));
    expect(nonGet, "the demonstration form must not POST/PUT anything").toEqual([]);
  });

  test("in ar the document is RTL and the criteria ordinals are Arabic-Indic digits", async ({
    page,
  }) => {
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/ar/screening");
    await page.waitForLoadState("networkidle");

    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");

    // The marginal numeral is `Intl` output in the page's own numerals — a
    // Latin "1" here would mean the ordinal bypassed `formatNumber`.
    const list = page.locator("main ol");
    await expect(list).toHaveCount(1);
    const items = list.locator("> li");
    await expect(items).toHaveCount(3);
    for (let index = 0; index < 3; index += 1) {
      const ordinal = items.nth(index).locator("> span").first();
      await expect(ordinal).toHaveText(formatNumber("ar", index + 1));
    }

    // And the selector still swaps the locale while keeping this route — the
    // href computation reads the path, so `/ar/screening` + `en` is
    // `/en/screening`, asserted here on the real document as well as in
    // `locale-switch.spec.ts`.
    const hrefs = await page.locator('nav[data-nav-region="locale"] a[href]').evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute("href")),
    );
    expect(hrefs).toEqual(SUPPORTED_LOCALES.map((code) => swapLocale("/ar/screening", code)));
    report(`ar/screening locale hrefs = ${JSON.stringify(hrefs)}`);
  });
});
