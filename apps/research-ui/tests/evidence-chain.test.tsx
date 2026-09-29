import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceChain } from "@/components/evidence-chain";
import { demoEvidence } from "@/lib/mock-project";

import { OUT_OF_ORDER_NODES } from "./fixtures/presentation-fixture";

describe("EvidenceChain", () => {
  it("renders one item per node, in the order supplied", () => {
    render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(OUT_OF_ORDER_NODES.length);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels).toEqual(OUT_OF_ORDER_NODES.map((node) => node.label));
  });

  it("numbers the steps sequentially from one", () => {
    const { container } = render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} />);

    const renderedNumbers = Array.from(container.querySelectorAll("li")).map(
      (item) => item.firstElementChild?.textContent ?? "",
    );
    expect(renderedNumbers).toEqual(OUT_OF_ORDER_NODES.map((_node, index) => String(index + 1)));
  });

  it("renders each node kind and detail alongside its label", () => {
    render(<EvidenceChain nodes={OUT_OF_ORDER_NODES} />);

    for (const node of OUT_OF_ORDER_NODES) {
      expect(screen.getByRole("heading", { name: node.label })).toBeInTheDocument();
      expect(screen.getByText(node.kind)).toBeInTheDocument();
      expect(screen.getByText(node.detail)).toBeInTheDocument();
    }
  });

  it("renders every node of the demonstration fixture in its declared order", () => {
    render(<EvidenceChain nodes={demoEvidence} />);

    const renderedLabels = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(renderedLabels).toEqual(demoEvidence.map((node) => node.label));
  });
});
