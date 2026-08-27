// LayerDock frontend — Convert / History / Settings.

const state = {
  queue: [], // {name, size, path, status, progress, outputPath}
};

function el(id) { return document.getElementById(id); }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch (e) {
    return iso;
  }
}

/* ---------- Convert view ---------- */

function renderQueue() {
  const dropzone = el("dropzone");
  const queueView = el("queueView");
  const list = el("queueList");
  const downloadAllBtn = el("downloadAllBtn");

  if (state.queue.length === 0) {
    dropzone.classList.remove("hidden");
    queueView.classList.add("hidden");
    return;
  }

  dropzone.classList.add("hidden");
  queueView.classList.remove("hidden");
  list.innerHTML = "";

  const anyDone = state.queue.some((i) => i.status === "done");
  downloadAllBtn.disabled = !anyDone;

  state.queue.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "queue-item";

    let statusLabel = "Queued";
    if (item.status === "parsing") statusLabel = "Analyzing…";
    if (item.status === "converting") statusLabel = `Converting… ${item.progress}%`;
    if (item.status === "done") statusLabel = "Done";
    if (item.status === "error") statusLabel = `Error: ${item.error}`;

    row.innerHTML = `
      <div class="queue-item-icon">PDF</div>
      <div class="queue-item-body">
        <div class="queue-item-top">
          <div class="queue-item-name">${item.name}</div>
          <div class="queue-item-status status-${item.status}">${statusLabel}</div>
        </div>
        <div class="queue-item-meta">${formatSize(item.size)}</div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${item.status === "done" ? 100 : item.progress}%"></div>
        </div>
      </div>
      <div class="queue-item-action">
        ${item.status === "done"
        ? `<button class="btn-ghost btn-small" data-action="reveal" data-index="${index}">Reveal</button>`
        : `<button class="btn-primary btn-small" data-action="convert" data-index="${index}" ${item.status === "converting" || item.status === "parsing" ? "disabled" : ""}>Convert</button>`
      }
      </div>
    `;
    list.appendChild(row);
  });

  list.querySelectorAll('[data-action="convert"]').forEach((btn) =>
    btn.addEventListener("click", () => convertFile(parseInt(btn.dataset.index)))
  );
  list.querySelectorAll('[data-action="reveal"]').forEach((btn) =>
    btn.addEventListener("click", () => {
      const item = state.queue[parseInt(btn.dataset.index)];
      if (item.outputPath) window.pywebview.api.open_folder(item.outputPath);
    })
  );
}

function addFiles(files) {
  files.forEach((f) => {
    state.queue.push({
      name: f.name,
      size: f.size,
      path: f.path || null,
      status: "queued",
      progress: 0,
      outputPath: null,
      error: null,
    });
  });
  renderQueue();
}

async function convertFile(index) {
  const item = state.queue[index];
  if (!item.path) {
    item.status = "error";
    item.error = "No file path (drag-drop not yet supported for conversion)";
    renderQueue();
    return;
  }
  item.status = "parsing";
  item.progress = 0;
  renderQueue();

  const parseRes = await window.pywebview.api.parse_pdf(item.path);
  if (!parseRes.ok) {
    item.status = "error";
    item.error = parseRes.error;
    renderQueue();
    return;
  }

  item.status = "converting";
  renderQueue();
  await window.pywebview.api.convert_pdf(item.path, String(index));
}

async function convertAll() {
  state.queue.forEach((item, index) => {
    if (item.status === "queued" || item.status === "error") convertFile(index);
  });
}

async function downloadAll() {
  const doneItems = state.queue.filter((i) => i.status === "done" && i.outputPath);
  const uniqueFolders = [...new Set(doneItems.map((i) => i.outputPath))];
  for (const path of uniqueFolders) {
    await window.pywebview.api.open_folder(path);
  }
}

window.onConvertProgress = (jobId, pct) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  item.progress = pct;
  renderQueue();
};

window.onConvertDone = (jobId, outputPath) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  item.status = "done";
  item.progress = 100;
  item.outputPath = outputPath;
  renderQueue();
};

