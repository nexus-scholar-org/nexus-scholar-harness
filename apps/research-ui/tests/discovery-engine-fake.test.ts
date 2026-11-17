import { describe, expect, it } from "vitest";

import { discoveryEngine } from "./fixtures/discovery-engine";

/**
 * The fake discovery engine against the M10a packet
 * (`docs/architecture/research_ui/DISCOVERY_API_PACKET.md`, "The database choice per harvest"):
 * the screens' tests only mean something if the fake answers as the engine does.
 */

type Json = Record<string, unknown>;
const names = (body: unknown) => ((body as Json).providers as Json[]).map((p) => p.name);

describe("discovery engine fake (M10a)", () => {
  it("answers ?providers= with the chosen databases first, canonical, in the order given, then the others", () => {
    const fake = discoveryEngine();
    const answer = fake.handle("GET", "/api/v1/discovery/plan?providers=Crossref,Semantic%20Scholar,biorxiv", null);
    expect(answer.status).toBe(200);
    const body = answer.body as Json;
    expect(names(body)).toEqual(["crossref", "semanticscholar", "biorxiv", "openalex", "arxiv", "pubmed"]);
    expect(body.requested_providers).toEqual(["crossref", "semanticscholar", "biorxiv"]);
    expect(body.protocol_providers).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]);
    const rows = (body.providers as Json[]).map((p) => [p.name, p.selected, p.status]);
    expect(rows).toEqual([
      ["crossref", true, "translated"],
      ["semanticscholar", true, "translated"],
      ["biorxiv", true, "selected"],
      ["openalex", false, "not_selected"],
      ["arxiv", false, "not_selected"],
      ["pubmed", false, "not_selected"],
    ]);
  });

  it("keeps a database named twice once, at its first place", () => {
    const fake = discoveryEngine();
    const body = fake.handle("GET", "/api/v1/discovery/plan?providers=arxiv,crossref,arxiv", null).body as Json;
    expect(body.requested_providers).toEqual(["arxiv", "crossref"]);
    expect(names(body).slice(0, 2)).toEqual(["arxiv", "crossref"]);
  });

  it("answers without ?providers= in the known order, the protocol's list selected, requested_providers null", () => {
    const fake = discoveryEngine({ protocolProviders: ["Crossref", "openalex", "Scopus", "crossref"] });
    const body = fake.handle("GET", "/api/v1/discovery/plan", null).body as Json;
    expect(names(body)).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"]);
    // As `run_providers`: canonical, unknown names dropped, a repeat kept once, the protocol's order.
    expect(body.protocol_providers).toEqual(["crossref", "openalex"]);
    expect(body.requested_providers).toBeNull();
    expect((body.providers as Json[]).filter((p) => p.selected).map((p) => p.name)).toEqual(["openalex", "crossref"]);
  });

  it("falls back to the default suite for a protocol list with no known database", () => {
    const fake = discoveryEngine({ protocolProviders: [] });
    const body = fake.handle("GET", "/api/v1/discovery/plan", null).body as Json;
    expect(body.protocol_providers).toEqual(["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]);
  });

  it.each([
    ["an unknown name", "openalex,scopus", ["scopus"]],
    ["an empty item", "openalex,,crossref", [""]],
    ["an empty list", "", [""]],
  ])("refuses %s with PROVIDER_UNKNOWN and the engine's details", (_label, value, unknown) => {
    const fake = discoveryEngine();
    const answer = fake.handle("GET", `/api/v1/discovery/plan?providers=${value}`, null);
    expect(answer.status).toBe(422);
    const detail = (answer.body as { detail: Json }).detail;
    expect(detail.code).toBe("PROVIDER_UNKNOWN");
    expect(detail.details).toEqual({ unknown, known: ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"] });
  });

  it("refuses an unknown or empty providers body on a run, and starts nothing", () => {
    const fake = discoveryEngine();
    for (const providers of [["openalex", "scopus"], []]) {
      const answer = fake.handle("POST", "/api/v1/discovery/runs", { providers });
      expect(answer.status).toBe(422);
      expect((answer.body as { detail: Json }).detail.code).toBe("PROVIDER_UNKNOWN");
    }
    expect(fake.runs).toHaveLength(0);
  });

  it("records requested_providers on the run, runs the legs in that order and lists it on the runs summary", () => {
    const fake = discoveryEngine();
    expect(fake.handle("POST", "/api/v1/discovery/runs", { providers: ["Crossref", "openalex", "crossref"] }).status).toBe(202);
    const summary = ((fake.handle("GET", "/api/v1/discovery/runs", null).body as Json).runs as Json[])[0];
    expect(summary.requested_providers).toEqual(["crossref", "openalex"]);
    const detail = fake.handle("GET", "/api/v1/discovery/runs/run_001", null).body as Json;
    expect(detail.requested_providers).toEqual(["crossref", "openalex"]);
    expect((detail.legs as Json[]).map((l) => l.provider)).toEqual(["crossref", "openalex"]);
  });

  it("records requested_providers null for a run sent no providers, which searches the protocol's list", () => {
    const fake = discoveryEngine({ protocolProviders: ["arxiv", "crossref"] });
    fake.handle("POST", "/api/v1/discovery/runs", {});
    const detail = fake.handle("GET", "/api/v1/discovery/runs/run_001", null).body as Json;
    expect(detail.requested_providers).toBeNull();
    expect((detail.legs as Json[]).map((l) => l.provider)).toEqual(["arxiv", "crossref"]);
  });

  it("gives a protocol database the run left out the report reason not_selected_for_run, and never for a run without a choice", () => {
    const fake = discoveryEngine();
    fake.handle("POST", "/api/v1/discovery/runs", { providers: ["crossref", "openalex"] });
    const chosen = fake.handle("GET", "/api/v1/discovery/report", null).body as Json;
    expect(chosen.not_searched).toEqual([
      { database: "semanticscholar", reason: "not_selected_for_run" },
      { database: "arxiv", reason: "not_selected_for_run" },
      { database: "pubmed", reason: "not_selected_for_run" },
      { database: "biorxiv", reason: "off by default" },
    ]);
    const plain = discoveryEngine();
    plain.handle("POST", "/api/v1/discovery/runs", {});
    expect((plain.handle("GET", "/api/v1/discovery/report", null).body as Json).not_searched).toEqual([{ database: "biorxiv", reason: "off by default" }]);
  });
});
