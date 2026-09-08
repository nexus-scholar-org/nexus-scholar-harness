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
  batchNo: null,
  activeJob: null,
  reasons: {},
  pipelines: null,
  pipelineSpec: null,
  pipelineId: null,
  pipelineTab: "form",
  pipelineDirty: false,
  dryRunResult: null,
  pipelineMsg: "",
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

async function postJSON(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = JSON.stringify((await res.json()).detail || detail);
    } catch (_) { /* non-JSON body */ }
    throw new Error(`POST ${path} -> ${res.status} ${detail}`);
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

/* ---------------- job runner tray ---------------- */

const RUNNER_TRIGGERS = ["sync", "trust_context", "screen_collect", "graph", "export", "status"];
let jobStream = null;

function buildRunnerButtons(rows) {
  const wrap = $("#runner-buttons");
  wrap.innerHTML = "";
  rows
    .filter((r) => RUNNER_TRIGGERS.includes(r.action_id))
    .forEach((r) => {
      const b = el("button", "btn", r.label);
      b.title = r.command;
      b.dataset.action = r.action_id;
      b.onclick = () => startAction(r.action_id);
      wrap.append(b);
    });
}

async function startAction(actionId) {
  clearErr();
  try {
    const res = await postJSON("/api/v1/jobs/start", { action_id: actionId });
    listenJob(res.job);
  } catch (err) {
    showErr(err.message);
  }
}

async function runAction(actionId) {
  clearErr();
  const res = await postJSON("/api/v1/jobs/start", { action_id: actionId });
  listenJob(res.job);
  return res.job;
}

function listenJob(job) {
  state.activeJob = job.job_id;
  if (jobStream) jobStream.close();
  $("#active-job-wrap").classList.remove("hidden");
  const tail = $("#job-tail");
  tail.innerHTML = "";
  renderJobMeta(job);
  setRunnerPill(job.state);
  jobStream = new EventSource(`/api/v1/jobs/${job.job_id}/stream`);
  jobStream.onerror = () => {};
  jobStream.addEventListener("snapshot", (e) => renderJob(JSON.parse(e.data).job, false));
  jobStream.addEventListener("job", (e) => renderJob(JSON.parse(e.data).job, true));
  jobStream.addEventListener("log", (e) => appendTail(JSON.parse(e.data).line));
}

function renderJobMeta(job) {
  const badge = $("#job-badge");
  badge.textContent = `${job.action_id} · ${job.job_id}`;
  $("#job-pid").textContent = job.pid != null ? "pid " + job.pid : (job.state === "running" ? "spawning…" : "pid —");
  $("#job-cmd").textContent = (job.command || []).join(" ");
  $("#job-cancel").classList.toggle("hidden", !["queued", "running"].includes(job.state));
}

function setRunnerPill(stateName) {
  const pill = $("#runner-state");
  pill.className = "badge";
  pill.textContent = stateName;
  if (stateName === "success") pill.classList.add("ok");
  else if (stateName === "failed" || stateName === "cancelled") pill.classList.add("err");
  else if (stateName === "running" || stateName === "queued") pill.classList.add("accent");
}

function renderJob(job, isTerminal) {
  renderJobMeta(job);
  setRunnerPill(job.state);
  document.querySelectorAll("#runner-buttons .btn").forEach((b) => {
    b.classList.toggle("busy", b.dataset.action === job.action_id && ["queued", "running"].includes(job.state));
  });
  if (["success", "failed", "cancelled"].includes(job.state)) {
    appendTail(`⟶ job ${job.job_id} finished (state=${job.state}, exit=${job.exit_code})`, true);
    if (isTerminal && jobStream) {
      setTimeout(() => {
        if (jobStream) jobStream.close();
        jobStream = null;
      }, 3000);
    }
  }
}

function appendTail(line, dim) {
  const tail = $("#job-tail");
  const div = document.createElement("div");
  if (dim) div.className = "tail-dim";
  div.textContent = line || " ";
  tail.append(div);
  tail.scrollTop = tail.scrollHeight;
}

