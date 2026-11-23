import { render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScreeningAgreement } from "@/components/screening-agreement";
import { ScreeningExport } from "@/components/screening-export";
import { HOME_COPY, ScreeningHome } from "@/components/screening-home";
import { ScreeningImport } from "@/components/screening-import";
import { ScreeningPilot } from "@/components/screening-pilot";
import { PILOT_COPY } from "@/components/screening-pilot-copy";
import { ScreeningPrepare } from "@/components/screening-prepare";
import { ScreeningProposals } from "@/components/screening-proposals";
import { ScreeningPublish } from "@/components/screening-publish";

/**
 * H-screening-read-performance, question 5 (finding 47: an almost blank first
 * paint): while the engine answers, a screen shows its name as a heading, the
 * sentence it already had, and empty cards; nothing moves.
 */

afterEach(() => vi.unstubAllGlobals());

function engineThatNeverAnswers() {
  vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => undefined)));
}

function expectStill(container: HTMLElement) {
  const frame = container.querySelector("[data-loading-frame]");
  expect(frame).not.toBeNull();
  expect(frame).toHaveAttribute("aria-busy", "true");
  expect(frame!.querySelectorAll("[data-loading-card]").length).toBeGreaterThan(0);
  expect(container.querySelector('[class*="animate-"]')).toBeNull();
}

describe("loading-frame", () => {
  it.each(["en", "fr", "ar"] as const)("Screening home (%s) shows its heading, its sentence and empty cards", (locale) => {
    engineThatNeverAnswers();
    const { container } = render(<ScreeningHome locale={locale} />);
    expect(screen.getByRole("heading", { level: 1, name: HOME_COPY[locale].eyebrow })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(HOME_COPY[locale].loading);
    expect(container.querySelectorAll("[data-loading-card]")).toHaveLength(3);
    expectStill(container);
  });

  it("the pilot page shows its heading and sentence", () => {
    engineThatNeverAnswers();
    const { container } = render(<ScreeningPilot locale="en" />);
    expect(screen.getByRole("heading", { level: 1, name: PILOT_COPY.en.eyebrow })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(PILOT_COPY.en.loading);
    expectStill(container);
  });

  const others: Array<[string, () => ReactElement]> = [
    ["prepare", () => <ScreeningPrepare locale="en" />],
    ["proposals", () => <ScreeningProposals locale="en" />],
    ["agreement", () => <ScreeningAgreement locale="en" />],
    ["publish", () => <ScreeningPublish locale="en" />],
    ["export", () => <ScreeningExport locale="en" />],
    ["import", () => <ScreeningImport locale="en" />],
  ];
  it.each(others)("%s shows a heading and empty cards while it reads", (_name, page) => {
    engineThatNeverAnswers();
    const { container } = render(page());
    // Export also has its phone notice's heading, hidden on a desktop by CSS.
    expect(container.querySelector("[data-loading-frame] h1")?.textContent).toBeTruthy();
    expectStill(container);
  });
});
