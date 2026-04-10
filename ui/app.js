const elements = {
  sessionList: document.getElementById("session-list"),
  fileList: document.getElementById("file-list"),
  modeSelect: document.getElementById("mode-select"),
  sourceText: document.getElementById("source-text"),
  editorTitle: document.getElementById("editor-title"),
  rewriteBtn: document.getElementById("rewrite-btn"),
  saveFileBtn: document.getElementById("save-file-btn"),
  saveWinnerBtn: document.getElementById("save-winner-btn"),
  newSessionBtn: document.getElementById("new-session-btn"),
  newFileBtn: document.getElementById("new-file-btn"),
  xaiJudgeToggle: document.getElementById("xai-judge-toggle"),
  winnerLabel: document.getElementById("winner-label"),
  activeModeLabel: document.getElementById("active-mode-label"),
  winnerText: document.getElementById("winner-text"),
  winnerWhy: document.getElementById("winner-why"),
  candidateList: document.getElementById("candidate-list"),
  styleSignalList: document.getElementById("style-signal-list"),
  donorSnippetList: document.getElementById("donor-snippet-list"),
  savedOutputList: document.getElementById("saved-output-list"),
  statusPill: document.getElementById("status-pill"),
  draftCount: document.getElementById("draft-count"),
  modeCount: document.getElementById("mode-count"),
};

const templates = {
  session: document.getElementById("session-item-template"),
  file: document.getElementById("file-item-template"),
  candidate: document.getElementById("candidate-template"),
};

let state = {
  modes: {},
  sessions: [],
  currentSessionId: "",
  currentFileId: "",
  lastResult: null,
  lastError: "",
};

function uid(prefix) {
  return `${prefix}_${crypto.randomUUID().slice(0, 8)}`;
}

function buildDefaultState() {
  const sessionId = uid("session");
  const fileId = uid("file");
  return {
    modes: {},
    currentSessionId: sessionId,
    currentFileId: fileId,
    lastResult: null,
    lastError: "",
    sessions: [
      {
        id: sessionId,
        name: "Main workspace",
        createdAt: new Date().toISOString(),
        files: [
          {
            id: fileId,
            name: "Draft 01",
            text: "",
            mode: "ptbr_twitter_mode",
            rewrites: [],
          },
        ],
      },
    ],
  };
}

function normalizeWorkspacePayload(payload) {
  return {
    ...buildDefaultState(),
    sessions: payload.sessions || [],
    currentSessionId: payload.sessions?.[0]?.id || "",
    currentFileId: payload.sessions?.[0]?.files?.[0]?.id || "",
    modes: {},
    lastResult: null,
    lastError: "",
  };
}

function getCurrentSession() {
  return state.sessions.find((session) => session.id === state.currentSessionId) || state.sessions[0];
}

function getCurrentFile() {
  const session = getCurrentSession();
  return session?.files.find((file) => file.id === state.currentFileId) || session?.files[0];
}

function setStatus(kind, label) {
  elements.statusPill.textContent = label;
  elements.statusPill.className = `status-pill ${kind}`;
}

function setEmptyBlock(container, text) {
  container.innerHTML = `<div class="empty-state">${text}</div>`;
}

function renderSessions() {
  elements.sessionList.innerHTML = "";
  state.sessions.forEach((session) => {
    const node = templates.session.content.firstElementChild.cloneNode(true);
    node.textContent = session.name;
    node.classList.toggle("active", session.id === state.currentSessionId);
    node.addEventListener("click", () => {
      state.currentSessionId = session.id;
      state.currentFileId = session.files[0]?.id || "";
      render();
    });
    elements.sessionList.appendChild(node);
  });
}

function renderFiles() {
  const session = getCurrentSession();
  elements.fileList.innerHTML = "";
  if (!session?.files.length) {
    setEmptyBlock(elements.fileList, "No files in this session yet.");
    return;
  }
  session.files.forEach((file) => {
    const node = templates.file.content.firstElementChild.cloneNode(true);
    node.textContent = file.name;
    node.classList.toggle("active", file.id === state.currentFileId);
    node.addEventListener("click", () => {
      state.currentFileId = file.id;
      render();
    });
    elements.fileList.appendChild(node);
  });
}

function renderModeSelect() {
  const currentFile = getCurrentFile();
  const modes = Object.keys(state.modes);
  elements.modeSelect.innerHTML = "";
  modes.forEach((mode) => {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    if (mode === currentFile?.mode) {
      option.selected = true;
    }
    elements.modeSelect.appendChild(option);
  });
  elements.modeCount.textContent = String(modes.length);
}

function renderEditor() {
  const file = getCurrentFile();
  elements.editorTitle.textContent = file?.name || "Draft";
  elements.sourceText.value = file?.text || "";
  if (file?.mode) {
    elements.modeSelect.value = file.mode;
  }
}