async function cancelActiveJob() {
  const jobId = state.activeJob;
  if (!jobId) return;
  try {
    await postJSON(`/api/v1/jobs/${jobId}/cancel`, {});
  } catch (err) {
    showErr(err.message);
  }
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
  const pillRow = el("div", "pill-row");
  pillRow.append(
    el("span", "badge accent", status.playbook_type),
    el("span", "badge", status.title),
  );
  phaseCard.append(pillRow);
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

  const bar = el("div", "batch-toolbar");
  const collectBtn = el("button", "btn primary", "Run Collect (assemble included/excluded)");
  collectBtn.onclick = () => runAction("screen_collect").catch((e) => showErr(e.message));
  bar.append(collectBtn);
  view.append(bar);

  const card = el("div", "card");
  card.append(el("h3", "", `Screening batches · ${payload.count}`));
  const tbl = el("table", "tbl");
  tbl.innerHTML = `<thead><tr><th>Batch</th><th>Items</th><th>Decisions</th><th>State</th><th></th></tr></thead>`;
  const body = el("tbody", "");
  payload.batches.forEach((b) => {
    const tr = el("tr", "");
    const stateBadge = b.collected
      ? el("span", "badge ok", "collected")
      : (b.decisions_count > 0 ? el("span", "badge warn", "needs collect") : el("span", "badge", "pending"));
    const tdBtn = el("td", "");
    const review = el("button", "btn", b.decisions_count > 0 ? "Review / edit" : "Open screening room");
    review.onclick = () => {
      state.batchNo = parseInt(b.name.replace(/\D/g, ""), 10);
      renderView();
    };
    tdBtn.append(review);
    const tdState = el("td", "");
    tdState.append(stateBadge);
    tr.append(
      el("td", "mono", b.name),
      el("td", "", String(b.items)),
      el("td", "", `${b.decisions_count}/${b.items}`),
      tdState,
      tdBtn,
    );
    body.append(tr);
  });
  tbl.append(body);
  card.append(tbl);
  view.append(card);

  if (state.batchNo != null) {
    await renderBatchRoom();
  } else {
    const hint = el("div", "card");
    hint.append(el("div", "empty", "Select a batch above to open the interactive screening room."));
    view.append(hint);
  }
}

function reasonOptions(batchData) {
  const criteria = (batchData.items.protocol || {}).screening_criteria || {};
  const inc = (criteria.inclusion || []).map((c) => ({ code: c.id, text: c.criterion }));
  const exc = (criteria.exclusion || []).map((c) => ({ code: c.id, text: `${c.criterion}${c.reason_category ? " (" + c.reason_category + ")" : ""}` }));
  return { inc, exc };
}

function paperCard(wsid, paper, batchData, existing) {
  const card = el("div", "paper-card");
  card.dataset.ws = wsid;

  const head = el("div", "p-head");
  head.append(el("span", "p-title", paper.title || "Untitled"), el("span", "badge accent", wsid));
  card.append(head);

  const meta = el("div", "p-meta");
  meta.append(
    el("span", "", paper.year || "—"),
    el("span", "", paper.venue || "—"),
    el("span", "", paper.doi || "—"),
  );
  card.append(meta);

  const abs = paper.abstract && paper.abstract !== "No abstract available." ? paper.abstract : "";
  card.append(el("div", "p-abs", abs));

  const decision = el("div", "p-decision");
  const seg = el("div", "seg");
  const existingDecision = existing && existing.decision ? existing.decision.toUpperCase() : "";
  const incB = el("button", existingDecision === "INCLUDE" ? "active" : "", "Include");
  const excB = el("button", existingDecision === "EXCLUDE" ? "active" : "", "Exclude");
  let current = existingDecision;
  function toggle(kind) {
    current = current === kind ? "" : kind;
    incB.classList.toggle("active", current === "INCLUDE");
    excB.classList.toggle("active", current === "EXCLUDE");
  }
  incB.onclick = () => toggle("INCLUDE");
  excB.onclick = () => toggle("EXCLUDE");
  seg.append(incB, excB);

  const cfd = el("input");
  cfd.type = "range";
  cfd.min = "0";
  cfd.max = "1";
  cfd.step = "0.05";
  cfd.className = "cfd-range";
  cfd.value = String(existing ? existing.confidence : 0.85);
  const cfdLabel = el("span", "cfd", Number(cfd.value).toFixed(2));
  cfd.oninput = () => { cfdLabel.textContent = Number(cfd.value).toFixed(2); };

  const { inc: incReasons, exc: excReasons } = reasonOptions(batchData);
  const sel = el("select", "reason-select");
  sel.append(option("", "reason code…"));
  incReasons.forEach((r) => sel.append(option(r.code, r.code + " (INC)", existing && (existing.matched_inclusion_criteria || []).includes(r.code))));
  excReasons.forEach((r) => sel.append(option(r.code, r.code + " (EXC)", existing && (existing.violated_exclusion_criteria || []).includes(r.code))));
  sel.append(option("", "other — see note"));
  if (sel.options.length <= 1) sel.append(option("", "no criteria in protocol"));

  const note = el("input");
  note.type = "text";
  note.className = "note-input";
  note.placeholder = "screening note / reasoning…";
  if (existing && existing.screening_reasoning) note.value = existing.screening_reasoning;

  decision.append(seg, cfd, cfdLabel, sel, note);
  card.append(decision);
  return card;
}

