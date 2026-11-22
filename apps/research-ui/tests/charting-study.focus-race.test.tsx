import { act, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { flush, installEngine, makeChartingTable, makeRow, renderStudy } from "./charting-helpers";

/**
 * H-charting-focus-fault (2026-11-22): after Ctrl+Down the focus must reach the first field of the
 * next study, and a focus asked for after a save must not pull the researcher back once they have
 * moved on. The browser test "chart five studies from the abstract by keyboard" failed at times
 * because the next study opened with the focus nowhere: an effect run left over from the save's
 * render spent the focus request on the previous study, whose fields were about to go.
 */

afterEach(() => vi.unstubAllGlobals());

const field = (id: string) => document.querySelector(`[data-field="${id}"]`) as HTMLElement;
const position = () => document.querySelector("[data-position]");

function key(target: Element, init: KeyboardEventInit) {
  target.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
}

function threeStudies() {
  return makeChartingTable([makeRow(1, { abstract: "One." }), makeRow(2, { abstract: "Two." }), makeRow(3, { abstract: "Three." })]);
}

type ActFlag = { IS_REACT_ACT_ENVIRONMENT?: boolean };

describe("charting-study.focus-race", () => {
  it("Ctrl+Down pressed as soon as a saved value shows: the next study opens with the focus on its first field", async () => {
    installEngine(threeStudies());
    // The next study is read over the network, as from the engine: its answer comes a task later,
    // so the screen shows its loading state first and the previous study's fields go.
    const answer = globalThis.fetch;
    vi.stubGlobal("fetch", async (input: string, init?: RequestInit) => {
      if (String(input).includes("/charting/records/STU-002")) await new Promise((resolve) => setTimeout(resolve, 20));
      return answer(input, init);
    });
    await renderStudy("STU-001");
    const yes = field("cross_camera").querySelector("input") as HTMLInputElement;
    const notApplicable = field("cross_camera").querySelector('[data-special="not_applicable"]') as HTMLElement;
    yes.focus();
    // From here React schedules its own work, as in the browser: the render that shows the saved
    // value commits first and its effects run in a later task.
    const flag = globalThis as ActFlag;
    const was = flag.IS_REACT_ACT_ENVIRONMENT;
    flag.IS_REACT_ACT_ENVIRONMENT = false;
    try {
      // The key arrives the moment the saved Not applicable is on screen, before those effects run.
      const pressed = new Promise<void>((resolve) => {
        const observer = new MutationObserver(() => {
          if (notApplicable.getAttribute("aria-pressed") !== "true") return;
          observer.disconnect();
          key(document.activeElement ?? document.body, { key: "ArrowDown", ctrlKey: true });
          resolve();
        });
        observer.observe(notApplicable, { attributes: true, attributeFilter: ["aria-pressed"] });
      });
      key(yes, { key: "a", altKey: true, code: "KeyA" });
      await pressed;
      await waitFor(() => expect(position()).toHaveTextContent("Study 2 of 3"));
      await waitFor(() => expect(field("sensor_problems").contains(document.activeElement)).toBe(true));
    } finally {
      flag.IS_REACT_ACT_ENVIRONMENT = was;
    }
  });

  it("Alt+A then Ctrl+Down before the save's answer: the focus stays on the next study's first field", async () => {
    installEngine(threeStudies());
    await renderStudy("STU-001");
    const yes = field("cross_camera").querySelector("input") as HTMLInputElement;
    yes.focus();
    await act(async () => {
      key(yes, { key: "a", altKey: true, code: "KeyA" });
      key(yes, { key: "ArrowDown", ctrlKey: true });
      for (let i = 0; i < 50; i += 1) await Promise.resolve();
    });
    await flush();
    await flush();
    expect(position()).toHaveTextContent("Study 2 of 3");
    expect(field("sensor_problems").contains(document.activeElement)).toBe(true);
  });

  it("Alt+N, then another field before the save's answer: the focus stays in the field the researcher went to", async () => {
    installEngine(threeStudies());
    await renderStudy("STU-001");
    const random = field("split").querySelector("input") as HTMLInputElement;
    const yes = field("cross_camera").querySelector("input") as HTMLInputElement;
    random.focus();
    await act(async () => {
      key(random, { key: "n", altKey: true, code: "KeyN" });
      yes.focus();
      for (let i = 0; i < 50; i += 1) await Promise.resolve();
    });
    await flush();
    expect(field("split").querySelector('[data-special="not_reported"]')).toHaveAttribute("aria-pressed", "true");
    expect(document.activeElement).toBe(yes);
  });

  it("Alt+N with the focus left in the field: the focus moves to the Not reported button once the input is off", async () => {
    installEngine(threeStudies());
    await renderStudy("STU-001");
    const random = field("split").querySelector("input") as HTMLInputElement;
    random.focus();
    await act(async () => {
      key(random, { key: "n", altKey: true, code: "KeyN" });
      for (let i = 0; i < 50; i += 1) await Promise.resolve();
    });
    await flush();
    expect(document.activeElement).toBe(field("split").querySelector('[data-special="not_reported"]'));
  });
});
