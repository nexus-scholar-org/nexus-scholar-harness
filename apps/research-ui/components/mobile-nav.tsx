"use client";

import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from "@headlessui/react";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { useState } from "react";

import { PrimaryNavList } from "./primary-nav";

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
 * on the `landmark-unique` rule while the disclosure is open.
 */
export function MobileNav({ currentItemId = "overview" }: { currentItemId?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-3 lg:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={MOBILE_NAV_PANEL_ID}
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        <Bars3Icon aria-hidden="true" className="size-5" />
        <span className="sr-only">{MOBILE_NAV_TRIGGER_LABEL}</span>
      </button>

      <Dialog open={open} onClose={setOpen}>
        <DialogBackdrop className="fixed inset-0 bg-slate-900/30" />
        <DialogPanel
          id={MOBILE_NAV_PANEL_ID}
          className="fixed inset-y-0 right-0 w-full max-w-sm overflow-y-auto bg-white p-6 shadow-xl"
        >
          <nav aria-label="Primary (mobile menu)">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-base font-semibold text-slate-950">Main menu</DialogTitle>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                <XMarkIcon aria-hidden="true" className="size-5" />
                <span className="sr-only">{MOBILE_NAV_CLOSE_LABEL}</span>
              </button>
            </div>
            <div className="mt-6">
              <PrimaryNavList variant="stacked" currentItemId={currentItemId} />
            </div>
          </nav>
        </DialogPanel>
      </Dialog>
    </div>
  );
}
