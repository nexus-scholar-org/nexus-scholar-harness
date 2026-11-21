import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HighlightedText, OTHER_STYLE, segment, termClass } from "@/components/highlighted-text";

/** M8b-triage-highlights: the highlighter takes any text and spans (spec 03, M8b points 1, 4, 5). */

describe("segment", () => {
  it("returns the whole text as one piece with no spans", () => {
    expect(segment("weed map", [], [])).toEqual([{ start: 0, end: 8, style: null, quotes: [] }]);
    expect(segment("", [], [])).toEqual([]);
  });

  it("cuts at every boundary and keeps a term inside a quote (overlap layering)", () => {
    const text = "UAV imagery of weeds in maize";
    const pieces = segment(text, [{ start: 15, end: 20, style: 1 }], [{ start: 4, end: 23, key: "INC-01" }]);
    expect(pieces.map((p) => [text.slice(p.start, p.end), p.style, p.quotes])).toEqual([
      ["UAV ", null, []],
      ["imagery of ", null, ["INC-01"]],
      ["weeds", 1, ["INC-01"]],
      [" in", null, ["INC-01"]],
      [" maize", null, []],
    ]);
  });

  it("names both criteria where two quotes overlap", () => {
    const pieces = segment("abcdef", [], [
      { start: 0, end: 4, key: "INC-02" },
      { start: 2, end: 6, key: "EXC-01" },
    ]);
    expect(pieces.map((p) => p.quotes)).toEqual([["INC-02"], ["EXC-01", "INC-02"], ["EXC-01"]]);
  });

  it("drops spans out of range, reversed, empty or not whole numbers", () => {
    const pieces = segment("abc", [
      { start: -1, end: 2, style: 0 },
      { start: 2, end: 9, style: 0 },
      { start: 2, end: 1, style: 0 },
      { start: 1, end: 1, style: 0 },
      { start: 0.5, end: 2, style: 0 },
    ], []);
    expect(pieces).toEqual([{ start: 0, end: 3, style: null, quotes: [] }]);
  });

  it("never cuts a surrogate pair", () => {
    const text = "a\u{1D465}b"; // a mathematical italic x: two UTF-16 code units
    expect(segment(text, [{ start: 2, end: 4, style: 0 }], [])).toEqual([{ start: 0, end: 4, style: null, quotes: [] }]);
    expect(segment(text, [{ start: 1, end: 3, style: 0 }], []).map((p) => text.slice(p.start, p.end))).toEqual(["a", "\u{1D465}", "b"]);
  });
});

describe("HighlightedText", () => {
  it("renders the text unchanged, as plain text nodes when nothing is marked", () => {
    const { container } = render(
      <p>
        <HighlightedText text="Drone weed mapping" />
      </p>,
    );
    expect(container.querySelector("p")!.childNodes[0].nodeType).toBe(Node.TEXT_NODE);
    expect(container.textContent).toBe("Drone weed mapping");
  });

  it("marks terms with their style, never colour alone, and hides them when switched off", () => {
    const terms = [
      { start: 0, end: 5, style: 0 },
      { start: 6, end: 10, style: OTHER_STYLE },
    ];
    const { container, rerender } = render(<HighlightedText text="Drone weed mapping" terms={terms} />);
    const marks = [...container.querySelectorAll("[data-term]")];
    expect(marks.map((m) => [m.textContent, m.getAttribute("data-term")])).toEqual([["Drone", "0"], ["weed", "4"]]);
    expect(marks[0].className).toMatch(/decoration-solid/);
    expect(marks[1].className).toMatch(/decoration-wavy/);
    rerender(<HighlightedText text="Drone weed mapping" terms={terms} showTerms={false} />);
    expect(container.querySelectorAll("[data-term]")).toHaveLength(0);
    expect(container.textContent).toBe("Drone weed mapping");
  });

  it("gives each of the five styles its own line style", () => {
    const styles = [0, 1, 2, 3, 4].map((s) => termClass(s).match(/decoration-(solid|double|dashed|dotted|wavy)/)![1]);
    expect(new Set(styles).size).toBe(5);
  });

  it("hands a quote's pieces to renderQuote with the term still inside", () => {
    const { container } = render(
      <HighlightedText
        text="UAV imagery of weeds"
        terms={[{ start: 15, end: 20, style: 2 }]}
        quotes={[{ start: 4, end: 20, key: "INC-01" }]}
        renderQuote={(keys, children) => <a data-q={keys.join(" ")}>{children}</a>}
      />,
    );
    const quote = container.querySelector("[data-q]")!;
    expect(quote.getAttribute("data-q")).toBe("INC-01");
    expect(quote.textContent).toBe("imagery of weeds");
    expect(quote.querySelector('[data-term="2"]')!.textContent).toBe("weeds");
    expect(container.textContent).toBe("UAV imagery of weeds");
  });

  it("keeps right-to-left text in order", () => {
    const text = "صور الطائرات المسيّرة للأعشاب";
    const { container } = render(<HighlightedText text={text} terms={[{ start: 4, end: 12, style: 0 }]} />);
    expect(container.textContent).toBe(text);
    expect(container.querySelector("[data-term]")!.textContent).toBe(text.slice(4, 12));
  });
});
