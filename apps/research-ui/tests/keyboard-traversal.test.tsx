import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createPortal } from "react-dom";
import { describe, expect, it, vi } from "vitest";

import { LocaleDocument } from "@/components/locale-document";
import { OverviewPage } from "@/components/overview-page";
import { LOCALE_METADATA, SUPPORTED_LOCALES, type Locale } from "@/i18n";
import { CATALOGS } from "@/messages";

import { KeyboardProbe } from "./fixtures/keyboard-probe";

const FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';

/** A stable, readable label for a focusable element, used in ordered assertions. */
function describeFocusable(element: Element): string {
  const tag = element.tagName.toLowerCase();
  const text = (element.textContent ?? "").trim();
  return text.length > 0 ? `${tag}:${text}` : tag;
}

/**
 * The pathname the mocked router reports, so the locale selector's links match
 * the document under test. `usePathname()` is a client hook with no meaning
 * outside a running app router.
 */
let currentPath = "/en";

vi.mock("next/navigation", () => ({
  usePathname: () => currentPath,
}));

/**
 * The route's tab stops, in DOM order, for one locale.
 *
 * This is the **union of tab stops across viewport widths**, not a per-viewport
 * tab ring: no single real viewport produces all of them, because
 * `primary-nav.tsx` is `hidden lg:block`, `mobile-nav.tsx` is `lg:hidden`, and
 * `display: none` removes an element from the focus order. The locale selector
 * is deliberately NOT in that set — it carries no breakpoint (D-I18N-11), so its
 * three links are real tab stops at 375px and at 1440px alike, and they are
 * listed after the mobile trigger because the switcher is the last header item.
 */
function expectedTabStops(locale: Locale): string[] {
  return [
    `a:${CATALOGS[locale]["a11y.skipToMain"]}`,
    `a:${CATALOGS[locale]["nav.overview"]}`,
    `button:${CATALOGS[locale]["a11y.openMainNavigation"]}`,
    ...SUPPORTED_LOCALES.map((code) => `a:${LOCALE_METADATA[code].endonym}`),
  ];
}

/**
 * Keyboard traversal, simulated in jsdom.
 *
 * This asserts that a Tab press moves `document.activeElement` to a different
 * element on each successive press and that focus eventually leaves the
 * container instead of being trapped. It does NOT prove rendered focus order,
 * visible focus rings, or that a real browser's tab ring matches jsdom's.
 * See `GATES.md` (deferred to packet UI-00b).
 */
