const capsEl = {
  whatItIsCopy: document.getElementById("what-it-is-copy"),
  capabilitiesPanel: document.getElementById("capabilities-panel"),
  howItWorksList: document.getElementById("how-it-works-list"),
  promptExamples: document.getElementById("prompt-examples"),
  uiModePanel: document.getElementById("ui-mode-panel"),
  scopeInPanel: document.getElementById("scope-in-panel"),
  scopeOutPanel: document.getElementById("scope-out-panel"),
};

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

function capabilitiesFallback() {
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

async function fetchCapabilities() {
  try {
    const response = await fetch("/v1/capabilities");
    if (!response.ok) {
      throw new Error("capabilities unavailable");
    }
    const payload = await response.json();
    return payload && typeof payload === "object" ? payload : capabilitiesFallback();
  } catch (_error) {
    return capabilitiesFallback();
  }
}

function renderWhatItIs() {
  capsEl.whatItIsCopy.innerHTML = `
    Brotherizer is three things working together:
    <span class="inline-code">Core</span> generates and reranks rewrites,
    <span class="inline-code">Runtime</span> turns those rewrites into durable jobs,
    and <span class="inline-code">Companion</span> shows a readable review surface when the result needs inspection.
  `;
}

function renderCapabilities(caps) {
  const generation = caps.providers?.generation || {};
  const judge = caps.providers?.judge || {};
  const limits = caps.limits || {};
  const ui = caps.ui || {};

  capsEl.capabilitiesPanel.innerHTML = `
    <div class="guide-stack">
      <div>${chip(`generation:${generation.name || "unknown"}`)} ${chip(generation.model || "unknown")}</div>
      <div>${judge.enabled ? chip(`judge:${judge.name || "unknown"}`, "is-good") : chip("judge:off")} ${judge.model ? chip(judge.model) : ""}</div>
      <div>${chip(`max chars:${limits.max_input_chars ?? "?"}`)} ${chip(`max candidates:${limits.max_candidate_count ?? "?"}`)}</div>
      <div>${chip(`companion:${ui.companion_enabled ? "on" : "off"}`)} ${chip(`modes:${(ui.modes || []).join("/") || "n/a"}`)}</div>
    </div>
  `;
}

function renderHowItWorks() {
  const steps = [
    {
      title: "1. Send text, mode, and optional surface",
      copy:
        "The LLM or client sends text plus a mode like casual_us_human_mode and optionally a surface like reply, caption, or note.",
    },
    {
      title: "2. Brotherizer builds a rewrite context",
      copy:
        "It brings in donor memory, formatting pack rules, and mode logic before generation starts.",
    },
    {
      title: "3. It generates multiple candidates",
      copy:
        "The engine creates multiple options, reranks them, and can optionally run the judge path for extra confidence.",
    },
    {
      title: "4. Runtime stores a durable job",
      copy:
        "The result becomes a runtime job with winner, candidates, insight, and later a chosen candidate if a user or client overrides the winner.",
    },
    {
      title: "5. Companion opens only when it helps",
      copy:
        "In auto mode, the Companion appears when the text is long, the top candidates are close, or the workflow benefits from review.",
    },
  ];

  capsEl.howItWorksList.innerHTML = steps
    .map(
      (step) => `
        <li class="step-card">
          <p class="step-index">${escapeHtml(step.title)}</p>
          <p class="step-copy">${escapeHtml(step.copy)}</p>
        </li>
      `,
    )
    .join("");
}

function renderPrompts() {
  capsEl.promptExamples.textContent = [
    'brotherize this',
    'brotherize this in casual_us_human_mode',
    'brotherize this as a reply',
    'brotherize this paragraph in ptbr_narrative with note surface',
    'show me the top options before choosing',
  ].join("\n");
}

function renderUiModes() {
  capsEl.uiModePanel.innerHTML = `
    <div class="guide-stack">
      <div><span class="inline-code">off</span> — the LLM gets the result and the Companion stays invisible.</div>
      <div><span class="inline-code">auto</span> — the Companion opens only when the runtime thinks review adds value.</div>
      <div><span class="inline-code">always</span> — every rewrite also opens the review surface for human inspection.</div>
    </div>
  `;
}

function renderScope() {
  capsEl.scopeInPanel.innerHTML = `
    <div class="guide-stack">
      <div>${chip("phrase rewrite", "is-good")} ${chip("paragraph rewrite", "is-good")}</div>
      <div>${chip("candidate ranking", "is-good")} ${chip("winner vs chosen", "is-good")}</div>
      <div>${chip("surface_mode", "is-good")} ${chip("review_url", "is-good")}</div>
      <div>${chip("onboarding", "is-good")} ${chip("companion review", "is-good")}</div>
    </div>
  `;

  capsEl.scopeOutPanel.innerHTML = `
    <div class="guide-stack">
      <div>${chip("whole-file parity")} ${chip("document rewrite")}</div>
      <div>${chip("section chunking")} ${chip("document IR")}</div>
      <div>${chip("streaming rewrite")} ${chip("agent-side MCP adapter")}</div>
      <div>${chip("silent promises of file support", "is-danger")}</div>
    </div>
  `;
}

async function bootstrap() {
  const caps = await fetchCapabilities();
  renderWhatItIs();
  renderCapabilities(caps);
  renderHowItWorks();
  renderPrompts();
  renderUiModes();
  renderScope();
}

bootstrap();