function option(value, text, selected) {
  const o = document.createElement("option");
  o.value = value;
  o.textContent = text;
  o.selected = Boolean(selected);
  return o;
}

function collectDecisions() {
  const rows = [];
  document.querySelectorAll("#view-screening .paper-card").forEach((card) => {
    const wsid = card.dataset.ws;
    const active = card.querySelector(".seg button.active");
    if (!wsid || !active) return;
    const decision = active.textContent.toUpperCase();
    const rec = {
      workspace_id: wsid,
      decision,
      confidence: parseFloat(card.querySelector(".cfd-range").value),
    };
    const reason = card.querySelector(".reason-select").value;
    if (reason.startsWith("INC")) rec.matched_inclusion_criteria = [reason];
    else if (reason.startsWith("EXC")) rec.violated_exclusion_criteria = [reason];
    const note = card.querySelector(".note-input").value.trim();
    if (note) rec.screening_reasoning = note;
    rows.push(rec);
  });
  return rows;
}

async function renderBatchRoom() {
  const n = state.batchNo;
  const view = $("#view-screening");
  view.innerHTML = ""; // re-render the batch room only (batch table not shown here)
  clearErr();
  let data;
  try {
    data = await api(`/api/v1/screening/batch/${n}`);
  } catch (err) {
    showErr(err.message);
    return;
  }
  const card = el("div", "card");
  const head = el("div", "batch-toolbar");
  head.append(el("h3", "", `Screening room · batch ${n} · ${data.items.papers.length} papers`));
  const saveBtn = el("button", "btn primary", "Save Batch Decisions");
  saveBtn.onclick = async () => {
    const decisions = collectDecisions();
    if (!decisions.length) {
      showErr("Please select at least one decision (Include or Exclude) before saving.");
      return;
    }
    try {
      await postJSON(`/api/v1/screening/batch/${n}/decisions`, {
        batch: n,
        decisions,
        reviewed_by: "console",
        timestamp: new Date().toISOString(),
      });
      renderView();
    } catch (err) {
      showErr(err.message);
    }
  };
  head.append(saveBtn);
  const back = el("button", "btn", "← back to batches");
  back.onclick = () => { state.batchNo = null; renderView(); };
  head.append(back);
  card.append(head);

  const existingById = {};
  (data.decisions || []).forEach((d) => {
    existingById[d.workspace_id || d.study_id] = d;
  });
  data.items.papers.forEach((p) => {
    card.append(paperCard(p.workspace_id || p.study_id, p, data, existingById[p.workspace_id || p.study_id]));
  });
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

  view.append(auditForm());

  const card = el("div", "card");
  if (!payload.items.length) card.append(el("div", "empty", "no audit events match"));
  else payload.items.forEach((evt) => card.append(auditRow(evt)));
  view.append(card);
}