window.onConvertError = (jobId, error) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  item.status = "error";
  item.error = error;
  renderQueue();
};

/* ---------- History view ---------- */

async function loadHistory() {
  const list = el("historyList");
  list.innerHTML = `<div class="empty-note">Loading…</div>`;
  const res = await window.pywebview.api.get_history();
  if (!res.ok) {
    list.innerHTML = `<div class="empty-note">Failed to load history: ${res.error}</div>`;
    return;
  }
  if (res.items.length === 0) {
    list.innerHTML = `<div class="empty-note">No conversions yet.</div>`;
    return;
  }
  list.innerHTML = "";
  res.items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "queue-item";
    const ok = item.status === "done";
    row.innerHTML = `
      <div class="queue-item-icon">PDF</div>
      <div class="queue-item-body">
        <div class="queue-item-top">
          <div class="queue-item-name">${item.source_name || "Unknown"}</div>
          <div class="queue-item-status ${ok ? "status-done" : "status-error"}">
            ${ok ? `${item.page_count || "?"} pages` : `Error`}
          </div>
        </div>
        <div class="queue-item-meta">${formatDate(item.created_at)}${ok ? "" : ` · ${item.error || ""}`}</div>
      </div>
      <div class="queue-item-action">
        ${ok ? `<button class="btn-ghost btn-small" data-reveal="${item.output_path}">Reveal</button>` : ""}
      </div>
    `;
    list.appendChild(row);
  });
  list.querySelectorAll("[data-reveal]").forEach((btn) =>
    btn.addEventListener("click", () => window.pywebview.api.open_folder(btn.dataset.reveal))
  );
}

async function clearHistory() {
  await window.pywebview.api.clear_history();
  loadHistory();
}

/* ---------- Settings view ---------- */

async function loadSettings() {
  const res = await window.pywebview.api.get_settings();
  if (!res.ok) return;
  el("outputFolderValue").textContent = res.output_folder_override
    ? res.output_folder_override
    : 'Automatic — a "LayerDock Output" folder next to each source PDF';
  el("dataDirValue").textContent = res.data_dir;
}

async function changeOutputFolder() {
  const res = await window.pywebview.api.choose_output_folder_override();
  if (res.ok) loadSettings();
}

async function resetOutputFolder() {
  await window.pywebview.api.reset_output_folder_override();
  loadSettings();
}

/* ---------- Shared ---------- */

async function checkBackend() {
  const dot = el("backendStatus");
  const text = el("backendStatusText");
  try {
    const res = await window.pywebview.api.ping();
    if (res && res.ok) {
      dot.classList.add("online");
      text.textContent = "Backend ready";
    } else {
      throw new Error("bad response");
    }
  } catch (e) {
    dot.classList.add("offline");
    text.textContent = "Backend unavailable";
  }
}

async function pickFiles() {
  const picked = await window.pywebview.api.select_files();
  if (picked && picked.length) addFiles(picked);
}

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  el(viewName + "View").classList.remove("hidden");
  if (viewName === "history") loadHistory();
  if (viewName === "settings") loadSettings();
}

function wireEvents() {
  el("selectFilesBtn").addEventListener("click", pickFiles);
  el("addMoreBtn").addEventListener("click", pickFiles);
  el("convertAllBtn").addEventListener("click", convertAll);
  el("downloadAllBtn").addEventListener("click", downloadAll);
  el("clearHistoryBtn").addEventListener("click", clearHistory);
  el("changeOutputFolderBtn").addEventListener("click", changeOutputFolder);
  el("resetOutputFolderBtn").addEventListener("click", resetOutputFolder);
  el("openDataFolderBtn").addEventListener("click", () => window.pywebview.api.open_data_folder());

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      switchView(btn.dataset.view);
    });
  });

  const dropzone = el("dropzone");
  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const files = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.toLowerCase().endsWith(".pdf")
    );
    if (files.length) addFiles(files);
  });
}

window.addEventListener("pywebviewready", () => {
  wireEvents();
  checkBackend();
});