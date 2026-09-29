import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { AxeResults, Result } from "axe-core";
import { describe, expect, it } from "vitest";

import RootLayout, { DOCUMENT_LANG, metadata } from "@/app/layout";
import HomePage from "@/app/page";
import { AppShell, MAIN_CONTENT_ID } from "@/components/app-shell";
import { MOBILE_NAV_CLOSE_LABEL, MOBILE_NAV_TRIGGER_LABEL } from "@/components/mobile-nav";
import { PRIMARY_NAV_ITEMS, UNAVAILABLE_NAV_TEXT } from "@/components/primary-nav";

const SKIP_LINK_LABEL = "Skip to main content";

/** Renders the real `/` route: the UI-01 shell wrapping the overview page. */
function renderRoute() {
  return render(
    <RootLayout>
      <HomePage />
    </RootLayout>,
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
      <AppShell>
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
    renderRoute();

    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toHaveAttribute("aria-label", "Primary");
  });

  it("keeps the navigation reachable without opening the mobile disclosure", () => {
    renderRoute();

    expect(screen.queryByRole("dialog")).toBeNull();
    const nav = screen.getByRole("navigation", { name: "Primary" });
    expect(within(nav).getByRole("link", { name: "Overview" })).toBeInTheDocument();
  });

  it("marks the active surface with aria-current and only that surface", () => {
    renderRoute();

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const current = within(nav)
      .getAllByRole("link")
      .filter((link) => link.getAttribute("aria-current") === "page");

    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Overview");
  });

  it("offers no link to a route that does not exist", () => {
    renderRoute();

    // The only two links in the whole route: the skip link and the one route
    // that exists. Anything else would be a dead-route fiction.
    const hrefs = Array.from(document.querySelectorAll("a[href]")).map((link) => link.getAttribute("href"));
    expect(hrefs).toEqual([`#${MAIN_CONTENT_ID}`, "/"]);

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
    const user = userEvent.setup();
    renderRoute();

    await user.click(screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }));

    // Queried from the DOM rather than by role on purpose: while the modal
    // disclosure is open, Headless UI marks the rest of the page `aria-hidden`,
    // which is correct modal behaviour but would hide the desktop landmark from
    // a role query and make this assertion vacuous.
    const names = Array.from(document.querySelectorAll("nav")).map((nav) => nav.getAttribute("aria-label"));
    expect(names).toEqual(["Primary", "Primary (mobile menu)"]);
    expect(new Set(names).size).toBe(names.length);
  });

  /**
   * Assemble the rendered route into a real document, run axe over it, and
   * restore the tree.
   *
   * React omits `<html>`/`<body>` when a layout is mounted into a container, so
   * the container's children are already exactly what `<body>` would contain.
   * They are transplanted onto the real body so document-level rules have a
   * document to evaluate, then restored in a `finally` so React's unmount still
   * finds its own nodes.
   *
   * The assembly mirrors what Next.js renders and nothing more: the shell's
   * elements come from the layout's own output, `lang` is the layout's exported
   * `DOCUMENT_LANG`, and the title comes from the layout's exported `metadata`.
   * Nothing is invented.
   *
   * Note that anything Headless UI has *portaled* — the open disclosure panel —
   * is already a child of the real `body` and so is not moved or restored here;
   * React's own cleanup removes it.
   *
   * `lang` and `title` are set on the real document too, and are restored in the
   * same `finally`: they are global state this helper mutates, and leaking them
   * into the next test in the file would make that test's axe result depend on
   * execution order.
   */
  async function runAxeOnRealDocument(container: HTMLElement): Promise<AxeResults> {
    expect(metadata.title).toBeTruthy();
    expect(DOCUMENT_LANG).toBeTruthy();
    const previousLang = document.documentElement.getAttribute("lang");
    const previousTitle = document.title;
    document.documentElement.setAttribute("lang", DOCUMENT_LANG);
    document.title = String(metadata.title);

    const moved: ChildNode[] = [];
    while (container.firstChild) {
      moved.push(container.firstChild);
      document.body.appendChild(container.firstChild);
    }

    try {
      return await axe.run(document.documentElement);
    } finally {
      for (const node of moved.reverse()) {
        container.appendChild(node);
      }
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
    const { container } = renderRoute();
    const results = await runAxeOnRealDocument(container);

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
    const { container } = renderRoute();

    await user.click(screen.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Premise check: if Headless UI did not aria-hide the page, this test would
    // be re-running the previous one and proving nothing about the open state.
    const appShell = container.querySelector("header")?.parentElement;
    expect(appShell).not.toBeNull();
    expect(appShell?.closest("[aria-hidden='true']")).not.toBeNull();

    const results = await runAxeOnRealDocument(container);

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
