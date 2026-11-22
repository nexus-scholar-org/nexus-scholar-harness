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

type ActFlag = { IS_REACT_ACT_ENVIRONMENT?: boolean };
const actFlag = globalThis as ActFlag;
const actWas = actFlag.IS_REACT_ACT_ENVIRONMENT;

afterEach(() => {
  vi.unstubAllGlobals();
  // The first test lets React schedule its own work; every test after it starts with act again.
  actFlag.IS_REACT_ACT_ENVIRONMENT = actWas;
});

const field = (id: string) => document.querySelector(`[data-field="${id}"]`) as HTMLElement;
const position = () => document.querySelector("[data-position]");

function key(target: Element, init: KeyboardEventInit) {
  target.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
}

function studies(count: number) {
  return makeChartingTable(Array.from({ length: count }, (_, i) => makeRow(i + 1, { abstract: `Study ${i + 1}.` })));
}

/** Runs `then` once `ready()` holds after a change of `aria-pressed`; fails after `ms`, so the test always ends. */
function onPressed(element: Element, ready: () => boolean, then: () => void, ms = 2000): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const observer = new MutationObserver(() => {
      if (!ready()) return;
      observer.disconnect();
      clearTimeout(timer);
      then();
      resolve();
    });
    const timer = setTimeout(() => {
      observer.disconnect();
      reject(new Error("the saved value never showed"));
    }, ms);
    observer.observe(element, { attributes: true, attributeFilter: ["aria-pressed"] });
  });
}

describe("charting-study.focus-race", () => {
  it("Ctrl+Down pressed as soon as a saved value shows: the next study opens with the focus on its first field, four times over", async () => {
    installEngine(studies(5));
    // Each next study is read over the network, as from the engine: its answer comes a task later,
    // so the screen shows its loading state first and the previous study's fields go.
    const answer = globalThis.fetch;
    vi.stubGlobal("fetch", async (input: string, init?: RequestInit) => {
      if (/\/charting\/records\/STU-00[2-5]/.test(String(input))) await new Promise((resolve) => setTimeout(resolve, 20));
      return answer(input, init);
    });
    await renderStudy("STU-001");
    // From here React schedules its own work, as in the browser: the render that shows the saved
    // value commits first and its effects run in a later task. Whether the key lands in that gap
    // depends on timing in jsdom too (most runs on origin/main lose the focus, not all), so the move
    // is made four times: a regression passes only if every one of them misses the gap.
    actFlag.IS_REACT_ACT_ENVIRONMENT = false;
    for (let k = 1; k <= 4; k += 1) {
      const yes = field("cross_camera").querySelector("input") as HTMLInputElement;
      const notApplicable = field("cross_camera").querySelector('[data-special="not_applicable"]') as HTMLElement;
      yes.focus();
      // The key arrives the moment the saved Not applicable is on screen, before those effects run.
      const pressed = onPressed(
        notApplicable,
        () => notApplicable.getAttribute("aria-pressed") === "true",
        () => key(document.activeElement ?? document.body, { key: "ArrowDown", ctrlKey: true }),
      );
      key(yes, { key: "a", altKey: true, code: "KeyA" });
      await pressed;
      await waitFor(() => expect(position()).toHaveTextContent(`Study ${k + 1} of 5`));
      await waitFor(() => expect(field("sensor_problems").contains(document.activeElement)).toBe(true));
    }
  });

  it("Alt+A then Ctrl+Down before the save's answer: the focus stays on the next study's first field", async () => {
    installEngine(studies(3));
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
    installEngine(studies(3));
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
    installEngine(studies(3));
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
