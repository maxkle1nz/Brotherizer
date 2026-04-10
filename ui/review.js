const state = {
  job: null,
  capabilities: null,
  lastError: "",
  mode: "runtime",
};

const el = {
  kpiGrid: document.getElementById("kpi-grid"),
  requestChips: document.getElementById("request-chips"),
  statusStrip: document.getElementById("status-strip"),
  sourceCopy: document.getElementById("source-copy"),
  runtimeInsight: document.getElementById("runtime-insight"),
  capabilitiesCopy: document.getElementById("capabilities-copy"),
  choiceHistory: document.getElementById("choice-history"),
  winnerTitle: document.getElementById("winner-title"),
  winnerChips: document.getElementById("winner-chips"),
  winnerCopy: document.getElementById("winner-copy"),
  winnerWhy: document.getElementById("winner-why"),
  choosePanel: document.getElementById("choose-panel"),
  candidateStack: document.getElementById("candidate-stack"),
  loadDemoBtn: document.getElementById("load-demo-btn"),
};

let errorNode = null;

const params = new URLSearchParams(window.location.search);

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function chip(label, className = "") {
  return `<span class="chip ${className}">${escapeHtml(label)}</span>`;
}

function statusChip(label, status) {
  return `<span class="status-chip" data-status="${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function emptyBlock(message, className = "empty-state") {
  return `<div class="${className}">${escapeHtml(message)}</div>`;
}

function currentJobId() {
  const match = window.location.pathname.match(/^\/review\/([^/]+)$/);
  return match?.[1] || params.get("job") || params.get("job_id") || "";
}

function normalizeCapabilities(payload) {
  if (!payload || typeof payload !== "object") {
    return demoCapabilities();
  }

  return {
    providers: payload.providers || {},
    limits: payload.limits || {},
    ui: payload.ui || {},
    features: payload.features || {},
  };
}

function normalizeJob(payload) {
  const request = payload.request || {};
  const candidates = Array.isArray(payload.candidates)
    ? payload.candidates.map((candidate, index) => ({
        candidate_id: candidate.candidate_id || candidate.id || `brc_candidate_${index + 1}`,
        rank: candidate.rank ?? index + 1,
        label: candidate.label || "candidate",
        text: candidate.text || "",
        score: candidate.score ?? candidate.rerank_score ?? null,
        why: candidate.why || "",
        ...candidate,
      }))
    : [];
  const winnerCandidateId =
    payload.winner_candidate_id ||
    payload.winner?.candidate_id ||
    payload.winner?.id ||
    null;
  const chosenCandidateId = payload.chosen_candidate_id || payload.chosen?.candidate_id || null;
  const winner =
    payload.winner ||
    candidates.find((candidate) => candidate.candidate_id === winnerCandidateId) ||
    candidates[0] ||
    null;
  const chosen =
    payload.chosen ||
    candidates.find((candidate) => candidate.candidate_id === chosenCandidateId) ||
    null;

  return {
    job_id: payload.job_id || "brw_demo",
    status: payload.status || "completed",
    source_text:
      payload.source_text ||
      request.text ||
      payload.source?.text ||
      "",
    request: {
      mode: request.mode || payload.mode || "casual_us_human_mode",
      surface_mode: request.surface_mode || payload.surface_mode || "reply",
      query: request.query || payload.query || "",
    },
    insight: payload.insight || {},
    winner_candidate_id: winnerCandidateId,
    chosen_candidate_id: chosenCandidateId,
    review_url: payload.review_url || window.location.href,
    candidates,
    winner,
    chosen,
    choice_history: Array.isArray(payload.choice_history)
      ? payload.choice_history
      : payload.choice
        ? [payload.choice]
        : [],
    timestamps: payload.timestamps || {
      created_at: payload.created_at || "",
      updated_at: payload.updated_at || "",
      completed_at: payload.completed_at || "",
    },
  };
}

function demoCapabilities() {
  return {
    providers: {
      generation: {
        name: "perplexity",
        model: "sonar",
      },
      judge: {
        enabled: true,
        name: "xai",
        model: "grok-4-1-fast-reasoning",
      },
    },
    limits: {
      max_input_chars: 120000,
      max_candidate_count: 8,
      supports_document_rewrite: false,
    },
    ui: {
      companion_enabled: true,
      modes: ["off", "auto", "always"],
    },
    features: {
      surface_mode: true,
      choose_candidate: true,
      streaming: false,
    },
  };
}

function demoJob() {
  return normalizeJob({
    job_id: "brw_demo_job",
    status: "chosen",
    request: {
      mode: "casual_us_human_mode",
      surface_mode: "reply",
      text:
        "I think the product idea is strong, but the page still sounds too polished and a bit distant.",
      query: "Make it sound more internet-native and less brochure.",
    },
    winner_candidate_id: "brc_win",
    chosen_candidate_id: "brc_alt",
    review_url: `${window.location.origin}/ui/review.html?demo=1`,
    insight: {
      mode: "casual_us_human_mode",
      surface_mode: "reply",
      judge_enabled: true,
      formatting_pack: "casual_us_reply",
    },
    candidates: [
      {
        candidate_id: "brc_win",
        rank: 1,
        label: "winner",
        text:
          "The idea is solid. The page just still sounds a little too polished and not quite like someone actually saying it.",
        score: 4.21,
        why: "Closest to source while sounding more natural and spoken.",
      },
      {
        candidate_id: "brc_alt",
        rank: 2,
        label: "sharper",
        text:
          "The idea's there. The page just still reads a bit polished and weirdly distant.",
        score: 4.08,
        why: "Punchier and more internet-native, but slightly less faithful.",
      },
      {
        candidate_id: "brc_safe",
        rank: 3,
        label: "safer",
        text:
          "The concept works. The page still feels overly polished and a little detached.",
        score: 3.92,
        why: "Clean and usable, but flatter than the top options.",
      },
    ],
    choice_history: [
      {
        choice_id: "brch_engine",
        candidate_id: "brc_win",
        actor_type: "engine",
        actor_id: "brotherizer",
        reason: "Highest rerank score.",
        created_at: "2026-04-10T01:44:12Z",
      },
      {
        choice_id: "brch_user",
        candidate_id: "brc_alt",
        actor_type: "user",
        actor_id: "demo-user",
        reason: "Preferred the punchier option.",
        created_at: "2026-04-10T01:45:18Z",
      },
    ],
    timestamps: {
      created_at: "2026-04-10T01:44:01Z",
      updated_at: "2026-04-10T01:45:18Z",
      completed_at: "2026-04-10T01:44:12Z",
    },
  });
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = payload?.error?.message || payload?.error || `Request failed: ${response.status}`;
    throw new Error(error);
  }
  return payload;
}

async function loadCapabilities() {
  try {
    const payload = await fetchJson("/v1/capabilities");
    state.capabilities = normalizeCapabilities(payload);
  } catch (_error) {
    state.capabilities = demoCapabilities();
  }
}

async function loadJob() {
  const jobId = currentJobId();
  if (!jobId || params.get("demo") === "1") {
    state.job = demoJob();
    return;
  }

  try {
    const payload = await fetchJson(`/v1/jobs/${encodeURIComponent(jobId)}`);
    state.job = normalizeJob(payload);
    state.lastError = "";
  } catch (error) {
    state.job = null;
    state.lastError = error.message;
  }
}

function renderKpis() {
  const job = state.job;
  const candidates = job?.candidates || [];
  const completedAt = job?.timestamps?.completed_at || "not completed yet";
  const judgeLabel = state.capabilities?.providers?.judge?.enabled ? "judge on" : "judge off";
  const chosenLabel = job?.chosen_candidate_id ? "manual choice saved" : "engine winner only";

  el.kpiGrid.innerHTML = [
    {
      label: "Job",
      value: job?.job_id || "unknown",
      copy: completedAt,
    },
    {
      label: "Candidates",
      value: String(candidates.length),
      copy: chosenLabel,
    },
    {
      label: "Judge",
      value: judgeLabel,
      copy: state.capabilities?.providers?.judge?.model || "not available",
    },
  ]
    .map(
      (item) => `
        <article class="metric-card">
          <p class="eyebrow">${escapeHtml(item.label)}</p>
          <strong>${escapeHtml(item.value)}</strong>
          <p class="metric-copy">${escapeHtml(item.copy)}</p>
        </article>
      `,
    )
    .join("");
}

function renderRequest() {
  const job = state.job;
  if (!job) {
    el.requestChips.innerHTML = "";
    el.statusStrip.innerHTML = emptyBlock("No runtime job loaded.");
    el.sourceCopy.innerHTML = emptyBlock("Use ?job=brw_xxx or load the demo job.");
    return;
  }

  const requestChips = [
    chip(job.request.mode),
    chip(`surface:${job.request.surface_mode}`),
    job.request.query ? chip(`goal:${job.request.query}`) : "",
  ]
    .filter(Boolean)
    .join("");
  el.requestChips.innerHTML = requestChips;

  const statusBits = [
    statusChip(job.status, job.status),
    job.winner_candidate_id ? chip(`winner:${job.winner_candidate_id}`) : "",
    job.chosen_candidate_id ? chip(`chosen:${job.chosen_candidate_id}`, "is-good") : chip("chosen:none"),
  ]
    .filter(Boolean)
    .join("");
  el.statusStrip.innerHTML = statusBits;

  const sourceText = job.source_text || "Runtime payload did not include source text.";
  el.sourceCopy.innerHTML = `<pre class="code-block">${escapeHtml(sourceText)}</pre>`;
}

function renderCapabilities() {
  const insight = state.job?.insight || {};
  const caps = state.capabilities || demoCapabilities();
  const generation = caps.providers?.generation || {};
  const judge = caps.providers?.judge || {};
  const limits = caps.limits || {};
  const features = caps.features || {};
  const ui = caps.ui || {};

  el.capabilitiesCopy.innerHTML = `
    <div class="guide-stack">
      <div>${chip(`gen:${generation.name || "unknown"}`)} ${chip(generation.model || "unknown")}</div>
      <div>${judge.enabled ? chip(`judge:${judge.name || "unknown"}`, "is-good") : chip("judge:off")} ${judge.model ? chip(judge.model) : ""}</div>
      <div>${chip(`max chars:${limits.max_input_chars ?? "?"}`)} ${chip(`max candidates:${limits.max_candidate_count ?? "?"}`)}</div>
      <div>${chip(`ui:${(ui.modes || []).join("/") || "n/a"}`)} ${features.surface_mode ? chip("surface-aware", "is-good") : chip("surface-aware:off")}</div>
      <div>${features.choose_candidate ? chip("choose-candidate", "is-good") : chip("choose-candidate:off")} ${limits.supports_document_rewrite ? chip("document-mode:on") : chip("document-mode:off")}</div>
    </div>
  `;

  const insightRows = [
    insight.mode ? chip(`mode:${insight.mode}`) : "",
    insight.surface_mode ? chip(`surface:${insight.surface_mode}`) : "",
    typeof insight.judge_enabled === "boolean"
      ? chip(`judge:${insight.judge_enabled ? "on" : "off"}`, insight.judge_enabled ? "is-good" : "")
      : "",
    insight.formatting_pack ? chip(`pack:${insight.formatting_pack}`) : "",
  ].filter(Boolean);

  el.runtimeInsight.innerHTML = insightRows.length
    ? `<div class="guide-stack"><div>${insightRows.join(" ")}</div></div>`
    : emptyBlock("No runtime insight returned for this job yet.");
}

function renderChoiceHistory() {
  const history = state.job?.choice_history || [];
  if (!history.length) {
    el.choiceHistory.innerHTML = emptyBlock("No explicit choice history yet. This job is still winner-only.");
    return;
  }

  el.choiceHistory.innerHTML = history
    .map(
      (entry) => `
        <div class="guide-card">
          <p class="eyebrow">${escapeHtml(entry.actor_type || "actor")} ${entry.created_at ? `· ${escapeHtml(entry.created_at)}` : ""}</p>
          <div class="guide-copy">
            <div>${chip(entry.candidate_id || "candidate")}</div>
            <p>${escapeHtml(entry.reason || "No reason recorded.")}</p>
          </div>
        </div>
      `,
    )
    .join("");
}

function renderWinner() {
  const job = state.job;
  const winner = job?.winner;
  const chosen = job?.chosen;

  if (!winner) {
    el.winnerTitle.textContent = "Winner";
    el.winnerChips.innerHTML = "";
    el.winnerCopy.innerHTML = emptyBlock("No winner returned for this job.");
    el.winnerWhy.innerHTML = emptyBlock("Why-this-won data will land here once the runtime returns it.");
    el.choosePanel.innerHTML = emptyBlock("Candidate choice becomes available after the runtime exposes candidates.");
    return;
  }

  el.winnerTitle.textContent = chosen ? "Chosen output" : "Engine winner";
  el.winnerChips.innerHTML = [
    chip(winner.label || "winner"),
    winner.score != null ? chip(`score:${winner.score}`) : "",
    chosen ? chip("chosen", "is-good") : chip("winner"),
  ]
    .filter(Boolean)
    .join("");
  el.winnerCopy.textContent = chosen?.text || winner.text || "";
  const rationale =
    chosen && chosen.candidate_id !== winner.candidate_id
      ? chosen.why ||
        state.job?.choice_history?.[state.job.choice_history.length - 1]?.reason ||
        "This output was chosen after review. Runtime rationale for the override was not returned."
      : winner.why;
  el.winnerWhy.innerHTML = rationale
    ? `<p>${escapeHtml(rationale)}</p>`
    : emptyBlock("No rationale returned for the current selected output.");

  const reviewUrl = job.review_url ? `<p><span class="inline-code">review_url</span> ${escapeHtml(job.review_url)}</p>` : "";
  el.choosePanel.innerHTML = `
    <div class="guide-stack">
      <p>Winner stays immutable. Chosen can move if a client or user selects a different candidate.</p>
      ${reviewUrl}
      ${job.chosen_candidate_id
        ? `<p>Current chosen candidate: <span class="inline-code">${escapeHtml(job.chosen_candidate_id)}</span></p>`
        : `<p>No chosen candidate yet. The engine winner is still the effective output.</p>`}
    </div>
  `;
}

async function chooseCandidate(candidateId) {
  const job = state.job;
  if (!job || params.get("demo") === "1" || job.job_id === "brw_demo_job") {
    job.chosen_candidate_id = candidateId;
    job.chosen = job.candidates.find((candidate) => candidate.candidate_id === candidateId) || null;
    job.choice_history = [
      ...(job.choice_history || []),
      {
        choice_id: `brch_demo_${crypto.randomUUID().slice(0, 6)}`,
        candidate_id: candidateId,
        actor_type: "user",
        actor_id: "local-demo",
        reason: "Demo choice from the Companion review lane.",
        created_at: new Date().toISOString(),
      },
    ];
    job.status = "chosen";
    render();
    return;
  }

  try {
    const payload = await fetchJson(`/v1/jobs/${encodeURIComponent(job.job_id)}/choose`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        candidate_id: candidateId,
        actor: {
          type: "user",
          id: "companion-ui",
        },
        reason: "Chosen from Brotherizer Companion review UI.",
      }),
    });
    state.job = normalizeJob({
      ...job,
      ...payload,
      candidates: job.candidates,
      winner: job.winner,
      choice_history: [...(job.choice_history || []), payload.choice].filter(Boolean),
    });
    state.lastError = "";
  } catch (error) {
    state.lastError = error.message;
  }
  render();
}

function renderCandidates() {
  const job = state.job;
  const candidates = job?.candidates || [];

  if (!candidates.length) {
    el.candidateStack.innerHTML = emptyBlock("No candidates available yet.");
    return;
  }

  el.candidateStack.innerHTML = candidates
    .map((candidate) => {
      const isWinner = candidate.candidate_id === job.winner_candidate_id;
      const isChosen = candidate.candidate_id === job.chosen_candidate_id;

      return `
        <article class="candidate-card ${isWinner ? "is-winner" : ""} ${isChosen ? "is-chosen" : ""}">
          <div class="card-meta">
            <div>
              <p class="eyebrow">Candidate</p>
              <h2 class="candidate-rank">#${escapeHtml(candidate.rank ?? "?")}</h2>
            </div>
            <div class="chip-row">
              ${chip(candidate.label || "candidate")}
              ${candidate.score != null ? chip(`score:${candidate.score}`) : ""}
              ${isWinner ? chip("winner", "is-signal") : ""}
              ${isChosen ? chip("chosen", "is-good") : ""}
            </div>
          </div>
          <div class="candidate-copy">${escapeHtml(candidate.text || "")}</div>
          <p class="candidate-why">${escapeHtml(candidate.why || "No explanation returned for this candidate.")}</p>
          <div class="candidate-actions">
            <button class="choose-button ${isChosen ? "is-chosen" : ""}" type="button" data-candidate-id="${escapeHtml(candidate.candidate_id)}">
              ${isChosen ? "Chosen" : "Choose this"}
            </button>
            <span class="muted-note">${escapeHtml(candidate.candidate_id || "")}</span>
          </div>
        </article>
      `;
    })
    .join("");

  Array.from(el.candidateStack.querySelectorAll("[data-candidate-id]")).forEach((button) => {
    button.addEventListener("click", () => {
      chooseCandidate(button.getAttribute("data-candidate-id"));
    });
  });
}

function renderErrors() {
  if (!state.lastError) {
    if (errorNode) {
      errorNode.remove();
      errorNode = null;
    }
    return;
  }

  if (!errorNode) {
    errorNode = document.createElement("article");
    errorNode.className = "callout-card";
    document.querySelector(".companion-shell").appendChild(errorNode);
  }

  errorNode.className = "callout-card";
  errorNode.innerHTML = `
    <p class="eyebrow">Runtime note</p>
    <div class="error-copy">${escapeHtml(state.lastError)}</div>
  `;
}

function render() {
  renderKpis();
  renderRequest();
  renderCapabilities();
  renderChoiceHistory();
  renderWinner();
  renderCandidates();
  renderErrors();
}

async function bootstrap() {
  await Promise.all([loadCapabilities(), loadJob()]);
  render();
}

el.loadDemoBtn.addEventListener("click", () => {
  params.set("demo", "1");
  history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
  state.lastError = "";
  state.job = demoJob();
  state.capabilities = state.capabilities || demoCapabilities();
  render();
});

bootstrap().catch((error) => {
  state.lastError = error.message;
  state.capabilities = demoCapabilities();
  state.job = null;
  render();
});
