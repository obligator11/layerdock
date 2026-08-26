// LayerDock frontend — Step 2: UI shell + PDF parsing wired in.

const state = {
  queue: [], // {name, size, path, status}
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

  if (state.queue.length === 0) {
    dropzone.classList.remove("hidden");
    queueView.classList.add("hidden");
    return;
  }

  dropzone.classList.add("hidden");
  queueView.classList.remove("hidden");
  list.innerHTML = "";

  state.queue.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "queue-item";
    row.innerHTML = `
      <div class="queue-item-icon">PDF</div>
      <div>
        <div class="queue-item-name">${item.name}</div>
        <div class="queue-item-meta">${formatSize(item.size)}</div>
      </div>
      <div class="queue-item-status" data-index="${index}" style="cursor:pointer;">${item.status}</div>
    `;
    row.querySelector(".queue-item-status").addEventListener("click", () => parseFile(index));
    list.appendChild(row);
  });
}

function addFiles(files) {
  files.forEach((f) => {
    state.queue.push({
      name: f.name,
      size: f.size,
      path: f.path || null,
      status: "Queued",
    });
  });
  renderQueue();
}

async function parseFile(index) {
  const item = state.queue[index];
  if (!item.path) {
    item.status = "No path (use Select PDF, not drag-drop, for now)";
    renderQueue();
    return;
  }
  item.status = "Parsing…";
  renderQueue();

  const res = await window.pywebview.api.parse_pdf(item.path);
  if (res.ok) {
    item.status = `${res.page_count}p · ${res.image_count} imgs · ${res.scanned_pages} scanned`;
  } else {
    item.status = `Error: ${res.error}`;
  }
  renderQueue();
}

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
