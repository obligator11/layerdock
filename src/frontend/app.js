// LayerDock frontend — Convert / History / Settings, with batch tracking + cancel.

const state = {
  queue: [], // {name, size, path, status, progress, outputPath, flaggedPages}
  batch: null, // {total, done, succeeded, failed, cancelled, flaggedCount}
};

function el(id) { return document.getElementById(id); }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch (e) {
    return iso;
  }
}

/* ---------- Toasts ---------- */

function showToast(message, kind = "default") {
  const stack = el("toastStack");
  const toast = document.createElement("div");
  toast.className = `toast${kind !== "default" ? " toast-" + kind : ""}`;
  toast.textContent = message;
  stack.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast-out");
    setTimeout(() => toast.remove(), 200);
  }, 2600);
}

/* ---------- Batch summary ---------- */

function renderBatchSummary() {
  const banner = el("batchSummary");
  if (!state.batch) {
    banner.classList.add("hidden");
    return;
  }
  const b = state.batch;
  const stillRunning = b.done < b.total;

  if (stillRunning) {
    banner.innerHTML = `<span>Converting batch… ${b.done}/${b.total} done</span>`;
  } else {
    const parts = [`${b.succeeded} succeeded`];
    if (b.failed) parts.push(`${b.failed} failed`);
    if (b.cancelled) parts.push(`${b.cancelled} cancelled`);
    if (b.flaggedCount) parts.push(`${b.flaggedCount} need review`);
    banner.innerHTML = `
      <span>Batch complete — ${parts.join(" · ")}</span>
      <button class="btn-ghost btn-small" id="dismissBatchBtn">Dismiss</button>
    `;
    const dismissBtn = document.getElementById("dismissBatchBtn");
    if (dismissBtn) dismissBtn.addEventListener("click", () => {
      state.batch = null;
      renderBatchSummary();
    });
  }
  banner.classList.remove("hidden");
}

