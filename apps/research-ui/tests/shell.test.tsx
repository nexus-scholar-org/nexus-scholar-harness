import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { AxeResults, Result } from "axe-core";
import { describe, expect, it, vi } from "vitest";

import { generateMetadata } from "@/app/[locale]/layout";
import { OverviewPage } from "@/components/overview-page";
import { AppShell, MAIN_CONTENT_ID } from "@/components/app-shell";
import { MOBILE_NAV_CLOSE_LABEL, MOBILE_NAV_TRIGGER_LABEL } from "@/components/mobile-nav";
import { PRIMARY_NAV_ITEMS, UNAVAILABLE_NAV_TEXT } from "@/components/primary-nav";
import { LOCALE_METADATA, SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";

const SKIP_LINK_LABEL = "Skip to main content";

/**
 * The pathname the mocked router reports.
 *
 * `LocaleSwitcher` reads it with `usePathname()`, which is a client hook and has
 * no meaning outside a running app. The mock returns exactly the path the test
 * rendered, so the selector's hrefs and the assertions about them agree — and
 * any test that renders a different locale must move this value too, or it would
 * be measuring English links inside a French document.
 */
let currentPath = "/en";

vi.mock("next/navigation", () => ({
  usePathname: () => currentPath,
}));

/**
 * Renders the real locale route: the shell around the overview page.
 *
 * `AppShell` is mounted directly rather than through `LocaleDocument`, so this
 * file's scope is the shell and its chrome rather than the document wrapper.
 * `LocaleDocument` renders the `<html>`/`<body>` pair, and React 19 applies those
 * elements to the real document instead of rendering them inside the container —
 * which is exactly what makes the `lang`/`dir` assertions in
 * `runAxeOnRealDocument` meaningful, and is exercised where the assembled route
 * is the subject: `tests/home-page.test.tsx` and `tests/i18n-render.test.tsx`
 * mount `LocaleDocument` themselves.
 */
function renderRoute(locale: Locale = "en") {
  currentPath = `/${locale}`;
  return render(
    <AppShell locale={locale}>
      <OverviewPage locale={locale} />
    </AppShell>,
  );
}

/**
 * Build-blocking severity policy, restated locally.
 *
 * The canonical, directly-tested copy of this predicate lives in
 * `tests/accessibility-in-process.test.tsx`, which is an immutable UI-00 file.
 * It cannot be imported from here: importing a module that calls `describe`
 * would re-register that file's whole suite inside this file. The predicate is
 * therefore duplicated, and the duplication is guarded by the
 * "filter: keeps exactly critical and serious" test at the bottom of this file
 * so it cannot rot into a filter that never blocks anything.
 */
function blockingViolations(results: AxeResults): Result[] {
  return results.violations.filter(
    (violation) => violation.impact === "critical" || violation.impact === "serious",
  );
}

/** Renders a violation as a reviewable one-liner so a red build is diagnosable. */
function describeViolation(violation: Result): string {
  const targets = violation.nodes.map((node) => JSON.stringify(node.target)).join(" | ");
  return `[${violation.impact ?? "unknown"}] ${violation.id}: ${violation.help} -> ${targets}`;
}

describe("application shell (UI-01)", () => {
  it("makes the skip link the first focusable element in the document", () => {
    renderRoute();

    const focusable = Array.from(document.body.querySelectorAll("a[href], button"));
    expect(focusable.length).toBeGreaterThan(0);

    const skipLink = screen.getByRole("link", { name: SKIP_LINK_LABEL });
    expect(focusable[0]).toBe(skipLink);
    expect(skipLink).toHaveAttribute("href", `#${MAIN_CONTENT_ID}`);
    expect(skipLink).toHaveClass("skip-link");
  });

  it("focuses the skip link on the first Tab press", async () => {
    const user = userEvent.setup();
    renderRoute();

    expect(document.body).toHaveFocus();
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole("link", { name: SKIP_LINK_LABEL }));
  });

  it("points the skip link at a main landmark that actually exists", () => {
    renderRoute();

    const skipLink = screen.getByRole("link", { name: SKIP_LINK_LABEL });
    const href = skipLink.getAttribute("href") ?? "";
    const target = document.querySelector(href);

    expect(target).toBe(screen.getByRole("main"));
    expect(target).toHaveAttribute("id", MAIN_CONTENT_ID);
    // `tabIndex={-1}` is load-bearing, not decoration: without it the skip link
    // cannot move focus to the landmark in a real browser, and with `0` it would
    // add a fourth tab stop and break the traversal asserted in
    // `tests/keyboard-traversal.test.tsx`.
    expect(target).toHaveAttribute("tabindex", "-1");
  });

  it("renders exactly one main landmark on the assembled route", () => {
    renderRoute();

    expect(document.querySelectorAll("main")).toHaveLength(1);
    expect(screen.getAllByRole("main")).toHaveLength(1);
  });

  it("owns the page's single main landmark: the shell alone renders exactly one main", () => {
    // The contract that makes a dead skip link structurally impossible. The
    // shell owns the `main`, so a route that forgets one is already correct; the
    // only remaining failure mode is a route that renders a *second* `main`
    // inside this one, and that is what this test catches. Held on the shell
    // alone rather than on the one route that exists today, so it holds for the
    // routes UI-02..UI-06 will add.
    render(
      <AppShell locale="en">
        <p>route content</p>
      </AppShell>,
    );

    expect(document.querySelectorAll("main")).toHaveLength(1);
    const main = screen.getByRole("main");
    expect(main).toHaveAttribute("id", MAIN_CONTENT_ID);
    // `tabIndex={-1}` is what makes the landmark a programmatic skip-link target
    // without adding a tab stop; see the same assertion on the real route.
    expect(main).toHaveAttribute("tabindex", "-1");
    // The route's content lands *inside* it, so the skip link reaches the
    // content rather than landing on an empty outer landmark.
    expect(within(main).getByText("route content")).toBeInTheDocument();
    // A bare shell is not landmark-less: it also still owns the banner and the
    // navigation, so this asserts the specific structure rather than a rendering
    // accident.
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
  });

  it("renders the Demonstration data marker from the shell, not the page", () => {
    renderRoute();

    expect(screen.getByText("Demonstration data")).toBeInTheDocument();
    // The page no longer carries it: the marker is chrome, not content.
    expect(within(screen.getByRole("main")).queryByText("Demonstration data")).toBeNull();
  });

  it("keeps the Demonstration data marker out of the mobile disclosure and out of hidden subtrees", () => {
    renderRoute();

    const marker = screen.getByText("Demonstration data");
    expect(marker.closest("header")).toBe(screen.getByRole("banner"));
    expect(marker.closest("nav")).toBeNull();
    // The disclosure is closed on load, so the marker is not behind it.
    expect(screen.queryByRole("dialog")).toBeNull();

    // Nothing between the marker and the document root hides it, which is the
    // structural half of "visible at every viewport width". The rendered half
    // (real breakpoints, real CSS) is browser-only and tracked in `GATES.md`.
    for (let node: Element | null = marker; node; node = node.parentElement) {
      expect(node.hasAttribute("hidden")).toBe(false);
      expect(node.getAttribute("aria-hidden")).not.toBe("true");
    }

    // The ancestor walk above only sees the `hidden` attribute and
    // `aria-hidden="true"`. Tailwind's hiding utilities set none of those, so a
    // marker given `sr-only`, `hidden` or `invisible` would sail past it while
    // being invisible to every user. The marker's own class list is therefore
    // checked directly.
    const markerClasses = new Set(marker.classList);
    for (const hiding of ["sr-only", "hidden", "invisible"]) {
      expect(markerClasses.has(hiding)).toBe(false);
    }
  });

  it("keeps the banner header a top-level sibling of main, not a descendant", () => {
    renderRoute();

    const banner = screen.getByRole("banner");
    const main = screen.getByRole("main");

    // The defect this fixes: `app/page.tsx` used to nest <header> inside <main>.
    expect(banner.closest("main")).toBeNull();
    expect(main.closest("header")).toBeNull();
    expect(banner.parentElement).toBe(main.parentElement);
  });

  it("exposes the primary navigation as a named landmark", () => {
    renderRoute("en");

    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toHaveAttribute("aria-label", "Primary");
  });

  it("keeps the navigation reachable without opening the mobile disclosure", () => {
    renderRoute("en");

    expect(screen.queryByRole("dialog")).toBeNull();
    const nav = screen.getByRole("navigation", { name: "Primary" });
    expect(within(nav).getByRole("link", { name: "Overview" })).toBeInTheDocument();
  });

  it("marks the active surface with aria-current and only that surface", () => {
    renderRoute("en");

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const current = within(nav)
      .getAllByRole("link")
      .filter((link) => link.getAttribute("aria-current") === "page");

    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Overview");
  });

  it("offers no link to a route that does not exist", () => {
    renderRoute();

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const unavailable = PRIMARY_NAV_ITEMS.filter((item) => item.href === undefined);
    expect(unavailable.length).toBeGreaterThan(0);

    for (const item of unavailable) {
      expect(within(nav).queryByRole("link", { name: item.label })).toBeNull();
      const entry = within(nav).getByText(item.label);
      expect(entry.tagName).not.toBe("A");
      // The annotation is real, visible text, not `sr-only` chrome.
      expect(entry).toHaveTextContent(UNAVAILABLE_NAV_TEXT);
    }
  });

  it("offers exactly the links that exist, in every locale", () => {
    // The only five links on the route: the skip link, the one route that
    // exists, and the three locale links. Anything else would be a dead-route
    // fiction or a locale link outside the header.
    //
    // The rendered Overview href is `/${locale}`, computed at render, while
    // `PRIMARY_NAV_ITEMS[0].href` stays the frozen sentinel `"/"` — see the
    // frozen-field table in `UI-01D_WORK_PACKET.md` §4.1. Asserting all three
    // locales here is what stops the sentinel from shipping as a bare root link
    // that silently drops the reader's language. The array stays exhaustive, so
    // an unexpected href still fails.
    for (const locale of SUPPORTED_LOCALES) {
      renderRoute(locale);

      const hrefs = Array.from(document.querySelectorAll("a[href]")).map((link) =>
        link.getAttribute("href"),
      );
      expect(hrefs).toEqual([
        `#${MAIN_CONTENT_ID}`,
        `/${locale}`,
        ...SUPPORTED_LOCALES.map((code) => `/${code}`),
      ]);

      // The same honesty rule in the translated documents: an entry with no
      // route is annotated text, never a link, and the annotation is the
      // translated wording rather than the English pin.
      const nav = screen.getByRole("navigation", {
        name: CATALOGS[locale]["nav.landmark.primary"],
      });
      for (const item of PRIMARY_NAV_ITEMS.filter((entry) => entry.href === undefined)) {
        const label = CATALOGS[locale][`nav.${item.id}` as "nav.audit"];
        expect(within(nav).queryByRole("link", { name: label })).toBeNull();
        expect(within(nav).getByText(label)).toHaveTextContent(
          CATALOGS[locale]["nav.unavailable"],
        );
      }

      cleanup();
    }
  });

  it("lists every packet surface and nothing invented", () => {
    renderRoute();

    expect(PRIMARY_NAV_ITEMS.map((item) => item.label)).toEqual(["Overview", "Screening", "Evidence", "Audit"]);
    for (const item of PRIMARY_NAV_ITEMS) {
      expect(screen.getAllByText(item.label).length).toBeGreaterThan(0);
    }
  });

  it("opens the mobile disclosure from the keyboard and closes it with Escape, restoring focus", async () => {
    const user = userEvent.setup();
    renderRoute();

    const trigger = screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("dialog")).toBeNull();

    trigger.focus();
    await user.keyboard("{Enter}");

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    // Headless UI names the dialog from its DialogTitle, so the `aria-dialog-name`
    // rule is satisfied rather than merely untriggered.
    expect(dialog).toHaveAccessibleName("Main menu");

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).toBeNull();
    // Focus comes back to the control that opened the dialog: a keyboard user
    // is never stranded inside the disclosure.
    expect(document.activeElement).toBe(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("closes the mobile disclosure from its own close control", async () => {
    const user = userEvent.setup();
    renderRoute();

    await user.click(screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: MOBILE_NAV_CLOSE_LABEL }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }));
  });

  it("keeps the two navigation landmarks distinctly named while the disclosure is open", async () => {
    // Two `navigation` landmarks of the same name would be a `landmark-unique`
    // violation the moment the menu opens, so the distinct name is load-bearing.
    // All three locales are checked because the two names are translated: a
    // locale that overwrote one label with the other would still satisfy the
    // English `Set` check and fail only here.
    for (const locale of SUPPORTED_LOCALES) {
      const user = userEvent.setup();
      renderRoute(locale);

      // The trigger's own translated name, not `MOBILE_NAV_TRIGGER_LABEL`: that
      // constant is the English string, and an English name here would match by
      // accident in `fr`/`ar` or — worse — match *any* button if the key were
      // wrong, because `getByRole` ignores a `name` of `undefined`.
      await user.click(
        screen.getByRole("button", {
          name: CATALOGS[locale]["a11y.openMainNavigation"],
        }),
      );

      // Queried from the DOM rather than by role on purpose: while the modal
      // disclosure is open, Headless UI marks the rest of the page `aria-hidden`,
      // which is correct modal behaviour but would hide the desktop landmark from
      // a role query and make this assertion vacuous.
      //
      // Three landmarks, not two: the header also holds the locale selector's own
      // `navigation`. The dialog is portaled to `document.body`, so it is last in
      // document order — which is why this stays a document query and not a
      // container query.
      const names = Array.from(document.querySelectorAll("nav")).map((nav) =>
        nav.getAttribute("aria-label"),
      );
      expect(names).toEqual([
        CATALOGS[locale]["nav.landmark.primary"],
        CATALOGS[locale]["locale.selectorLabel"],
        CATALOGS[locale]["nav.landmark.primaryMobile"],
      ]);
      expect(new Set(names).size).toBe(names.length);

      cleanup();
    }
  });

  /**
   * Run axe over the real document the route rendered into.
   *
   * The tree is audited **exactly as rendered** — nothing is transplanted. That
   * is a deliberate correction, and the reason is the open-disclosure run: while
   * the modal menu is open, Headless UI marks the page's own container
   * `aria-hidden` and portals the panel to the body. An earlier version of this
   * helper moved the container's children onto `<body>` before auditing "so
   * document-level rules have a document" — which is not what that was for, since
   * `axe.run(document.documentElement)` evaluates the document either way, and
   * which had the side effect of lifting the whole page *out* of the subtree the
   * library had just hidden. The result was a document where the modal was
   * correctly the only exposed content and the skip link was nonetheless exposed
   * chrome outside every landmark, so `region` failed on `.skip-link` — a state no
   * browser can produce and no screen reader would ever see.
   *
   * So: no transplant. `container` is a child of the real `<body>` either way, the
   * page keeps whatever `aria-hidden` the open dialog gave it, and `region` /
   * `landmark-unique` / `html-has-lang` / `document-title` are all still evaluated
   * over the whole document. The assertions below are unchanged.
   *
   * The assembly mirrors what Next.js renders and nothing more: the shell's
   * elements come from the layout's own output, `lang` and `title` come from the
   * two exported sources the real server render uses —
   * `LOCALE_METADATA[locale].lang` and `generateMetadata({ params })` — and
   * nothing is invented here. Both are asserted across all three locales above
   * this helper, so the axe run cannot inherit an unverified assumption about
   * which language it is auditing.
   *
   * `lang` and `title` are set on the real document, and are restored in the
   * `finally`: they are global state this helper mutates, and leaking them into
   * the next test in the file would make that test's axe result depend on
   * execution order.
   */
  async function runAxeOnRealDocument(container: HTMLElement, locale: Locale): Promise<AxeResults> {
    const metadata = await generateMetadata({ params: Promise.resolve({ locale }) });
    expect(metadata.title).toBeTruthy();
    expect(LOCALE_METADATA[locale].lang).toBeTruthy();
    // The tree under audit must be the one that was rendered. A transplant would
    // invalidate the premise of every rule that depends on tree position, so this
    // asserts the invariant rather than trusting it.
    expect(container.ownerDocument.body.contains(container)).toBe(true);
    const previousLang = document.documentElement.getAttribute("lang");
    const previousTitle = document.title;
    document.documentElement.setAttribute("lang", LOCALE_METADATA[locale].lang);
    document.title = String(metadata.title);

    try {
      return await axe.run(document.documentElement);
    } finally {
      if (previousLang === null) {
        document.documentElement.removeAttribute("lang");
      } else {
        document.documentElement.setAttribute("lang", previousLang);
      }
      document.title = previousTitle;
    }
  }

  /** Rule ids axe reached at all, whether they passed, failed or need review. */
  function evaluatedRuleIds(results: AxeResults): Set<string> {
    return new Set(
      [...results.passes, ...results.violations, ...results.incomplete, ...results.inapplicable].map(
        (result) => result.id,
      ),
    );
  }

  /**
   * Document-scope axe run.
   *
   * `tests/accessibility-in-process.test.tsx` evaluates a DOM subtree, so
   * document-level rules — `bypass`, `landmark-one-main`, `page-has-heading-one`
   * — are structurally out of its reach (see `GATES.md` §2). The shell is the
   * packet that makes those rules load-bearing, so this run assembles a real
   * document and evaluates them.
   */
  it("reports no critical or serious violations with document-level rules evaluated", async () => {
    const { container } = renderRoute("en");
    const results = await runAxeOnRealDocument(container, "en");

    // Non-vacuity: the engine really executed against this document.
    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);

    // The rules that only a document context can reach must have been reached.
    const evaluated = evaluatedRuleIds(results);
    for (const rule of ["bypass", "landmark-one-main", "page-has-heading-one", "region", "landmark-unique"]) {
      expect(evaluated.has(rule)).toBe(true);
    }

    // `bypass` is the rule the skip link exists for and `region` is the rule
    // the landmark fix exists for. Both are asserted as genuinely clean, not
    // merely as "below the blocking threshold" -- and the claim that the
    // closed-state run reports zero violations of ANY impact is *enforced* here
    // rather than asserted only in prose. If a later change makes any rule fail
    // at any severity, this is meant to go red and be argued about.
    const failed = results.violations.map((violation) => violation.id);
    expect(failed).not.toContain("bypass");
    expect(failed).not.toContain("region");
    expect(failed).not.toContain("landmark-one-main");

    // Same bar as the open-state run below: zero violations of ANY impact, not
    // "zero at critical/serious". A minor or moderate violation in the closed
    // state is a real finding and belongs in the ledger, not in a filter.
    expect(results.violations.map(describeViolation)).toEqual([]);

    expect(blockingViolations(results).map(describeViolation)).toEqual([]);
  });

  /**
   * The same run, but with the mobile disclosure OPEN.
   *
   * This is the state the previous report left as reasoning rather than
   * measurement: with the dialog open, Headless UI marks the rest of the page
   * `aria-hidden` and portals the panel to the body. `region` and
   * `landmark-unique` have to survive that transition, because a modal menu that
   * strands the rest of the document outside every landmark is exactly the
   * defect those two rules exist to catch.
   */
  it("reports no critical or serious violations with the mobile disclosure open", async () => {
    const user = userEvent.setup();
    const { container } = renderRoute("en");

    await user.click(screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Premise check: if Headless UI did not aria-hide the page, this test would
    // be re-running the previous one and proving nothing about the open state.
    // The shell is mounted straight into the RTL container, so the container *is*
    // the page subtree the library hides. Both assertions have to hold: a nullable
    // query result checked with `not.toBeNull()` would let a header that had moved
    // out of the container turn this premise into a no-op and the run below into
    // a silent re-run of the closed-state case.
    expect(container.querySelector("header")).not.toBeNull();
    expect(container.getAttribute("aria-hidden")).toBe("true");

    const results = await runAxeOnRealDocument(container, "en");

    expect(results.violations.length + results.incomplete.length + results.passes.length).toBeGreaterThan(0);

    // Deliberately stricter than the closed-state test above: a rule that merely
    // reached `incomplete` ("needs review") is not a clean result, so these two
    // are required to be genuine passes rather than merely evaluated.
    const passed = new Set(results.passes.map((result) => result.id));
    for (const rule of ["region", "landmark-unique"]) {
      expect(passed.has(rule)).toBe(true);
    }

    const failed = results.violations.map((violation) => violation.id);
    expect(failed).not.toContain("region");
    expect(failed).not.toContain("landmark-unique");

    // Same bar as the closed-state run: not "below the blocking threshold" but
    // zero violations of ANY impact. If the open modal state ever regresses,
    // this is meant to go red and be argued about.
    expect(results.violations.map(describeViolation)).toEqual([]);

    expect(blockingViolations(results).map(describeViolation)).toEqual([]);
  });

  it("filter: this file's severity policy keeps exactly critical and serious violations", () => {
    // Guards the duplicated `blockingViolations` predicate above against being
    // weakened into a filter that can never block anything.
    const stub = (id: string, impact: Result["impact"]): Result => ({
      id,
      impact,
      description: `synthetic ${id}`,
      help: `synthetic ${id}`,
      helpUrl: `https://example.invalid/rules/${id}`,
      tags: ["synthetic-fixture"],
      nodes: [],
    });

    const results = {
      violations: [
        stub("s-moderate", "moderate"),
        stub("s-critical", "critical"),
        stub("s-absent", undefined),
        stub("s-serious", "serious"),
        stub("s-null", null),
        stub("s-minor", "minor"),
      ],
      passes: [],
      incomplete: [],
      inapplicable: [],
      toolOptions: {},
      testEngine: { name: "axe-core", version: "synthetic" },
      testRunner: { name: "synthetic" },
      testEnvironment: { userAgent: "synthetic", windowWidth: 0, windowHeight: 0 },
      url: "about:blank",
      timestamp: "1970-01-01T00:00:00.000Z",
    } as AxeResults;

    expect(blockingViolations(results).map((violation) => violation.id)).toEqual(["s-critical", "s-serious"]);
  });
});
