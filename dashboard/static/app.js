/* Shared utilities */
const $ = id => document.getElementById(id);
const setHtml = (id, html) => { const el = $(id); if (el) el.innerHTML = html; };
const setText = (id, text) => { const el = $(id); if (el) el.textContent = text; };

function esc(value) {
  return String(value).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* Money with enough precision that a fraction of a cent stays visible. */
function usd(value, empty = 'no successes') {
  if (value === null || value === undefined) return empty;
  const n = Number(value);
  return '$' + (Math.abs(n) >= 1 ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : n.toFixed(6));
}

function statCard(value, label, note, tone) {
  return `<div class="card stat"><div class="stat-value ${tone || ''}">${esc(value)}</div>
    <div class="stat-label">${esc(label)}</div><div class="text-muted small">${esc(note || '')}</div></div>`;
}

function fetchJson(url, options) {
  return fetch(url, options).then(r => r.json().then(body => ({ ok: r.ok, body })));
}

const COMPONENTS = ['model', 'runtime', 'observability', 'control', 'human_review', 'remediation'];

function breakdownTable(costs) {
  return `<table><thead><tr><th>Component</th><th>USD</th></tr></thead><tbody>${
    COMPONENTS.map(c => `<tr><td>${c.replace('_', ' ')}</td><td class="num">${usd(costs[c])}</td></tr>`).join('')
  }</tbody></table>`;
}
