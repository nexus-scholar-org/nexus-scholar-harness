"use strict";

/* Nexus Scholar Harness Console - read-only observability SPA (M5.2).
 * Data-driven, no framework: each view fetches from /api/v1 and re-renders.
 * Auto-refresh: reload-on-focus plus a global SSE change-tick stream. */

const state = {
  view: "dashboard",
  literatureKind: "included",
  litSearch: "",
  synthFiles: null,
  synthDir: null,
  synthSelected: null,
  auditAction: "",
  auditAgent: "",
};

const PHASES = [
  { key: "PHASE_1_DISCOVERY", label: "1 Discover" },
  { key: "PHASE_1_HARVESTING", label: "2 Screen & Harvest" },
  { key: "PHASE_2_SYNTHESIS", label: "3 Synthesize" },
  { key: "PHASE_3_COMPLETE", label: "4 Verify & Trust" },
];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) { /* non-JSON body */ }
    throw new Error(`GET ${path} -> ${res.status} ${detail}`);
  }
  return res.json();
}

function showErr(msg) {
  const box = $("#view-err");
  box.textContent = msg;
  box.classList.remove("hidden");
}
function clearErr() {
  $("#view-err").classList.add("hidden");
}

function fmtTime(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleString([], { dateStyle: "short", timeStyle: "medium" });
}
function fmtBytes(b) {
  if (b == null) return "—";
  if (b >= 1 << 20) return (b / (1 << 20)).toFixed(1) + " MB";
  if (b >= 1 << 10) return (b / (1 << 10)).toFixed(0) + " KB";
  return b + " B";
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function kpi(label, value, sub) {
  const box = el("div", "kpi");
  box.append(el("div", "k-label", label), el("div", "k-value", String(value)));
  if (sub) box.append(el("div", "k-sub", sub));
  return box;
}

/* ---------------- status / dashboard ---------------- */

function phaseChips(current) {
  const row = el("div", "phase-row");
  PHASES.forEach((p, i) => {
    let cls = "phase-step";
    const idx = PHASES.findIndex((x) => x.key === current);
    if (idx > i || current === "PHASE_3_COMPLETE") cls += " done";
    if (p.key === current) cls += " current";
    row.append(el("span", cls, p.label));
    if (i < PHASES.length - 1) row.append(el("span", "arrow", "→"));
  });
  return row;
}

async function renderDashboard() {
  const [status] = await Promise.all([api("/api/v1/workspace/status")]);
  const view = $("#view-dashboard");
  view.innerHTML = "";

  const grid = el("div", "kpi-grid");
  grid.append(
    kpi("Discovered", status.discovered_count),
    kpi("Deduplicated", status.deduped_count),
    kpi("Verified", status.verified_count),
    kpi("Included", status.included_count, `${status.excluded_count} excluded`),
    kpi("PDFs", status.pdfs_count, `${status.extracted_count} extracted`),
    kpi("Vector chunks", status.vector_chunks),
    kpi("Graph nodes", status.graph_nodes),
    kpi("Synthesis", status.synthesis_generated ? "ready" : "pending", status.matrix_rows + " matrix rows"),
  );
  view.append(grid);

  const phaseCard = el("div", "card");
  phaseCard.append(el("h3", "", "Pipeline phase"));
  phaseCard.append(phaseChips(status.phase));
  phaseCard.append(
    el("div", "pill-row").append(
      el("span", "badge accent", status.playbook_type),
      el("span", "badge", status.title),
    ),
  );
  view.append(phaseCard);

  const recent = el("div", "card");
  recent.append(el("h3", "", "Recent audit events"));
  if (!status.latest_events.length) {
    recent.append(el("div", "empty", "no audit events yet"));
  } else {
    status.latest_events.slice().reverse().forEach((evt) => recent.append(auditRow(evt)));
  }
  view.append(recent);
}

/* ---------------- literature ---------------- */

function litFields(doc) {
  const t = doc.title || doc.name || doc.doi || doc.id || "untitled";
  const year = doc.year || (doc.publication_date || "").slice(0, 4);
  return { title: t, year };
}

function renderLitRows(docs, kind) {
  const tbl = el("table", "tbl");
  const head = el("thead", "");
  head.innerHTML = `<tr><th>Title</th><th>Year</th><th>Authors</th><th>Venue</th><th>ID</th></tr>`;
  tbl.append(head);
  const body = el("tbody", "");
  docs.forEach((d) => {
    const { title, year } = litFields(d);
    const auth = Array.isArray(d.authors)
      ? d.authors.map((a) => (typeof a === "string" ? a : a.name || a.author || a.family || "")).filter(Boolean).slice(0, 5).join(", ")
      : d.authors || "—";
    const venue = d.venue || d.source || d.host_venue || d.journal || "—";
    const id = d.doi || d.openalex_id || d.s2_paper_id || d.arxiv_id || d.id || "—";
    const tr = el("tr", "");
    tr.innerHTML = `<td>${esc(title)}</td><td>${esc(year || "—")}</td>`;
    tr.append(el("td", "", auth), el("td", "", venue), el("td", "mono", id));
    body.append(tr);
  });
  tbl.append(body);
  return tbl;
}

async function renderLiterature() {
  const view = $("#view-literature");
  view.innerHTML = "";
  const { literatureKind: kind, litSearch } = state;

  const url = kind === "candidates" ? "/api/v1/literature/candidates?limit=500" : `/api/v1/literature/${kind}`;
  const payload = await api(url);
  const docs = Array.isArray(payload) ? payload : (payload.items || []);

  const bar = el("div", "filter-bar");
  const seg = el("div", "seg");
  ["included", "excluded", "candidates"].forEach((k) => {
    const b = el("button", k === kind ? "active" : "", k[0].toUpperCase() + k.slice(1));
    b.onclick = () => { state.literatureKind = k; renderView(); };
    seg.append(b);
  });
  const input = el("input", "");
  input.placeholder = "filter by title / id / venue…";
  input.value = litSearch;
  input.oninput = (e) => { state.litSearch = e.target.value.toLowerCase(); renderView(); };
  bar.append(seg, input);
  view.append(bar);

  const filtered = litSearch ? docs.filter((d) => JSON.stringify(d).toLowerCase().includes(litSearch)) : docs;
  const card = el("div", "card");
  card.append(el("h3", "", `${kind} · ${filtered.length}/${docs.length}`));
  if (!filtered.length) card.append(el("div", "empty", "no items match"));
  else card.append(renderLitRows(filtered, kind));
  view.append(card);
}

/* ---------------- screening ---------------- */

async function renderScreening() {
  const view = $("#view-screening");
  view.innerHTML = "";
  const payload = await api("/api/v1/screening/batches");
  const card = el("div", "card");
  card.append(el("h3", "count", `Screening batches · ${payload.count}`));
  const tbl = el("table", "tbl");
  tbl.innerHTML = `<thead><tr><th>Batch</th><th>Items</th><th>Decisions</th><th>Collected</th><th>Decision file</th></tr></thead>`;
  const body = el("tbody", "");
  payload.batches.forEach((b) => {
    const tr = el("tr", "");
    tr.append(
      el("td", "mono", b.name),
      el("td", "", String(b.items)),
      el("td", "", String(b.decisions_count)),
      el("td", "", b.collected ? "yes" : "—"),
      el("td", "mono", b.decisions_file || "—"),
    );
    body.append(tr);
  });
  tbl.append(body);
  card.append(tbl);
  view.append(card);
}

/* ---------------- harvest & extract ---------------- */

async function renderHarvest() {
  const view = $("#view-harvest");
  view.innerHTML = "";
  const c = await api("/api/v1/harvest/corpus");

  const grid = el("div", "kpi-grid");
  grid.append(
    kpi("PDFs", c.pdf_count, "under pdfs/"),
    kpi("Extracted", c.extracted_count, "under extracted/"),
    kpi("Manifest", c.manifest && c.manifest.length != null ? c.manifest.length : (c.manifest ? "present" : "—"), "pdf_manifest.json"),
  );
  view.append(grid);

  const card = el("div", "card");
  card.append(el("h3", "count", `Corpus · ${c.pdf_count} PDFs`));
  const tbl = el("table", "tbl");
  tbl.innerHTML = `<thead><tr><th>PDF</th><th>Size</th><th>Extracted</th></tr></thead>`;
  const body = el("tbody", "");
  const extNames = new Set(c.extracted.map((x) => x.name));
  c.pdfs.forEach((p) => {
    const stem = p.name.replace(/\.pdf$/i, "");
    const extName = stem + ".md";
    const tr = el("tr", "");
    tr.append(
      el("td", "mono", p.name),
      el("td", "", fmtBytes(p.size_bytes)),
      el("td", "", extNames.has(extName) ? "yes" : "—"),
    );
    body.append(tr);
  });
  tbl.append(body);
  card.append(tbl);
  view.append(card);
}

/* ---------------- synthesis & trust ---------------- */

const fileKindLabels = {
  consensus: "Consensus synthesis",
  matrix: "Evidence matrix",
  rq_review: "RQ review",
  review: "Literature review",
  other: "File",
  trust: "Trust consensus",
  rob: "Risk of bias",
  coi: "Conflict-of-interest audit",
  open_science: "Open-science artifacts",
  retraction: "Retraction check",
};

function fileChips(files, dir, kindKey) {
  const grid = el("div", "file-grid");
  files.forEach((f) => {
    const chip = el("button", "file-chip" + (state.synthSelected === dir + "/" + f.name ? " selected" : ""));
    chip.append(
      el("div", "f-name", f.name),
      el("div", "f-meta", fileKindLabels[f.kind] + " · " + fmtBytes(f.size_bytes)),
    );
    chip.onclick = async () => {
      state.synthDir = dir;
      state.synthSelected = dir + "/" + f.name;
      renderView();
    };
    grid.append(chip);
  });
  return grid;
}

async function renderSynthesis() {
  const view = $("#view-synthesis");
  view.innerHTML = "";
  const [synth, phase4] = await Promise.all([api("/api/v1/synthesis"), api("/api/v1/phase4")]);
  state.synthFiles = { synthesis: synth.files, phase4: phase4.files };

  const card = el("div", "card");
  card.append(el("h3", "count", `Synthesis artifacts · ${synth.count}`));
  if (synth.files.length) card.append(fileChips(synth.files, "synthesis"));
  else card.append(el("div", "empty", "no synthesis/ files yet"));
  const card4 = el("div", "card");
  card4.append(el("h3", "count", `Trust & verification · ${phase4.count}`));
  if (phase4.files.length) card4.append(fileChips(phase4.files, "phase4"));
  else card4.append(el("div", "empty", "no phase4/ files yet"));
  view.append(card, card4);

  if (state.synthSelected) {
    const [dir, name] = state.synthSelected.split("/");
    const doc = await api(`/api/v1/${dir}/${encodeURIComponent(name)}`);
    const mdBox = el("div", "md-doc");
    mdBox.className = "md md-doc";
    mdBox.innerHTML = marked.parse(doc.content, { gfm: true });
    view.append(mdBox);
  }
}

/* ---------------- graph ---------------- */

function renderGraph() {
  const view = $("#view-graph");
  view.innerHTML = "";
  const wrap = el("div", "iframe-wrap");
  const frame = el("iframe");
  frame.src = "/api/v1/assets/graph";
  wrap.append(frame);
  view.append(wrap);
}

/* ---------------- audit ---------------- */

function auditRow(evt) {
  const box = el("div", "audit-evt");
  const head = el("div", "a-head");
  head.className = "a-head";
  head.append(
    el("span", "badge accent mono", evt.action || "EVENT"),
    el("span", "a-ts", fmtTime(evt.timestamp)),
    el("span", "badge" + (evt.status === "OK" || evt.status === "SUCCESS" ? " ok" : ""), evt.status || ""),
    el("span", "badge", evt.agent_or_tool || "—"),
  );
  box.append(head);
  box.append(el("div", "a-desc", evt.description || evt.event || ""));
  const body = el("div", "a-body");
  body.className = "a-body";
  const details = el("details", "audit-json");
  details.append(el("summary", "", "show full record"));
  const pre = el("pre", "json");
  pre.textContent = JSON.stringify(evt, null, 2);
  details.append(pre);
  body.append(details);
  box.append(body);
  return box;
}

async function renderAudit() {
  const view = $("#view-audit");
  view.innerHTML = "";
  const q = new URLSearchParams();
  if (state.auditAction) q.set("action", state.auditAction);
  if (state.auditAgent) q.set("agent", state.auditAgent);
  q.set("limit", "300");
  const payload = await api("/api/v1/audit/events?" + q.toString());

  const bar = el("div", "filter-bar");
  const input = el("input", "");
  input.placeholder = "filter by action (e.g. SYNC)";
  input.value = state.auditAction;
  input.oninput = (e) => { state.auditAction = e.target.value.trim().toUpperCase(); renderView(); };
  const bar2 = el("input", "");
  bar2.placeholder = "filter by agent / tool";
  bar2.value = state.auditAgent;
  bar2.oninput = (e) => { state.auditAgent = e.target.value.trim(); renderView(); };
  bar.append(input, bar2, el("span", "badge accent", payload.total + " events"));
  view.append(bar);

  const card = el("div", "card");
  if (!payload.items.length) card.append(el("div", "empty", "no audit events match"));
  else payload.items.forEach((evt) => card.append(auditRow(evt)));
  view.append(card);
}

/* ---------------- agent exchange ---------------- */

async function renderActions() {
  const view = $("#view-actions");
  view.innerHTML = "";
  const payload = await api("/api/v1/agents/actions");
  const card = el("div", "card");
  card.append(el("h3", "count", `Actions · ${payload.rows.length}`));
  const tbl = el("table", "tbl action-tbl");
  tbl.innerHTML = `<thead><tr><th>Action</th><th>Label</th><th>Runs as</th><th>MCP tool</th><th>Mutates</th></tr></thead>`;
  const body = el("tbody", "");
  payload.rows.forEach((r) => {
    const tr = el("tr", "");
    tr.append(
      el("td", "mono", r.action_id),
      el("td", "", r.label),
      el("td", "mono", r.command),
      el("td", "mcp-tool", r.mcp_tool || "—"),
      el("td", "", r.mutates ? "yes" : "no"),
    );
    body.append(tr);
  });
  tbl.append(body);
  const scroll = el("div", "scroll-x");
  scroll.append(tbl);
  card.append(scroll);
  view.append(card);
}

/* ---------------- dispatch ---------------- */

const RENDERERS = {
  dashboard: renderDashboard,
  literature: renderLiterature,
  screening: renderScreening,
  harvest: renderHarvest,
  synthesis: renderSynthesis,
  graph: renderGraph,
  audit: renderAudit,
  actions: renderActions,
};

const TITLES = {
  dashboard: "Dashboard",
  literature: "Literature",
  screening: "Screening",
  harvest: "Harvest & Extract",
  synthesis: "Synthesis & Trust",
  graph: "Knowledge Graph",
  audit: "Audit Trail",
  actions: "Agent Exchange",
};

async function renderView() {
  const view = $("#view-" + state.view);
  clearErr();
  try {
    await RENDERERS[state.view]();
    $("#view-title").textContent = TITLES[state.view];
  } catch (err) {
    showErr(err.message);
  }
}

function switchView(name) {
  state.view = name;
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  $$(".view").forEach((v) => {
    const active = v.id === "view-" + name;
    v.classList.toggle("active", active);
    v.setAttribute("aria-hidden", String(!active));
  });
  renderView();
}

/* ---------------- live refresh wiring ---------------- */

function boot() {
  const ws = $("#sidebar-ws");
  Promise.all([api("/api/v1/workspace/status"), api("/api/v1/workspace/meta")])
    .then(([status]) => {
      ws.textContent = (status.title && status.title !== "Unknown" ? status.title + " · " : "") + status.workspace;
      if (status.title && status.title !== "Unknown") $("#view-meta").textContent = status.workspace;
    })
    .catch((e) => showErr(e.message));

  $$(".nav-item").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.view)));
  $("#reload-btn").addEventListener("click", renderView);

  window.addEventListener("focus", renderView);

  const evtSource = new EventSource("/api/v1/events/tick");
  const pill = $("#live-pill");
  evtSource.onopen = () => pill.classList.add("on");
  evtSource.onerror = () => pill.classList.remove("on");
  evtSource.addEventListener("tick", renderView);

  renderView();
}

document.addEventListener("DOMContentLoaded", boot);