function batchTick(kind, flaggedCount = 0) {
  if (!state.batch) return;
  state.batch.done += 1;
  if (kind === "succeeded") state.batch.succeeded += 1;
  if (kind === "failed") state.batch.failed += 1;
  if (kind === "cancelled") state.batch.cancelled += 1;
  state.batch.flaggedCount += flaggedCount;
  renderBatchSummary();
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
    if (item.status === "cancelled") statusLabel = "Cancelled";
    if (item.status === "done") {
      statusLabel = "Done";
      if (item.flaggedPages && item.flaggedPages.length) {
        statusLabel = `Done · review pages ${item.flaggedPages.join(", ")}`;
      }
    }
    if (item.status === "error") statusLabel = `Error: ${item.error}`;

    const isActive = item.status === "converting" || item.status === "parsing";

    let actionHtml = "";
    if (item.status === "done") {
      actionHtml = `
        <button class="btn-ghost btn-small" data-action="reveal" data-index="${index}">Reveal</button>
        <button class="btn-ghost btn-small btn-icon-danger" data-action="delete" data-index="${index}" title="Remove from queue">✕</button>
      `;
    } else if (isActive) {
      actionHtml = `<button class="btn-ghost btn-small" data-action="cancel" data-index="${index}">Cancel</button>`;
    } else {
      actionHtml = `
        <button class="btn-primary btn-small" data-action="convert" data-index="${index}">Convert</button>
        <button class="btn-ghost btn-small btn-icon-danger" data-action="delete" data-index="${index}" title="Remove from queue">✕</button>
      `;
    }

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
      <div class="queue-item-action">${actionHtml}</div>
    `;
    list.appendChild(row);
  });

  list.querySelectorAll('[data-action="convert"]').forEach((btn) =>
    btn.addEventListener("click", () => convertFile(parseInt(btn.dataset.index)))
  );
  list.querySelectorAll('[data-action="cancel"]').forEach((btn) =>
    btn.addEventListener("click", () => cancelFile(parseInt(btn.dataset.index)))
  );
  list.querySelectorAll('[data-action="reveal"]').forEach((btn) =>
    btn.addEventListener("click", () => {
      const item = state.queue[parseInt(btn.dataset.index)];
      if (item.outputPath) window.pywebview.api.open_folder(item.outputPath);
    })
  );
  list.querySelectorAll('[data-action="delete"]').forEach((btn) =>
    btn.addEventListener("click", () => deleteFile(parseInt(btn.dataset.index)))
  );
}

function deleteFile(index) {
  state.queue.splice(index, 1);
  renderQueue();
  showToast("Removed from queue");
}

function clearQueue() {
  const anyActive = state.queue.some((i) => i.status === "converting" || i.status === "parsing");
  if (anyActive) {
    const proceed = confirm("Some files are still converting. Remove them from the queue anyway? (running conversions will keep saving to disk, they just won't be tracked here)");
    if (!proceed) return;
  }
  state.queue = [];
  state.batch = null;
  renderQueue();
  renderBatchSummary();
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
      flaggedPages: [],
    });
  });
  renderQueue();
}

async function convertFile(index, isBatch = false) {
  const item = state.queue[index];
  if (!item.path) {
    item.status = "error";
    item.error = "No file path (drag-drop not yet supported for conversion)";
    renderQueue();
    if (isBatch) batchTick("failed");
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
    if (isBatch) batchTick("failed");
    return;
  }

  item.status = "converting";
  renderQueue();
  await window.pywebview.api.convert_pdf(item.path, String(index));
}

async function cancelFile(index) {
  await window.pywebview.api.cancel_conversion(String(index));
  showToast("Cancelling…");
}

async function convertAll() {
  const targets = state.queue
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.status === "queued" || item.status === "error" || item.status === "cancelled");

  if (targets.length === 0) return;

  state.batch = { total: targets.length, done: 0, succeeded: 0, failed: 0, cancelled: 0, flaggedCount: 0 };
  renderBatchSummary();

  targets.forEach(({ index }) => convertFile(index, true));
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

window.onConvertDone = (jobId, outputPath, flaggedPages) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  const wasBatchItem = state.batch !== null;
  item.status = "done";
  item.progress = 100;
  item.outputPath = outputPath;
  item.flaggedPages = flaggedPages || [];
  renderQueue();
  if (wasBatchItem) batchTick("succeeded", item.flaggedPages.length ? 1 : 0);
};

window.onConvertError = (jobId, error) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  const wasBatchItem = state.batch !== null;
  item.status = "error";
  item.error = error;
  renderQueue();
  if (wasBatchItem) batchTick("failed");
};

window.onConvertCancelled = (jobId) => {
  const item = state.queue[parseInt(jobId)];
  if (!item) return;
  const wasBatchItem = state.batch !== null;
  item.status = "cancelled";
  item.progress = 0;
  renderQueue();
  if (wasBatchItem) batchTick("cancelled");
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
    const statusClass = ok ? "status-done" : item.status === "cancelled" ? "status-cancelled" : "status-error";
    let statusText = "Error";
    if (ok) statusText = `${item.page_count || "?"} pages`;
    if (item.status === "cancelled") statusText = "Cancelled";

    row.innerHTML = `
      <div class="queue-item-icon">PDF</div>
      <div class="queue-item-body">
        <div class="queue-item-top">
          <div class="queue-item-name">${item.source_name || "Unknown"}</div>
          <div class="queue-item-status ${statusClass}">${statusText}</div>
        </div>
        <div class="queue-item-meta">${formatDate(item.created_at)}${ok ? "" : item.error ? ` · ${item.error}` : ""}${item.flagged_pages ? ` · review pages ${item.flagged_pages}` : ""}</div>
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
  showToast("History cleared");
}

/* ---------- Settings view ---------- */

async function loadSettings() {
  const res = await window.pywebview.api.get_settings();
  if (res.ok) {
    el("outputFolderValue").textContent = res.output_folder_override
      ? res.output_folder_override
      : 'Automatic — a "LayerDock Output" folder next to each source PDF';
    el("dataDirValue").textContent = res.data_dir;
  }
  checkOcrStatus();
}

async function checkOcrStatus() {
  const el2 = el("ocrStatusValue");
  el2.textContent = "Checking…";
  try {
    const res = await window.pywebview.api.check_ocr();
    if (res.available) {
      el2.textContent = `Available (Tesseract ${res.version})`;
      el2.style.color = "var(--success)";
    } else {
      el2.textContent = res.error || "Not found — scanned PDFs will convert without text recognition.";
      el2.style.color = "var(--warn)";
    }
  } catch (e) {
    el2.textContent = `Bridge error: ${e.message || e}`;
    el2.style.color = "var(--danger)";
  }
}

async function changeOutputFolder() {
  const res = await window.pywebview.api.choose_output_folder_override();
  if (res.ok) {
    loadSettings();
    showToast("Output folder updated", "success");
  }
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
  el("clearQueueBtn").addEventListener("click", clearQueue);
  el("clearHistoryBtn").addEventListener("click", clearHistory);
  el("changeOutputFolderBtn").addEventListener("click", changeOutputFolder);
  el("resetOutputFolderBtn").addEventListener("click", resetOutputFolder);
  el("openDataFolderBtn").addEventListener("click", () => window.pywebview.api.open_data_folder());
  el("recheckOcrBtn").addEventListener("click", checkOcrStatus);

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