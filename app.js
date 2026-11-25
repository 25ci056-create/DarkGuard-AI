/** app.js – main app shell: stepper, navigation, analysis flow */
import { getMe, logout, createAudit, getAuditStatus, getAudit, api } from "./api.js";
import { getState, setState, subscribe, allUploadsReady } from "./store.js";
import { initUploadSlots, getFiles } from "./upload.js";
import { renderReport, renderReportSkeleton } from "./report.js";

// ── Auth guard ────────────────────────────────────────────────────────────────
const meRes = await getMe();
if (!meRes.ok) {
  window.location.href = "/login";
}

// ── User info ─────────────────────────────────────────────────────────────────
setState({ user: meRes.user });
const avatarEl = document.getElementById("user-avatar");
const emailEl  = document.getElementById("user-email");
if (meRes.user) {
  const initials = (meRes.user.full_name || meRes.user.email || "U")
    .split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  avatarEl.textContent = initials;
  emailEl.textContent = meRes.user.email || "";
  emailEl.setAttribute("aria-label", `Signed in as ${meRes.user.email}`);
}

document.getElementById("logout-btn").addEventListener("click", async () => {
  await logout();
  window.location.href = "/login";
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = "") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast${type ? " " + type : ""}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 5000);
}

// ── Step navigation ───────────────────────────────────────────────────────────
let currentStep = 1;

function goToStep(step) {
  currentStep = step;
  setState({ currentStep: step });

  document.querySelectorAll(".step-view").forEach((el, i) => {
    el.classList.toggle("active", i + 1 === step);
  });

  // Desktop stepper
  [1, 2, 3].forEach(s => {
    const el = document.getElementById(`stepper-${s}`);
    if (!el) return;
    el.className = "stepper-step" + (s === step ? " active" : s < step ? " done" : "");
    el.setAttribute("aria-current", s === step ? "step" : "false");
  });

  updateButtons();
}

function updateButtons() {
  const backBtn     = document.getElementById("back-btn");
  const continueBtn = document.getElementById("continue-btn");
  const state       = getState();

  backBtn.style.display = currentStep > 1 ? "" : "none";

  if (currentStep === 1) {
    continueBtn.style.display = "";
    const otherMissing = state.platform === "other" && !state.platformOther;
    continueBtn.disabled = !state.platform || otherMissing;
    continueBtn.textContent = "Continue";
  } else if (currentStep === 2) {
    continueBtn.style.display = "";
    document.getElementById("upload-grid").style.display = "";
    document.querySelector(".upload-privacy").style.display = "";
    document.getElementById("analysis-screen").style.display = "none";
    continueBtn.disabled = !allUploadsReady();
    continueBtn.textContent = "Check my order";
  } else {
    continueBtn.style.display = "none";
  }
}

document.getElementById("back-btn").addEventListener("click", () => {
  if (currentStep > 1) goToStep(currentStep - 1);
});

document.getElementById("continue-btn").addEventListener("click", async () => {
  if (currentStep === 1) {
    goToStep(2);
  } else if (currentStep === 2) {
    await startAnalysis();
  }
});

// ── Step 1: Marketplace ───────────────────────────────────────────────────────
const marketplaceGrid = document.getElementById("marketplace-grid");
const otherWrap       = document.getElementById("other-input-wrap");
const otherInput      = document.getElementById("other-app-name");

marketplaceGrid.addEventListener("click", e => {
  const card = e.target.closest(".marketplace-card");
  if (!card) return;
  const platform = card.dataset.platform;

  document.querySelectorAll(".marketplace-card").forEach(c => {
    const sel = c === card;
    c.classList.toggle("selected", sel);
    c.setAttribute("aria-checked", sel);
  });

  setState({ platform });
  otherWrap.classList.toggle("visible", platform === "other");
  if (platform !== "other") setState({ platformOther: "" });
  updateButtons();
});

otherInput.addEventListener("input", () => {
  setState({ platformOther: otherInput.value.trim() });
  updateButtons();
});

// ── Step 2: Uploads ───────────────────────────────────────────────────────────
initUploadSlots(updateButtons);