describe("keyboard traversal", () => {
  it("moves the active element on every successive Tab", async () => {
    const user = userEvent.setup();
    render(<KeyboardProbe />);

    const first = screen.getByRole("link", { name: "First link" });
    const second = screen.getByRole("button", { name: "Second action" });
    const third = screen.getByRole("textbox", { name: "Third field" });

    const visited: Element[] = [];
    expect(document.body).toHaveFocus();

    for (const expected of [first, second, third]) {
      await user.tab();
      expect(document.activeElement).toBe(expected);
      visited.push(document.activeElement as Element);
    }

    expect(new Set(visited).size).toBe(visited.length);
  });

  it("does not trap focus: Tab past the last element leaves the focusable set", async () => {
    const user = userEvent.setup();
    render(<KeyboardProbe />);

    const third = screen.getByRole("textbox", { name: "Third field" });
    await user.tab();
    await user.tab();
    await user.tab();
    expect(document.activeElement).toBe(third);

    await user.tab();
    expect(document.activeElement).not.toBe(third);
    expect(document.activeElement).not.toBe(screen.getByRole("link", { name: "First link" }));
  });

  it("Shift+Tab walks back to the previous element", async () => {
    const user = userEvent.setup();
    render(<KeyboardProbe />);

    const second = screen.getByRole("button", { name: "Second action" });
    const third = screen.getByRole("textbox", { name: "Third field" });

    await user.tab();
    await user.tab();
    expect(document.activeElement).toBe(second);

    await user.tab();
    expect(document.activeElement).toBe(third);

    await user.tab({ shift: true });
    expect(document.activeElement).toBe(second);
  });

  for (const locale of SUPPORTED_LOCALES) {
    it(`routes the real locale page through the shell: skip link first, then the navigation, then the locale selector (${locale})`, async () => {
      // This is the converted UI-00 tripwire.
      //
      // UI-00 asserted that the route rendered ZERO focusable elements, on
      // purpose: so that the first packet to add navigation would break the
      // build and force this suite to be pointed at the real route. That is what
      // UI-01 did — the skip link and the primary navigation are now the route's
      // only tab stops, and the assertion below is a positive, ordered statement
      // about them instead of an absence. UI-01d added the locale selector, so the
      // ordered list grows by three links and is now asserted per locale: the
      // tripwire is only a tripwire if a new tab stop turns it red, in *every*
      // locale, not just the English one the labels happen to be pinned from.
      //
      // The order asserted below is the **union of tab stops across viewport
      // widths, in DOM order** — not a per-viewport tab ring. No single real
      // viewport produces all of them: `primary-nav.tsx` is `hidden lg:block` and
      // `mobile-nav.tsx` is `lg:hidden`, and `display: none` removes an element
      // from the focus order. At 375px the real order is
      // [skip, trigger, English, Français, العربية] (the `Overview` link is not a
      // tab stop); at >=1024px it is [skip, Overview, English, Français,
      // العربية] (the trigger is not a tab stop). jsdom applies no stylesheet, so
      // it reports all six at once. See `GATES.md` §3.
      //
      // This union is deliberately the assertion: it is the converted tripwire, so
      // any new tab stop a later packet introduces turns it red, and narrowing it
      // to a per-viewport set would destroy that.
      //
      // NOTE (measured, not assumed): the tripwire did NOT go red on its own. It
      // rendered the page in isolation, and UI-01 moved the shell into the
      // layout, so the page still contributes no focusable elements of its own.
      // The tripwire was therefore also silently *stale* — its comment claimed to
      // watch "the route" while only ever watching one component. UI-01 converted
      // it to render the assembled route, which is what it always claimed to
      // cover, and UI-01d keeps it rendering the assembled locale route.
      //
      // The scope stays `document.body`, NOT RTL's `container`. The stack includes
      // `@headlessui/react`, whose `Dialog` renders through `createPortal` into
      // `document.body`, outside the container. A container-scoped query would go
      // blind the moment the mobile disclosure is opened. The control test below
      // proves that.
      const user = userEvent.setup();
      currentPath = `/${locale}`;
      const { unmount } = render(
        <LocaleDocument locale={locale}>
          <OverviewPage locale={locale} />
        </LocaleDocument>,
      );

      const focusable = Array.from(document.body.querySelectorAll(FOCUSABLE));

      // Non-vacuity: the route really does expose focusable elements now.
      expect(focusable.length).toBeGreaterThan(0);

      // Asserted as an ordered list of described elements, not merely a count, so
      // a reordered or extra tab stop fails too. Unchanged from the converted
      // tripwire: the union across viewport widths, in DOM order (see above).
      expect(focusable.map(describeFocusable)).toEqual(expectedTabStops(locale));

      // The first of them is the skip link, and it is the element a real Tab
      // press lands on.
      expect(focusable[0]).toBe(
        screen.getByRole("link", { name: CATALOGS[locale]["a11y.skipToMain"] }),
      );
      expect(document.body).toHaveFocus();
      await user.tab();
      expect(document.activeElement).toBe(focusable[0]);

      // Walking forward covers every tab stop, in order. userEvent walks the same
      // jsdom union described above — a real 375px or >=1024px ring is a strict
      // subset of it, not the same sequence (see `GATES.md` §3).
      for (const expected of focusable.slice(1)) {
        await user.tab();
        expect(document.activeElement).toBe(expected);
      }

      // ...and walking back does too, so focus is not trapped in either direction.
      for (const expected of focusable.slice(0, -1).reverse()) {
        await user.tab({ shift: true });
        expect(document.activeElement).toBe(expected);
      }

      // The backward walk above ended on the first stop, so forward from there
      // covers the whole ring: each remaining stop in order, and then one Tab
      // beyond the last.
      for (const expected of focusable.slice(1)) {
        await user.tab();
        expect(document.activeElement).toBe(expected);
      }

      await user.tab();
      expect(focusable).not.toContain(document.activeElement);
      expect(document.body).toHaveFocus();

      // ...and from the document start the ring begins again at the skip link —
      // userEvent's emulation of the browser's tab ring, not a focus trap in the
      // shell.
      await user.tab();
      expect(document.activeElement).toBe(focusable[0]);

      unmount();
    });
  }

  it("records that the page component contributes no tab stops of its own", () => {
    // The original UI-00 observation, kept because it is still true and still
    // useful: every tab stop on the route belongs to the shell, so a later
    // packet that adds an interactive control to page content is adding a new
    // tab stop, not extending an existing sequence. This is asserted against
    // `document.body` for the portal reason given above.
    const { container } = render(<OverviewPage locale="en" />);

    expect(document.body.querySelectorAll(FOCUSABLE)).toHaveLength(0);

    // The container is genuinely a strict subset here (it is not merely
    // equivalent by accident), so the weaker query really is insufficient.
    expect(container.ownerDocument.body).toBe(document.body);
  });

  it("control: the focusable tripwire is not blind to portaled DOM", () => {
    // Asserts nothing about the application. It exists so the tripwire above
    // cannot silently regress into a container-scoped query that a
    // `createPortal` (as used by @headlessui/react) would render straight
    // past. If the tripwire is ever re-scoped to the RTL container, this fails.
    const { container } = render(
      <>
        <span>in-tree</span>
        {createPortal(<button type="button">Portaled action</button>, document.body)}
      </>,
    );

    // The container-scoped query misses the portal ...
    expect(container.querySelectorAll(FOCUSABLE)).toHaveLength(0);
    // ... the document-scoped query catches it.
    expect(document.body.querySelectorAll(FOCUSABLE)).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Portaled action" })).toBeInTheDocument();
  });
});
