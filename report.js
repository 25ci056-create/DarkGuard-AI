/** report.js – render the report card (Step 3) */
import { getState } from "./store.js";

const STATUS_CLASS = { FOUND: "found", WARNING: "warning", CLEAR: "clear" };
const STATUS_ICON  = { FOUND: "✗",    WARNING: "⚠",        CLEAR:  "✓"   };
const STATUS_LABEL = { FOUND: "FOUND", WARNING: "WARNING",  CLEAR: "CLEAR" };

export function renderReport(audit) {
  const result = audit.result || {};
  const ts = result.trust_score || {};
  const patterns = result.patterns || [];
  const platform = audit.platform_other || audit.platform || "Unknown";
  const isSimulated = audit.is_simulated;

  // Eyebrow
  document.getElementById("report-eyebrow").textContent =
    `REPORT CARD · ${platform.toUpperCase()}`;

  // AI badge
  const badgeWrap = document.getElementById("ai-badge-wrap");
  badgeWrap.innerHTML = `
    <div class="ai-badge${isSimulated ? " simulated" : ""}" role="status">
      ${isSimulated
        ? "⚠ SIMULATED DEMO RESULTS: AI not configured"
        : "✦ AI analysis"}
    </div>`;

  // Trust ring
  const score = ts.score ?? 0;
  const circumference = 100;
  const offset = circumference - (score / 10) * circumference;
  const ringFill = document.getElementById("trust-ring-fill");
  ringFill.setAttribute("stroke-dashoffset", offset);
  ringFill.setAttribute("class", `trust-ring-fill ${score >= 8 ? "high" : score >= 5 ? "medium" : "low"}`);
  document.getElementById("trust-ring-label").textContent = `${score}/10`;

  // Label & summary
  document.getElementById("trust-label").textContent = ts.label || "";
  document.getElementById("trust-summary").textContent =
    isSimulated
      ? "Simulated demo results – configure AI for real analysis."
      : `${ts.found_count || 0} suspicious pattern${ts.found_count !== 1 ? "s" : ""} detected.`;

  // Count pills
  const countsEl = document.getElementById("trust-counts");
  countsEl.innerHTML = "";
  if (ts.found_count > 0) {
    countsEl.innerHTML += `<span class="trust-count-pill found">${ts.found_count} FOUND</span>`;
  }
  if (ts.warning_count > 0) {
    countsEl.innerHTML += `<span class="trust-count-pill warning">${ts.warning_count} WARNING</span>`;
  }

  // Pattern cards
  const layout = document.getElementById("patterns-layout");
  layout.innerHTML = "";
  patterns.forEach(p => {
    layout.appendChild(buildPatternCard(p));
  });

  // Wire up score tooltip
  const btn = document.getElementById("score-info-btn");
  const tip = document.getElementById("score-tooltip");
  btn.addEventListener("click", () => {
    const show = tip.style.display === "none";
    tip.style.display = show ? "block" : "none";
    btn.setAttribute("aria-expanded", show);
  });
}

function buildPatternCard(p) {
  const status = p.status || "CLEAR";
  const cls = STATUS_CLASS[status] || "clear";
  const evidence = p.evidence || [];

  const card = document.createElement("div");
  card.className = "pattern-card";

  const header = document.createElement("div");
  header.className = "pattern-card-header";

  const name = document.createElement("div");
  name.className = "pattern-name";
  name.textContent = p.pattern_name || p.pattern_key || "";

  const badge = document.createElement("span");
  badge.className = `status-badge ${cls}`;
  badge.setAttribute("aria-label", STATUS_LABEL[status]);
  badge.innerHTML = `<span aria-hidden="true">${STATUS_ICON[status]}</span> ${STATUS_LABEL[status]}`;

  header.appendChild(name);
  header.appendChild(badge);

  const explanation = document.createElement("div");
  explanation.className = "pattern-explanation";
  explanation.textContent = p.explanation || "";

  // Evidence box
  const evBox = document.createElement("div");
  evBox.className = "evidence-box";
  if (evidence.length > 0) {
    const uploads = getState().uploads || {};
    evidence.forEach(ev => {
      const span = document.createElement("span");
      span.className = "evidence-highlight";
      span.textContent = ev.text
        ? `Screenshot ${ev.screenshot}: "${ev.text}"`
        : `Screenshot ${ev.screenshot}: see highlighted area`;
      evBox.appendChild(span);

      const preview = uploads[ev.screenshot]?.preview;
      if (preview) {
        const thumbWrap = document.createElement("button");
        thumbWrap.type = "button";
        thumbWrap.style.cssText = "margin-top:8px;display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid #E5E2D8;border-radius:8px;padding:6px 10px;cursor:pointer;font-size:0.75rem;color:#14594D;font-weight:500;";
        thumbWrap.setAttribute("aria-label", `View highlighted screenshot ${ev.screenshot}`);

        const img = document.createElement("img");
        img.src = preview;
        img.alt = `Screenshot ${ev.screenshot} thumbnail`;
        img.style.cssText = "width:36px;height:48px;object-fit:cover;border-radius:4px;border:2px solid #B91C1C;";

        const cap = document.createElement("span");
        cap.textContent = `View Screenshot ${ev.screenshot} (click to enlarge)`;

        thumbWrap.appendChild(img);
        thumbWrap.appendChild(cap);
        thumbWrap.addEventListener("click", () => openEvidenceModal(preview, `Screenshot ${ev.screenshot} – ${p.pattern_name || ""}`));
        evBox.appendChild(thumbWrap);
      }
    });
  } else {
    evBox.textContent = status === "CLEAR" ? "No evidence of this pattern." : "No specific text evidence extracted.";
  }

  const rule = document.createElement("div");
  rule.className = "pattern-rule";
  rule.textContent = `Rule: ${p.ccpa_reference || "CCPA Dark Patterns Guidelines, 2023"}`;

  card.appendChild(header);
  card.appendChild(explanation);
  card.appendChild(evBox);
  card.appendChild(rule);

  return card;
}

export function renderReportSkeleton() {
  const layout = document.getElementById("patterns-layout");
  layout.innerHTML = "";
  for (let i = 0; i < 5; i++) {
    const card = document.createElement("div");
    card.className = "pattern-card";
    card.innerHTML = `
      <div class="skeleton" style="height:20px;width:60%;margin-bottom:12px;"></div>
      <div class="skeleton" style="height:14px;width:100%;margin-bottom:6px;"></div>
      <div class="skeleton" style="height:14px;width:80%;margin-bottom:16px;"></div>
      <div class="skeleton" style="height:48px;width:100%;margin-bottom:8px;"></div>
      <div class="skeleton" style="height:12px;width:50%;"></div>`;
    layout.appendChild(card);
  }
}

function openEvidenceModal(src, title) {
  const modal = document.getElementById("evidence-modal");
  const img = document.getElementById("evidence-modal-img");
  const titleEl = document.getElementById("evidence-modal-title");
  if (!modal || !img) return;
  img.src = src;
  if (titleEl) titleEl.textContent = title;
  modal.style.display = "flex";
}

const closeBtn = document.getElementById("evidence-modal-close");
const modalEl = document.getElementById("evidence-modal");
closeBtn?.addEventListener("click", () => { if (modalEl) modalEl.style.display = "none"; });
modalEl?.addEventListener("click", e => { if (e.target === modalEl) modalEl.style.display = "none"; });
