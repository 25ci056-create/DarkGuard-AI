/** store.js – single source of truth for app state */

const _state = {
  user: null,
  currentStep: 1,
  platform: null,
  platformOther: "",
  uploads: { 1: null, 2: null, 3: null }, // {file, preview, name, size, status}
  auditId: null,
  auditResult: null,
};

const _listeners = new Set();

export function getState() { return { ..._state }; }

export function setState(patch) {
  Object.assign(_state, patch);
  _listeners.forEach(fn => fn({ ..._state }));
}

export function subscribe(fn) {
  _listeners.add(fn);
  return () => _listeners.delete(fn);
}

export function setUpload(slot, data) {
  _state.uploads = { ..._state.uploads, [slot]: data };
  _listeners.forEach(fn => fn({ ..._state }));
}

export function allUploadsReady() {
  return [1, 2, 3].every(s => _state.uploads[s]?.status === "ready");
}
