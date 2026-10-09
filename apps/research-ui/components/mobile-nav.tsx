"use client";

import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from "@headlessui/react";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { useState } from "react";

import { translate, type Locale } from "@/i18n";

import { PrimaryNavList } from "./primary-nav";

/**
 * The English source strings behind the disclosure's two accessible names.
 *
 * Frozen because they are byte-pins in `tests-browser/helpers.ts` and
 * `tests/shell.test.tsx`. They are **not** what gets rendered: the button's name
 * is `translate(locale, …)`, and packet UI-01d is precisely the change that makes
 * an English accessible-name locator a time-out on `/fr` and `/ar` — which is why
 * `data-nav-region="mobile-trigger"` now exists and why every browser locator
 * that will run against a translated document uses it instead.
 */
export const MOBILE_NAV_TRIGGER_LABEL = "Open main navigation";
export const MOBILE_NAV_CLOSE_LABEL = "Close main navigation";
export const MOBILE_NAV_PANEL_ID = "mobile-primary-nav";

/**
 * Narrow-screen navigation disclosure.
 *
 * Built on Headless UI's `Dialog`, which supplies the modal semantics, the
 * `Escape` handler and focus restoration, so a keyboard user cannot be stranded
 * inside it. It is a *secondary* route to the navigation only: the primary
 * `<nav>` is rendered unconditionally in `PrimaryNav`, and the trigger is
 * hidden from `lg:` upwards.
 *
 * The panel's entire content sits inside its own `<nav>` landmark, and the
 * landmark is named differently from the primary one, so the two never collide
 * on the `landmark-unique` rule while the disclosure is open. A third landmark
 * — the locale selector, also in the header — makes the distinctness of all
 * three names a per-locale property, and `tests/shell.test.tsx` asserts it for
 * every locale rather than only in English.
 *
 * Packet UI-01c removed the panel's heavy elevation shadow and the `rounded-*`
 * classes from the trigger and close control. In this application depth is not how
 * hierarchy is communicated, so a floating card for a menu was the one place
 * the old generated-SaaS language survived most visibly; separation now comes
 * from the backdrop, the hairline edge rule and the rules inside the panel. The
 * panel stays `w-full max-w-sm` and opaque, which is what keeps every text node
 * in it decidable for `color-contrast` at 375px (see `GATES.md` §3.6.2).
 *
 * **Direction (packet UI-01d, DC7/DC8).** The panel is anchored to the inline
 * end (`end-0`) and its edge rule is on the inline start (`border-s`), so in `ar`
 * it slides in from the left and its hairline is on the right — the side a reader
 * moving right-to-left expects, and the same side the lineage rail takes in the
 * evidence trail. The two icons are direction-neutral glyphs and are **not**
 * mirrored: a mirrored hamburger is a well-known way to make a control look like
 * it points the wrong way (D-I18N-09).
 */
export function MobileNav({
  locale,
  currentItemId,
}: {
  locale: Locale;
  currentItemId: string | undefined;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-4 lg:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={MOBILE_NAV_PANEL_ID}
        onClick={() => setOpen(true)}
        data-nav-region="mobile-trigger"
        className="inline-flex items-center gap-2 border border-rule-strong bg-leaf px-3 py-2 text-sm font-medium text-ink hover:bg-paper"
      >
        <Bars3Icon aria-hidden="true" className="size-5 text-ink-muted" />
        <span className="sr-only">{translate(locale, "a11y.openMainNavigation")}</span>
      </button>

      <Dialog open={open} onClose={setOpen}>
        <DialogBackdrop className="fixed inset-0 bg-ink/40" />
        <DialogPanel
          id={MOBILE_NAV_PANEL_ID}
          className="fixed inset-y-0 end-0 w-full max-w-sm overflow-y-auto border-s border-rule-strong bg-leaf p-6"
        >
          <nav
            aria-label={translate(locale, "nav.landmark.primaryMobile")}
            data-nav-region="mobile"
          >
            <div className="flex items-center justify-between border-b border-rule pb-4">
              <DialogTitle className="font-display text-base leading-6 text-ink">
                {translate(locale, "nav.mobileDialogTitle")}
              </DialogTitle>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="inline-flex items-center gap-2 border border-rule-strong px-3 py-2 text-sm font-medium text-ink hover:bg-paper"
              >
                <XMarkIcon aria-hidden="true" className="size-5 text-ink-muted" />
                <span className="sr-only">{translate(locale, "a11y.closeMainNavigation")}</span>
              </button>
            </div>
            <div className="mt-6">
              <PrimaryNavList
                variant="stacked"
                currentItemId={currentItemId}
                locale={locale}
              />
            </div>
          </nav>
        </DialogPanel>
      </Dialog>
    </div>
  );
}