function renderSavedOutputs() {
  const file = getCurrentFile();
  const rewrites = file?.rewrites || [];
  elements.draftCount.textContent = String(rewrites.length);
  elements.savedOutputList.innerHTML = "";
  if (!rewrites.length) {
    setEmptyBlock(elements.savedOutputList, "Saved winners will land here once you pick a good one.");
    return;
  }
  rewrites
    .slice()
    .reverse()
    .forEach((rewrite) => {
      const node = document.createElement("article");
      node.className = "saved-output-item";
      node.innerHTML = `
        <p class="eyebrow">${rewrite.mode}</p>
        <strong>${rewrite.label || "winner"}</strong>
        <p>${escapeHtml(rewrite.text)}</p>
      `;
      elements.savedOutputList.appendChild(node);
    });
}

function renderResult() {
  const result = state.lastResult;
  elements.candidateList.innerHTML = "";
  elements.styleSignalList.innerHTML = "";
  elements.donorSnippetList.innerHTML = "";
  elements.saveWinnerBtn.disabled = !result?.winner;

  if (!result) {
    elements.winnerLabel.textContent = "No run yet";
    elements.activeModeLabel.textContent = getCurrentFile()?.mode || "-";
    elements.winnerText.textContent = state.lastError || "Run a draft to see the chosen rewrite.";
    elements.winnerWhy.textContent = state.lastError ? "The engine returned an error for this run." : "";
    setEmptyBlock(elements.candidateList, "Candidates will appear here.");
    setEmptyBlock(elements.styleSignalList, "No style signals yet.");
    setEmptyBlock(elements.donorSnippetList, "Donor snippets will appear here.");
    return;
  }

  elements.winnerLabel.textContent = result.winner?.label || "winner";
  elements.activeModeLabel.textContent = getCurrentFile()?.mode || "-";
  elements.winnerText.textContent = result.winner?.text || "";
  elements.winnerWhy.textContent = result.winner?.why || "";

  if (!(result.candidates || []).length) {
    setEmptyBlock(elements.candidateList, "No candidates returned.");
  } else {
    result.candidates.forEach((candidate) => {
      const node = templates.candidate.content.firstElementChild.cloneNode(true);
      node.querySelector(".candidate-label").textContent = candidate.label || "candidate";
      node.querySelector(".candidate-score").textContent =
        candidate.rerank_score != null ? `score ${candidate.rerank_score}` : "";
      node.querySelector(".candidate-text").textContent = candidate.text || "";
      node.querySelector(".candidate-why").textContent = candidate.why || "";
      elements.candidateList.appendChild(node);
    });
  }

  if (!(result.style_signals || []).length) {
    setEmptyBlock(elements.styleSignalList, "No style radar signal matched this run.");
  } else {
    result.style_signals.forEach((signal) => {
      const node = document.createElement("div");
      node.className = "tag";
      node.innerHTML = `<strong>${escapeHtml(signal.title || signal.signal_key || "signal")}</strong>${escapeHtml(signal.description || "")}`;
      elements.styleSignalList.appendChild(node);
    });
  }

  if (!(result.donor_snippets || []).length) {
    setEmptyBlock(elements.donorSnippetList, "No donor snippets selected.");
  } else {
    result.donor_snippets.slice(0, 6).forEach((snippet) => {
      const node = document.createElement("div");
      node.className = "donor-snippet";
      node.innerHTML = `<strong>${escapeHtml(snippet.voice_bucket || "donor")}</strong><div>${escapeHtml(snippet.text || "")}</div>`;
      elements.donorSnippetList.appendChild(node);
    });
  }
}

function render() {
  renderSessions();
  renderFiles();
  renderModeSelect();
  renderEditor();
  renderSavedOutputs();
  renderResult();
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function saveEditorIntoFile() {
  const file = getCurrentFile();
  if (!file) {
    return;
  }
  file.text = elements.sourceText.value;
  file.mode = elements.modeSelect.value;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || "Request failed");
  }
  return payload;
}

async function createSession() {
  const name = window.prompt("Session name", `Workspace ${state.sessions.length + 1}`);
  if (!name) {
    return;
  }
  const sessionId = uid("session");
  const fileId = uid("file");
  const createdAt = new Date().toISOString();
  const newSession = {
    id: sessionId,
    name,
    createdAt,
    files: [
      {
        id: fileId,
        name: "Draft 01",
        text: "",
        mode: Object.keys(state.modes)[0] || "ptbr_twitter_mode",
        createdAt,
        updatedAt: createdAt,
        rewrites: [],
      },
    ],
  };
  await requestJson("/sessions", {
    method: "POST",
    body: JSON.stringify({
      id: sessionId,
      name,
      createdAt,
    }),
  });
  await requestJson("/files", {
    method: "POST",
    body: JSON.stringify({
      id: fileId,
      sessionId,
      name: "Draft 01",
      text: "",
      mode: newSession.files[0].mode,
      createdAt,
      updatedAt: createdAt,
    }),
  });
  state.sessions.unshift(newSession);
  state.currentSessionId = sessionId;
  state.currentFileId = fileId;
  render();
}

