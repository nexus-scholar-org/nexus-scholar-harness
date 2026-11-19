import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Hint } from "@/components/ui/base";
import { hintPlacement } from "@/components/ui/guidance";

/** 03-guidance rule 1.5 and "Right-to-left (ar)": placement in the logical direction (M10d). */

const VIEW = { width: 1280, height: 800 };
const BUTTON = { left: 600, right: 644, top: 200, bottom: 244 };

describe("hint.rtl", () => {
  it("opens on the inline-end side: the physical right in ltr, the physical left in rtl", () => {
    const ltr = hintPlacement(BUTTON, VIEW, false);
    expect(ltr.side).toBe("inline-end");
    expect(ltr.left).toBeGreaterThanOrEqual(BUTTON.right);
    const rtl = hintPlacement(BUTTON, VIEW, true);
    expect(rtl.side).toBe("inline-end");
    expect(rtl.left + rtl.width).toBeLessThanOrEqual(BUTTON.left);
  });

  it("falls back to below, then to the inline-start side, and never leaves the viewport", () => {
    const nearEnd = { left: 1180, right: 1224, top: 200, bottom: 244 };
    const below = hintPlacement(nearEnd, VIEW, false, 80);
    expect(below.side).toBe("below");
    expect(below.left + below.width).toBeLessThanOrEqual(VIEW.width - 16);
    const nearBottom = { left: 1180, right: 1224, top: 760, bottom: 790 };
    expect(hintPlacement(nearBottom, VIEW, false, 80).side).toBe("inline-start");
    const rtlNearEnd = { left: 40, right: 84, top: 760, bottom: 790 };
    expect(hintPlacement(rtlNearEnd, VIEW, true, 80).side).toBe("inline-start");
  });

  it("spans the content width below the button in a narrow window", () => {
    const narrow = hintPlacement({ left: 300, right: 344, top: 100, bottom: 144 }, { width: 375, height: 700 }, true);
    expect(narrow).toEqual({ side: "below", left: 16, top: 148, width: 343 });
  });

  it("reads the page direction when it opens and keeps its text dir=auto (a hint holds plain text, so a quoted value is ordered by the bidi algorithm, not isolated)", async () => {
    const user = userEvent.setup();
    render(
      <div dir="rtl">
        <span>المعرف</span>
        <Hint locale="ar" label="المعرف" text="يُكتب المعرف هكذا: 10.1000/xyz123" textKey="k.doi" />
      </div>,
    );
    const button = screen.getByRole("button", { name: "حول «المعرف»" });
    vi.spyOn(button, "getBoundingClientRect").mockReturnValue({ ...BUTTON, x: 600, y: 200, width: 44, height: 44, toJSON: () => ({}) } as DOMRect);
    vi.stubGlobal("innerWidth", VIEW.width);
    await user.click(button);
    const body = document.querySelector('[data-hint-body="k.doi"]') as HTMLElement;
    expect(body).toHaveAttribute("dir", "auto");
    expect(body).toHaveAttribute("data-placement", "inline-end");
    expect(parseFloat(body.style.left) + parseFloat(body.style.width)).toBeLessThanOrEqual(BUTTON.left);
    vi.unstubAllGlobals();
  });
});
