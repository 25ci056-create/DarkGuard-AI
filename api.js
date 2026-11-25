/** api.js – thin fetch wrapper for DarkGuard AI backend */

const BASE = "";

async function _request(method, path, body, isMultipart = false) {
  const opts = {
    method,
    credentials: "include",
    headers: {},
  };
  if (body && !isMultipart) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  } else if (body && isMultipart) {
    opts.body = body; // FormData
  }
  const res = await fetch(BASE + path, opts);
  const json = await res.json().catch(() => ({ ok: false, error: "Unexpected server response." }));
  if (!res.ok && !json.error) json.error = `Server error ${res.status}`;
  return json;
}

export const api = {
  get:    (path)         => _request("GET",    path),
  post:   (path, body)   => _request("POST",   path, body),
  delete: (path)         => _request("DELETE", path),
  upload: (path, form)   => _request("POST",   path, form, true),
};

export async function getHealth() { return api.get("/api/health"); }
export async function getMe()     { return api.get("/api/auth/me"); }
export async function logout()    { return api.post("/api/auth/logout"); }

export async function register(data)  { return api.post("/api/auth/register", data); }
export async function login(data)     { return api.post("/api/auth/login",    data); }
export async function forgotPw(email) { return api.post("/api/auth/forgot-password", { email }); }

export async function createAudit(form) { return api.upload("/api/audits", form); }
export async function getAuditStatus(id) { return api.get(`/api/audits/${id}/status`); }
export async function getAudit(id)       { return api.get(`/api/audits/${id}`); }
