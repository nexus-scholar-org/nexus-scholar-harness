import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InceptionCriteria } from "@/components/inception-criteria";
import { InceptionReview } from "@/components/inception-review";
import { InceptionShape } from "@/components/inception-shape";
import { stateCopy } from "@/lib/screening-states";
import { completeDraft, outOfScopeId, proofId } from "./fixtures/inception-engine";
import { setUp } from "./inception-helpers";

/**
 * Step 5's criteria section (spec 11, M11b part D) against the stateful fake: the out-of-scope
 * question asked here, "How you will screen" with the engine's options and no default for the
 * not-reported rule (answer 8), and Continue held while the rule is unchosen.
 */

afterEach(() => vi.unstubAllGlobals());

const decided = (extra: Record<string, unknown> = {}) =>
  completeDraft({ criteria_decisions: { [proofId()]: true, [outOfScopeId("closed-source models")]: true }, ...extra });
const putBodies = (engine: ReturnType<typeof setUp>["engine"]) =>
  engine.calls.filter((c) => c.method === "PUT").map((c) => (c.body as { draft: Record<string, unknown> }).draft);

describe("inception.criteria-block", () => {
  it("names why it cannot be written while something waits", async () => {
    setUp({ draft: completeDraft(), method: true });
    render(<InceptionCriteria locale="en" />);
    await screen.findByText("closed-source models", { selector: "[data-verbatim]" });
    await waitFor(() => expect(document.querySelector("[data-criteria-written]")).toHaveTextContent("Decide every criterion first."));
  });

  it("with every criterion decided, the header reads the counts, and the limits line is there", async () => {
    setUp({ draft: decided({ method_not_reported: "unclear" }), method: true });
    render(<InceptionCriteria locale="en" />);
    await waitFor(() => expect(document.querySelector("[data-criteria-written]")).toHaveTextContent("1 inclusion, 1 exclusion criteria"));
    expect(screen.getByText(/The wording checks compare words, not meaning/)).toBeTruthy();
  });

  it("the out-of-scope question is asked here: semicolons and line breaks separate items, commas do not", async () => {
    const { engine } = setUp({ draft: decided({ method_not_reported: "unclear" }), method: true });
    render(<InceptionCriteria locale="en" />);
    const field = (await screen.findByLabelText("Is anything out of scope?")) as HTMLTextAreaElement;
    expect(field.value).toBe("closed-source models");
    fireEvent.change(field, { target: { value: "closed-source models; satellite only\nindoor, greenhouse" } });
    fireEvent.click(screen.getByRole("button", { name: "Add an out-of-scope topic" }));
    expect(await screen.findByText("satellite only", { selector: "[data-verbatim]" })).toBeTruthy();
    expect(screen.getByText("indoor, greenhouse", { selector: "[data-verbatim]" })).toBeTruthy();
    expect(screen.getByText("Added 2 out-of-scope items")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Save draft and exit" }));
    await waitFor(() => expect(putBodies(engine).length).toBeGreaterThan(0));
    expect(putBodies(engine).at(-1)!.out_of_scope).toEqual(["closed-source models", "satellite only", "indoor, greenhouse"]);
  });

  it("Shape no longer asks it", async () => {
    setUp({ draft: completeDraft() });
    render(<InceptionShape locale="en" />);
    expect(await screen.findByText("Out of scope is asked with the criteria.")).toBeTruthy();
    expect(screen.queryByLabelText("Out of scope")).toBeNull();
  });
});

describe("inception.how-you-will-screen", () => {
  it("draws both questions with the engine's options; visibility is pre-selected, the rule has none and no 'recommended'", async () => {
    setUp({ draft: completeDraft({ method_blinding: "reveal_after_decision", method_not_reported: null }), method: true });
    render(<InceptionCriteria locale="en" />);
    const visibility = await screen.findByRole("group", { name: "When should the agent's draft for a record be shown to you?" });
    expect((within(visibility).getByRole("radio", { name: /After you decide the record/ }) as HTMLInputElement).checked).toBe(true);
    const rule = screen.getByRole("group", { name: /the agent's draft should/ });
    const radios = within(rule).getAllByRole("radio") as HTMLInputElement[];
    expect(radios.map((r) => r.value)).toEqual(["unclear", "decisive_first", "exclude"]);
    expect(radios.every((r) => !r.checked)).toBe(true);
    expect(rule.textContent).not.toMatch(/recommended/i);
    expect(rule).toHaveTextContent("96.8%");
    expect(rule).toHaveTextContent("92.2%");
    expect(rule).toHaveTextContent("Not measured.");
    expect(screen.getByText("You can change both later, from Prepare. The change is recorded beside the signed protocol.")).toBeTruthy();
  });

  it("follows the engine's order, never its own", async () => {
    setUp({ draft: completeDraft({ method_not_reported: null }), method: { order: ["exclude", "unclear", "decisive_first"] } });
    render(<InceptionCriteria locale="en" />);
    const rule = await screen.findByRole("group", { name: /the agent's draft should/ }, { timeout: 8000 });
    expect((within(rule).getAllByRole("radio") as HTMLInputElement[]).map((r) => r.value)).toEqual(["exclude", "unclear", "decisive_first"]);
  });

  it("while the rule is unchosen Continue is held and names why; a choice frees it and the save carries it", async () => {
    const { engine } = setUp({ draft: decided({ method_not_reported: null }), method: true });
    render(<InceptionCriteria locale="en" />);
    const go = await screen.findByRole("button", { name: /^Continue/ });
    await waitFor(() => expect(go).toBeDisabled());
    expect(document.querySelector("[data-rule-blocked]")).toHaveTextContent("Choose what the agent should do when a criterion is not reported, then continue.");
    expect(document.querySelector("[data-method-unchosen]")).toHaveTextContent("Not chosen yet");
    const rule = screen.getByRole("group", { name: /the agent's draft should/ });
    fireEvent.click(within(rule).getByRole("radio", { name: /Exclude only on a clear failure/ }));
    await waitFor(() => expect(go).toBeEnabled());
    fireEvent.click(go);
    await waitFor(() => expect(putBodies(engine).length).toBeGreaterThan(0));
    expect(putBodies(engine).at(-1)).toMatchObject({ method_blinding: "reveal_after_decision", method_not_reported: "decisive_first" });
  });

  it("a draft from before the question says so, with nothing selected", async () => {
    setUp({ draft: decided(), method: true });
    render(<InceptionCriteria locale="en" />);
    expect(await screen.findByText("This draft was started before this question existed.")).toBeTruthy();
    const rule = screen.getByRole("group", { name: /the agent's draft should/ });
    expect((within(rule).getAllByRole("radio") as HTMLInputElement[]).every((r) => !r.checked)).toBe(true);
  });

  it("the visibility question never holds Continue", async () => {
    setUp({ draft: decided({ method_not_reported: "unclear" }), method: true });
    render(<InceptionCriteria locale="en" />);
    const visibility = await screen.findByRole("group", { name: "When should the agent's draft for a record be shown to you?" });
    fireEvent.click(within(visibility).getByRole("radio", { name: /Beside the record/ }));
    await waitFor(() => expect(screen.getByRole("button", { name: /^Continue/ })).toBeEnabled());
  });
});

describe("review.how-you-will-screen (spec 11, Review delta (b))", () => {
  it("lists the two choices in words, says an unchosen rule is not chosen yet, and links back", async () => {
    setUp({ draft: decided({ method_blinding: "reveal_after_decision", method_not_reported: null }) });
    render(<InceptionReview locale="en" />);
    const group = await screen.findByRole("region", { name: "How you will screen" });
    expect(group).toHaveTextContent("The agent's draft is shown after you decide each record.");
    expect(group).toHaveTextContent("Not chosen yet");
    expect(within(group).getByRole("link", { name: "Change" }).getAttribute("href")).toContain("#field-method_not_reported");
  });

  it("names a chosen rule in words, never by its code", async () => {
    setUp({ draft: decided({ method_blinding: "show", method_not_reported: "decisive_first" }) });
    render(<InceptionReview locale="en" />);
    const group = await screen.findByRole("region", { name: "How you will screen" });
    expect(group).toHaveTextContent("The agent's draft is shown beside the record.");
    expect(group).toHaveTextContent("A criterion the abstract does not report leaves the record Unclear unless another criterion clearly fails.");
    expect(group.textContent).not.toMatch(/decisive_first/);
  });
});

describe("review D round 1", () => {
  it("finding 1: out-of-scope text typed but not added is saved with the page", async () => {
    const { engine } = setUp({ draft: decided({ method_not_reported: "unclear" }), method: true });
    render(<InceptionCriteria locale="en" />);
    const field = await screen.findByLabelText("Is anything out of scope?");
    fireEvent.change(field, { target: { value: "closed-source models\nsatellite only" } });
    fireEvent.click(screen.getByRole("button", { name: "Save draft and exit" }));
    await waitFor(() => expect(putBodies(engine).length).toBeGreaterThan(0));
    expect(putBodies(engine).at(-1)!.out_of_scope).toEqual(["closed-source models", "satellite only"]);
  });

  it("finding 2: a preview refused for an unchosen rule shows its own card", async () => {
    expect(stateCopy("en", "METHOD_RULE_UNCHOSEN").known).toBe(true);
    for (const locale of ["fr", "ar"] as const) expect(stateCopy(locale, "METHOD_RULE_UNCHOSEN").known).toBe(true);
    setUp({ draft: decided({ method_not_reported: null }), method: true });
    render(<InceptionReview locale="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Check the protocol" }));
    expect(await screen.findByText("Choose what the agent should do when a criterion is not reported")).toBeTruthy();
  });

  const imported = () => decided({ method_not_reported: "exclude", method_not_reported_source: "imported" });

  it("item 5: an imported rule is shown pre-selected and labelled, but holds Continue until confirmed", async () => {
    const { engine } = setUp({ draft: imported(), method: true });
    render(<InceptionCriteria locale="en" />);
    const rule = await screen.findByRole("group", { name: /the agent.s draft should/ }, { timeout: 8000 });
    expect(within(rule).getByRole("radio", { name: /Exclude when an inclusion criterion/ })).toBeChecked();
    expect(document.querySelector("[data-method-import]")).toHaveTextContent("From the imported protocol");
    expect(document.querySelector("[data-method-unchosen]")).toHaveTextContent("From the imported protocol: confirm this rule or choose another.");
    const go = screen.getByRole("button", { name: /^Continue/ });
    await waitFor(() => expect(go).toBeDisabled());
    fireEvent.click(screen.getByRole("button", { name: "Keep this rule" }));
    await waitFor(() => expect(go).toBeEnabled());
    expect(document.querySelector("[data-method-import]")).toHaveTextContent("From the imported protocol");
    fireEvent.click(go);
    await waitFor(() => expect(putBodies(engine).length).toBeGreaterThan(0));
    expect(putBodies(engine).at(-1)).toMatchObject({ method_not_reported: "exclude", method_not_reported_source: "confirmed" });
  });

  it("item 5: choosing another rule frees Continue and drops the import label", async () => {
    const { engine } = setUp({ draft: imported(), method: true });
    render(<InceptionCriteria locale="en" />);
    const rule = await screen.findByRole("group", { name: /the agent's draft should/ }, { timeout: 8000 });
    fireEvent.click(within(rule).getByRole("radio", { name: /Mark it Unclear whenever/ }));
    const go = screen.getByRole("button", { name: /^Continue/ });
    await waitFor(() => expect(go).toBeEnabled());
    await waitFor(() => expect(document.querySelector("[data-method-import]")).toBeNull());
    fireEvent.click(go);
    await waitFor(() => expect(putBodies(engine).length).toBeGreaterThan(0));
    expect(putBodies(engine).at(-1)).toMatchObject({ method_not_reported: "unclear", method_not_reported_source: "chosen" });
  });

  it("item 5: Review says an imported rule is not confirmed yet", async () => {
    setUp({ draft: imported(), method: true });
    render(<InceptionReview locale="en" />);
    const group = await screen.findByRole("region", { name: "How you will screen" });
    expect(group).toHaveTextContent("A record whose abstract does not report an inclusion criterion is excluded.");
    expect(group).toHaveTextContent("From the imported protocol; not confirmed yet.");
  });
});
