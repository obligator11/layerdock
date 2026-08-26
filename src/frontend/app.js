// LayerDock frontend — per-file Convert + progress bars, Convert All / Download All.

const state = {
  queue: [], // {name, size, path, status, progress, outputPath}
};

function el(id) { return document.getElementById(id); }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

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
  // progress/completion arrives async via onConvertProgress/onConvertDone below
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

// Called from Python via evaluate_js during conversion
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

function wireEvents() {
  el("selectFilesBtn").addEventListener("click", pickFiles);
  el("addMoreBtn").addEventListener("click", pickFiles);
  el("convertAllBtn").addEventListener("click", convertAll);
  el("downloadAllBtn").addEventListener("click", downloadAll);

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
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