async function createFile() {
  const session = getCurrentSession();
  if (!session) {
    return;
  }
  const name = window.prompt("File name", `Draft ${String(session.files.length + 1).padStart(2, "0")}`);
  if (!name) {
    return;
  }
  const fileId = uid("file");
  const createdAt = new Date().toISOString();
  const file = {
    id: fileId,
    name,
    text: "",
    mode: Object.keys(state.modes)[0] || "ptbr_twitter_mode",
    createdAt,
    updatedAt: createdAt,
    rewrites: [],
  };
  await requestJson("/files", {
    method: "POST",
    body: JSON.stringify({
      id: fileId,
      sessionId: session.id,
      name,
      text: "",
      mode: file.mode,
      createdAt,
      updatedAt: createdAt,
    }),
  });
  session.files.push(file);
  state.currentFileId = fileId;
  render();
}

async function fetchModes() {
  const response = await fetch("/modes");
  if (!response.ok) {
    throw new Error("Failed to load modes");
  }
  state.modes = await response.json();
}

async function fetchWorkspace() {
  const payload = await requestJson("/workspace");
  state = {
    ...normalizeWorkspacePayload(payload),
    modes: state.modes,
  };
}

async function initializeWorkspaceIfEmpty() {
  if (state.sessions.length) {
    return;
  }
  const sessionId = uid("session");
  const fileId = uid("file");
  const createdAt = new Date().toISOString();
  const defaultMode = Object.keys(state.modes)[0] || "ptbr_twitter_mode";

  await requestJson("/sessions", {
    method: "POST",
    body: JSON.stringify({
      id: sessionId,
      name: "Main workspace",
      createdAt,
    }),
  });
  await requestJson("/files", {
    method: "POST",
    body: JSON.stringify({
      id: fileId,
      sessionId,
      name: "Draft 01",
      text: "",
      mode: defaultMode,
      createdAt,
      updatedAt: createdAt,
    }),
  });
  await fetchWorkspace();
}

async function runRewrite() {
  const file = getCurrentFile();
  if (!file) {
    return;
  }
  await saveFile();
  setStatus("running", "running");
  elements.rewriteBtn.disabled = true;
  try {
    const response = await fetch("/rewrite", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: file.text,
        mode: file.mode,
        db: "data/corpus/brotherizer.db",
        use_xai_judge: elements.xaiJudgeToggle.checked,
      }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok && result.error) {
      throw new Error(result.error || "Rewrite failed");
    }
    state.lastResult = result;
    state.lastError = "";
    setStatus("done", "done");
  } catch (error) {
    state.lastResult = null;
    state.lastError = error.message;
    setStatus("error", "error");
  } finally {
    elements.rewriteBtn.disabled = false;
    render();
  }
}

function saveWinner() {
  return saveWinnerToBackend();
}

async function saveWinnerToBackend() {
  const file = getCurrentFile();
  const winner = state.lastResult?.winner;
  if (!file || !winner) {
    return;
  }
  const savedOutput = {
    id: uid("winner"),
    savedAt: new Date().toISOString(),
    mode: file.mode,
    label: winner.label || "winner",
    text: winner.text || "",
    why: winner.why || "",
  };
  await requestJson(`/files/${file.id}/saved-outputs`, {
    method: "POST",
    body: JSON.stringify(savedOutput),
  });
  file.rewrites.push(savedOutput);
  renderSavedOutputs();
}

async function saveFile() {
  const file = getCurrentFile();
  if (!file) {
    return;
  }
  saveEditorIntoFile();
  file.updatedAt = new Date().toISOString();
  await requestJson(`/files/${file.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: file.name,
      text: file.text,
      mode: file.mode,
      updatedAt: file.updatedAt,
    }),
  });
}

function attachEvents() {
  elements.newSessionBtn.addEventListener("click", createSession);
  elements.newFileBtn.addEventListener("click", createFile);
  elements.saveFileBtn.addEventListener("click", async () => {
    await saveFile();
    render();
  });
  elements.rewriteBtn.addEventListener("click", runRewrite);
  elements.saveWinnerBtn.addEventListener("click", saveWinner);
  elements.modeSelect.addEventListener("change", saveEditorIntoFile);
  elements.sourceText.addEventListener("input", saveEditorIntoFile);
}

async function bootstrap() {
  await fetchModes();
  await fetchWorkspace();
  await initializeWorkspaceIfEmpty();
  const currentFile = getCurrentFile();
  if (currentFile && !state.modes[currentFile.mode]) {
    currentFile.mode = Object.keys(state.modes)[0] || "";
  }
  attachEvents();
  render();
}

bootstrap().catch((error) => {
  setStatus("error", "error");
  elements.winnerText.textContent = error.message;
  elements.winnerWhy.textContent = "The workspace could not boot properly.";
});
