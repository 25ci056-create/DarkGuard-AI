/** upload.js – upload slot management */
import { getState, setUpload, setState } from "./store.js";

const SLOT_LABELS = {
  1: "1. Product page",
  2: "2. Cart",
  3: "3. Payment page",
};

const SLOT_ICONS = {
  1: "🖼️",
  2: "🛒",
  3: "💳",
};

let _activeSlot = null;
let _onUploadChange = null;

export function initUploadSlots(onChangeCallback) {
  _onUploadChange = onChangeCallback;
  renderAllSlots();

  // Hidden file input handler
  document.getElementById("file-input-hidden").addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file || _activeSlot === null) return;
    e.target.value = "";
    handleFile(_activeSlot, file);
  });
}

export function renderAllSlots() {
  const grid = document.getElementById("upload-grid");
  grid.innerHTML = "";
  for (let slot = 1; slot <= 3; slot++) {
    grid.appendChild(buildSlotCard(slot));
    setupDragDrop(grid.lastElementChild, slot);
  }
}

function buildSlotCard(slot) {
  const upload = getState().uploads[slot];
  const card = document.createElement("div");
  card.className = `upload-slot${upload ? (upload.status === "ready" ? " ready" : upload.status === "error" ? " error" : "") : " empty"}`;
  card.setAttribute("data-slot", slot);
  card.setAttribute("role", "button");
  card.setAttribute("tabindex", "0");
  card.setAttribute("aria-label", `${SLOT_LABELS[slot]}. ${upload ? "Uploaded. Click to replace." : "Click to upload."}`);

  // Thumbnail
  const thumb = document.createElement("div");
  thumb.className = "upload-thumb";
  if (upload?.preview) {
    const img = document.createElement("img");
    img.src = upload.preview;
    img.alt = `${SLOT_LABELS[slot]} preview`;
    thumb.appendChild(img);
  } else {
    thumb.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
      <path d="M21 15l-5-5L5 21"/>
    </svg>`;
  }

  // Info
  const info = document.createElement("div");
  info.className = "upload-info min-w-0";

  const label = document.createElement("div");
  label.className = "upload-label overflow-wrap";
  label.textContent = SLOT_LABELS[slot];

  const statusEl = document.createElement("div");
  statusEl.className = `upload-status${upload?.status === "ready" ? " ready" : upload?.status === "error" ? " error" : ""}`;
  statusEl.textContent = upload?.status === "ready"
    ? `✓ Uploaded (${upload.name})`
    : upload?.status === "uploading"
    ? "Uploading…"
    : upload?.status === "error"
    ? upload.error || "Error"
    : "Tap to upload";

  info.appendChild(label);
  info.appendChild(statusEl);

  // Actions
  if (upload?.status === "ready") {
    const actions = document.createElement("div");
    actions.className = "upload-actions";

    const replaceBtn = document.createElement("button");
    replaceBtn.type = "button";
    replaceBtn.className = "upload-action-btn";
    replaceBtn.textContent = "Replace";
    replaceBtn.addEventListener("click", e => { e.stopPropagation(); openPicker(slot); });

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "upload-action-btn remove";
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", e => { e.stopPropagation(); removeSlot(slot); });

    actions.appendChild(replaceBtn);
    actions.appendChild(removeBtn);
    info.appendChild(actions);
  }

  card.appendChild(thumb);
  card.appendChild(info);

  // Click to pick
  card.addEventListener("click", () => openPicker(slot));
  card.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openPicker(slot); }});

  return card;
}

function setupDragDrop(card, slot) {
  card.addEventListener("dragover", e => { e.preventDefault(); card.style.background = "#E8F5F3"; });
  card.addEventListener("dragleave", () => { card.style.background = ""; });
  card.addEventListener("drop", e => {
    e.preventDefault();
    card.style.background = "";
    const file = e.dataTransfer.files[0];
    if (file) handleFile(slot, file);
  });
}

function openPicker(slot) {
  _activeSlot = slot;
  const inp = document.getElementById("file-input-hidden");
  inp.click();
}

function removeSlot(slot) {
  setUpload(slot, null);
  renderAllSlots();
  if (_onUploadChange) _onUploadChange();
}

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_SIZE = 10 * 1024 * 1024;

function handleFile(slot, file) {
  // Client-side validation
  if (!ALLOWED_TYPES.includes(file.type)) {
    setUpload(slot, { status: "error", error: "Only JPG, PNG, WEBP accepted." });
    renderAllSlots();
    if (_onUploadChange) _onUploadChange();
    return;
  }
  if (file.size > MAX_SIZE) {
    setUpload(slot, { status: "error", error: `File too large (max 10 MB).` });
    renderAllSlots();
    if (_onUploadChange) _onUploadChange();
    return;
  }

  // Preview + mark ready (actual upload happens at "Check my order")
  const reader = new FileReader();
  reader.onload = ev => {
    setUpload(slot, {
      file,
      preview: ev.target.result,
      name: file.name,
      size: file.size,
      status: "ready",
    });
    renderAllSlots();
    if (_onUploadChange) _onUploadChange();
  };
  reader.readAsDataURL(file);
}

export function getFiles() {
  const state = getState();
  return {
    1: state.uploads[1]?.file || null,
    2: state.uploads[2]?.file || null,
    3: state.uploads[3]?.file || null,
  };
}