// ── Analysis ──────────────────────────────────────────────────────────────────
async function startAnalysis() {
  const state = getState();

  // Show analysis loading
  document.getElementById("upload-grid").style.display = "none";
  document.querySelector(".upload-privacy").style.display = "none";
  document.getElementById("analysis-screen").style.display = "flex";
  document.getElementById("bottom-bar").style.display = "none";

  const form = new FormData();
  form.append("platform", state.platform);
  if (state.platform === "other") {
    form.append("platform_other", state.platformOther);
  }
  const files = getFiles();
  for (const slot of [1, 2, 3]) {
    if (files[slot]) form.append(`image_${slot}`, files[slot]);
  }

  const createRes = await createAudit(form);
  if (!createRes.ok) {
    showToast(createRes.error || "Failed to start analysis.", "error");
    // Restore upload UI
    document.getElementById("upload-grid").style.display = "";
    document.querySelector(".upload-privacy").style.display = "";
    document.getElementById("analysis-screen").style.display = "none";
    document.getElementById("bottom-bar").style.display = "";
    return;
  }

  const auditId = createRes.audit_id;
  setState({ auditId });

  // Poll status
  const stageMap = {
    reading_text:      "stage-reading",
    comparing_prices:  "stage-comparing",
    checking_patterns: "stage-checking",
    building_report:   "stage-building",
  };
  const stageLabel = document.getElementById("analysis-stage-label");

  let done = false;
  while (!done) {
    await sleep(1500);
    const statusRes = await getAuditStatus(auditId);
    if (!statusRes.ok) break;
    stageLabel.textContent = statusRes.label || "Analysing…";
    // Highlight current stage
    Object.entries(stageMap).forEach(([key, id]) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = "analysis-stage-item" + (key === statusRes.status ? " active" : statusRes.done || isAfter(key, statusRes.status) ? " done" : "");
    });
    if (statusRes.done) done = true;
  }

  // Load full audit result
  const auditRes = await getAudit(auditId);
  if (!auditRes.ok || auditRes.audit.status !== "done") {
    showToast("Analysis failed. Please try again.", "error");
    document.getElementById("upload-grid").style.display = "";
    document.querySelector(".upload-privacy").style.display = "";
    document.getElementById("analysis-screen").style.display = "none";
    document.getElementById("bottom-bar").style.display = "";
    return;
  }

  setState({ auditResult: auditRes.audit });
  renderReportSkeleton();
  goToStep(3);

  // Render after a brief animation frame
  setTimeout(() => {
    renderReport(auditRes.audit);
    wireReportButtons(auditId, auditRes.audit);
  }, 200);

  // Restore bottom bar visibility (hidden on step 3)
  document.getElementById("bottom-bar").style.display = "";
  document.getElementById("continue-btn").style.display = "none";
}

function isAfter(stage, current) {
  const order = ["pending", "reading_text", "comparing_prices", "checking_patterns", "building_report", "done"];
  return order.indexOf(stage) < order.indexOf(current);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Report buttons ────────────────────────────────────────────────────────────
function wireReportButtons(auditId, audit) {
  document.getElementById("download-pdf-btn").addEventListener("click", () => {
    window.open(`/api/audits/${auditId}/complaint.pdf`, "_blank");
  });

  document.getElementById("download-pdf-btn").addEventListener("contextmenu", () => {});

  // TXT download (secondary)
  const actionsDiv = document.getElementById("report-actions");
  const txtBtn = document.createElement("button");
  txtBtn.type = "button";
  txtBtn.className = "btn-secondary";
  txtBtn.textContent = "⬇ Download .TXT";
  txtBtn.addEventListener("click", () => {
    window.open(`/api/audits/${auditId}/complaint.txt`, "_blank");
  });
  actionsDiv.insertBefore(txtBtn, actionsDiv.children[1]);

  // Share
  document.getElementById("share-btn").addEventListener("click", async () => {
    const platform = audit.platform_other || audit.platform || "app";
    const score = audit.result?.trust_score?.score ?? "N/A";
    const shareData = {
      title: "DarkGuard AI Report",
      text: `I audited ${platform} on DarkGuard AI. Trust Score: ${score}/10. Check if your favorite apps use dark patterns.`,
      url: window.location.href,
    };
    if (navigator.share) {
      try { await navigator.share(shareData); return; } catch {}
    }
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(`${shareData.text}\n${shareData.url}`);
      showToast("Copied to clipboard!", "success");
    } catch {
      showToast("Share not available. Use the download buttons.", "");
    }
  });

  // New audit
  document.getElementById("new-audit-btn").addEventListener("click", () => {
    window.location.reload();
  });

  // Delete my data
  document.getElementById("delete-data-btn")?.addEventListener("click", async () => {
    const res = await api.delete(`/api/audits/${auditId}/delete-data`);
    if (res.ok) {
      showToast("Audit data deleted.", "success");
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(res.error || "Failed to delete data.", "error");
    }
  });
}

// ── Keyboard: marketplace arrow keys ─────────────────────────────────────────
marketplaceGrid.addEventListener("keydown", e => {
  const cards = [...document.querySelectorAll(".marketplace-card")];
  const focused = document.activeElement;
  const idx = cards.indexOf(focused);
  if (idx === -1) return;
  let next;
  if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); next = (idx + 1) % cards.length; }
  if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); next = (idx - 1 + cards.length) % cards.length; }
  if (next !== undefined) cards[next].focus();
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); focused.click(); }
});

// Init
goToStep(1);
