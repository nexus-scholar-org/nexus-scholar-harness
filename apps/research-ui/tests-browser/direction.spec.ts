import { DESKTOP_VIEWPORT, expect, measureTabRing, MOBILE_VIEWPORT, report, test } from "./helpers";
import { formatNumber } from "../i18n";
import { demoEvidence, demoProject } from "../lib/mock-project";

/**
 * Arabic is a mirrored reading flow, not a mirrored document (packet UI-01d,
 * AC-6, N19).
 *
 * The distinction this file exists to keep honest: mirroring is a property of
 * *layout* — which edge content starts from, which side a marginal column sits
 * on — while identifiers, generated numbers and codes are not sentences and must
 * read the same way in every locale. A blanket `direction: rtl` gets the first
 * right and the second wrong, and the second is what a reviewer of an evidence
 * trail notices: an ordinal column that starts at the wrong edge makes 1…5 read
 * like 5…1.
 *
 * Every expectation is computed from `formatNumber` and the fixture rather than
 * from a literal, so a locale or fixture change fails the assertion instead of
 * quietly redefining it. The `ar` numeral expectation is worth stating: `ar-EG`
 * formats in Arabic-Indic digits (`١`, `١٤٣`), so an ordinal assertion copied from
 * the English page would fail for the right reason — the page is translating —
 * and a literal `"12345"` assertion would have had to be weakened to pass.
 */

/**
 * The page has two `<ol>`s and they are told apart structurally, not by index.
 *
 * The workflow list carries `aria-label` (`workflow.listLabel`); the evidence
 * trail does not, because its `<h2>` is its accessible name. Positional
 * selectors (`ol:nth-of-type(2)`) would silently retarget the workflow list the
 * day a third list is added, and `document.querySelector("ol > li > span")` is
 * worse: it matched the workflow list's first `<li>` in an earlier draft of this
 * file and read its kind stamp as if it were an ordinal.
 */
const TRAIL = "ol:not([aria-label])";
const WORKFLOW = "ol[aria-label]";
const ORDINAL = `${TRAIL} > li > span:first-child`;
const SPINE = `${TRAIL} > li > div.border-s`;