function auditForm() {
  const card = el("div", "card");
  card.append(el("h3", "", "Add log entry (append-only journal)"));
  const form = el("div", "annotate-form");

  const actionRow = el("div", "form-row");
  actionRow.append(el("label", "", "Action *"));
  const actionIn = el("input", "");
  actionIn.placeholder = "e.g. VERIFICATION_REVIEW";
  actionRow.append(actionIn);

  const agentRow = el("div", "form-row");
  agentRow.append(el("label", "", "Agent / tool"));
  const agentIn = el("input", "");
  agentIn.value = "scholar-harness-console";
  agentRow.append(agentIn);

  const statRow = el("div", "form-row");
  statRow.append(el("label", "", "Status"));
  const statSel = el("select", "");
  ["SUCCESS", "PARTIAL", "FAILED"].forEach((s) => statSel.append(option(s, s, s === "SUCCESS")));
  statRow.append(statSel);

  const descRow = el("div", "form-row full");
  descRow.append(el("label", "", "Description *"));
  const descIn = el("input", "");
  descIn.placeholder = "What happened and why it matters";
  descRow.append(descIn);

  form.append(actionRow, agentRow, statRow, descRow);

  const row = el("div", "form-row full");
  const submit = el("button", "btn primary", "Append event");
  submit.onclick = async () => {
    if (!actionIn.value.trim() || !descIn.value.trim()) {
      showErr("action and description are required");
      return;
    }
    try {
      await postJSON("/api/v1/audit/events", {
        action: actionIn.value.trim(),
        agent_or_tool: agentIn.value.trim() || "scholar-harness-console",
        description: descIn.value.trim(),
        status: statSel.value,
      });
      actionIn.value = "";
      descIn.value = "";
      renderView();
    } catch (err) {
      showErr(err.message);
    }
  };
  row.append(submit);
  form.append(row);
  card.append(form);
  return card;
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

/* ---------------- pipeline builder (M5.4 no-code) ---------------- */

const ARCHETYPES = ["PRISMA_SLR", "SCOPING_REVIEW", "RAPID_EVIDENCE", "DESIGN_SCIENCE", "STUDENT_DISSERTATION"];
const BUILTIN_IDS = new Set([
  "prisma_slr_default",
  "scoping_review_default",
  "rapid_evidence_default",
  "design_science_default",
  "student_dissertation_default",
]);
const ON_FAIL = ["abort", "skip", "continue"];

function splitCommand(s) {
  const out = [];
  let cur = "", q = false;
  for (const ch of String(s)) {
    if (ch === '"') { q = !q; continue; }
    if ((ch === " " || ch === "\t") && !q) { if (cur) { out.push(cur); cur = ""; } continue; }
    cur += ch;
  }
  if (cur) out.push(cur);
  return out;
}

function uniquePipelineId(base) {
  let cand = String(base || "pipeline").replace(/[^A-Za-z0-9_-]/g, "_");
  if (!cand) cand = "pipeline";
  let n = 2;
  while ((state.pipelines || []).includes(cand)) cand = `${base}-${n++}`;
  return cand;
}

function blankSpec(base) {
  return {
    schema_version: "0.1.0",
    id: uniquePipelineId(base),
    archetype: "PRISMA_SLR",
    name: "",
    workspace_slug: "",
    settings: {},
    nodes: [],
    edges: [],
    dry_run: { per_node_limit: 25 },
    created_by: "console",
    fingerprint: "",
  };
}

function nextNodeIndex(nodes) {
  let m = 0;
  nodes.forEach((n) => {
    const mm = /_(\d+)$/.exec(n.id || "");
    if (mm) m = Math.max(m, parseInt(mm[1], 10));
  });
  return m + 1;
}

function blankNode(idx) {
  return {
    id: "node_" + idx,
    kit: "scholar-search-kit",
    command: [],
    args: {},
    inputs: [],
    outputs: [],
    on_fail: "abort",
    requires_decision: false,
  };
}

async function editPipeline(id, clone) {
  try {
    const res = await api("/api/v1/pipelines/" + encodeURIComponent(id));
    const spec = JSON.parse(JSON.stringify(res.spec));
    if (clone) spec.id = uniquePipelineId(id + "-copy");
    state.pipelineSpec = spec;
    state.pipelineId = null;
    state.pipelineDirty = false;
    state.pipelineTab = "form";
    state.dryRunResult = null;
    state.pipelineMsg = "";
    renderView();
  } catch (err) {
    showErr(err.message);
  }
}

function openGallery() {
  state.pipelineSpec = null;
  state.pipelineId = null;
  state.pipelineTab = "form";
  state.pipelineDirty = false;
  state.dryRunResult = null;
  state.pipelineMsg = "";
  renderView();
}

function savedBadge() {
  if (state.pipelineDirty) return "unsaved edits";
  return state.pipelineId && state.pipelineId === state.pipelineSpec.id
    ? "saved · " + state.pipelineId
    : "draft · not saved yet";
}

function canRunPipeline() {
  return Boolean(state.pipelineSpec && state.pipelineId && state.pipelineId === state.pipelineSpec.id && !state.pipelineDirty);
}

function markDirty() {
  state.pipelineDirty = true;
  const bad = $("#view-pipelines .p-dirty");
  if (bad) { bad.textContent = "unsaved edits"; bad.classList.add("warn"); }
  const run = $("#view-pipelines .p-run");
  if (run) run.disabled = true;
}

async function renderPipelines() {
  const view = $("#view-pipelines");
  view.innerHTML = "";
  const payload = await api("/api/v1/pipelines");
  state.pipelines = payload.ids;
  view.append(galleryCard(payload.ids));
  if (state.pipelineSpec) view.append(pipelineEditor());
}

function galleryCard(ids) {
  const card = el("div", "card");
  const head = el("div", "batch-toolbar");
  head.append(el("h3", "count", `Pipeline templates & saved specs · ${ids.length}`));
  const newBtn = el("button", "btn primary", "+ New blank");
  newBtn.title = "Start from an empty PipelineSpec";
  newBtn.onclick = () => {
    state.pipelineSpec = blankSpec("my_pipeline");
    state.pipelineId = null;
    state.pipelineDirty = false;
    state.pipelineTab = "form";
    state.dryRunResult = null;
    state.pipelineMsg = "";
    renderView();
  };
  head.append(newBtn);
  card.append(head);

  const grid = el("div", "gallery");
  ids.forEach((id) => {
    const pc = el("div", "p-card");
    pc.append(el("div", "p-name", id));
    pc.append(el("div", "p-hint", BUILTIN_IDS.has(id) ? "builtin template · browse or clone" : "saved spec in .harness-console/pipelines/"));
    const row = el("div", "pill-row");
    const open = el("button", "btn", "Open");
    open.title = "Open in the builder";
    open.onclick = () => editPipeline(id, false);
    const clone = el("button", "btn", "Clone");
    clone.title = "Duplicate as a new draft";
    clone.onclick = () => editPipeline(id, true);
    row.append(open, clone);
    pc.append(row);
    grid.append(pc);
  });
  card.append(grid);
  return card;
}

function pipelineEditor() {
  const root = el("div", "p-editor");
  const spec = state.pipelineSpec;
  const head = el("div", "batch-toolbar");
  const back = el("button", "btn", "← gallery");
  back.onclick = openGallery;
  head.append(back);

  const tabs = el("div", "p-tabs");
  ["form", "json"].forEach((t) => {
    const b = el("button", "btn" + (state.pipelineTab === t ? " primary" : ""), t);
    b.title = t === "form" ? "No-code form editor" : "Raw PipelineSpec JSON";
    b.onclick = () => switchPipelineTab(t);
    tabs.append(b);
  });
  head.append(tabs);

  head.append(el("span", "badge p-dirty" + (state.pipelineDirty ? " warn" : ""), savedBadge()));

  const dry = el("button", "btn", "Dry-run");
  dry.title = "Validate + plan execution order (writes nothing canonical)";
  dry.onclick = dryRunSpec;
  const save = el("button", "btn primary", "Save");
  save.title = "Validate and persist PipelineSpec to .harness-console/pipelines/";
  save.onclick = saveSpec;
  const run = el("button", "btn accent p-run", "Run");
  run.disabled = !canRunPipeline();
  run.title = canRunPipeline() ? "Run the saved pipeline via the Job Runner" : "Save the spec first to enable Run";
  run.onclick = runPipeline;
  const exp = el("button", "btn", "Export .sh");
  exp.title = "Download the rendered `uv run` shell script (saves first if needed)";
  exp.onclick = exportScript;
  head.append(dry, save, run, exp);
  root.append(head);

  if (state.pipelineTab === "json") root.append(pipelineJSONCard(spec));
  else root.append(pipelineFormCard(spec));

  if (state.dryRunResult) root.append(dryRunPanel(state.dryRunResult));
  if (state.pipelineMsg) root.append(el("div", "empty", state.pipelineMsg));
  else root.append(el("div", "foot-hint", "Nodes run via `uv run <kit command>` · `{{key}}` resolves settings / slots / node outputs · Dry-run never writes canonical files"));

  root.addEventListener("input", markDirty);
  root.addEventListener("change", markDirty);
  return root;
}

function pRow(labelText, input) {
  const row = el("div", "form-row");
  row.append(el("label", "", labelText), input);
  return row;
}

function pipelineFormCard(spec) {
  const card = el("div", "card");
  card.append(el("h3", "", "Spec · form"));

  const top = el("div", "spec-grid");
  const idIn = el("input");
  idIn.type = "text";
  idIn.dataset.pf = "id";
  idIn.value = spec.id;
  top.append(pRow("id *", idIn));
  const archSel = el("select");
  archSel.dataset.pf = "archetype";
  ARCHETYPES.forEach((a) => archSel.append(option(a, a, a === spec.archetype)));
  top.append(pRow("archetype", archSel));
  const nameIn = el("input");
  nameIn.type = "text";
  nameIn.dataset.pf = "name";
  nameIn.value = spec.name || "";
  top.append(pRow("name", nameIn));
  const wsIn = el("input");
  wsIn.type = "text";
  wsIn.dataset.pf = "workspace_slug";
  wsIn.value = spec.workspace_slug || "";
  top.append(pRow("workspace slug", wsIn));
  const limIn = el("input");
  limIn.type = "number";
  limIn.min = "1";
  limIn.dataset.pf = "dryperm";
  limIn.value = String(((spec.dry_run || {}).per_node_limit) || 25);
  top.append(pRow("dry-run per-node limit", limIn));
  card.append(top);

  const settingsIn = el("textarea");
  settingsIn.dataset.pf = "settings";
  settingsIn.rows = 5;
  settingsIn.value = JSON.stringify(spec.settings || {}, null, 2);
  const settingsRow = el("div", "form-row full");
  settingsRow.append(el("label", "", "settings (JSON) — plain keys like queries / provider_priority"), settingsIn);
  card.append(settingsRow);

  const sec = el("div", "full");
  sec.append(el("h4", "", "Nodes"));
  spec.nodes.forEach((n, idx) => sec.append(nodeCard(spec, n, idx)));
  const addBtn = el("button", "btn", "+ Add node");
  addBtn.onclick = () => {
    if (!collectEditor()) return;
    state.pipelineSpec.nodes.push(blankNode(nextNodeIndex(state.pipelineSpec.nodes)));
    state.pipelineDirty = true;
    renderView();
  };
  sec.append(addBtn);
  card.append(sec);

  card.append(pipelineEdgesSummary(spec));
  return card;
}

function nodeCard(spec, node, idx) {
  const nc = el("div", "node-card");
  const head = el("div", "node-head full");
  head.append(el("span", "badge accent", "N" + (idx + 1)));
  head.append(el("span", "mono", node.id));
  const rm = el("button", "btn danger", "Remove");
  rm.onclick = () => {
    if (!collectEditor()) return;
    const s = state.pipelineSpec;
    const id = s.nodes[idx].id;
    s.nodes = s.nodes.filter((_, i) => i !== idx);
    s.edges = s.edges.filter((e) => e[0] !== id && e[1] !== id);
    state.pipelineDirty = true;
    renderView();
  };
  head.append(rm);
  nc.append(head);

  const idIn = el("input");
  idIn.type = "text";
  idIn.dataset.node = "id";
  idIn.value = node.id;
  idIn.title = "renaming updates edges; `{{old.output}}` refs must be updated by hand";
  idIn.onchange = () => {
    const oldId = node.id;
    if (!collectEditor()) return;
    const s = state.pipelineSpec;
    const newId = s.nodes[idx].id;
    if (oldId && oldId !== newId) s.edges = s.edges.map((e) => e.map((x) => (x === oldId ? newId : x)));
    renderView();
  };
  nc.append(pRow("node id", idIn));

  const kitIn = el("input");
  kitIn.type = "text";
  kitIn.dataset.node = "kit";
  kitIn.value = node.kit;
  kitIn.placeholder = "e.g. scholar-search-kit";
  nc.append(pRow("kit", kitIn));

  const cmdIn = el("input");
  cmdIn.type = "text";
  cmdIn.dataset.node = "command";
  cmdIn.value = (node.command || []).join(" ");
  cmdIn.placeholder = "e.g. scholar-search run";
  nc.append(pRow("command (uv run …)", cmdIn));

  const onfailSel = el("select");
  onfailSel.dataset.node = "onfail";
  ON_FAIL.forEach((o) => onfailSel.append(option(o, o + (o === "skip" ? " (skip node)" : o === "continue" ? " (continue rest)" : ""), o === node.on_fail)));
  nc.append(pRow("on failure", onfailSel));

  const rdIn = el("input");
  rdIn.type = "checkbox";
  rdIn.dataset.node = "rd";
  rdIn.checked = Boolean(node.requires_decision);

  const argsIn = el("textarea");
  argsIn.dataset.node = "args";
  argsIn.rows = 5;
  argsIn.value = node.args && Object.keys(node.args).length ? JSON.stringify(node.args, null, 2) : "{}";
  nc.append(pRow("args (JSON) — may use {{...}} templates", argsIn));

  const outIn = el("textarea");
  outIn.dataset.node = "outputs";
  outIn.rows = 2;
  outIn.value = (node.outputs || []).join("\n");
  const outRow = pRow("outputs — one per line", outIn);
  outRow.classList.add("full");
  nc.append(outRow);

  const rdRow = pRow("requires decision (agent handoff)", rdIn);
  rdRow.classList.add("full");
  nc.append(rdRow);

  const deps = el("div", "deps");
  spec.nodes.forEach((other) => {
    if (other.id === node.id) return;
    const cb = el("input");
    cb.type = "checkbox";
    const has = spec.edges.some((e) => e[0] === other.id && e[1] === node.id);
    cb.checked = has;
    cb.onchange = () => {
      if (cb.checked) {
        if (!state.pipelineSpec.edges.some((e) => e[0] === other.id && e[1] === node.id)) state.pipelineSpec.edges.push([other.id, node.id]);
      } else {
        state.pipelineSpec.edges = state.pipelineSpec.edges.filter((e) => !(e[0] === other.id && e[1] === node.id));
      }
      markDirty();
      updateEdgesHint();
    };
    const lbl = el("label", "");
    lbl.append(cb, el("span", "mono", other.id));
    deps.append(lbl);
  });
  const depsRow = el("div", "full");
  depsRow.append(el("label", "", "depends on"), deps);
  nc.append(depsRow);
  return nc;
}

function pipelineEdgesSummary(spec) {
  const box = el("div", "full");
  box.append(el("label", "", "Edges"));
  const chips = el("div", "chips");
  if (!spec.edges.length) chips.append(el("span", "badge", "no edges — nodes run independently"));
  else spec.edges.forEach((e) => chips.append(el("span", "badge", e[0] + " → " + e[1])));
  box.append(chips);
  box.dataset.edgebox = "1";
  return box;
}

function updateEdgesHint() {
  const box = $("#view-pipelines [data-edgebox]");
  if (!box) return;
  box.innerHTML = "";
  box.append(el("label", "", "Edges"));
  const chips = el("div", "chips");
  if (!state.pipelineSpec.edges.length) chips.append(el("span", "badge", "no edges — nodes run independently"));
  else state.pipelineSpec.edges.forEach((e) => chips.append(el("span", "badge", e[0] + " → " + e[1])));
  box.append(chips);
}

function pipelineJSONCard(spec) {
  const card = el("div", "card");
  card.append(el("h3", "", "Spec · raw JSON"));
  const ta = el("textarea");
  ta.dataset.pj = "1";
  ta.className = "json-editor";
  ta.value = JSON.stringify(spec, null, 2);
  card.append(ta);
  const row = el("div", "form-row full");
  const apply = el("button", "btn", "Apply JSON to editor");
  apply.onclick = () => {
    clearErr();
    if (!collectJSON()) return;
    state.pipelineDirty = true;
    state.pipelineMsg = "JSON applied — validate with Dry-run, then Save";
    renderView();
  };
  row.append(apply, el("span", "foot-hint", "Schema 0.1.0 · server validates on Dry-run / Save"));
  card.append(row);
  return card;
}

function switchPipelineTab(t) {
  if (t === state.pipelineTab) return;
  clearErr();
  if (t === "form" && !collectJSON()) return;
  state.pipelineTab = t;
  renderView();
}

function collectEditor() {
  if (state.pipelineTab === "json") return collectJSON();
  const root = $("#view-pipelines .p-editor");
  if (!root || !state.pipelineSpec) return null;
  const spec = state.pipelineSpec;
  const val = (sel) => { const n = root.querySelector(sel); return n ? n.value : ""; };

  spec.id = val('[data-pf="id"]').trim() || spec.id;
  spec.name = val('[data-pf="name"]').trim();
  spec.archetype = val('[data-pf="archetype"]') || "PRISMA_SLR";
  spec.workspace_slug = val('[data-pf="workspace_slug"]').trim();
  const lim = parseInt(val('[data-pf="dryperm"]'), 10);
  spec.dry_run = { per_node_limit: Number.isFinite(lim) && lim > 0 ? lim : 25 };

  const settingsRaw = val('[data-pf="settings"]').trim();
  if (settingsRaw) {
    try { spec.settings = JSON.parse(settingsRaw); }
    catch (_) { showErr("settings is not valid JSON"); return null; }
  } else spec.settings = {};

  const cards = Array.from(root.querySelectorAll(".node-card"));
  try {
    cards.forEach((nc, idx) => {
      if (idx >= spec.nodes.length) return;
      const node = spec.nodes[idx];
      node.id = (nc.querySelector('[data-node="id"]').value.trim() || node.id);
      node.kit = nc.querySelector('[data-node="kit"]').value.trim();
      node.command = splitCommand(nc.querySelector('[data-node="command"]').value);
      const argsRaw = nc.querySelector('[data-node="args"]').value.trim();
      node.args = argsRaw ? JSON.parse(argsRaw) : {};
      node.outputs = nc.querySelector('[data-node="outputs"]').value.split(/\r?\n|,/).map((s) => s.trim()).filter(Boolean);
      node.on_fail = nc.querySelector('[data-node="onfail"]').value || "abort";
      node.requires_decision = nc.querySelector('[data-node="rd"]').checked;
    });
  } catch (err) {
    showErr("node args is not valid JSON: " + err.message);
    return null;
  }
  return spec;
}

function collectJSON() {
  const ta = $("#view-pipelines [data-pj]");
  if (!ta) return null;
  try {
    state.pipelineSpec = JSON.parse(ta.value);
    return state.pipelineSpec;
  } catch (err) {
    showErr("spec JSON is not valid: " + err.message);
    return null;
  }
}

async function saveSpec() {
  const spec = collectEditor();
  if (!spec) return;
  clearErr();
  try {
    const res = await postJSON("/api/v1/pipelines", { spec });
    state.pipelineSpec = res.spec;
    state.pipelineId = res.spec.id;
    state.pipelineDirty = false;
    state.dryRunResult = null;
    state.pipelineMsg = "saved " + res.spec.id + " (fingerprint " + res.spec.fingerprint.slice(0, 24) + "…)";
    renderView();
  } catch (err) {
    showErr(err.message);
  }
}

async function dryRunSpec() {
  const spec = collectEditor();
  if (!spec) return;
  clearErr();
  try {
    if (state.pipelineDirty || !state.pipelineId || state.pipelineId !== spec.id) {
      const res = await postJSON("/api/v1/pipelines", { spec });
      state.pipelineSpec = res.spec;
      state.pipelineId = res.spec.id;
      state.pipelineDirty = false;
    }
    const body = { per_node_limit: (spec.dry_run || {}).per_node_limit || 25 };
    const dry = await postJSON("/api/v1/pipelines/" + encodeURIComponent(state.pipelineId) + "/dry-run", body);
    state.dryRunResult = dry;
    state.pipelineMsg = dry.message;
    renderView();
  } catch (err) {
    showErr(err.message);
  }
}

async function runPipeline() {
  if (!canRunPipeline()) { showErr("save the spec first, then run"); return; }
  clearErr();
  try {
    const res = await postJSON("/api/v1/jobs/start", { action_id: "pipeline", pipeline_id: state.pipelineId });
    listenJob(res.job);
  } catch (err) {
    showErr(err.message);
  }
}

async function exportScript() {
  const spec = collectEditor();
  if (!spec) return;
  clearErr();
  try {
    if (state.pipelineDirty || !state.pipelineId || state.pipelineId !== spec.id) {
      const res = await postJSON("/api/v1/pipelines", { spec });
      state.pipelineSpec = res.spec;
      state.pipelineId = res.spec.id;
      state.pipelineDirty = false;
    }
    const res = await fetch(`/api/v1/pipelines/${encodeURIComponent(state.pipelineId)}/export?script_format=sh`);
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = JSON.stringify((await res.json()).detail || detail); } catch (_) { /* non-JSON body */ }
      throw new Error(`GET export -> ${res.status} ${detail}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = state.pipelineId + ".sh";
    document.body.append(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    state.pipelineMsg = "exported " + state.pipelineId + ".sh — run with `bash <script> [workspace]`";
    renderView();
  } catch (err) {
    showErr(err.message);
  }
}

function dryRunPanel(res) {
  const box = el("div", "drypanel" + (res.valid ? " ok" : " err"));
  const head = el("div", "a-head");
  head.append(el("span", "badge" + (res.valid ? " ok" : " err"), res.valid ? "valid" : "invalid"));
  head.append(el("span", "p-hint", res.message || ""));
  box.append(head);
  if (res.errors && res.errors.length) {
    const ul = el("ul", "strip");
    res.errors.forEach((e) => ul.append(el("li", "e-msg", "- " + e)));
    box.append(ul);
  }
  if (res.warnings && res.warnings.length) {
    const ul = el("ul", "strip");
    res.warnings.forEach((e) => ul.append(el("li", "w-msg", "~ " + e)));
    box.append(ul);
  }
  if (res.nodes_ordered && res.nodes_ordered.length) {
    const chips = el("div", "chips");
    res.nodes_ordered.forEach((id) => chips.append(el("span", "badge", id)));
    const row = el("div", "full");
    row.append(el("label", "", "execution order"), chips);
    box.append(row);
  }
  if (res.requires_decision && res.requires_decision.length) {
    const chips = el("div", "chips");
    res.requires_decision.forEach((id) => chips.append(el("span", "badge warn", id + " · handoff")));
    const row = el("div", "full");
    row.append(el("label", "", "requires decision"), chips);
    box.append(row);
  }
  return box;
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
  pipelines: renderPipelines,
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
  pipelines: "Pipeline Builder",
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

  api("/api/v1/agents/actions")
    .then((p) => buildRunnerButtons(p.rows))
    .catch((e) => showErr(e.message));
  const tray = $("#runner-tray");
  $("#tray-toggle").addEventListener("click", () => {
    const minimized = tray.classList.toggle("minimized");
    $("#tray-toggle").textContent = minimized ? "expand" : "minimize";
  });
  $("#job-cancel").addEventListener("click", cancelActiveJob);

  window.addEventListener("focus", renderView);

  const evtSource = new EventSource("/api/v1/events/tick");
  const pill = $("#live-pill");
  evtSource.onopen = () => pill.classList.add("on");
  evtSource.onerror = () => pill.classList.remove("on");
  evtSource.addEventListener("tick", renderView);

  renderView();
}

document.addEventListener("DOMContentLoaded", boot);