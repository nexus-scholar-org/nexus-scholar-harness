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

/**
 * M3i-harvest-robustness: the fake against `DISCOVERY_API_PACKET.md` ("`preparation` and
 * `POST /discovery/runs/{run}/prepare`"). The engine's side of the same shapes and codes is pinned by
 * `tests/console/test_harvest_preparation_api.py`.
 */
describe("discovery engine fake (M3i)", () => {
  const KEYS = ["can_finish", "cannot_finish", "ended_at", "job_id", "marker", "message", "stage", "stages", "state"];
  const preparation = (fake: ReturnType<typeof discoveryEngine>, route: string) => {
    const body = fake.handle("GET", route, null).body as Json;
    return (route.endsWith("/runs") ? (body.runs as Json[])[0].preparation : body.preparation) as Json;
  };

  it("carries the engine's preparation keys on the runs, the run and the hand-off", () => {
    const fake = discoveryEngine({ runs: 1, preparation: "failed" });
    for (const route of ["/api/v1/discovery/runs", "/api/v1/discovery/runs/run_001", "/api/v1/discovery/handoff"]) {
      const view = preparation(fake, route);
      expect(Object.keys(view).sort()).toEqual(KEYS);
      expect([view.state, view.stage, view.marker, view.can_finish, view.job_id]).toEqual(["failed", "verification", true, true, null]);
      expect(Object.keys(view.stages as Json)).toEqual(["deduplication", "hydration"]);
    }
    expect(preparation(discoveryEngine({ runs: 1 }), "/api/v1/discovery/runs").state).toBe("ready");
    expect((discoveryEngine().handle("GET", "/api/v1/discovery/handoff", null).body as Json).preparation).toBeNull();
  });

  it("offers no works of an unfinished harvest, and refuses its accept before NOTHING_STAGED", () => {
    const fake = discoveryEngine({ runs: 1, preparation: "interrupted", legacyRun: true });
    const handoff = fake.handle("GET", "/api/v1/discovery/handoff", null).body as Json;
    expect((handoff.corpus as Json).state).toBe("EMPTY");
    expect((handoff.corpus as Json).from_discovery).toBe(false);
    expect(handoff.provider_mix).toEqual([]);
    expect([(handoff.preparation as Json).stage, (handoff.preparation as Json).marker]).toEqual([null, false]);
    const refused = fake.handle("POST", "/api/v1/screening/corpus/accept", null);
    expect(refused.status).toBe(409);
    expect((refused.body as { detail: Json }).detail).toMatchObject({ code: "PREPARATION_UNFINISHED", details: { run: "run_001", state: "interrupted", stage: null } });
  });

  it("finishes from the saved records with a prepare job, and refuses what the engine refuses", () => {
    const fake = discoveryEngine({ runs: 2, preparation: "failed" });
    const reason = (run: string) => ((fake.handle("POST", `/api/v1/discovery/runs/${run}/prepare`, {}).body as { detail: { code: string; details: Json } }).detail);
    expect(fake.handle("POST", "/api/v1/discovery/runs/run_009/prepare", {}).status).toBe(404);
    expect(reason("run_001")).toMatchObject({ code: "PREPARATION_NOT_AVAILABLE", details: { reason: "superseded" } });
    const started = fake.handle("POST", "/api/v1/discovery/runs/run_002/prepare", {});
    expect(started.status).toBe(202);
    const job = (started.body as { job: Json }).job;
    expect(job.kind).toBe("prepare");
    const done = (fake.handle("GET", `/api/v1/discovery/jobs/${job.job_id}`, null).body as { job: Json }).job;
    expect([done.state, (done.result as Json).run, (done.result as Json).status, (done.result as Json).resumed_from]).toEqual(["succeeded", "run_002", "PENDING_CORPUS_ACCEPT", "hydration"]);
    expect(preparation(fake, "/api/v1/discovery/runs").state).toBe("ready");
    expect(reason("run_002")).toMatchObject({ code: "PREPARATION_NOT_AVAILABLE", details: { reason: "already_prepared" } });
    expect(fake.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/discovery/runs")).toHaveLength(0);
  });

  it("keeps the earlier ready run as the corpus after a search that was stopped (review finding 10)", () => {
    const fake = discoveryEngine({ runs: 1, holdRun: true });
    const job = (fake.handle("POST", "/api/v1/discovery/runs", {}).body as { job: Json }).job;
    fake.handle("POST", `/api/v1/discovery/jobs/${job.job_id}/cancel`, {});
    const rows = (fake.handle("GET", "/api/v1/discovery/runs", null).body as Json).runs as Json[];
    expect(rows.map((r) => [r.run, (r.preparation as Json).state])).toEqual([["run_002", "none"], ["run_001", "ready"]]);
    const handoff = fake.handle("GET", "/api/v1/discovery/handoff", null).body as Json;
    expect([handoff.run, (handoff.corpus as Json).from_discovery, (handoff.preparation as Json).state]).toEqual(["run_001", true, "ready"]);
    expect(fake.handle("POST", "/api/v1/screening/corpus/accept", null).status).toBe(200);
  });

  it("says why an unfinished run cannot be finished: the corpus is accepted, or the records are gone (review finding 3)", () => {
    const frozen = preparation(discoveryEngine({ runs: 1, preparation: "failed", accepted: true }), "/api/v1/discovery/runs");
    expect([frozen.can_finish, frozen.cannot_finish]).toEqual([false, "corpus_accepted"]);
    const gone = preparation(discoveryEngine({ runs: 1, preparation: "failed", recordsMissing: true }), "/api/v1/discovery/runs");
    expect([gone.can_finish, gone.cannot_finish]).toEqual([false, "records_missing"]);
  });

  it("reads a stop after the search before the next step: cancelled, stopped before verification", () => {
    const fake = discoveryEngine({ holdAfterSearch: true });
    const job = (fake.handle("POST", "/api/v1/discovery/runs", {}).body as { job: Json }).job;
    const running = preparation(fake, "/api/v1/discovery/runs");
    expect([running.state, running.stage, running.job_id]).toEqual(["running", "hydration", job.job_id]);
    const cancelled = (fake.handle("POST", `/api/v1/discovery/jobs/${job.job_id}/cancel`, {}).body as { job: Json }).job;
    expect([cancelled.state, (cancelled.result as Json).status]).toEqual(["cancelled", "CANCELLED"]);
    const stopped = preparation(fake, "/api/v1/discovery/runs");
    expect([stopped.state, stopped.stage, stopped.can_finish]).toEqual(["stopped", "verification", true]);
  });
});