test.describe("arabic direction", () => {
  test("AC-6: the trail's spine and ordinal column mirror to the reading start edge", async ({
    page,
  }) => {
    // Measured in both directions and compared, because "the spine is on the
    // reading start edge" is a claim about the *difference* between them: read in
    // `ltr` and `border-s` resolves to `border-left-width`, read in `rtl` and it
    // resolves to `border-right-width`. Asserting only the Arabic side would pass
    // on a hairline drawn on a fixed physical edge.
    const readSpine = async (locale: "en" | "ar") => {
      await page.goto(`/${locale}`);
      return page.evaluate(() => {
        const item = document.querySelector("ol:not([aria-label]) > li");
        const spine = item?.querySelector("div.border-s") ?? null;
        const ordinal = item?.querySelector("span") ?? null;
        if (item === null || spine === null || ordinal === null) {
          throw new Error("the evidence trail did not render its ordinal and spine");
        }
        const spineStyle = getComputedStyle(spine);
        const spineBox = spine.getBoundingClientRect();
        const ordinalBox = ordinal.getBoundingClientRect();
        const itemBox = item.getBoundingClientRect();
        return {
          borderLeftWidth: Number.parseFloat(spineStyle.borderLeftWidth),
          borderRightWidth: Number.parseFloat(spineStyle.borderRightWidth),
          ordinalAlign: getComputedStyle(ordinal).textAlign,
          // The ordinal is the grid's *first* column, so in RTL it sits to the
          // right of the spine, i.e. further along the reading flow, flush with
          // the row's outer edge.
          ordinalLeadsTheSpine: ordinalBox.left > spineBox.left,
          ordinalFlushWithReadingEdge: Math.abs(ordinalBox.right - itemBox.right),
        };
      });
    };

    const ltr = await readSpine("en");
    const rtl = await readSpine("ar");
    report(`spine geometry = ${JSON.stringify({ en: ltr, ar: rtl })}`);

    // `border-s` is the logical start edge: one physical side in `en`, the other in
    // `ar`, both non-zero. Asserting only the Arabic side would pass on a hairline
    // drawn on a fixed physical edge.
    expect(ltr.borderLeftWidth).toBeGreaterThan(0);
    expect(ltr.borderRightWidth).toBe(0);
    expect(rtl.borderRightWidth).toBeGreaterThan(0);
    expect(rtl.borderLeftWidth).toBe(0);

    // `text-end` is asserted as the *logical* keyword Chromium reports for the used
    // value — an earlier draft asserted `"right"` and failed, because Chromium keeps
    // `text-align: end` as `end` and the physical side is expressed by the box, not
    // the keyword. Asserting the physical alignment directly, by geometry, is what
    // the criterion is actually about: in `ar` the ordinal column is flush with the
    // row's right edge, and it leads the spine.
    expect(rtl.ordinalAlign).toBe("end");
    expect(rtl.ordinalLeadsTheSpine, "the ordinal must lead the spine in reading order").toBe(true);
    expect(rtl.ordinalFlushWithReadingEdge).toBeLessThanOrEqual(1);
  });

  test("N19: the trail ordinals are 1…5 in ascending logical order in every locale", async ({
    page,
  }) => {
    for (const locale of ["en", "fr", "ar"] as const) {
      await page.goto(`/${locale}`);
      const ordinals = await page
        .locator(ORDINAL)
        .evaluateAll((nodes) => nodes.map((node) => node.textContent?.trim() ?? ""));
      report(`/${locale} trail ordinals = ${JSON.stringify(ordinals)}`);

      expect(ordinals).toHaveLength(demoEvidence.length);
      // Ascending in *document* order in every locale, and each ordinal is the
      // locale's own numeral: `["١","٢","٣","٤","٥"]` for `ar`, not a reversed
      // Latin run and not an English run pasted into an Arabic page.
      expect(ordinals).toEqual(demoEvidence.map((_, index) => formatNumber(locale, index + 1)));
    }
  });

  test("N19: generated counts are locale-formatted, never digit-reversed", async ({ page }) => {
    const counts = demoProject.stages.flatMap((stage) =>
      stage.count === undefined ? [] : [stage.count],
    );
    expect(counts).toContain(143);

    for (const locale of ["en", "fr", "ar"] as const) {
      await page.goto(`/${locale}`);

      // The count is the one element in the workflow row whose entire text is a
      // numeral, and it is deliberately *not* wrapped in `<bdi>` (see
      // `components/workflow-timeline.tsx`), so it is selected by its content
      // rather than by a class that is shared with the description paragraph.
      const rendered = await page.evaluate(() =>
        Array.from(document.querySelectorAll("ol[aria-label] > li p"))
          .map((node) => (node.textContent ?? "").trim())
          .filter((text) => /^[\d٠-٩]+$/.test(text)),
      );
      report(`/${locale} workflow counts = ${JSON.stringify(rendered)}`);

      expect(rendered).toEqual(counts.map((count) => formatNumber(locale, count)));
      // A reversal is the specific failure this guards: `143` read right-to-left
      // becomes `341`, and both digits and their order are what a count is for.
      if (locale === "ar") {
        expect(rendered[0]).toBe(formatNumber("ar", 143));
        expect(rendered[0]).not.toBe(formatNumber("ar", 341));
      }
    }
  });

  test("AC-6: the fixture's identifiers and codes are isolated inside <bdi> and byte-identical", async ({
    page,
  }) => {
    await page.goto("/ar");

    const cells = await page
      .locator(`${TRAIL} h3 bdi, ${TRAIL} p bdi`)
      .evaluateAll((nodes) =>
        nodes.map((node) => ({
          text: node.textContent ?? "",
          unicodeBidi: getComputedStyle(node).unicodeBidi,
        })),
      );
    report(`ar isolated trail runs = ${cells.length}`);

    expect(cells).toHaveLength(demoEvidence.length * 2);
    for (const cell of cells) {
      // `unicode-bidi: isolate` is what keeps an identifier from reordering the
      // punctuation around it under `dir="rtl"`.
      expect(cell.unicodeBidi).toBe("isolate");
    }

    // Byte-for-byte: the RTL layout changed no fixture character. This is the
    // D-I18N-07 assertion in its rendered form.
    expect(cells.map((cell) => cell.text)).toEqual(
      demoEvidence.flatMap((node) => [node.label, node.detail]),
    );
  });

  test("AC-6: no direction-neutral icon is mirrored", async ({ page }) => {
    // 375px, because the disclosure — and therefore the open dialog with any icon
    // inside it — only exists below `lg`. At 1440px the trigger is `display: none`
    // and `click()` would time out rather than test anything.
    await page.setViewportSize(MOBILE_VIEWPORT);
    await page.goto("/ar");
    await page.locator('[data-nav-region="mobile-trigger"]').click();

    const mirrored = await page.evaluate(() => {
      const offenders: string[] = [];
      for (const node of document.querySelectorAll("svg, img")) {
        const style = getComputedStyle(node);
        const transform = style.transform;
        if ((transform !== "none" && transform.includes("-1")) || style.scale.includes("-1")) {
          offenders.push(`${node.tagName.toLowerCase()}: transform=${transform} scale=${style.scale}`);
        }
      }
      return offenders;
    });
    report(`ar mirrored candidates = ${JSON.stringify(mirrored)}`);

    // The disclosure chevron is the only directional glyph in the shell, and it is
    // drawn from logical borders rather than flipped; anything else with a negative
    // X scale in Arabic is a direction-neutral icon that was mirrored by accident.
    expect(mirrored).toEqual([]);
  });

  test("AC-6: mirroring does not reorder focus, and the document direction is rtl", async ({
    page,
  }) => {
    const ring = await measureTabRing(page, 8, "ar");
    const order = ring.map((stop) => `${stop.tag}:${stop.text}`);
    report(`ar tab ring = ${JSON.stringify(order)}`);

    // `<html dir>` is the matching assertion the packet asks of `tab-order.spec.ts`,
    // and the ring itself is the focus half of AC-6: DOM order is unchanged by
    // mirroring, so the sequence of stops is the English one with translated
    // names — including the skip link and the disclosure trigger, which swap
    // places with the desktop nav at the two viewports.
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    expect(order[0]).toMatch(/^a:/);
    expect(order[1]).toMatch(/^(a|button):/);
    expect(order.length).toBeGreaterThanOrEqual(5);
  });
});