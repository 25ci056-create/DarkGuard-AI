/** auth.js – login/register page logic */
import { register, login, forgotPw, getMe } from "./api.js";

// ── Redirect if already logged in ────────────────────────────────────────────
getMe().then(res => {
  if (res.ok) window.location.href = "/app";
});

// ── Tab switching ─────────────────────────────────────────────────────────────
const tabs = document.querySelectorAll(".auth-tab");
const panels = document.querySelectorAll(".auth-panel");

function switchTab(tabId) {
  tabs.forEach(t => {
    const sel = t.dataset.tab === tabId;
    t.setAttribute("aria-selected", sel);
  });
  panels.forEach(p => {
    const active = p.id === `panel-${tabId}`;
    p.classList.toggle("active", active);
    if (active) p.querySelector("input")?.focus();
  });
}

tabs.forEach(t => {
  t.addEventListener("click", () => switchTab(t.dataset.tab));
  // Arrow-key support
  t.addEventListener("keydown", e => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      const all = [...tabs];
      const idx = all.indexOf(t);
      const next = e.key === "ArrowRight" ? (idx + 1) % all.length : (idx - 1 + all.length) % all.length;
      all[next].click();
      all[next].focus();
    }
  });
});

// ── Password show/hide ────────────────────────────────────────────────────────
document.querySelectorAll(".auth-toggle-pw").forEach(btn => {
  btn.addEventListener("click", () => {
    const inp = document.getElementById(btn.dataset.target);
    const show = inp.type === "password";
    inp.type = show ? "text" : "password";
    btn.textContent = show ? "Hide" : "Show";
    btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
});

// ── Password strength ─────────────────────────────────────────────────────────
const regPw = document.getElementById("reg-password");
const pwBar = document.getElementById("pw-strength-bar");
function pwStrength(pw) {
  if (!pw) return 0;
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}
regPw?.addEventListener("input", () => {
  const s = pwStrength(regPw.value);
  const widths = ["0%", "20%", "40%", "65%", "85%", "100%"];
  const colors = ["#EF4444", "#EF4444", "#F59E0B", "#F59E0B", "#10B981", "#10B981"];
  pwBar.style.width = widths[s] || "0%";
  pwBar.style.background = colors[s] || "#EF4444";
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = "") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast${type ? " " + type : ""}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ── Validation helpers ────────────────────────────────────────────────────────
function setErr(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}
function clearErrs(...ids) { ids.forEach(id => setErr(id, "")); }

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  const span = btn.querySelector(".btn-text");
  if (span) span.textContent = loading ? "Please wait…" : btn.dataset.originalText || span.textContent;
}

// ── Sign in ───────────────────────────────────────────────────────────────────
const signinForm = document.getElementById("signin-form");
const signinSubmit = document.getElementById("signin-submit");
signinSubmit.dataset.originalText = "Sign in";

signinForm.addEventListener("submit", async e => {
  e.preventDefault();
  clearErrs("signin-email-err", "signin-pw-err", "signin-form-err");

  const email = document.getElementById("signin-email").value.trim();
  const password = document.getElementById("signin-password").value;
  const remember = document.getElementById("signin-remember").checked;

  let valid = true;
  if (!validateEmail(email)) { setErr("signin-email-err", "Please enter a valid email."); valid = false; }
  if (!password) { setErr("signin-pw-err", "Password is required."); valid = false; }
  if (!valid) return;

  setLoading(signinSubmit, true);
  const res = await login({ email, password, remember_me: remember });
  setLoading(signinSubmit, false);

  if (res.ok) {
    window.location.href = "/app";
  } else {
    setErr("signin-form-err", res.error || "Sign in failed.");
  }
});

// ── Register ──────────────────────────────────────────────────────────────────
const regForm = document.getElementById("register-form");
const regSubmit = document.getElementById("register-submit");
regSubmit.dataset.originalText = "Create account";

regForm.addEventListener("submit", async e => {
  e.preventDefault();
  clearErrs("reg-name-err", "reg-email-err", "reg-pw-err", "reg-confirm-err", "reg-terms-err", "reg-form-err");

  const full_name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const confirm_password = document.getElementById("reg-confirm").value;
  const terms = document.getElementById("reg-terms").checked;

  let valid = true;
  if (!full_name) { setErr("reg-name-err", "Full name is required."); valid = false; }
  if (!validateEmail(email)) { setErr("reg-email-err", "Please enter a valid email."); valid = false; }
  if (password.length < 8) { setErr("reg-pw-err", "Password must be at least 8 characters."); valid = false; }
  if (password !== confirm_password) { setErr("reg-confirm-err", "Passwords do not match."); valid = false; }
  if (!terms) { setErr("reg-terms-err", "You must agree to the terms."); valid = false; }
  if (!valid) return;

  setLoading(regSubmit, true);
  const res = await register({ full_name, email, password, confirm_password });
  setLoading(regSubmit, false);

  if (res.ok) {
    window.location.href = "/app";
  } else {
    setErr("reg-form-err", res.error || "Registration failed.");
  }
});

// ── Forgot password ───────────────────────────────────────────────────────────
document.getElementById("forgot-pw-btn").addEventListener("click", async () => {
  const email = document.getElementById("signin-email").value.trim();
  if (!validateEmail(email)) {
    setErr("signin-email-err", "Enter your email address first.");
    return;
  }
  const res = await forgotPw(email);
  if (res.ok) {
    showToast(res.message || "Reset link sent if that email exists.", "success");
  } else {
    showToast(res.error || "Something went wrong.", "error");
  }
});

// ── Social buttons – show "not configured" message ────────────────────────────
["google-signin-btn", "google-register-btn", "apple-signin-btn", "apple-register-btn"].forEach(id => {
  const btn = document.getElementById(id);
  if (btn) {
    // Check health to see if configured
    btn.addEventListener("click", () => {
      if (btn.disabled) {
        showToast(
          btn.id.includes("google")
            ? "Google sign-in isn't configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env."
            : "Apple sign-in isn't configured yet. Add Apple credentials to .env.",
          "error"
        );
      }
    });
    // Remove disabled if actually configured (checked via health endpoint)
  }
});

// Check health to enable social buttons if configured
fetch("/api/health").then(r => r.json()).then(h => {
  if (h.google?.configured) {
    ["google-signin-btn", "google-register-btn"].forEach(id => {
      const b = document.getElementById(id);
      if (b) { b.disabled = false; b.title = ""; }
    });
  }
  if (h.apple?.configured) {
    ["apple-signin-btn", "apple-register-btn"].forEach(id => {
      const b = document.getElementById(id);
      if (b) { b.disabled = false; b.title = ""; }
    });
  }
}).catch(() => {});
