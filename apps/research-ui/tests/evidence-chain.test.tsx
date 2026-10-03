import { cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceChain } from "@/components/evidence-chain";
import { demoEvidence } from "@/lib/mock-project";
import { SUPPORTED_LOCALES } from "@/i18n";
import { CATALOGS } from "@/messages";

import { OUT_OF_ORDER_NODES } from "./fixtures/presentation-fixture";

describe("EvidenceChain", () => {
  it("renders one item per node, in the order supplied", () => {
    render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} locale="en" />);

    expect(screen.getAllByRole("listitem")).toHaveLength(OUT_OF_ORDER_NODES.length);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels).toEqual(OUT_OF_ORDER_NODES.map((node) => node.label));
  });

  it("numbers the steps sequentially from one", () => {
    const { container } = render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} locale="en" />);

    const renderedNumbers = Array.from(container.querySelectorAll("li")).map(
      (item) => item.firstElementChild?.textContent ?? "",
    );
    expect(renderedNumbers).toEqual(OUT_OF_ORDER_NODES.map((_node, index) => String(index + 1)));
  });

  it("renders each node kind and detail alongside its label", () => {
    render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} locale="en" />);

    for (const node of OUT_OF_ORDER_NODES) {
      expect(screen.getByRole("heading", { name: node.label })).toBeInTheDocument();
      expect(screen.getByText(node.detail, { selector: "bdi" })).toBeInTheDocument();
    }

    // `kind` is a canonical token in the data and a translated word on screen, so
    // the label a reader sees is the catalog value, not the token — checked per
    // locale because an untranslated passthrough would satisfy the English run.
    for (const locale of SUPPORTED_LOCALES) {
      cleanup();
      render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} locale={locale} />);

      for (const node of OUT_OF_ORDER_NODES) {
        const kind = CATALOGS[locale][`evidenceKind.${node.kind}` as "evidenceKind.document"];
        expect(screen.getByText(kind)).toBeInTheDocument();
        // The token itself must never be rendered: it is data, not chrome.
        if (kind !== node.kind) {
          expect(screen.queryByText(node.kind)).toBeNull();
        }
      }
      // The fixture's own text is untouched by translation.
      for (const node of OUT_OF_ORDER_NODES) {
        expect(screen.getByText(node.detail, { selector: "bdi" })).toBeInTheDocument();
      }
    }
  });

  it("renders every node of the demonstration fixture in its declared order", () => {
    render(<EvidenceChain nodes={demoEvidence} locale="en" />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    // Labels are the frozen fixture's own words and are asserted byte for byte:
    // they are the demonstration record, not chrome.
    expect(renderedLabels).toEqual(demoEvidence.map((node) => node.label));

    for (const node of demoEvidence) {
      expect(screen.getByText(CATALOGS.en[`evidenceKind.${node.kind}` as "evidenceKind.chunk"])).toBeInTheDocument();
      expect(screen.getByText(node.detail, { selector: "bdi" })).toBeInTheDocument();
    }
  });
});
