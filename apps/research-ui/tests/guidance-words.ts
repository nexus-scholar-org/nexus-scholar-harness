/**
 * M10d measurement: the words a sighted reader sees on a rendered screen.
 *
 * Skipped: elements with the `hidden` attribute or `aria-hidden`, a hint's
 * panel (`data-hint-body`), screen-reader-only text, and the body of a closed
 * `<details>` (its summary counts). A word is a run of characters with at
 * least one letter or digit.
 */
export function visibleWords(root: Element = document.body): string[] {
  const words: string[] = [];
  const walk = (node: Node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      for (const word of (node.textContent ?? "").split(/\s+/)) if (/[\p{L}\p{N}]/u.test(word)) words.push(word);
      return;
    }
    if (!(node instanceof Element)) return;
    if (node.hasAttribute("hidden") || node.getAttribute("aria-hidden") === "true") return;
    if (node.matches("[data-hint-body], .sr-only, script, style, template")) return;
    if (node instanceof HTMLDetailsElement && !node.open) {
      const summary = node.querySelector(":scope > summary");
      if (summary) walk(summary);
      return;
    }
    node.childNodes.forEach(walk);
  };
  walk(root);
  return words;
}
